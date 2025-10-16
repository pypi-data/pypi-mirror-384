"""
Rate limiting and query complexity analysis for Django GraphQL Auto-Generation.

This module provides comprehensive rate limiting, query depth analysis,
and complexity scoring to prevent abuse and resource exhaustion.
"""

import hashlib
import logging
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple

import graphene
from django.conf import settings
from django.core.cache import cache
from graphql import GraphQLError
from graphql.execution import ExecutionResult
from graphql.language import ast

# Import des nouvelles exceptions personnalisées
from ..core.exceptions import QueryComplexityError, QueryDepthError, RateLimitError

logger = logging.getLogger(__name__)


class RateLimiter:
    """Limiteur de taux pour les requêtes GraphQL."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 3600,
                 cache_prefix: str = "graphql_rate_limit"):
        """
        Initialise le limiteur de taux.

        Args:
            max_requests: Nombre maximum de requêtes par fenêtre
            window_seconds: Taille de la fenêtre en secondes
            cache_prefix: Préfixe pour les clés de cache
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.cache_prefix = cache_prefix

    def is_allowed(self, identifier: str) -> Tuple[bool, int]:
        """
        Vérifie si une requête est autorisée.

        Args:
            identifier: Identifiant unique (IP, user_id, etc.)

        Returns:
            Tuple (autorisé, temps_avant_reset)
        """
        cache_key = f"{self.cache_prefix}:{identifier}"
        current_time = int(time.time())
        window_start = current_time - self.window_seconds

        # Récupération des requêtes dans la fenêtre actuelle
        requests = cache.get(cache_key, [])

        # Filtrage des requêtes dans la fenêtre
        requests = [req_time for req_time in requests if req_time > window_start]

        # Vérification de la limite
        if len(requests) >= self.max_requests:
            # Calcul du temps avant le prochain reset
            oldest_request = min(requests) if requests else current_time
            retry_after = oldest_request + self.window_seconds - current_time
            return False, max(0, retry_after)

        # Ajout de la requête actuelle
        requests.append(current_time)

        # Sauvegarde dans le cache
        cache.set(cache_key, requests, self.window_seconds + 60)

        return True, 0

    def check_rate_limit(self, identifier: str) -> Tuple[bool, int]:
        """
        Vérifie si l'identifiant a dépassé la limite de taux.

        Args:
            identifier: Identifiant unique (IP, utilisateur, etc.)

        Returns:
            Tuple[bool, int]: (est_autorisé, temps_restant_en_secondes)
        """
        return self.is_allowed(identifier)

    def get_remaining_requests(self, identifier: str) -> int:
        """Retourne le nombre de requêtes restantes."""
        cache_key = f"{self.cache_prefix}:{identifier}"
        current_time = int(time.time())
        window_start = current_time - self.window_seconds

        requests = cache.get(cache_key, [])
        requests = [req_time for req_time in requests if req_time > window_start]

        return max(0, self.max_requests - len(requests))


class QueryComplexityAnalyzer:
    """Analyseur de complexité des requêtes GraphQL."""

    def __init__(self, max_complexity: int = 1000):
        """
        Initialise l'analyseur de complexité.

        Args:
            max_complexity: Complexité maximale autorisée
        """
        self.max_complexity = max_complexity
        self.field_complexity: Dict[str, int] = {}
        self.type_complexity: Dict[str, int] = {}

    def set_field_complexity(self, field_name: str, complexity: int):
        """
        Définit la complexité d'un champ.

        Args:
            field_name: Nom du champ
            complexity: Score de complexité
        """
        self.field_complexity[field_name] = complexity
        logger.info(f"Complexité définie pour le champ {field_name}: {complexity}")

    def set_type_complexity(self, type_name: str, complexity: int):
        """
        Définit la complexité d'un type.

        Args:
            type_name: Nom du type
            complexity: Score de complexité
        """
        self.type_complexity[type_name] = complexity
        logger.info(f"Complexité définie pour le type {type_name}: {complexity}")

    def analyze_query(self, query_ast) -> int:
        """
        Analyse la complexité d'une requête.

        Args:
            query_ast: AST de la requête GraphQL

        Returns:
            Score de complexité total
        """
        total_complexity = 0

        for definition in query_ast.definitions:
            if hasattr(definition, 'operation') and definition.operation == 'query':
                total_complexity += self._analyze_selection_set(definition.selection_set)

        return total_complexity

    def analyze_complexity(self, query_ast) -> int:
        """
        Analyse la complexité d'une requête GraphQL.

        Args:
            query_ast: AST de la requête GraphQL

        Returns:
            int: Score de complexité de la requête
        """
        return self.analyze_query(query_ast)

    def _analyze_selection_set(self, selection_set,
                               multiplier: int = 1) -> int:
        """Analyse récursive d'un ensemble de sélections."""
        complexity = 0

        for selection in selection_set.selections:
            if isinstance(selection, ast.Field):
                field_complexity = self._get_field_complexity(selection.name.value)

                # Gestion des arguments (pagination, filtres)
                args_multiplier = self._calculate_args_multiplier(selection.arguments)

                # Complexité du champ
                complexity += field_complexity * multiplier * args_multiplier

                # Analyse récursive des sous-champs
                if selection.selection_set:
                    complexity += self._analyze_selection_set(
                        selection.selection_set,
                        multiplier * args_multiplier
                    )

            elif isinstance(selection, ast.InlineFragment):
                if selection.selection_set:
                    complexity += self._analyze_selection_set(
                        selection.selection_set, multiplier
                    )

            elif isinstance(selection, ast.FragmentSpread):
                # Pour les fragments nommés, on applique une complexité de base
                complexity += 10 * multiplier

        return complexity

    def _get_field_complexity(self, field_name: str) -> int:
        """Retourne la complexité d'un champ."""
        # Complexité personnalisée
        if field_name in self.field_complexity:
            return self.field_complexity[field_name]

        # Complexité par défaut basée sur le nom du champ
        if field_name.endswith('_set') or field_name.endswith('s'):
            return 10  # Champs de liste
        elif field_name in ['id', 'pk']:
            return 1   # Champs simples
        else:
            return 5   # Champs normaux

    def _calculate_args_multiplier(self, arguments) -> int:
        """Calcule le multiplicateur basé sur les arguments."""
        multiplier = 1

        for arg in arguments:
            if arg.name.value in ['first', 'last', 'limit']:
                # Arguments de pagination
                if isinstance(arg.value, ast.IntValue):
                    limit = int(arg.value.value)
                    multiplier = max(multiplier, min(limit, 100))  # Cap à 100

            elif arg.name.value in ['offset', 'skip']:
                # Arguments d'offset (moins coûteux)
                multiplier = max(multiplier, 2)

        return multiplier


class QueryDepthAnalyzer:
    """Analyseur de profondeur des requêtes GraphQL."""

    def __init__(self, max_depth: int = 10):
        """
        Initialise l'analyseur de profondeur.

        Args:
            max_depth: Profondeur maximale autorisée
        """
        self.max_depth = max_depth

    def analyze_query(self, query_ast) -> int:
        """
        Analyse la profondeur d'une requête.

        Args:
            query_ast: AST de la requête GraphQL

        Returns:
            Profondeur maximale de la requête
        """
        max_depth = 0

        for definition in query_ast.definitions:
            if hasattr(definition, 'operation') and definition.operation == 'query':
                depth = self._analyze_selection_set(definition.selection_set, 1)
                max_depth = max(max_depth, depth)

        return max_depth

    def _analyze_selection_set(self, selection_set,
                               current_depth: int) -> int:
        """Analyse récursive de la profondeur."""
        max_depth = current_depth

        for selection in selection_set.selections:
            if isinstance(selection, ast.Field):
                if selection.selection_set:
                    depth = self._analyze_selection_set(
                        selection.selection_set, current_depth + 1
                    )
                    max_depth = max(max_depth, depth)

            elif isinstance(selection, ast.InlineFragment):
                if selection.selection_set:
                    depth = self._analyze_selection_set(
                        selection.selection_set, current_depth
                    )
                    max_depth = max(max_depth, depth)

        return max_depth


class GraphQLSecurityMiddleware:
    """Middleware de sécurité pour GraphQL."""

    def __init__(self,
                 rate_limiter: RateLimiter = None,
                 complexity_analyzer: QueryComplexityAnalyzer = None,
                 depth_analyzer: QueryDepthAnalyzer = None):
        """
        Initialise le middleware de sécurité.

        Args:
            rate_limiter: Limiteur de taux
            complexity_analyzer: Analyseur de complexité
            depth_analyzer: Analyseur de profondeur
        """
        self.rate_limiter = rate_limiter or RateLimiter()
        self.complexity_analyzer = complexity_analyzer or QueryComplexityAnalyzer()
        self.depth_analyzer = depth_analyzer or QueryDepthAnalyzer()

    def process_request(self, request, query_ast):
        """
        Traite une requête avant exécution.

        Args:
            request: Requête HTTP Django
            query_ast: AST de la requête GraphQL

        Raises:
            RateLimitExceeded: Si la limite de taux est dépassée
            QueryComplexityExceeded: Si la complexité est trop élevée
            QueryDepthExceeded: Si la profondeur est trop élevée
        """
        # Identification de l'utilisateur
        identifier = self._get_user_identifier(request)

        # Vérification du rate limiting
        allowed, retry_after = self.rate_limiter.is_allowed(identifier)
        if not allowed:
            logger.warning(f"Rate limit dépassé pour {identifier}")
            raise RateLimitError(
                "Trop de requêtes. Veuillez réessayer plus tard.",
                retry_after
            )

        # Analyse de la complexité
        complexity = self.complexity_analyzer.analyze_query(query_ast)
        if complexity > self.complexity_analyzer.max_complexity:
            logger.warning(f"Complexité trop élevée: {complexity}")
            raise QueryComplexityError(
                f"Requête trop complexe (score: {complexity})",
                complexity,
                self.complexity_analyzer.max_complexity
            )

        # Analyse de la profondeur
        depth = self.depth_analyzer.analyze_query(query_ast)
        if depth > self.depth_analyzer.max_depth:
            logger.warning(f"Profondeur trop élevée: {depth}")
            raise QueryDepthError(
                f"Requête trop profonde (profondeur: {depth})",
                depth,
                self.depth_analyzer.max_depth
            )

        # Log des métriques
        logger.info(f"Requête autorisée - Complexité: {complexity}, Profondeur: {depth}")

    def _get_user_identifier(self, request) -> str:
        """Obtient un identifiant unique pour l'utilisateur."""
        # Priorité à l'utilisateur authentifié
        if hasattr(request, 'user') and request.user.is_authenticated:
            return f"user:{request.user.id}"

        # Sinon, utilisation de l'IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')

        return f"ip:{ip}"


class QueryMetrics:
    """Collecteur de métriques pour les requêtes GraphQL."""

    def __init__(self):
        self.metrics: Dict[str, List[Dict]] = defaultdict(list)
        self.max_entries = 1000  # Limite pour éviter la surcharge mémoire

    def record_query(self, identifier: str, complexity: int, depth: int,
                     execution_time: float, success: bool):
        """
        Enregistre les métriques d'une requête.

        Args:
            identifier: Identifiant de l'utilisateur
            complexity: Complexité de la requête
            depth: Profondeur de la requête
            execution_time: Temps d'exécution en secondes
            success: Succès de l'exécution
        """
        metric = {
            'timestamp': datetime.now(),
            'complexity': complexity,
            'depth': depth,
            'execution_time': execution_time,
            'success': success
        }

        # Limitation du nombre d'entrées
        if len(self.metrics[identifier]) >= self.max_entries:
            self.metrics[identifier].pop(0)

        self.metrics[identifier].append(metric)

    def get_user_stats(self, identifier: str, hours: int = 24) -> Dict[str, Any]:
        """
        Retourne les statistiques d'un utilisateur.

        Args:
            identifier: Identifiant de l'utilisateur
            hours: Nombre d'heures à analyser

        Returns:
            Dictionnaire des statistiques
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [
            m for m in self.metrics[identifier]
            if m['timestamp'] > cutoff_time
        ]

        if not recent_metrics:
            return {
                'total_queries': 0,
                'avg_complexity': 0,
                'avg_depth': 0,
                'avg_execution_time': 0,
                'success_rate': 0
            }

        total_queries = len(recent_metrics)
        successful_queries = sum(1 for m in recent_metrics if m['success'])

        return {
            'total_queries': total_queries,
            'avg_complexity': sum(m['complexity'] for m in recent_metrics) / total_queries,
            'avg_depth': sum(m['depth'] for m in recent_metrics) / total_queries,
            'avg_execution_time': sum(m['execution_time'] for m in recent_metrics) / total_queries,
            'success_rate': successful_queries / total_queries if total_queries > 0 else 0
        }


# Instances globales
default_rate_limiter = RateLimiter(
    max_requests=getattr(settings, 'GRAPHQL_RATE_LIMIT_REQUESTS', 100),
    window_seconds=getattr(settings, 'GRAPHQL_RATE_LIMIT_WINDOW', 3600)
)

default_complexity_analyzer = QueryComplexityAnalyzer(
    max_complexity=getattr(settings, 'GRAPHQL_MAX_COMPLEXITY', 1000)
)

default_depth_analyzer = QueryDepthAnalyzer(
    max_depth=getattr(settings, 'GRAPHQL_MAX_DEPTH', 10)
)

default_security_middleware = GraphQLSecurityMiddleware(
    rate_limiter=default_rate_limiter,
    complexity_analyzer=default_complexity_analyzer,
    depth_analyzer=default_depth_analyzer
)

query_metrics = QueryMetrics()


def rate_limit(max_requests: int = 100, window_seconds: int = 3600):
    """
    Décorateur pour limiter le taux des mutations.

    Args:
        max_requests: Nombre maximum de requêtes
        window_seconds: Fenêtre de temps en secondes
    """
    limiter = RateLimiter(max_requests, window_seconds)

    def decorator(func):
        @wraps(func)
        def wrapper(self, info, *args, **kwargs):
            request = info.context
            identifier = default_security_middleware._get_user_identifier(request)

            allowed, retry_after = limiter.is_allowed(identifier)
            if not allowed:
                raise RateLimitError(
                    f"Limite de {max_requests} requêtes par {window_seconds}s dépassée",
                    retry_after
                )

            return func(self, info, *args, **kwargs)
        return wrapper
    return decorator


class SecurityInfo(graphene.ObjectType):
    """Informations de sécurité pour un utilisateur."""

    remaining_requests = graphene.Int(description="Requêtes restantes")
    window_reset_time = graphene.Int(description="Temps avant reset en secondes")
    current_complexity_limit = graphene.Int(description="Limite de complexité actuelle")
    current_depth_limit = graphene.Int(description="Limite de profondeur actuelle")


class QueryStats(graphene.ObjectType):
    """Statistiques des requêtes d'un utilisateur."""

    total_queries = graphene.Int(description="Nombre total de requêtes")
    avg_complexity = graphene.Float(description="Complexité moyenne")
    avg_depth = graphene.Float(description="Profondeur moyenne")
    avg_execution_time = graphene.Float(description="Temps d'exécution moyen")
    success_rate = graphene.Float(description="Taux de succès")


class SecurityQuery(graphene.ObjectType):
    """Queries pour les informations de sécurité."""

    security_info = graphene.Field(
        SecurityInfo,
        description="Informations de sécurité pour l'utilisateur actuel"
    )

    query_stats = graphene.Field(
        QueryStats,
        hours=graphene.Int(default_value=24),
        description="Statistiques des requêtes"
    )

    def resolve_security_info(self, info):
        """Retourne les informations de sécurité."""
        request = info.context
        identifier = default_security_middleware._get_user_identifier(request)

        remaining = default_rate_limiter.get_remaining_requests(identifier)

        return SecurityInfo(
            remaining_requests=remaining,
            window_reset_time=default_rate_limiter.window_seconds,
            current_complexity_limit=default_complexity_analyzer.max_complexity,
            current_depth_limit=default_depth_analyzer.max_depth
        )

    def resolve_query_stats(self, info, hours: int = 24):
        """Retourne les statistiques des requêtes."""
        request = info.context
        identifier = default_security_middleware._get_user_identifier(request)

        stats = query_metrics.get_user_stats(identifier, hours)

        return QueryStats(
            total_queries=stats['total_queries'],
            avg_complexity=stats['avg_complexity'],
            avg_depth=stats['avg_depth'],
            avg_execution_time=stats['avg_execution_time'],
            success_rate=stats['success_rate']
        )

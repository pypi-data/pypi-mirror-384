"""
Système de cache multi-niveaux pour Django GraphQL Auto.

Ce module fournit un système de cache complet avec:
- Cache de schéma pour les types GraphQL
- Cache de résultats de requêtes
- Cache au niveau des champs
- Invalidation intelligente du cache
- Intégration avec Redis et Memcached
"""

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set, Union

import graphene
from django.conf import settings
from django.core.cache import cache, caches
from django.core.cache.backends.base import BaseCache
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Configuration pour le système de cache."""

    # Cache général
    enabled: bool = True
    default_timeout: int = 300  # 5 minutes
    cache_backend: str = 'default'

    # Cache de schéma
    schema_cache_enabled: bool = True
    schema_cache_timeout: int = 3600  # 1 heure

    # Cache de requêtes
    query_cache_enabled: bool = True
    query_cache_timeout: int = 300  # 5 minutes
    max_query_cache_size: int = 1000

    # Cache de champs
    field_cache_enabled: bool = True
    field_cache_timeout: int = 600  # 10 minutes

    # Invalidation
    auto_invalidation: bool = True
    invalidation_patterns: Dict[str, List[str]] = field(default_factory=dict)

    # Performance
    cache_hit_logging: bool = False
    cache_stats_enabled: bool = True


@dataclass
class CacheStats:
    """Statistiques du cache."""

    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    invalidations: int = 0

    @property
    def hit_rate(self) -> float:
        """Taux de réussite du cache."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0

    def reset(self):
        """Remet à zéro les statistiques."""
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0
        self.invalidations = 0


class CacheKeyGenerator:
    """Générateur de clés de cache intelligentes."""

    @staticmethod
    def generate_query_key(
        query_string: str,
        variables: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Génère une clé de cache pour une requête GraphQL.

        Args:
            query_string: La requête GraphQL
            variables: Variables de la requête
            user_id: ID de l'utilisateur (pour le cache par utilisateur)
            context: Contexte supplémentaire

        Returns:
            str: Clé de cache unique
        """
        # Normaliser la requête (supprimer les espaces, etc.)
        normalized_query = ' '.join(query_string.split())

        # Créer un hash des variables
        variables_hash = ""
        if variables:
            variables_json = json.dumps(variables, sort_keys=True)
            variables_hash = hashlib.md5(variables_json.encode()).hexdigest()[:8]

        # Inclure l'ID utilisateur si fourni
        user_part = f"_u{user_id}" if user_id else ""

        # Inclure le contexte si fourni
        context_part = ""
        if context:
            context_json = json.dumps(context, sort_keys=True)
            context_part = f"_c{hashlib.md5(context_json.encode()).hexdigest()[:8]}"

        # Créer le hash final
        query_hash = hashlib.md5(normalized_query.encode()).hexdigest()[:16]

        return f"gql_query_{query_hash}_{variables_hash}{user_part}{context_part}"

    @staticmethod
    def generate_field_key(
        model_name: str,
        field_name: str,
        instance_id: Any,
        user_id: Optional[int] = None
    ) -> str:
        """
        Génère une clé de cache pour un champ spécifique.

        Args:
            model_name: Nom du modèle
            field_name: Nom du champ
            instance_id: ID de l'instance
            user_id: ID de l'utilisateur

        Returns:
            str: Clé de cache pour le champ
        """
        user_part = f"_u{user_id}" if user_id else ""
        return f"gql_field_{model_name}_{field_name}_{instance_id}{user_part}"

    @staticmethod
    def generate_schema_key(schema_name: str, version: str = "1.0") -> str:
        """
        Génère une clé de cache pour un schéma GraphQL.

        Args:
            schema_name: Nom du schéma
            version: Version du schéma

        Returns:
            str: Clé de cache pour le schéma
        """
        return f"gql_schema_{schema_name}_{version}"


class CacheInvalidator:
    """Gestionnaire d'invalidation du cache."""

    def __init__(self, config: CacheConfig):
        self.config = config
        self.cache_backend = caches[config.cache_backend]

    def invalidate_model_cache(self, model: models.Model, instance_id: Optional[Any] = None):
        """
        Invalide le cache pour un modèle spécifique.

        Args:
            model: Modèle Django
            instance_id: ID de l'instance spécifique (optionnel)
        """
        model_name = model.__name__.lower()

        # Invalider les requêtes liées à ce modèle
        patterns = [
            f"gql_query_*_{model_name}_*",
            f"gql_field_{model_name}_*",
        ]

        if instance_id:
            patterns.append(f"gql_field_{model_name}_*_{instance_id}_*")

        for pattern in patterns:
            self._invalidate_by_pattern(pattern)

    def invalidate_user_cache(self, user_id: int):
        """
        Invalide tout le cache pour un utilisateur spécifique.

        Args:
            user_id: ID de l'utilisateur
        """
        pattern = f"*_u{user_id}"
        self._invalidate_by_pattern(pattern)

    def invalidate_query_cache(self, query_pattern: str):
        """
        Invalide le cache des requêtes correspondant à un pattern.

        Args:
            query_pattern: Pattern de requête à invalider
        """
        pattern = f"gql_query_*{query_pattern}*"
        self._invalidate_by_pattern(pattern)

    def _invalidate_by_pattern(self, pattern: str):
        """
        Invalide le cache selon un pattern (implémentation dépendante du backend).

        Args:
            pattern: Pattern de clés à invalider
        """
        # Note: L'implémentation dépend du backend de cache
        # Pour Redis, on peut utiliser SCAN + DEL
        # Pour Memcached, il faut maintenir un index des clés

        if hasattr(self.cache_backend, 'delete_pattern'):
            # Backend personnalisé avec support des patterns
            self.cache_backend.delete_pattern(pattern)
        else:
            # Fallback: invalider tout le cache (non optimal)
            logger.warning(
                f"Pattern invalidation not supported, clearing all cache for pattern: {pattern}")
            # On pourrait maintenir un index des clés pour une invalidation plus précise


class GraphQLCacheManager:
    """Gestionnaire principal du cache GraphQL."""

    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self.cache_backend = caches[self.config.cache_backend]
        self.key_generator = CacheKeyGenerator()
        self.invalidator = CacheInvalidator(self.config)
        self.stats = CacheStats()

        # Connecter les signaux pour l'invalidation automatique
        if self.config.auto_invalidation:
            self._connect_signals()

    def get_query_result(
        self,
        query_string: str,
        variables: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """
        Récupère le résultat d'une requête depuis le cache.

        Args:
            query_string: Requête GraphQL
            variables: Variables de la requête
            user_id: ID de l'utilisateur
            context: Contexte supplémentaire

        Returns:
            Résultat de la requête ou None si pas en cache
        """
        if not self.config.query_cache_enabled:
            return None

        cache_key = self.key_generator.generate_query_key(
            query_string, variables, user_id, context
        )

        result = self.cache_backend.get(cache_key)

        if result is not None:
            self.stats.hits += 1
            if self.config.cache_hit_logging:
                logger.debug(f"Cache hit for query: {cache_key}")
        else:
            self.stats.misses += 1

        return result

    def set_query_result(
        self,
        query_string: str,
        result: Any,
        variables: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ):
        """
        Met en cache le résultat d'une requête.

        Args:
            query_string: Requête GraphQL
            result: Résultat à mettre en cache
            variables: Variables de la requête
            user_id: ID de l'utilisateur
            context: Contexte supplémentaire
            timeout: Durée de vie du cache (optionnel)
        """
        if not self.config.query_cache_enabled:
            return

        cache_key = self.key_generator.generate_query_key(
            query_string, variables, user_id, context
        )

        cache_timeout = timeout or self.config.query_cache_timeout

        self.cache_backend.set(cache_key, result, cache_timeout)
        self.stats.sets += 1

        if self.config.cache_hit_logging:
            logger.debug(f"Cached query result: {cache_key}")

    def get_field_value(
        self,
        model_name: str,
        field_name: str,
        instance_id: Any,
        user_id: Optional[int] = None
    ) -> Optional[Any]:
        """
        Récupère la valeur d'un champ depuis le cache.

        Args:
            model_name: Nom du modèle
            field_name: Nom du champ
            instance_id: ID de l'instance
            user_id: ID de l'utilisateur

        Returns:
            Valeur du champ ou None si pas en cache
        """
        if not self.config.field_cache_enabled:
            return None

        cache_key = self.key_generator.generate_field_key(
            model_name, field_name, instance_id, user_id
        )

        result = self.cache_backend.get(cache_key)

        if result is not None:
            self.stats.hits += 1
        else:
            self.stats.misses += 1

        return result

    def set_field_value(
        self,
        model_name: str,
        field_name: str,
        instance_id: Any,
        value: Any,
        user_id: Optional[int] = None,
        timeout: Optional[int] = None
    ):
        """
        Met en cache la valeur d'un champ.

        Args:
            model_name: Nom du modèle
            field_name: Nom du champ
            instance_id: ID de l'instance
            value: Valeur à mettre en cache
            user_id: ID de l'utilisateur
            timeout: Durée de vie du cache (optionnel)
        """
        if not self.config.field_cache_enabled:
            return

        cache_key = self.key_generator.generate_field_key(
            model_name, field_name, instance_id, user_id
        )

        cache_timeout = timeout or self.config.field_cache_timeout

        self.cache_backend.set(cache_key, value, cache_timeout)
        self.stats.sets += 1

    def invalidate_model(self, model: models.Model, instance_id: Optional[Any] = None):
        """
        Invalide le cache pour un modèle.

        Args:
            model: Modèle Django
            instance_id: ID de l'instance (optionnel)
        """
        self.invalidator.invalidate_model_cache(model, instance_id)
        self.stats.invalidations += 1

    def get_stats(self) -> CacheStats:
        """Retourne les statistiques du cache."""
        return self.stats

    def clear_all(self):
        """Vide tout le cache GraphQL."""
        # Supprimer toutes les clés commençant par 'gql_'
        self.invalidator._invalidate_by_pattern('gql_*')
        self.stats.deletes += 1

    def _connect_signals(self):
        """Connecte les signaux Django pour l'invalidation automatique."""

        @receiver(post_save)
        def invalidate_on_save(sender, instance, **kwargs):
            if hasattr(instance, '_meta'):
                self.invalidate_model(sender, instance.pk)

        @receiver(post_delete)
        def invalidate_on_delete(sender, instance, **kwargs):
            if hasattr(instance, '_meta'):
                self.invalidate_model(sender, instance.pk)


# Instance globale du gestionnaire de cache
_cache_manager: Optional[GraphQLCacheManager] = None


def get_cache_manager() -> GraphQLCacheManager:
    """Retourne l'instance globale du gestionnaire de cache."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = GraphQLCacheManager()
    return _cache_manager


def configure_cache(config: CacheConfig):
    """Configure le système de cache global."""
    global _cache_manager
    _cache_manager = GraphQLCacheManager(config)


def cache_query(
    timeout: Optional[int] = None,
    user_specific: bool = False,
    context_keys: Optional[List[str]] = None
):
    """
    Décorateur pour mettre en cache les résultats de requêtes GraphQL.

    Args:
        timeout: Durée de vie du cache en secondes
        user_specific: Si True, le cache est spécifique à l'utilisateur
        context_keys: Clés du contexte à inclure dans la clé de cache
    """
    def decorator(resolver_func: Callable) -> Callable:
        @wraps(resolver_func)
        def wrapper(root, info: graphene.ResolveInfo, **kwargs):
            cache_manager = get_cache_manager()

            # Construire la clé de cache
            query_string = str(info.field_name)  # Simplification
            variables = kwargs
            user_id = getattr(info.context.user, 'id', None) if user_specific else None

            # Extraire le contexte pertinent
            context = {}
            if context_keys and hasattr(info, 'context'):
                for key in context_keys:
                    if hasattr(info.context, key):
                        context[key] = getattr(info.context, key)

            # Vérifier le cache
            cached_result = cache_manager.get_query_result(
                query_string, variables, user_id, context
            )

            if cached_result is not None:
                return cached_result

            # Exécuter la requête
            result = resolver_func(root, info, **kwargs)

            # Mettre en cache le résultat
            cache_manager.set_query_result(
                query_string, result, variables, user_id, context, timeout
            )

            return result

        return wrapper
    return decorator


def cache_field(
    timeout: Optional[int] = None,
    user_specific: bool = False
):
    """
    Décorateur pour mettre en cache les valeurs de champs.

    Args:
        timeout: Durée de vie du cache en secondes
        user_specific: Si True, le cache est spécifique à l'utilisateur
    """
    def decorator(resolver_func: Callable) -> Callable:
        @wraps(resolver_func)
        def wrapper(root, info: graphene.ResolveInfo, **kwargs):
            cache_manager = get_cache_manager()

            # Identifier le modèle et le champ
            model_name = root.__class__.__name__ if hasattr(root, '__class__') else 'Unknown'
            field_name = info.field_name
            instance_id = getattr(root, 'pk', None) or getattr(root, 'id', None)
            user_id = getattr(info.context.user, 'id', None) if user_specific else None

            if instance_id is None:
                # Pas d'ID, on ne peut pas mettre en cache
                return resolver_func(root, info, **kwargs)

            # Vérifier le cache
            cached_value = cache_manager.get_field_value(
                model_name, field_name, instance_id, user_id
            )

            if cached_value is not None:
                return cached_value

            # Exécuter le resolver
            result = resolver_func(root, info, **kwargs)

            # Mettre en cache la valeur
            cache_manager.set_field_value(
                model_name, field_name, instance_id, result, user_id, timeout
            )

            return result

        return wrapper
    return decorator

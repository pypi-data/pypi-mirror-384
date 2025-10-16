"""
Dedicated authentication middleware for Django GraphQL Auto-Generation.

This middleware provides consistent authentication processing for all GraphQL requests,
including JWT token validation, user context injection, and security logging.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union

from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

# Ensure middleware logs are visible during development
# If project LOGGING is not configured for this module, attach a console handler in DEBUG.
try:
    from django.conf import settings as _dj_settings  # reuse settings safely

    if getattr(_dj_settings, "DEBUG", False):
        logger.setLevel(logging.DEBUG)
        if not logger.handlers:
            _handler = logging.StreamHandler()
            _handler.setLevel(logging.DEBUG)
            _formatter = logging.Formatter(
                "%(levelname)s %(asctime)s %(name)s %(message)s"
            )
            _handler.setFormatter(_formatter)
            logger.addHandler(_handler)
except Exception:
    # Never fail app startup due to logging setup issues
    pass


class GraphQLAuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware pour l'authentification GraphQL avec support JWT.

    Ce middleware :
    - Valide les tokens JWT dans les requêtes GraphQL
    - Injecte l'utilisateur authentifié dans le contexte
    - Enregistre les événements d'authentification
    - Gère la limitation de débit pour les tentatives d'authentification
    """

    def __init__(self, get_response=None):
        """
        Initialise le middleware d'authentification.

        Args:
            get_response: Fonction de réponse Django
        """
        super().__init__(get_response)
        self.get_response = get_response

        # Configuration du middleware
        self.jwt_header_prefix = getattr(settings, "JWT_AUTH_HEADER_PREFIX", "Bearer")
        self.jwt_header_name = getattr(
            settings, "JWT_AUTH_HEADER_NAME", "HTTP_AUTHORIZATION"
        )
        self.enable_audit_logging = getattr(
            settings, "GRAPHQL_ENABLE_AUDIT_LOGGING", True
        )
        self.enable_rate_limiting = getattr(
            settings, "GRAPHQL_ENABLE_AUTH_RATE_LIMITING", True
        )

        # Mode debug - bypass authentication when DEBUG=True
        self.debug_mode = getattr(settings, "DEBUG", False)

        # Cache des utilisateurs pour optimiser les performances
        self.user_cache_timeout = getattr(
            settings, "JWT_USER_CACHE_TIMEOUT", 300
        )  # 5 minutes

    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """
        Traite la requête entrante pour l'authentification.

        Args:
            request: Requête HTTP Django

        Returns:
            None pour continuer le traitement, HttpResponse pour court-circuiter
        """
        # Ne traiter que les requêtes GraphQL
        if not self._is_graphql_request(request):
            return None

        # En mode debug, bypass l'authentification et créer un utilisateur de test
        if self.debug_mode:
            self._setup_debug_user(request)
            # Log at INFO to ensure visibility with default settings
            logger.info("Authentication bypassed for GraphQL request (DEBUG=True)")
            logger.debug("Debug mode: Authentication bypassed for GraphQL request")
            return None

        # Extraire et valider le token JWT
        token = self._extract_jwt_token(request)
        user = None
        auth_method = "anonymous"

        if token:
            user = self._authenticate_jwt_token(token, request)
            if user:
                auth_method = "jwt"
                self._log_authentication_event(request, user, "success", auth_method)
            else:
                self._log_authentication_event(request, None, "invalid_token", "jwt")

        # Injecter l'utilisateur dans le contexte de la requête
        request.user = user or AnonymousUser()
        request.auth_method = auth_method
        request.auth_timestamp = datetime.now(timezone.utc)

        return None

    def process_response(
        self, request: HttpRequest, response: HttpResponse
    ) -> HttpResponse:
        """
        Traite la réponse pour ajouter des headers de sécurité.

        Args:
            request: Requête HTTP Django
            response: Réponse HTTP Django

        Returns:
            Réponse HTTP modifiée
        """
        if self._is_graphql_request(request):
            # Ajouter des headers de sécurité
            response["X-Content-Type-Options"] = "nosniff"
            response["X-Frame-Options"] = "DENY"
            response["X-XSS-Protection"] = "1; mode=block"

            # Ajouter des informations d'authentification dans les headers (pour le debug)
            if hasattr(request, "auth_method"):
                response["X-Auth-Method"] = request.auth_method

        return response

    def _is_graphql_request(self, request: HttpRequest) -> bool:
        """
        Détermine si la requête est une requête GraphQL.

        Args:
            request: Requête HTTP Django

        Returns:
            True si c'est une requête GraphQL
        """
        # Vérifier l'URL
        graphql_endpoints = getattr(
            settings, "GRAPHQL_ENDPOINTS", ["/graphql/", "/graphql"]
        )
        if any(request.path.startswith(endpoint) for endpoint in graphql_endpoints):
            return True

        # Vérifier le Content-Type pour les requêtes POST
        content_type = request.content_type.lower()
        if "application/json" in content_type and request.method == "POST":
            # Vérifier si le body contient une query GraphQL
            try:
                import json

                if hasattr(request, "body"):
                    body = json.loads(request.body.decode("utf-8"))
                    return "query" in body or "mutation" in body
            except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
                pass

        return False

    def _extract_jwt_token(self, request: HttpRequest) -> Optional[str]:
        """
        Extrait le token JWT de la requête.

        Args:
            request: Requête HTTP Django

        Returns:
            Token JWT ou None si non trouvé
        """
        # Vérifier le header Authorization
        auth_header = request.META.get(self.jwt_header_name, "")
        if auth_header:
            header = auth_header.strip()
            lower = header.lower()
            prefix_lower = self.jwt_header_prefix.lower()
            if lower.startswith(f"{prefix_lower} "):
                parts = header.split(" ", 1)
                if len(parts) == 2 and parts[1]:
                    return parts[1]

        # Vérifier les cookies (optionnel)
        cookie_name = getattr(settings, "JWT_AUTH_COOKIE", None)
        if cookie_name:
            return request.COOKIES.get(cookie_name)

        # Vérifier les paramètres de requête (pour les WebSockets)
        # Vérifier les paramètres de requête (pour les WebSockets)
        return request.GET.get("token")

    def _authenticate_jwt_token(
        self, token: str, request: HttpRequest
    ) -> Optional[User]:
        """
        Authentifie un token JWT et retourne l'utilisateur.

        Args:
            token: Token JWT à valider
            request: Requête HTTP Django

        Returns:
            Instance User ou None si l'authentification échoue
        """
        try:
            # Vérifier le cache utilisateur d'abord
            cache_key = f"jwt_user_{hash(token)}"
            cached_user_id = cache.get(cache_key)

            if cached_user_id:
                try:
                    user = User.objects.get(id=cached_user_id)
                    if user.is_active:
                        return user
                except User.DoesNotExist:
                    cache.delete(cache_key)

            # Valider le token JWT
            from ..extensions.auth import JWTManager

            payload = JWTManager.verify_token(token)

            if not payload:
                return None

            # Récupérer l'utilisateur
            # Support standard JWT 'sub' claim as fallback
            user_id = payload.get("user_id") or payload.get("sub")
            if not user_id:
                return None

            user = User.objects.get(id=user_id)

            # Vérifier que l'utilisateur est actif
            if not user.is_active:
                self._log_authentication_event(request, user, "inactive_user", "jwt")
                return None

            # Mettre en cache l'utilisateur
            cache.set(cache_key, user.id, self.user_cache_timeout)

            return user

        except User.DoesNotExist:
            logger.warning(
                f"Utilisateur introuvable pour le token JWT: {payload.get('user_id') if 'payload' in locals() else 'unknown'}"
            )
            return None
        except Exception as e:
            logger.error(f"Erreur lors de l'authentification JWT: {e}")
            return None

    def _log_authentication_event(
        self,
        request: HttpRequest,
        user: Optional[User],
        event_type: str,
        auth_method: str,
    ) -> None:
        """
        Enregistre un événement d'authentification pour l'audit.

        Args:
            request: Requête HTTP Django
            user: Utilisateur concerné (peut être None)
            event_type: Type d'événement (success, failure, invalid_token, etc.)
            auth_method: Méthode d'authentification utilisée
        """
        if not self.enable_audit_logging:
            return

        try:
            # Utiliser le système d'audit complet
            from ..extensions.audit import audit_logger

            # Mapper les types d'événements vers le système d'audit
            if event_type == "success":
                audit_logger.log_login_attempt(request, user, success=True)
            elif event_type == "invalid_token":
                from ..extensions.audit import AuditEventType

                audit_logger.log_token_event(
                    request,
                    user,
                    AuditEventType.TOKEN_INVALID,
                    success=False,
                    error_message="Token JWT invalide",
                )
            elif event_type == "inactive_user":
                audit_logger.log_login_attempt(
                    request,
                    user,
                    success=False,
                    error_message="Compte utilisateur inactif",
                )
            else:
                # Fallback vers l'ancien système de logging
                self._legacy_log_authentication_event(
                    request, user, event_type, auth_method
                )

        except ImportError:
            # Fallback si le système d'audit n'est pas disponible
            self._legacy_log_authentication_event(
                request, user, event_type, auth_method
            )
        except Exception as e:
            logger.error(f"Erreur lors de l'audit d'authentification: {e}")
            # Fallback vers l'ancien système
            self._legacy_log_authentication_event(
                request, user, event_type, auth_method
            )

    def _legacy_log_authentication_event(
        self,
        request: HttpRequest,
        user: Optional[User],
        event_type: str,
        auth_method: str,
    ) -> None:
        """
        Système de logging d'authentification de fallback.

        Args:
            request: Requête HTTP Django
            user: Utilisateur concerné (peut être None)
            event_type: Type d'événement (success, failure, invalid_token, etc.)
            auth_method: Méthode d'authentification utilisée
        """
        # Informations de base sur la requête
        client_ip = self._get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "Unknown")

        # Créer l'entrée de log
        log_data = {
            "event_type": event_type,
            "auth_method": auth_method,
            "user_id": user.id if user else None,
            "username": user.username if user else None,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_path": request.path,
            "request_method": request.method,
        }

        # Logger selon le type d'événement
        if event_type == "success":
            logger.info(f"Authentification réussie: {log_data}")
        elif event_type in ["invalid_token", "inactive_user"]:
            logger.warning(f"Tentative d'authentification échouée: {log_data}")
        else:
            logger.error(f"Événement d'authentification: {log_data}")

        # Optionnel: Envoyer vers un système d'audit externe
        self._send_to_audit_system(log_data)

    def _get_client_ip(self, request: HttpRequest) -> str:
        """
        Récupère l'adresse IP du client en tenant compte des proxies.

        Args:
            request: Requête HTTP Django

        Returns:
            Adresse IP du client
        """
        # Vérifier les headers de proxy
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.META.get("HTTP_X_REAL_IP")
        if real_ip:
            return real_ip

        return request.META.get("REMOTE_ADDR", "Unknown")

    def _send_to_audit_system(self, log_data: Dict[str, Any]) -> None:
        """
        Envoie les données d'audit vers un système externe (optionnel).

        Args:
            log_data: Données d'audit à envoyer
        """
        # Cette méthode peut être étendue pour envoyer vers :
        # - Une base de données d'audit dédiée
        # - Un service de logging externe (Elasticsearch, Splunk, etc.)
        # - Un système SIEM
        # - Un webhook d'audit

        audit_webhook_url = getattr(settings, "AUDIT_WEBHOOK_URL", None)
        if audit_webhook_url:
            try:
                import requests

                requests.post(audit_webhook_url, json=log_data, timeout=5)
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi vers le système d'audit: {e}")

    def _setup_debug_user(self, request: HttpRequest) -> None:
        """
        Configure un utilisateur de debug pour les requêtes en mode debug.

        Args:
            request: Requête HTTP Django
        """
        try:
            # Essayer de récupérer ou créer un utilisateur de debug
            debug_user, created = User.objects.get_or_create(
                username="debug_user",
                defaults={
                    "email": "debug@example.com",
                    "first_name": "Debug",
                    "last_name": "User",
                    "is_active": True,
                    "is_staff": True,
                    "is_superuser": True,
                },
            )

            if created:
                logger.info("Debug user created for development mode")

            # Injecter l'utilisateur de debug dans le contexte
            request.user = debug_user
            request.auth_method = "debug"
            request.auth_timestamp = datetime.now(timezone.utc)

        except Exception as e:
            logger.warning(f"Could not create debug user, using AnonymousUser: {e}")
            # Fallback vers un utilisateur anonyme avec des permissions étendues
            request.user = AnonymousUser()
            request.auth_method = "debug_anonymous"
            request.auth_timestamp = datetime.now(timezone.utc)


class GraphQLRateLimitMiddleware(MiddlewareMixin):
    """
    Middleware de limitation de débit spécifique aux requêtes d'authentification GraphQL.

    Ce middleware protège contre les attaques par force brute en limitant :
    - Les tentatives de connexion par IP
    - Les tentatives de connexion par utilisateur
    - Les requêtes GraphQL par IP
    """

    def __init__(self, get_response=None):
        """
        Initialise le middleware de limitation de débit.

        Args:
            get_response: Fonction de réponse Django
        """
        super().__init__(get_response)
        self.get_response = get_response

        # Configuration de la limitation de débit
        self.login_attempts_limit = getattr(settings, "AUTH_LOGIN_ATTEMPTS_LIMIT", 5)
        self.login_attempts_window = getattr(
            settings, "AUTH_LOGIN_ATTEMPTS_WINDOW", 900
        )  # 15 minutes
        self.graphql_requests_limit = getattr(settings, "GRAPHQL_REQUESTS_LIMIT", 100)
        self.graphql_requests_window = getattr(
            settings, "GRAPHQL_REQUESTS_WINDOW", 3600
        )  # 1 heure

        # Mode debug - bypass rate limiting when DEBUG=True
        self.debug_mode = getattr(settings, "DEBUG", False)

    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """
        Vérifie les limites de débit avant de traiter la requête.

        Args:
            request: Requête HTTP Django

        Returns:
            HttpResponse avec erreur 429 si limite dépassée, None sinon
        """
        if not self._is_graphql_request(request):
            return None

        # En mode debug, bypass la limitation de débit
        if self.debug_mode:
            logger.info("Rate limiting bypassed for GraphQL request (DEBUG=True)")
            logger.debug("Debug mode: Rate limiting bypassed for GraphQL request")
            return None

        # Stocker la requête pour l'audit
        self._current_request = request

        client_ip = self._get_client_ip(request)

        # Vérifier la limite générale des requêtes GraphQL
        if self._is_rate_limited(
            f"graphql_requests_{client_ip}",
            self.graphql_requests_limit,
            self.graphql_requests_window,
        ):
            return self._create_rate_limit_response("Trop de requêtes GraphQL")

        # Vérifier spécifiquement les tentatives de connexion
        if self._is_login_request(request):
            if self._is_rate_limited(
                f"login_attempts_{client_ip}",
                self.login_attempts_limit,
                self.login_attempts_window,
            ):
                return self._create_rate_limit_response(
                    "Trop de tentatives de connexion"
                )

        return None

    def _is_graphql_request(self, request: HttpRequest) -> bool:
        """
        Détermine si la requête est une requête GraphQL.

        Args:
            request: Requête HTTP Django

        Returns:
            True si c'est une requête GraphQL
        """
        graphql_endpoints = getattr(
            settings, "GRAPHQL_ENDPOINTS", ["/graphql/", "/graphql"]
        )
        return any(request.path.startswith(endpoint) for endpoint in graphql_endpoints)

    def _is_login_request(self, request: HttpRequest) -> bool:
        """
        Détermine si la requête est une tentative de connexion.

        Args:
            request: Requête HTTP Django

        Returns:
            True si c'est une tentative de connexion
        """
        try:
            import json

            if hasattr(request, "body") and request.body:
                body = json.loads(request.body.decode("utf-8"))
                query = body.get("query", "")
                return (
                    "login" in query.lower()
                    or "mutation" in query.lower()
                    and "login" in query.lower()
                )
        except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
            pass
        return False

    def _is_rate_limited(self, cache_key: str, limit: int, window: int) -> bool:
        """
        Vérifie si une clé de cache a dépassé sa limite de débit.

        Args:
            cache_key: Clé de cache à vérifier
            limit: Limite de requêtes
            window: Fenêtre de temps en secondes

        Returns:
            True si la limite est dépassée
        """
        current_time = int(time.time())
        window_start = current_time - window

        # Récupérer les tentatives existantes
        attempts = cache.get(cache_key, [])

        # Filtrer les tentatives dans la fenêtre de temps
        recent_attempts = [attempt for attempt in attempts if attempt > window_start]

        # Vérifier la limite
        if len(recent_attempts) >= limit:
            return True

        # Ajouter la tentative actuelle
        recent_attempts.append(current_time)
        cache.set(cache_key, recent_attempts, window)

        return False

    def _get_client_ip(self, request: HttpRequest) -> str:
        """
        Récupère l'adresse IP du client.

        Args:
            request: Requête HTTP Django

        Returns:
            Adresse IP du client
        """
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "Unknown")

    def _create_rate_limit_response(self, message: str) -> HttpResponse:
        """
        Crée une réponse HTTP 429 pour la limitation de débit.

        Args:
            message: Message d'erreur

        Returns:
            HttpResponse avec statut 429
        """
        import json

        # Enregistrer l'événement de limitation de débit dans l'audit
        try:
            from django.http import HttpRequest

            from ..extensions.audit import audit_logger

            # Créer une requête factice pour l'audit si nécessaire
            if hasattr(self, "_current_request"):
                audit_logger.log_rate_limit_exceeded(
                    self._current_request, "GraphQL rate limit"
                )
        except Exception as e:
            logger.error(f"Erreur lors de l'audit de limitation de débit: {e}")

        response_data = {"errors": [{"message": message, "code": "RATE_LIMITED"}]}
        response = HttpResponse(
            json.dumps(response_data), content_type="application/json", status=429
        )
        response["Retry-After"] = "900"  # 15 minutes
        return response

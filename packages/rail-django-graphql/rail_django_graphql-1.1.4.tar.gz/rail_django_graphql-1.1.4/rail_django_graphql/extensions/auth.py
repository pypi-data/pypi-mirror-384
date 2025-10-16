"""
Authentication system for Django GraphQL Auto-Generation.

This module provides JWT-based authentication with built-in GraphQL mutations
for login, register, token refresh, and user management.
"""

import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

import graphene
import jwt
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from graphene_django import DjangoObjectType

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser

logger = logging.getLogger(__name__)

# User model will be retrieved dynamically when needed


def get_user_type():
    """Factory function to create UserType with proper model reference."""

    class UserType(DjangoObjectType):
        """GraphQL type for Django User model."""

        class Meta:
            model = get_user_model()
            fields = ('id', 'username', 'email', 'first_name', 'last_name',
                      'is_active', 'date_joined', 'last_login')

    return UserType


# Create a lazy reference that will be resolved when needed
_user_type = None


def UserType():
    """Lazy UserType that resolves the model when Django apps are ready."""
    global _user_type
    if _user_type is None:
        _user_type = get_user_type()
    return _user_type


class AuthPayload(graphene.ObjectType):
    """Payload returned by authentication mutations."""

    ok = graphene.Boolean(required=True, description="Indique si l'opération a réussi")
    user = graphene.Field(lambda: UserType(), description="Utilisateur authentifié")
    token = graphene.String(description="Token JWT d'authentification")
    refresh_token = graphene.String(description="Token de rafraîchissement")
    expires_at = graphene.DateTime(description="Date d'expiration du token")
    errors = graphene.List(graphene.String, required=True, description="Liste des erreurs")


class JWTManager:
    """Gestionnaire des tokens JWT pour l'authentification."""

    @staticmethod
    def get_jwt_secret() -> str:
        """Récupère la clé secrète JWT depuis les paramètres Django."""
        return getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY)

    @staticmethod
    def get_jwt_expiration() -> int:
        """Récupère la durée d'expiration du token en secondes.

        Supports non-expiring tokens when configured with 0 or None.
        Accepts either legacy `JWT_EXPIRATION_DELTA` or new
        `JWT_ACCESS_TOKEN_LIFETIME` setting (in seconds).
        """
        # Prefer explicit access token lifetime if present
        lifetime = getattr(settings, 'JWT_ACCESS_TOKEN_LIFETIME', None)
        if lifetime is None:
            lifetime = getattr(settings, 'JWT_EXPIRATION_DELTA', 3600 * 72)
        # Normalize types that might be timedelta
        if isinstance(lifetime, timedelta):
            lifetime_seconds = int(lifetime.total_seconds())
        else:
            lifetime_seconds = int(lifetime)
        return lifetime_seconds

    @staticmethod
    def get_refresh_expiration() -> int:
        """Récupère la durée d'expiration du refresh token en secondes.

        Accepts either legacy `JWT_REFRESH_EXPIRATION_DELTA` or new
        `JWT_REFRESH_TOKEN_LIFETIME` setting (in seconds).
        """
        lifetime = getattr(settings, 'JWT_REFRESH_TOKEN_LIFETIME', None)
        if lifetime is None:
            lifetime = getattr(settings, 'JWT_REFRESH_EXPIRATION_DELTA', 604800)
        if isinstance(lifetime, timedelta):
            lifetime_seconds = int(lifetime.total_seconds())
        else:
            lifetime_seconds = int(lifetime)
        return lifetime_seconds

    @classmethod
    def generate_token(cls, user: "AbstractUser") -> Dict[str, Any]:
        """
        Génère un token JWT pour l'utilisateur.

        Args:
            user: Instance de l'utilisateur Django

        Returns:
            Dict contenant le token, refresh_token et expires_at
        """
        now = timezone.now()
        access_lifetime = cls.get_jwt_expiration()
        refresh_lifetime = cls.get_refresh_expiration()
        # If access_lifetime is 0 or negative, treat as non-expiring (no 'exp')
        expiration = None if access_lifetime <= 0 else now + timedelta(seconds=access_lifetime)
        refresh_expiration = now + timedelta(seconds=refresh_lifetime)

        payload = {
            'user_id': user.id,
            'username': user.username,
            'iat': now,
            'type': 'access'
        }
        # Only include 'exp' if token should expire
        if expiration is not None:
            payload['exp'] = expiration

        refresh_payload = {
            'user_id': user.id,
            'exp': refresh_expiration,
            'iat': now,
            'type': 'refresh'
        }

        token = jwt.encode(payload, cls.get_jwt_secret(), algorithm='HS256')
        refresh_token = jwt.encode(refresh_payload, cls.get_jwt_secret(), algorithm='HS256')

        return {
            'token': token,
            'refresh_token': refresh_token,
            'expires_at': expiration
        }

    @classmethod
    def verify_token(cls, token: str) -> Optional[Dict[str, Any]]:
        """
        Vérifie et décode un token JWT.

        Args:
            token: Token JWT à vérifier

        Returns:
            Payload décodé ou None si le token est invalide
        """
        try:
            payload = jwt.decode(token, cls.get_jwt_secret(), algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token JWT expiré")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token JWT invalide: {e}")
            return None

    @classmethod
    def refresh_token(cls, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Rafraîchit un token d'accès à partir d'un refresh token.

        Args:
            refresh_token: Token de rafraîchissement

        Returns:
            Nouveau token d'accès ou None si le refresh token est invalide
        """
        payload = cls.verify_token(refresh_token)
        if not payload or payload.get('type') != 'refresh':
            return None

        try:
            User = get_user_model()
            user = User.objects.get(id=payload['user_id'])
            return cls.generate_token(user)
        except User.DoesNotExist:
            logger.warning(
                f"Utilisateur introuvable pour le refresh token: {payload.get('user_id')}")
            return None


class LoginMutation(graphene.Mutation):
    """Mutation de connexion utilisateur."""

    class Arguments:
        username = graphene.String(required=True, description="Nom d'utilisateur")
        password = graphene.String(required=True, description="Mot de passe")

    Output = AuthPayload

    def mutate(self, info, username: str, password: str):
        """
        Authentifie un utilisateur et retourne un token JWT.

        Args:
            username: Nom d'utilisateur
            password: Mot de passe

        Returns:
            AuthPayload avec le token et les informations utilisateur
        """
        try:
            # Authentification de l'utilisateur
            user = authenticate(username=username, password=password)

            if not user:
                return AuthPayload(
                    ok=False,
                    errors=["Nom d'utilisateur ou mot de passe incorrect"]
                )

            if not user.is_active:
                return AuthPayload(
                    ok=False,
                    errors=["Compte utilisateur désactivé"]
                )

            # Génération du token JWT
            token_data = JWTManager.generate_token(user)

            # Mise à jour de la dernière connexion
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])

            logger.info(f"Connexion réussie pour l'utilisateur: {username}")

            return AuthPayload(
                ok=True,
                user=user,
                token=token_data['token'],
                refresh_token=token_data['refresh_token'],
                expires_at=token_data['expires_at'],
                errors=[]
            )

        except Exception as e:
            logger.error(f"Erreur lors de la connexion: {e}")
            return AuthPayload(
                ok=False,
                errors=["Erreur interne lors de la connexion"]
            )


class RegisterMutation(graphene.Mutation):
    """Mutation d'inscription utilisateur."""

    class Arguments:
        username = graphene.String(required=True, description="Nom d'utilisateur")
        email = graphene.String(required=True, description="Adresse email")
        password = graphene.String(required=True, description="Mot de passe")
        first_name = graphene.String(description="Prénom")
        last_name = graphene.String(description="Nom de famille")

    Output = AuthPayload

    def mutate(self, info, username: str, email: str, password: str,
               first_name: str = "", last_name: str = ""):
        """
        Crée un nouvel utilisateur et retourne un token JWT.

        Args:
            username: Nom d'utilisateur
            email: Adresse email
            password: Mot de passe
            first_name: Prénom (optionnel)
            last_name: Nom de famille (optionnel)

        Returns:
            AuthPayload avec le token et les informations utilisateur
        """
        try:
            # Get the User model dynamically
            User = get_user_model()

            # Validation des données
            errors = []

            # Vérification de l'unicité du nom d'utilisateur
            if User.objects.filter(username=username).exists():
                errors.append("Ce nom d'utilisateur est déjà utilisé")

            # Vérification de l'unicité de l'email
            if User.objects.filter(email=email).exists():
                errors.append("Cette adresse email est déjà utilisée")

            # Validation du mot de passe
            try:
                validate_password(password)
            except ValidationError as e:
                errors.extend(e.messages)

            if errors:
                return AuthPayload(ok=False, errors=errors)

            # Création de l'utilisateur
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            # Génération du token JWT
            token_data = JWTManager.generate_token(user)

            logger.info(f"Inscription réussie pour l'utilisateur: {username}")

            return AuthPayload(
                ok=True,
                user=user,
                token=token_data['token'],
                refresh_token=token_data['refresh_token'],
                expires_at=token_data['expires_at'],
                errors=[]
            )

        except Exception as e:
            logger.error(f"Erreur lors de l'inscription: {e}")
            return AuthPayload(
                ok=False,
                errors=["Erreur interne lors de l'inscription"]
            )


class RefreshTokenMutation(graphene.Mutation):
    """Mutation de rafraîchissement de token."""

    class Arguments:
        refresh_token = graphene.String(required=True, description="Token de rafraîchissement")

    Output = AuthPayload

    def mutate(self, info, refresh_token: str):
        """
        Rafraîchit un token d'accès.

        Args:
            refresh_token: Token de rafraîchissement

        Returns:
            AuthPayload avec le nouveau token
        """
        try:
            token_data = JWTManager.refresh_token(refresh_token)

            if not token_data:
                return AuthPayload(
                    ok=False,
                    errors=["Token de rafraîchissement invalide ou expiré"]
                )

            # Récupération de l'utilisateur pour le retourner
            payload = JWTManager.verify_token(token_data['token'])
            User = get_user_model()
            user = User.objects.get(id=payload['user_id'])

            return AuthPayload(
                ok=True,
                user=user,
                token=token_data['token'],
                refresh_token=token_data['refresh_token'],
                expires_at=token_data['expires_at'],
                errors=[]
            )

        except Exception as e:
            logger.error(f"Erreur lors du rafraîchissement du token: {e}")
            return AuthPayload(
                ok=False,
                errors=["Erreur interne lors du rafraîchissement du token"]
            )


class LogoutMutation(graphene.Mutation):
    """Mutation de déconnexion utilisateur."""

    class Arguments:
        pass  # Pas d'arguments nécessaires, on utilise le token dans le contexte

    ok = graphene.Boolean(required=True)
    errors = graphene.List(graphene.String, required=True)

    def mutate(self, info):
        """
        Déconnecte l'utilisateur (côté client principalement).

        Note: Avec JWT, la déconnexion est principalement côté client.
        Cette mutation peut être étendue pour maintenir une blacklist de tokens.
        """
        try:
            # Pour l'instant, on retourne simplement un succès
            # Dans une implémentation plus avancée, on pourrait :
            # - Ajouter le token à une blacklist
            # - Invalider tous les tokens de l'utilisateur
            # - Logger la déconnexion

            return LogoutMutation(ok=True, errors=[])

        except Exception as e:
            logger.error(f"Erreur lors de la déconnexion: {e}")
            return LogoutMutation(
                ok=False,
                errors=["Erreur interne lors de la déconnexion"]
            )


class MeQuery(graphene.ObjectType):
    """Query pour récupérer les informations de l'utilisateur connecté."""

    me = graphene.Field(lambda: UserType(), description="Informations de l'utilisateur connecté")

    def resolve_me(self, info):
        """
        Retourne les informations de l'utilisateur connecté.

        Returns:
            User instance ou None si non authentifié
        """
        user = info.context.user
        if user and user.is_authenticated:
            return user
        return None


class AuthMutations(graphene.ObjectType):
    """Mutations d'authentification disponibles."""

    login = LoginMutation.Field(description="Connexion utilisateur")
    register = RegisterMutation.Field(description="Inscription utilisateur")
    refresh_token = RefreshTokenMutation.Field(description="Rafraîchissement du token")
    logout = LogoutMutation.Field(description="Déconnexion utilisateur")


def get_user_from_token(token: str) -> Optional["AbstractUser"]:
    """
    Récupère un utilisateur à partir d'un token JWT.

    Args:
        token: Token JWT

    Returns:
        Instance User ou None si le token est invalide
    """
    payload = JWTManager.verify_token(token)
    if not payload:
        return None

    try:
        User = get_user_model()
        return User.objects.get(id=payload['user_id'])
    except User.DoesNotExist:
        return None


def authenticate_request(info) -> Optional["AbstractUser"]:
    """
    Authentifie une requête GraphQL à partir du token dans les headers.

    Args:
        info: Contexte GraphQL

    Returns:
        Instance User ou None si non authentifié
    """
    request = info.context

    # Récupération du token depuis les headers
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth_header.startswith('Bearer '):
        return None

    token = auth_header.split(' ')[1]
    return get_user_from_token(token)

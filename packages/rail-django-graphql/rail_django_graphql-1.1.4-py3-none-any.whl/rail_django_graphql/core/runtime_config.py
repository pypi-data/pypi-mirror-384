"""
Runtime configuration management for Django GraphQL Auto-Generation.

This module provides functionality to update configuration at runtime
without requiring server restarts.
"""

import json
import logging
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from django.conf import settings
from django.core.cache import cache
from django.core.signals import request_started
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@dataclass
class ConfigurationChange:
    """
    Représente un changement de configuration.

    Attributes:
        key: Clé de configuration modifiée
        old_value: Ancienne valeur
        new_value: Nouvelle valeur
        timestamp: Horodatage du changement
        user: Utilisateur ayant effectué le changement
        reason: Raison du changement
    """

    key: str
    old_value: Any
    new_value: Any
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    user: Optional[str] = None
    reason: Optional[str] = None


class RuntimeConfigManager:
    """
    Gestionnaire de configuration runtime avec support pour les mises à jour
    dynamiques et les callbacks de notification.
    """

    def __init__(self):
        self._config_cache: Dict[str, Any] = {}
        self._change_callbacks: Dict[str, List[Callable]] = {}
        self._change_history: List[ConfigurationChange] = []
        self._lock = threading.RLock()
        self._cache_prefix = "runtime_config:"
        self._cache_timeout = 600  # 10 minutes
        self._max_history_size = 1000
        self._load_initial_config()

    def _load_initial_config(self) -> None:
        """Charge la configuration initiale depuis les settings Django."""
        try:
            # Charger la configuration rail_django_graphql
            graphql_config = getattr(settings, "rail_django_graphql", {})
            self._config_cache.update(graphql_config)

            # Charger d'autres configurations pertinentes
            runtime_config = getattr(settings, "RUNTIME_CONFIG", {})
            self._config_cache.update(runtime_config)

            logger.info(
                f"Configuration initiale chargée: {len(self._config_cache)} paramètres"
            )

        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration initiale: {e}")

    def get_config(self, key: str, default: Any = None, use_cache: bool = True) -> Any:
        """
        Récupère une valeur de configuration.

        Args:
            key: Clé de configuration (support des clés imbriquées avec '.')
            default: Valeur par défaut si la clé n'existe pas
            use_cache: Utiliser le cache Redis si disponible

        Returns:
            Valeur de configuration ou valeur par défaut
        """
        if use_cache:
            cache_key = f"{self._cache_prefix}{key}"
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

        with self._lock:
            # Support des clés imbriquées (ex: "mutation_settings.nested_relations")
            keys = key.split(".")
            value = self._config_cache

            try:
                for k in keys:
                    if isinstance(value, dict):
                        value = value[k]
                    else:
                        return default

                # Mettre en cache si demandé
                if use_cache:
                    cache_key = f"{self._cache_prefix}{key}"
                    cache.set(cache_key, value, self._cache_timeout)

                return value

            except (KeyError, TypeError):
                return default

    def set_config(
        self,
        key: str,
        value: Any,
        user: Optional[str] = None,
        reason: Optional[str] = None,
        persist: bool = False,
    ) -> bool:
        """
        Met à jour une valeur de configuration.

        Args:
            key: Clé de configuration
            value: Nouvelle valeur
            user: Utilisateur effectuant le changement
            reason: Raison du changement
            persist: Sauvegarder dans un fichier de configuration

        Returns:
            True si la mise à jour a réussi
        """
        try:
            with self._lock:
                old_value = self.get_config(key, use_cache=False)

                # Mettre à jour la configuration
                keys = key.split(".")
                config_ref = self._config_cache

                # Naviguer jusqu'au parent de la clé finale
                for k in keys[:-1]:
                    if k not in config_ref:
                        config_ref[k] = {}
                    config_ref = config_ref[k]

                # Mettre à jour la valeur finale
                config_ref[keys[-1]] = value

                # Invalider le cache
                cache_key = f"{self._cache_prefix}{key}"
                cache.delete(cache_key)

                # Enregistrer le changement
                change = ConfigurationChange(
                    key=key,
                    old_value=old_value,
                    new_value=value,
                    user=user,
                    reason=reason,
                )
                self._add_change_to_history(change)

                # Notifier les callbacks
                self._notify_change_callbacks(key, old_value, value)

                # Persister si demandé
                if persist:
                    self._persist_config_change(key, value)

                logger.info(
                    f"Configuration mise à jour: {key} = {value} (par {user or 'système'})"
                )
                return True

        except Exception as e:
            logger.error(
                f"Erreur lors de la mise à jour de la configuration {key}: {e}"
            )
            return False

    def reload_config(self, config_source: Optional[str] = None) -> bool:
        """
        Recharge la configuration depuis la source.

        Args:
            config_source: Source spécifique à recharger (optionnel)

        Returns:
            True si le rechargement a réussi
        """
        try:
            with self._lock:
                old_config = self._config_cache.copy()

                # Recharger depuis les settings Django
                self._load_initial_config()

                # Recharger depuis un fichier spécifique si spécifié
                if config_source and Path(config_source).exists():
                    with open(config_source, "r", encoding="utf-8") as f:
                        file_config = json.load(f)
                        self._config_cache.update(file_config)

                # Vider le cache
                self._clear_config_cache()

                # Notifier les changements
                self._notify_config_reload(old_config, self._config_cache)

                logger.info("Configuration rechargée avec succès")
                return True

        except Exception as e:
            logger.error(f"Erreur lors du rechargement de la configuration: {e}")
            return False

    def register_change_callback(
        self, key: str, callback: Callable[[str, Any, Any], None]
    ) -> None:
        """
        Enregistre un callback pour les changements de configuration.

        Args:
            key: Clé de configuration à surveiller
            callback: Fonction appelée lors des changements (key, old_value, new_value)
        """
        with self._lock:
            if key not in self._change_callbacks:
                self._change_callbacks[key] = []
            self._change_callbacks[key].append(callback)

        logger.debug(f"Callback enregistré pour la clé: {key}")

    def unregister_change_callback(self, key: str, callback: Callable) -> None:
        """
        Désenregistre un callback de changement.

        Args:
            key: Clé de configuration
            callback: Fonction callback à supprimer
        """
        with self._lock:
            if key in self._change_callbacks:
                try:
                    self._change_callbacks[key].remove(callback)
                    if not self._change_callbacks[key]:
                        del self._change_callbacks[key]
                except ValueError:
                    pass

    def get_change_history(
        self, key: Optional[str] = None, limit: int = 100
    ) -> List[ConfigurationChange]:
        """
        Récupère l'historique des changements de configuration.

        Args:
            key: Clé spécifique (optionnel)
            limit: Nombre maximum d'entrées à retourner

        Returns:
            Liste des changements de configuration
        """
        with self._lock:
            history = self._change_history

            if key:
                history = [change for change in history if change.key == key]

            return history[-limit:] if limit else history

    def export_config(self, keys: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Exporte la configuration actuelle.

        Args:
            keys: Clés spécifiques à exporter (optionnel)

        Returns:
            Dictionnaire de configuration
        """
        with self._lock:
            if keys:
                exported = {}
                for key in keys:
                    value = self.get_config(key, use_cache=False)
                    if value is not None:
                        exported[key] = value
                return exported
            else:
                return self._config_cache.copy()

    def import_config(
        self,
        config: Dict[str, Any],
        user: Optional[str] = None,
        reason: str = "Configuration import",
    ) -> bool:
        """
        Importe une configuration.

        Args:
            config: Dictionnaire de configuration à importer
            user: Utilisateur effectuant l'import
            reason: Raison de l'import

        Returns:
            True si l'import a réussi
        """
        try:
            success_count = 0
            for key, value in config.items():
                if self.set_config(key, value, user, reason):
                    success_count += 1

            logger.info(
                f"Configuration importée: {success_count}/{len(config)} paramètres"
            )
            return success_count == len(config)

        except Exception as e:
            logger.error(f"Erreur lors de l'import de configuration: {e}")
            return False

    def validate_config(
        self, config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[str]]:
        """
        Valide la configuration actuelle ou fournie.

        Args:
            config: Configuration à valider (optionnel, utilise la config actuelle sinon)

        Returns:
            Dictionnaire des erreurs de validation par clé
        """
        validation_errors = {}
        config_to_validate = config or self._config_cache

        try:
            # Validation des types de base
            for key, value in config_to_validate.items():
                errors = []

                # Validation spécifique pour rail_django_graphql
                if key == "mutation_settings" and isinstance(value, dict):
                    if "nested_relations_config" in value:
                        nested_config = value["nested_relations_config"]
                        if not isinstance(nested_config, dict):
                            errors.append(
                                "nested_relations_config doit être un dictionnaire"
                            )
                        else:
                            for model, enabled in nested_config.items():
                                if not isinstance(enabled, bool):
                                    errors.append(
                                        f"nested_relations_config.{model} doit être un booléen"
                                    )

                if errors:
                    validation_errors[key] = errors

            return validation_errors

        except Exception as e:
            logger.error(f"Erreur lors de la validation de configuration: {e}")
            return {"validation_error": [str(e)]}

    def _add_change_to_history(self, change: ConfigurationChange) -> None:
        """Ajoute un changement à l'historique."""
        self._change_history.append(change)

        # Limiter la taille de l'historique
        if len(self._change_history) > self._max_history_size:
            self._change_history = self._change_history[-self._max_history_size :]

    def _notify_change_callbacks(
        self, key: str, old_value: Any, new_value: Any
    ) -> None:
        """Notifie les callbacks de changement."""
        callbacks = self._change_callbacks.get(key, [])
        for callback in callbacks:
            try:
                callback(key, old_value, new_value)
            except Exception as e:
                logger.error(f"Erreur dans le callback pour {key}: {e}")

    def _notify_config_reload(
        self, old_config: Dict[str, Any], new_config: Dict[str, Any]
    ) -> None:
        """Notifie les callbacks lors d'un rechargement complet."""
        all_keys = set(old_config.keys()) | set(new_config.keys())

        for key in all_keys:
            old_value = old_config.get(key)
            new_value = new_config.get(key)

            if old_value != new_value:
                self._notify_change_callbacks(key, old_value, new_value)

    def _clear_config_cache(self) -> None:
        """Vide le cache de configuration."""
        try:
            # Vider le cache Redis pour toutes les clés de configuration
            cache_pattern = f"{self._cache_prefix}*"
            # Note: Cette implémentation dépend du backend de cache utilisé
            cache.clear()  # Méthode simple, peut être optimisée
        except Exception as e:
            logger.warning(f"Impossible de vider le cache de configuration: {e}")

    def _persist_config_change(self, key: str, value: Any) -> None:
        """Persiste un changement de configuration dans un fichier."""
        try:
            config_file = getattr(
                settings, "RUNTIME_CONFIG_FILE", "runtime_config.json"
            )
            config_path = Path(config_file)

            # Charger la configuration existante
            existing_config = {}
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    existing_config = json.load(f)

            # Mettre à jour avec la nouvelle valeur
            keys = key.split(".")
            config_ref = existing_config
            for k in keys[:-1]:
                if k not in config_ref:
                    config_ref[k] = {}
                config_ref = config_ref[k]
            config_ref[keys[-1]] = value

            # Sauvegarder
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(existing_config, f, indent=2, ensure_ascii=False)

            logger.debug(f"Configuration persistée: {key}")

        except Exception as e:
            logger.error(f"Erreur lors de la persistance de {key}: {e}")


# Instance globale du gestionnaire de configuration runtime
runtime_config = RuntimeConfigManager()


# Fonctions utilitaires
def get_runtime_config(key: str, default: Any = None) -> Any:
    """
    Fonction utilitaire pour récupérer une configuration runtime.

    Args:
        key: Clé de configuration
        default: Valeur par défaut

    Returns:
        Valeur de configuration
    """
    return runtime_config.get_config(key, default)


def set_runtime_config(
    key: str,
    value: Any,
    user: Optional[str] = None,
    reason: Optional[str] = None,
    persist: bool = False,
) -> bool:
    """
    Fonction utilitaire pour mettre à jour une configuration runtime.

    Args:
        key: Clé de configuration
        value: Nouvelle valeur
        user: Utilisateur
        reason: Raison du changement
        persist: Persister le changement

    Returns:
        True si la mise à jour a réussi
    """
    return runtime_config.set_config(key, value, user, reason, persist)


def reload_runtime_config(config_source: Optional[str] = None) -> bool:
    """
    Fonction utilitaire pour recharger la configuration runtime.

    Args:
        config_source: Source de configuration

    Returns:
        True si le rechargement a réussi
    """
    return runtime_config.reload_config(config_source)


# Signal handler pour recharger la configuration au démarrage des requêtes
@receiver(request_started)
def check_config_updates(sender, **kwargs):
    """Vérifie les mises à jour de configuration au début de chaque requête."""
    # Cette fonction peut être utilisée pour vérifier périodiquement
    # les mises à jour de configuration depuis une source externe
    pass

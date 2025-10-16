"""
Django app configuration for rail-django-graphql library.

This module configures:
- Django application for automatic GraphQL schema generation
- Signal and hook configuration
- Core component initialization
- Library settings validation
"""

import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class RailDjangoGraphQLConfig(AppConfig):
    """Django app configuration for rail-django-graphql library."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rail_django_graphql'
    verbose_name = 'Rail Django GraphQL'
    label = 'rail_django_graphql'

    def ready(self):
        """Initialize the application after Django has loaded."""
        try:
            # Setup performance monitoring if enabled
            self._setup_performance_monitoring()

            # Setup Django signals
            self._setup_signals()

            # Validate library configuration
            self._validate_configuration()

            # Initialize schema registry
            self._initialize_schema_registry()

            # Invalidate metadata cache on startup
            self._invalidate_cache_on_startup()

            logger.info("Rail Django GraphQL library initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing Rail Django GraphQL library: {e}")
            # Don't raise in production to avoid breaking the app
            if self._is_debug_mode():
                raise

    def _setup_performance_monitoring(self):
        """Setup performance monitoring if enabled."""
        try:
            from .conf import settings
            if settings.MONITORING_SETTINGS.get('ENABLE_METRICS', False):
                from .middleware.performance import setup_performance_monitoring
                setup_performance_monitoring()
                logger.debug("Performance monitoring setup completed")
        except ImportError as e:
            logger.warning(f"Could not setup performance monitoring: {e}")
        except Exception as e:
            logger.error(f"Error setting up performance monitoring: {e}")

    def _setup_signals(self):
        """Configure Django signals for automatic schema generation."""
        try:
            from .conf import settings
            if settings.SCHEMA_REGISTRY.get('ENABLE_AUTO_DISCOVERY', True):
                # Import signals to register them
                from . import signals  # This will be created later
                logger.debug("Django signals setup completed")
        except ImportError as e:
            logger.debug(f"Signals module not found, skipping: {e}")
        except Exception as e:
            logger.warning(f"Could not setup signals: {e}")

    def _validate_configuration(self):
        """Validate library configuration."""
        try:
            from .conf import validate_configuration
            validate_configuration()
            logger.debug("Configuration validation completed")
        except Exception as e:
            logger.warning(f"Configuration validation failed: {e}")
            if self._is_debug_mode():
                raise

    def _initialize_schema_registry(self):
        """Initialize the schema registry."""
        try:
            from .conf import settings
            if settings.SCHEMA_REGISTRY.get('ENABLE_AUTO_DISCOVERY', True):
                from .core.registry import schema_registry
                schema_registry.discover_schemas()
                logger.debug("Schema registry initialization completed")
        except ImportError as e:
            logger.debug(f"Schema registry not available: {e}")
        except Exception as e:
            logger.warning(f"Could not initialize schema registry: {e}")

    def _is_debug_mode(self):
        """Check if we're in debug mode."""
        try:
            from django.conf import settings as django_settings
            return getattr(django_settings, 'DEBUG', False)
        except:
            return False

    def _configure_environment(self):
        """Configure l'environnement pour l'application."""
        import os

        # Configuration des logs pour l'application
        logging.getLogger('rail_django_graphql').setLevel(
            logging.DEBUG if os.environ.get('DEBUG') else logging.INFO
        )

    def _invalidate_cache_on_startup(self):
        """Invalidate metadata cache on application startup."""
        try:
            from .extensions.metadata import invalidate_cache_on_startup
            invalidate_cache_on_startup()
            logger.info("Metadata cache invalidated on startup")
        except ImportError:
            logger.warning("Could not import cache invalidation function")
        except Exception as e:
            logger.error(f"Error invalidating cache on startup: {e}")


# Backward compatibility alias
DjangoGraphQLAutoConfig = RailDjangoGraphQLConfig

"""
GraphQL Meta Configuration System

This module provides the GraphQLMeta class for configuring GraphQL behavior
on Django models, including custom resolvers, filters, and advanced filtering options.
"""

import logging
from typing import Any, Callable, Dict, List, Optional, Type, Union

from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models import Q

logger = logging.getLogger(__name__)


class GraphQLMeta:
    """
    Meta class for configuring GraphQL behavior on Django models.

    This class provides configuration options for:
    - Custom resolvers that can intercept and modify model queries
    - Custom filters for advanced filtering capabilities
    - Quick filter for primitive model values across nested relationships
    - Field-specific configurations

    Usage:
        class MyModel(models.Model):
            name = models.CharField(max_length=100)
            email = models.EmailField()
            created_at = models.DateTimeField(auto_now_add=True)

            class GraphQLMeta:
                # Custom resolvers
                custom_resolvers = {
                    'active_users': 'get_active_users_resolver',
                    'recent_posts': lambda queryset, info, **kwargs: queryset.filter(created_at__gte=timezone.now() - timedelta(days=7))
                }

                # Custom filters
                custom_filters = {
                    'is_premium': lambda queryset, value: queryset.filter(subscription__type='premium') if value else queryset,
                    'has_posts': lambda queryset, value: queryset.filter(posts__isnull=not value).distinct()
                }

                # Quick filter configuration
                filters = {
                    'quick': ['name', 'email', 'profile__bio', 'posts__title']
                }

                # Field configurations
                filter_fields = {
                    'name': ['exact', 'icontains', 'startswith'],
                    'email': ['exact', 'icontains'],
                    'created_at': ['exact', 'gte', 'lte', 'range']
                }

                # Ordering configuration
                ordering = ['name', 'created_at', '-created_at']
    """

    def __init__(self, model_class: Type[models.Model]):
        """
        Initialize GraphQLMeta configuration for a model.

        Args:
            model_class: The Django model class this meta is attached to
        """
        self.model_class = model_class
        self._meta_config = getattr(model_class, "GraphQLMeta", None)

        # Initialize configuration attributes
        self.custom_resolvers = self._get_config_attr("custom_resolvers", {})
        self.custom_filters = self._get_config_attr("custom_filters", {})
        self.filters = self._get_config_attr("filters", {})
        self.filter_fields = self._get_config_attr("filter_fields", {})
        self.ordering = self._get_config_attr("ordering", [])
        self.exclude_fields = self._get_config_attr("exclude_fields", [])
        self.include_fields = self._get_config_attr("include_fields", None)

        # Validate configuration
        self._validate_configuration()

    def _get_config_attr(self, attr_name: str, default: Any) -> Any:
        """
        Get configuration attribute from the model's GraphQLMeta class.

        Args:
            attr_name: Name of the attribute to retrieve
            default: Default value if attribute is not found

        Returns:
            The attribute value or default
        """
        if self._meta_config and hasattr(self._meta_config, attr_name):
            return getattr(self._meta_config, attr_name)
        return default

    def _validate_configuration(self) -> None:
        """
        Validate the GraphQLMeta configuration for common errors.

        Raises:
            ValueError: If configuration is invalid
        """
        # Validate custom resolvers
        if not isinstance(self.custom_resolvers, dict):
            raise ValueError(
                f"custom_resolvers must be a dictionary, got {type(self.custom_resolvers)}"
            )

        # Validate custom filters
        if not isinstance(self.custom_filters, dict):
            raise ValueError(
                f"custom_filters must be a dictionary, got {type(self.custom_filters)}"
            )

        # Validate filters configuration
        if not isinstance(self.filters, dict):
            raise ValueError(f"filters must be a dictionary, got {type(self.filters)}")

        # Validate quick filter fields
        quick_fields = self.filters.get("quick", [])
        if quick_fields and not isinstance(quick_fields, list):
            raise ValueError(
                f"filters['quick'] must be a list, got {type(quick_fields)}"
            )

        # Validate quick filter field paths
        for field_path in quick_fields:
            if not isinstance(field_path, str):
                raise ValueError(
                    f"Quick filter field paths must be strings, got {type(field_path)} for {field_path}"
                )

            # Validate field path exists on model
            self._validate_field_path(field_path)

    def _validate_field_path(self, field_path: str) -> None:
        """
        Validate that a field path exists on the model.

        Args:
            field_path: Field path to validate (e.g., 'name', 'profile__bio')

        Raises:
            ValueError: If field path is invalid
        """
        try:
            current_model = self.model_class
            field_parts = field_path.split("__")

            for i, field_name in enumerate(field_parts):
                try:
                    field = current_model._meta.get_field(field_name)

                    # If this is not the last part, it should be a relation
                    if i < len(field_parts) - 1:
                        if hasattr(field, "related_model"):
                            current_model = field.related_model
                        else:
                            raise ValueError(
                                f"Field '{field_name}' in path '{field_path}' is not a relation"
                            )

                except FieldDoesNotExist:
                    raise ValueError(
                        f"Field '{field_name}' does not exist on model {current_model.__name__}"
                    )

        except Exception as e:
            logger.warning(
                f"Could not validate field path '{field_path}' on model {self.model_class.__name__}: {e}"
            )

    def get_custom_resolver(self, resolver_name: str) -> Optional[Callable]:
        """
        Get a custom resolver by name.

        Args:
            resolver_name: Name of the resolver to retrieve

        Returns:
            The resolver function or None if not found
        """
        resolver = self.custom_resolvers.get(resolver_name)

        if isinstance(resolver, str):
            # If it's a string, try to get it as a method from the model
            if hasattr(self.model_class, resolver):
                return getattr(self.model_class, resolver)
            else:
                logger.warning(
                    f"Custom resolver method '{resolver}' not found on model {self.model_class.__name__}"
                )
                return None

        return resolver

    def get_custom_filter(self, filter_name: str) -> Optional[Callable]:
        """
        Get a custom filter by name.

        Args:
            filter_name: Name of the filter to retrieve

        Returns:
            The filter function or None if not found
        """
        filter_func = self.custom_filters.get(filter_name)

        if isinstance(filter_func, str):
            # If it's a string, try to get it as a method from the model
            if hasattr(self.model_class, filter_func):
                return getattr(self.model_class, filter_func)
            else:
                logger.warning(
                    f"Custom filter method '{filter_func}' not found on model {self.model_class.__name__}"
                )
                return None

        return filter_func

    def get_custom_filters(self) -> Dict[str, Any]:
        """
        Get all custom filters as django-filter Filter instances.

        Returns:
            Dictionary mapping filter names to Filter instances
        """
        from django_filters import BooleanFilter, CharFilter, NumberFilter

        filter_instances = {}

        for filter_name, filter_func in self.custom_filters.items():
            # Convert string method names to actual methods
            if isinstance(filter_func, str):
                if hasattr(self.model_class, filter_func):
                    method = getattr(self.model_class, filter_func)
                    # Create appropriate filter type based on filter name or default to CharFilter
                    if (
                        "bool" in filter_name.lower()
                        or filter_name.startswith("has_")
                        or filter_name.startswith("is_")
                    ):
                        filter_instances[filter_name] = BooleanFilter(method=method)
                    elif (
                        "count" in filter_name.lower()
                        or "number" in filter_name.lower()
                    ):
                        filter_instances[filter_name] = NumberFilter(method=method)
                    else:
                        filter_instances[filter_name] = CharFilter(method=method)
                else:
                    logger.warning(
                        f"Custom filter method '{filter_func}' not found on model {self.model_class.__name__}"
                    )
            elif callable(filter_func):
                # For callable functions, wrap them in CharFilter
                filter_instances[filter_name] = CharFilter(method=filter_func)
            else:
                logger.warning(
                    f"Custom filter '{filter_name}' is neither string nor callable"
                )

        return filter_instances

    def apply_custom_resolver(
        self, resolver_name: str, queryset: models.QuerySet, info: Any, **kwargs
    ) -> models.QuerySet:
        """
        Apply a custom resolver to a queryset.

        Args:
            resolver_name: Name of the resolver to apply
            queryset: The queryset to modify
            info: GraphQL resolve info
            **kwargs: Additional arguments

        Returns:
            Modified queryset
        """
        resolver = self.get_custom_resolver(resolver_name)

        if resolver:
            try:
                if callable(resolver):
                    return resolver(queryset, info, **kwargs)
                else:
                    logger.warning(f"Custom resolver '{resolver_name}' is not callable")
            except Exception as e:
                logger.error(f"Error applying custom resolver '{resolver_name}': {e}")

        return queryset

    def apply_custom_filter(
        self, filter_name: str, queryset: models.QuerySet, value: Any
    ) -> models.QuerySet:
        """
        Apply a custom filter to a queryset.

        Args:
            filter_name: Name of the filter to apply
            queryset: The queryset to filter
            value: The filter value

        Returns:
            Filtered queryset
        """
        filter_func = self.get_custom_filter(filter_name)

        if filter_func:
            try:
                if callable(filter_func):
                    return filter_func(queryset, value)
                else:
                    logger.warning(f"Custom filter '{filter_name}' is not callable")
            except Exception as e:
                logger.error(f"Error applying custom filter '{filter_name}': {e}")

        return queryset

    def apply_quick_filter(
        self, queryset: models.QuerySet, search_value: str
    ) -> models.QuerySet:
        """
        Apply quick filter to search across configured fields.

        Args:
            queryset: The queryset to filter
            search_value: The search value

        Returns:
            Filtered queryset
        """
        # Use quick_filter_fields if available, otherwise fall back to filters['quick']
        quick_fields = getattr(self, 'quick_filter_fields', None) or self.filters.get("quick", [])

        if not quick_fields or not search_value:
            return queryset

        # Build Q object for OR search across all quick fields
        q_objects = Q()

        for field_path in quick_fields:
            try:
                # Determine the appropriate lookup based on field type
                lookup = self._get_quick_filter_lookup(field_path)
                filter_kwargs = {f"{field_path}__{lookup}": search_value}
                q_objects |= Q(**filter_kwargs)

            except Exception as e:
                logger.warning(
                    f"Error building quick filter for field '{field_path}': {e}"
                )

        if q_objects:
            return queryset.filter(q_objects)

        return queryset

    def _get_quick_filter_lookup(self, field_path: str) -> str:
        """
        Determine the appropriate lookup type for a field in quick filter.

        Args:
            field_path: The field path to analyze

        Returns:
            The lookup type to use (e.g., 'icontains', 'exact')
        """
        try:
            # Navigate to the final field
            current_model = self.model_class
            field_parts = field_path.split("__")

            for i, field_name in enumerate(field_parts):
                field = current_model._meta.get_field(field_name)

                if i < len(field_parts) - 1:
                    # Navigate to related model
                    if hasattr(field, "related_model"):
                        current_model = field.related_model
                    else:
                        return "icontains"  # Default fallback
                else:
                    # This is the final field, determine lookup type
                    if isinstance(
                        field, (models.CharField, models.TextField, models.EmailField)
                    ):
                        return "icontains"
                    elif isinstance(
                        field,
                        (models.IntegerField, models.FloatField, models.DecimalField),
                    ):
                        return "exact"
                    elif isinstance(field, (models.DateField, models.DateTimeField)):
                        return "exact"
                    elif isinstance(field, models.BooleanField):
                        return "exact"
                    else:
                        return "icontains"  # Default for unknown types

        except Exception:
            return "icontains"  # Safe default

    def get_filter_fields(self) -> Dict[str, List[str]]:
        """
        Get the filter fields configuration.

        Returns:
            Dictionary mapping field names to allowed lookups
        """
        return self.filter_fields.copy()

    def get_ordering_fields(self) -> List[str]:
        """
        Get the ordering fields configuration.

        Returns:
            List of allowed ordering fields
        """
        return self.ordering.copy() if isinstance(self.ordering, list) else []

    def has_custom_resolver(self, resolver_name: str) -> bool:
        """
        Check if a custom resolver exists.

        Args:
            resolver_name: Name of the resolver to check

        Returns:
            True if resolver exists, False otherwise
        """
        return resolver_name in self.custom_resolvers

    def has_custom_filter(self, filter_name: str) -> bool:
        """
        Check if a custom filter exists.

        Args:
            filter_name: Name of the filter to check

        Returns:
            True if filter exists, False otherwise
        """
        return filter_name in self.custom_filters

    def has_quick_filter(self) -> bool:
        """
        Check if quick filter is configured.

        Returns:
            True if quick filter is configured, False otherwise
        """
        return bool(self.filters.get("quick"))


def get_model_graphql_meta(model_class: Type[models.Model]) -> GraphQLMeta:
    """
    Get or create GraphQLMeta configuration for a model.

    Args:
        model_class: The Django model class

    Returns:
        GraphQLMeta instance for the model
    """
    # Cache the meta instance on the model class
    if not hasattr(model_class, "_graphql_meta_instance"):
        model_class._graphql_meta_instance = GraphQLMeta(model_class)

    return model_class._graphql_meta_instance

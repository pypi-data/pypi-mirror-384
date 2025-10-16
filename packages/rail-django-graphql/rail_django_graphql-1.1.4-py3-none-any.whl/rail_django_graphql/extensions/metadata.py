"""
Model metadata schema for Django GraphQL Auto-Generation.

This module provides comprehensive metadata exposure for Django models to support
rich frontend interfaces including advanced filtering, CRUD operations, and
complex forms with nested fields.
"""

import hashlib
import logging
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Dict, List, Optional, Type, Union

import graphene
from django.apps import apps
from django.core.cache import cache
from django.db import models
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver
from graphql import GraphQLError

from ..conf import get_core_schema_settings
from ..core.settings import SchemaSettings
from ..generators.introspector import ModelIntrospector
from .caching import CacheConfig, get_cache_manager

# Remove imports that cause AppRegistryNotReady error
# from ..core.security import AuthorizationManager
# from ..extensions.permissions import PermissionLevel, OperationType

logger = logging.getLogger(__name__)

# Cache configuration for metadata
METADATA_CACHE_CONFIG = CacheConfig(
    enabled=True,
    default_timeout=1800,  # 30 minutes for metadata
    schema_cache_timeout=3600 * 24,  # 1 hour for schema metadata
    query_cache_timeout=900,  # 15 minutes for query metadata
    field_cache_timeout=1200,  # 20 minutes for field metadata
    cache_hit_logging=True,
    cache_stats_enabled=True,
)


def cache_metadata(
    timeout: int = None,
    user_specific: bool = True,
    invalidate_on_model_change: bool = True,
):
    """
    Decorator for caching metadata extraction methods.

    Args:
        timeout: Cache timeout in seconds (uses default if None)
        user_specific: Whether to include user ID in cache key
        invalidate_on_model_change: Whether to invalidate cache when model changes
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not METADATA_CACHE_CONFIG.enabled:
                return func(self, *args, **kwargs)

            # Generate cache key based on function name, args, and user
            cache_key_parts = [
                f"metadata_{func.__name__}",
                str(hash(str(args))),
                str(hash(str(sorted(kwargs.items())))),
            ]

            # Add user ID if user_specific and user is available
            if user_specific and len(args) > 0:
                # Try to find user in args or kwargs
                user = None
                if "user" in kwargs:
                    user = kwargs["user"]
                elif len(args) >= 3 and hasattr(
                    args[2], "id"
                ):  # Common pattern: (self, app_name, model_name, user)
                    user = args[2]

                if user and hasattr(user, "id"):
                    cache_key_parts.append(f"user_{user.id}")

            # Create final cache key
            cache_key_raw = "_".join(cache_key_parts)
            cache_key = f"metadata_{hashlib.md5(cache_key_raw.encode()).hexdigest()}"

            # Try to get from cache
            cache_manager = get_cache_manager()
            cached_result = cache.get(cache_key)

            if cached_result is not None:
                if METADATA_CACHE_CONFIG.cache_hit_logging:
                    logger.debug(f"Cache hit for metadata: {func.__name__}")
                return cached_result

            # Execute function and cache result
            result = func(self, *args, **kwargs)

            if result is not None:
                cache_timeout = timeout or METADATA_CACHE_CONFIG.default_timeout
                cache.set(cache_key, result, cache_timeout)

                if METADATA_CACHE_CONFIG.cache_hit_logging:
                    logger.debug(
                        f"Cached metadata result: {func.__name__} (timeout: {cache_timeout}s)"
                    )

            return result

        return wrapper

    return decorator


def invalidate_metadata_cache(model_name: str = None, app_name: str = None):
    """
    Invalidate metadata cache for specific model or all models.

    Args:
        model_name: Specific model name to invalidate (optional)
        app_name: Specific app name to invalidate (optional)
    """
    cache_manager = get_cache_manager()

    if model_name and app_name:
        # Invalidate specific model cache
        pattern = f"metadata_*{app_name}*{model_name}*"
        logger.info(f"Invalidating metadata cache for {app_name}.{model_name}")
    elif app_name:
        # Invalidate app cache
        pattern = f"metadata_*{app_name}*"
        logger.info(f"Invalidating metadata cache for app {app_name}")
    else:
        # Invalidate all metadata cache
        pattern = "metadata_*"
        logger.info("Invalidating all metadata cache")

    # Clear cache entries matching pattern
    try:
        cache_manager.invalidate_cache(pattern)
    except AttributeError:
        logger.warning(
            f"Failed to invalidate cache pattern {pattern}: 'GraphQLCacheManager' object has no attribute 'invalidate_cache'"
        )
        # Fallback: clear specific cache keys or all cache
        if model_name and app_name:
            cache.delete_many(
                [
                    f"metadata_{app_name}_{model_name}_model",
                    f"metadata_{app_name}_{model_name}_fields",
                    f"metadata_{app_name}_{model_name}_relationships",
                    f"metadata_{app_name}_{model_name}_filters",
                    f"metadata_{app_name}_{model_name}_mutations",
                ]
            )
        else:
            cache.clear()
    except Exception as e:
        logger.warning(f"Failed to invalidate cache pattern {pattern}: {e}")
        # Fallback: clear all cache
        cache.clear()


# Use lazy import to avoid AppRegistryNotReady error
def get_user_model_lazy():
    from django.contrib.auth import get_user_model

    return get_user_model()


@dataclass
class InputFieldMetadata:
    """Metadata for mutation input fields."""

    name: str
    field_type: str
    required: bool
    default_value: Optional[Any] = None
    description: Optional[str] = None
    choices: Optional[List[Dict[str, Any]]] = None
    validation_rules: Optional[Dict[str, Any]] = None
    widget_type: Optional[str] = None
    placeholder: Optional[str] = None
    help_text: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    pattern: Optional[str] = None
    related_model: Optional[str] = None
    multiple: bool = False


@dataclass
class MutationMetadata:
    """Metadata for GraphQL mutations."""

    name: str
    description: Optional[str] = None
    input_fields: List[InputFieldMetadata] = field(default_factory=list)
    return_type: Optional[str] = None
    requires_authentication: bool = True
    required_permissions: List[str] = field(default_factory=list)
    mutation_type: str = "custom"  # create, update, delete, custom
    model_name: Optional[str] = None
    form_config: Optional[Dict[str, Any]] = None
    validation_schema: Optional[Dict[str, Any]] = None
    success_message: Optional[str] = None
    error_messages: Optional[Dict[str, str]] = None


# ChoiceType : {"value":str,"label":str}    graphene class
class ChoiceType(graphene.ObjectType):
    value = graphene.String(required=True, description="Choice value")
    label = graphene.String(required=True, description="Choice label")


class FilterOptionType(graphene.ObjectType):
    """GraphQL type for individual filter options within a grouped filter."""

    name = graphene.String(
        required=True, description="Filter option name (e.g., 'slug__iexact')"
    )
    lookup_expr = graphene.String(
        required=True, description="Django lookup expression (e.g., 'iexact')"
    )
    help_text = graphene.String(
        required=True, description="Filter help text in French using field verbose_name"
    )
    filter_type = graphene.String(
        required=True, description="Filter class type (e.g., 'CharFilter')"
    )


class FilterFieldType(graphene.ObjectType):
    """GraphQL type for grouped filter field metadata."""

    field_name = graphene.String(required=True, description="Target model field name")
    is_nested = graphene.Boolean(
        required=True, description="Whether this is a nested filter"
    )
    related_model = graphene.String(description="Related model name for nested filters")
    is_custom = graphene.Boolean(
        required=True, description="Whether this includes custom filters"
    )
    options = graphene.List(
        FilterOptionType,
        required=True,
        description="List of filter options for this field",
    )


class InputFieldMetadataType(graphene.ObjectType):
    """GraphQL type for input field metadata."""

    name = graphene.String(required=True, description="Field name")
    field_type = graphene.String(required=True, description="Field data type")
    required = graphene.Boolean(required=True, description="Whether field is required")
    default_value = graphene.JSONString(description="Default value for the field")
    description = graphene.String(description="Field description")
    choices = graphene.List(
        graphene.JSONString, description="Available choices for the field"
    )
    validation_rules = graphene.JSONString(description="Validation rules as JSON")
    widget_type = graphene.String(description="Recommended UI widget type")
    placeholder = graphene.String(description="Placeholder text for input")
    help_text = graphene.String(description="Help text for the field")
    min_length = graphene.Int(description="Minimum length for string fields")
    max_length = graphene.Int(description="Maximum length for string fields")
    min_value = graphene.Float(description="Minimum value for numeric fields")
    max_value = graphene.Float(description="Maximum value for numeric fields")
    pattern = graphene.String(description="Regex pattern for validation")
    related_model = graphene.String(description="Related model name for foreign keys")
    multiple = graphene.Boolean(
        required=True, description="Whether field accepts multiple values"
    )


class MutationMetadataType(graphene.ObjectType):
    """GraphQL type for mutation metadata."""

    name = graphene.String(required=True, description="Mutation name")
    description = graphene.String(description="Mutation description")
    input_fields = graphene.List(
        InputFieldMetadataType,
        required=True,
        description="Input fields for the mutation",
    )
    return_type = graphene.String(description="Return type of the mutation")
    requires_authentication = graphene.Boolean(
        required=True, description="Whether mutation requires authentication"
    )
    required_permissions = graphene.List(
        graphene.String,
        required=True,
        description="Required permissions to execute mutation",
    )
    mutation_type = graphene.String(
        required=True, description="Type of mutation (create, update, delete, custom)"
    )
    model_name = graphene.String(description="Associated model name")
    form_config = graphene.JSONString(description="Frontend form configuration")
    validation_schema = graphene.JSONString(
        description="Validation schema for the mutation"
    )
    success_message = graphene.String(description="Success message template")
    error_messages = graphene.JSONString(description="Error message templates")


@dataclass
class FieldMetadata:
    """Metadata for a single model field."""

    name: str
    field_type: str
    is_required: bool
    is_nullable: bool
    null: bool
    default_value: Any
    help_text: str
    max_length: Optional[int]
    choices: Optional[List[Dict[str, str]]]
    is_primary_key: bool
    is_foreign_key: bool
    is_unique: bool
    is_indexed: bool
    has_auto_now: bool
    has_auto_now_add: bool
    blank: bool
    editable: bool
    verbose_name: str
    has_permission: bool


@dataclass
class RelationshipMetadata:
    """Metadata for model relationships."""

    name: str
    relationship_type: str
    # Embed full related model metadata (single-level depth by default)
    related_model: "ModelMetadata"
    related_app: str
    to_field: Optional[str]
    from_field: str
    is_reverse: bool
    is_required: bool
    many_to_many: bool
    one_to_one: bool
    foreign_key: bool
    on_delete: Optional[str]
    related_name: Optional[str]
    has_permission: bool
    verbose_name: str


@dataclass
class ModelMetadata:
    """Complete metadata for a Django model."""

    app_name: str
    model_name: str
    verbose_name: str
    verbose_name_plural: str
    table_name: str
    primary_key_field: str
    fields: List[FieldMetadata]
    relationships: List[RelationshipMetadata]
    permissions: List[str]
    ordering: List[str]
    unique_together: List[List[str]]
    indexes: List[Dict[str, Any]]
    abstract: bool
    proxy: bool
    managed: bool
    filters: List[Dict[str, Any]]
    mutations: List["MutationMetadata"]


class FieldMetadataType(graphene.ObjectType):
    """GraphQL type for field metadata."""

    name = graphene.String(required=True, description="Field name")
    field_type = graphene.String(required=True, description="Django field type")
    is_required = graphene.Boolean(
        required=True, description="Whether field is required"
    )
    is_nullable = graphene.Boolean(
        required=True, description="Whether field can be null"
    )
    null = graphene.Boolean(required=True, description="Whether field can be null")
    default_value = graphene.String(description="Default value as string")
    help_text = graphene.String(description="Field help text")
    max_length = graphene.Int(description="Maximum length for string fields")
    choices = graphene.List(ChoiceType, description="Field choices")
    is_primary_key = graphene.Boolean(
        required=True, description="Whether field is primary key"
    )
    is_foreign_key = graphene.Boolean(
        required=True, description="Whether field is foreign key"
    )
    is_unique = graphene.Boolean(
        required=True, description="Whether field has unique constraint"
    )
    is_indexed = graphene.Boolean(required=True, description="Whether field is indexed")
    has_auto_now = graphene.Boolean(
        required=True, description="Whether field has auto_now"
    )
    has_auto_now_add = graphene.Boolean(
        required=True, description="Whether field has auto_now_add"
    )
    blank = graphene.Boolean(required=True, description="Whether field can be blank")
    editable = graphene.Boolean(required=True, description="Whether field is editable")
    verbose_name = graphene.String(required=True, description="Field verbose name")
    has_permission = graphene.Boolean(
        required=True, description="Whether user has permission for this field"
    )


class RelationshipMetadataType(graphene.ObjectType):
    """GraphQL type for relationship metadata."""

    name = graphene.String(required=True, description="Relationship field name")
    relationship_type = graphene.String(
        required=True, description="Type of relationship"
    )
    related_model = graphene.Field(
        lambda: ModelMetadataType,
        required=True,
        description="Related model metadata",
    )
    related_app = graphene.String(required=True, description="Related model app")
    to_field = graphene.String(description="Target field name")
    from_field = graphene.String(required=True, description="Source field name")
    is_reverse = graphene.Boolean(
        required=True, description="Whether this is a reverse relationship"
    )
    is_required = graphene.Boolean(
        required=True, description="Whether this is a reverse relationship"
    )
    many_to_many = graphene.Boolean(
        required=True, description="Whether this is many-to-many"
    )
    one_to_one = graphene.Boolean(
        required=True, description="Whether this is one-to-one"
    )
    foreign_key = graphene.Boolean(
        required=True, description="Whether this is foreign key"
    )
    on_delete = graphene.String(description="On delete behavior")
    related_name = graphene.String(description="Related name for reverse lookups")
    has_permission = graphene.Boolean(
        required=True, description="Whether user has permission for this relationship"
    )
    verbose_name = graphene.String(required=True, description="Model verbose name")


class ModelMetadataType(graphene.ObjectType):
    """GraphQL type for complete model metadata."""

    app_name = graphene.String(required=True, description="Django app name")
    model_name = graphene.String(required=True, description="Model class name")
    verbose_name = graphene.String(required=True, description="Model verbose name")
    verbose_name_plural = graphene.String(
        required=True, description="Model verbose name plural"
    )
    table_name = graphene.String(required=True, description="Database table name")
    primary_key_field = graphene.String(
        required=True, description="Primary key field name"
    )
    fields = graphene.List(FieldMetadataType, required=True, description="Model fields")
    relationships = graphene.List(
        RelationshipMetadataType, required=True, description="Model relationships"
    )
    permissions = graphene.List(
        graphene.String, required=True, description="Available permissions"
    )
    ordering = graphene.List(
        graphene.String, required=True, description="Default ordering"
    )
    unique_together = graphene.List(
        graphene.List(graphene.String),
        required=True,
        description="Unique together constraints",
    )
    indexes = graphene.List(
        graphene.JSONString, required=True, description="Database indexes"
    )
    abstract = graphene.Boolean(required=True, description="Whether model is abstract")
    proxy = graphene.Boolean(required=True, description="Whether model is proxy")
    managed = graphene.Boolean(
        required=True, description="Whether model is managed by Django"
    )
    filters = graphene.List(
        FilterFieldType, required=True, description="Available filter fields"
    )
    mutations = graphene.List(
        MutationMetadataType,
        required=True,
        description="Available mutations for this model",
    )


class ModelMetadataExtractor:
    """Extracts comprehensive metadata from Django models."""

    def __init__(self, schema_name: str = "default", max_depth: int = 1):
        """
        Initialize the metadata extractor.

        Args:
            schema_name: Name of the schema configuration to use
            max_depth: Maximum depth for nested related model metadata
        """
        # Lazy import to avoid AppRegistryNotReady
        # from ..core.settings import get_schema_settings

        self.schema_name = schema_name
        self.max_depth = max_depth
        # self.settings = get_schema_settings(schema_name)

    @cache_metadata(
        timeout=1200, user_specific=True
    )  # 20 minutes cache for field metadata
    def _extract_field_metadata(self, field, user) -> Optional[FieldMetadata]:
        """
        Extract metadata for a single field with permission checking.

        Args:
            field: Django model field instance

        Returns:
            FieldMetadata if user has permission, None otherwise
        """
        # Lazy import to avoid AppRegistryNotReady
        from django.db import models

        # Get field choices
        choices = None
        if hasattr(field, "choices") and field.choices:
            choices = [
                {"value": choice[0], "label": choice[1]} for choice in field.choices
            ]

        # Get max length
        max_length = getattr(field, "max_length", None)

        # Get on_delete behavior for foreign keys (guard None)
        on_delete = None
        if getattr(field, "remote_field", None) is not None:
            remote_on_delete = getattr(field.remote_field, "on_delete", None)
            if remote_on_delete:
                on_delete = getattr(remote_on_delete, "__name__", None)

        # Simplified permission flag; adjust with actual permission checks if needed
        has_permission = True
        return FieldMetadata(
            name=field.name,
            field_type=field.__class__.__name__,
            is_required=not field.blank and field.default == models.NOT_PROVIDED,
            is_nullable=field.null,
            null=field.null,
            default_value=str(field.default)
            if field.default != models.NOT_PROVIDED
            else None,
            help_text=field.help_text or "",
            max_length=max_length,
            choices=choices,
            is_primary_key=field.primary_key,
            is_foreign_key=isinstance(field, models.ForeignKey),
            is_unique=field.unique,
            is_indexed=field.db_index,
            has_auto_now=getattr(field, "auto_now", False),
            has_auto_now_add=getattr(field, "auto_now_add", False),
            blank=field.blank,
            editable=field.editable,
            verbose_name=str(field.verbose_name),
            has_permission=has_permission,
        )

    @cache_metadata(
        timeout=1200, user_specific=True
    )  # 20 minutes cache for relationship metadata
    def _extract_relationship_metadata(
        self, field, user, current_depth: int = 0
    ) -> Optional[RelationshipMetadata]:
        """
        Extract metadata for relationship fields.

        Args:
            field: Django relationship field instance

        Returns:
            RelationshipMetadata if user has permission, None otherwise
        """
        # Lazy import to avoid AppRegistryNotReady
        from django.db import models

        related_model = field.related_model
        on_delete = None

        if getattr(field, "remote_field", None) is not None:
            remote_on_delete = getattr(field.remote_field, "on_delete", None)
            if remote_on_delete:
                on_delete = getattr(remote_on_delete, "__name__", None)

        # Simplified permission flag; adjust with actual checks if needed
        has_permission = True

        # Build embedded related model metadata (guard depth to avoid recursion)
        if related_model is None or not hasattr(related_model, "_meta"):
            return None

        related_app_label = getattr(related_model._meta, "app_label", "")
        related_model_class_name = related_model.__name__

        # Include nested relationships only if within max depth
        include_nested = current_depth < self.max_depth
        embedded_related = self.extract_model_metadata(
            app_name=related_app_label,
            model_name=related_model_class_name,
            user=user,
            nested_fields=include_nested,
            permissions_included=True,
            current_depth=current_depth + 1,
        )
        if embedded_related is None:
            return None

        return RelationshipMetadata(
            name=field.name,
            relationship_type=field.__class__.__name__,
            related_model=embedded_related,
            is_required=not field.blank,
            related_app=related_app_label,
            to_field=field.remote_field.name
            if hasattr(field, "remote_field") and field.remote_field
            else None,
            from_field=field.name,
            is_reverse=False,
            many_to_many=isinstance(field, models.ManyToManyField),
            one_to_one=isinstance(field, models.OneToOneField),
            foreign_key=isinstance(field, models.ForeignKey),
            on_delete=on_delete,
            related_name=getattr(field, "related_name", None),
            has_permission=has_permission,
            verbose_name=field.verbose_name,
        )

    @cache_metadata(
        timeout=1800, user_specific=False
    )  # 30 minutes cache for complete model metadata
    def extract_model_metadata(
        self,
        app_name: str,
        model_name: str,
        user,
        nested_fields: bool = True,
        permissions_included: bool = True,
        current_depth: int = 0,
    ) -> Optional[ModelMetadata]:
        """
        Extract complete metadata for a Django model.

        Args:
            app_name: Django app label
            model_name: Model class name
            user: Current user for permission checking
            nested_fields: Whether to include relationship metadata
            permissions_included: Whether to include permission information

        Returns:
            ModelMetadata with filtered fields based on permissions, or None on error
        """
        # Resolve the model from app and model name
        try:
            model = apps.get_model(app_name, model_name)
        except Exception as e:
            logger.error(
                "Model '%s' not found in app '%s': %s", model_name, app_name, e
            )
            return None

        introspector = ModelIntrospector(model, self.schema_name)

        # Extract field metadata with permission filtering using concrete model fields
        fields = []
        for django_field in model._meta.get_fields():
            # Only include concrete fields (exclude relations and auto-created reverse accessors)
            if getattr(django_field, "is_relation", False):
                continue
            if getattr(django_field, "auto_created", False):
                continue
            field_metadata = self._extract_field_metadata(django_field, user)
            if field_metadata:
                fields.append(field_metadata)

        # Extract relationship metadata with permission filtering (declared relations only)
        relationships = []
        if nested_fields:
            for django_field in model._meta.get_fields():
                if not getattr(django_field, "is_relation", False):
                    continue
                # Skip polymorphic_ctype field
                if django_field.name == "polymorphic_ctype":
                    continue
                # Skip auto-created reverse relations; they will be added below
                if getattr(django_field, "auto_created", False):
                    continue
                rel_metadata = self._extract_relationship_metadata(
                    django_field, user, current_depth=current_depth
                )
                if rel_metadata:
                    relationships.append(rel_metadata)

        # Always include reverse relationships
        if nested_fields:
            reverse_relations = introspector.get_reverse_relations()
            for rel_name, related_model in reverse_relations.items():
                # Build embedded metadata for reverse-related model with depth guard
                include_nested = current_depth < self.max_depth
                embedded_related = self.extract_model_metadata(
                    app_name=related_model._meta.app_label,
                    model_name=related_model.__name__,
                    user=user,
                    nested_fields=include_nested,
                    permissions_included=True,
                    current_depth=current_depth + 1,
                )
                if embedded_related is None:
                    continue
                relationships.append(
                    RelationshipMetadata(
                        name=rel_name,
                        verbose_name=related_model._meta.verbose_name,
                        relationship_type="ReverseRelation",
                        related_model=embedded_related,
                        related_app=related_model._meta.app_label,
                        to_field=None,
                        is_required=False,
                        from_field=rel_name,
                        is_reverse=True,
                        many_to_many=False,
                        one_to_one=False,
                        foreign_key=False,
                        on_delete=None,
                        related_name=rel_name,
                        has_permission=True,
                    )
                )

        # Get model permissions for the user
        permissions = []
        if permissions_included and user:
            # Lazy import to avoid AppRegistryNotReady
            from django.contrib.auth.models import AnonymousUser

            if not isinstance(user, AnonymousUser):
                app_label = model._meta.app_label
                model_name_code = model._meta.model_name

                # Check standard Django permissions
                for action in ["add", "change", "delete", "view"]:
                    perm_code = f"{app_label}.{action}_{model_name_code}"
                    if user.has_perm(perm_code):
                        permissions.append(perm_code)

        # Get ordering
        ordering = list(model._meta.ordering) if model._meta.ordering else []

        # Get unique_together
        unique_together = []
        if hasattr(model._meta, "unique_together") and model._meta.unique_together:
            unique_together = [
                list(constraint) for constraint in model._meta.unique_together
            ]

        # Get indexes
        indexes = []
        if hasattr(model._meta, "indexes"):
            for index in model._meta.indexes:
                indexes.append(
                    {
                        "name": index.name,
                        "fields": list(index.fields),
                        "unique": getattr(index, "unique", False),
                    }
                )

        # Extract filter metadata
        filters = self._extract_filter_metadata(model)

        # Extract mutations metadata
        mutations = self.extract_mutations_metadata(
            model,
        )

        return ModelMetadata(
            app_name=model._meta.app_label,
            model_name=model.__name__,
            verbose_name=str(model._meta.verbose_name),
            verbose_name_plural=str(model._meta.verbose_name_plural),
            table_name=model._meta.db_table,
            primary_key_field=model._meta.pk.name,
            fields=fields,
            relationships=relationships,
            permissions=permissions,
            ordering=ordering,
            unique_together=unique_together,
            indexes=indexes,
            abstract=model._meta.abstract,
            proxy=model._meta.proxy,
            managed=model._meta.managed,
            filters=filters,
            mutations=mutations,
        )

    def _has_field_permission(self, user, model: type, field_name: str) -> bool:
        """
        Check if user has permission to access a specific field.

        Args:
            user: Django user instance
            model: Django model class
            field_name: Name of the field to check

        Returns:
            bool: True if user has permission to access the field
        """
        # Lazy import to avoid AppRegistryNotReady
        from django.contrib.auth.models import AnonymousUser

        if isinstance(user, AnonymousUser):
            return False

        # Check basic view permission for the model
        app_label = model._meta.app_label
        model_name = model._meta.model_name
        view_permission = f"{app_label}.view_{model_name}"

        return user.has_perm(view_permission)

    @cache_metadata(
        timeout=1800, user_specific=False
    )  # 30 minutes cache for filter metadata (not user-specific)
    def _extract_filter_metadata(self, model) -> List[Dict[str, Any]]:
        """
        Extract comprehensive filter metadata for a Django model with enhanced features.

        Args:
            model: Django model class

        Returns:
            List of grouped filter field metadata dictionaries
        """
        try:
            # Import the enhanced filter generator
            from ..generators.filters import AdvancedFilterGenerator, EnhancedFilterGenerator
            from ..utils.graphql_meta import get_model_graphql_meta

            # Use the instance's max_depth parameter
            max_depth = self.max_depth

            # Create enhanced filter generator instance with configurable depth
            enhanced_generator = EnhancedFilterGenerator(
                max_nested_depth=max_depth,
                enable_nested_filters=True,
                schema_name=self.schema_name,
            )

            # Get grouped filters for the model
            grouped_filters = enhanced_generator.get_grouped_filters(model)

            # Get GraphQL meta for custom filters
            graphql_meta = get_model_graphql_meta(model)

            # Create a dictionary to group filters by field name
            grouped_filter_dict = {}

            # Process enhanced filters
            for grouped_filter in grouped_filters:
                field_name = grouped_filter.field_name

                # Get field verbose name for help text
                try:
                    field = model._meta.get_field(field_name)
                    verbose_name = str(field.verbose_name)
                except:
                    verbose_name = field_name

                options = []
                for operation in grouped_filter.operations:
                    filter_name = (
                        f"{field_name}__{operation.lookup_expr}"
                        if operation.lookup_expr != "exact"
                        else field_name
                    )

                    # Translate help text to French using verbose_name
                    help_text = self._translate_help_text_to_french(
                        operation.description, verbose_name
                    )

                    options.append(
                        {
                            "name": filter_name,
                            "lookup_expr": operation.lookup_expr,
                            "help_text": help_text,
                            "filter_type": operation.filter_type,
                        }
                    )
                grouped_filter_dict[field_name] = {
                    "field_name": field_name,
                    "is_nested": False,
                    "related_model": field.related_model.__name__
                    if field.related_model
                    else None,
                    "is_custom": False,
                    "options": options,
                }

            # Add nested filters from traditional generator - RESTRUCTURED TO PARENT LEVEL
            try:
                filter_generator = AdvancedFilterGenerator(
                    max_nested_depth=max_depth,  # Use configurable depth
                    enable_nested_filters=True,
                    schema_name=self.schema_name,
                )

                filter_class = filter_generator.generate_filter_set(model)

                # Process nested filters and restructure them to parent level
                for filter_name, filter_instance in filter_class.base_filters.items():
                    if "__" in filter_name and not filter_name.endswith("__count"):
                        field_parts = filter_name.split("__")
                        base_field_name = field_parts[0]
                        lookup_expr = "__".join(field_parts[1:])

                        # Skip if depth exceeds max_depth
                        if len(field_parts) - 1 > max_depth:
                            continue

                        # Get related model info
                        related_model = None
                        try:
                            field = model._meta.get_field(base_field_name)
                            if hasattr(field, "related_model"):
                                related_model = field.related_model.__name__
                        except:
                            continue

                        # Get verbose name for nested field
                        try:
                            verbose_name = str(field.verbose_name)
                        except:
                            verbose_name = base_field_name

                        # RESTRUCTURE: Move nested filters to parent level
                        # Instead of grouping under base_field_name, create individual entries
                        parent_filter_name = (
                            filter_name  # Use full filter name as parent
                        )

                        # Create help text for restructured filter
                        help_text = self._translate_help_text_to_french(
                            f"Filter by {lookup_expr} in related {base_field_name}",
                            verbose_name,
                        )

                        # Create individual filter entry at parent level
                        grouped_filter_dict[parent_filter_name] = {
                            "field_name": parent_filter_name,  # Use full name
                            "is_nested": True,
                            "related_model": related_model,
                            "is_custom": False,
                            "options": [
                                {
                                    "name": filter_name,
                                    "lookup_expr": lookup_expr,
                                    "help_text": help_text,
                                    "filter_type": filter_instance.__class__.__name__,
                                }
                            ],
                        }

            except Exception as e:
                logger.warning(
                    f"Error processing nested filters for {model.__name__}: {e}"
                )

            # ENHANCED: Add custom filters from GraphQLMeta with better quick filter support
            if graphql_meta:
                # Add quick filters with comprehensive field support
                if (
                    hasattr(graphql_meta, "quick_filter_fields")
                    and graphql_meta.quick_filter_fields
                ):
                    quick_fields = graphql_meta.quick_filter_fields

                    # Create comprehensive quick filter entry
                    grouped_filter_dict["quick"] = {
                        "field_name": "quick",
                        "is_nested": False,
                        "related_model": None,
                        "is_custom": True,
                        "options": [
                            {
                                "name": "quick",
                                "lookup_expr": "icontains",
                                "help_text": f"Recherche rapide dans les champs: {', '.join(quick_fields)}",
                                "filter_type": "CharFilter",
                            }
                        ],
                    }

                    # Also add individual quick filter options for each field
                    for quick_field in quick_fields:
                        if "__" in quick_field:  # Handle nested quick fields
                            # Add nested quick field as separate filter
                            quick_filter_name = (
                                f"quick_{quick_field.replace('__', '_')}"
                            )
                            grouped_filter_dict[quick_filter_name] = {
                                "field_name": quick_filter_name,
                                "is_nested": True,
                                "related_model": self._get_related_model_name(
                                    model, quick_field
                                ),
                                "is_custom": True,
                                "options": [
                                    {
                                        "name": quick_filter_name,
                                        "lookup_expr": "icontains",
                                        "help_text": f"Recherche rapide dans {quick_field}",
                                        "filter_type": "CharFilter",
                                    }
                                ],
                            }

                # Add custom filters
                if (
                    hasattr(graphql_meta, "custom_filters")
                    and graphql_meta.custom_filters
                ):
                    for (
                        custom_name,
                        custom_method,
                    ) in graphql_meta.custom_filters.items():
                        grouped_filter_dict[custom_name] = {
                            "field_name": custom_name,
                            "is_nested": False,
                            "related_model": None,
                            "is_custom": True,
                            "options": [
                                {
                                    "name": custom_name,
                                    "lookup_expr": "custom",
                                    "help_text": f"Filtre personnalisé: {custom_name}",
                                    "filter_type": "CustomFilter",
                                }
                            ],
                        }

            # Convert to list format and sort for consistency
            result = list(grouped_filter_dict.values())

            # Sort filters: regular fields first, then nested, then custom
            result.sort(key=lambda x: (x["is_custom"], x["is_nested"], x["field_name"]))

            return result

        except Exception as e:
            logger.error(f"Error extracting filter metadata for {model.__name__}: {e}")
            return []

    def _get_related_model_name(self, model, field_path: str) -> Optional[str]:
        """
        Get the related model name for a nested field path.

        Args:
            model: Base Django model
            field_path: Field path like 'author__username'

        Returns:
            Related model name or None
        """
        try:
            field_parts = field_path.split("__")
            current_model = model

            for field_name in field_parts[:-1]:  # Exclude the final field
                field = current_model._meta.get_field(field_name)
                if hasattr(field, "related_model"):
                    current_model = field.related_model
                else:
                    return None

            return current_model.__name__
        except:
            return None

    def _translate_help_text_to_french(
        self, original_text: str, verbose_name: str
    ) -> str:
        """
        Translate help text to French using field verbose_name.

        Args:
            original_text: Original English help text
            verbose_name: Field verbose name to use in translation

        Returns:
            French translated help text
        """
        # Basic translation mapping
        translations = {
            "exact": f"Correspondance exacte pour {verbose_name}",
            "iexact": f"Correspondance exacte insensible à la casse pour {verbose_name}",
            "contains": f"Contient le texte dans {verbose_name}",
            "icontains": f"Contient le texte (insensible à la casse) dans {verbose_name}",
            "startswith": f"Commence par le texte dans {verbose_name}",
            "istartswith": f"Commence par le texte (insensible à la casse) dans {verbose_name}",
            "endswith": f"Se termine par le texte dans {verbose_name}",
            "iendswith": f"Se termine par le texte (insensible à la casse) dans {verbose_name}",
            "in": f"Correspond à l'une des valeurs fournies pour {verbose_name}",
            "gt": f"Supérieur à la valeur pour {verbose_name}",
            "gte": f"Supérieur ou égal à la valeur pour {verbose_name}",
            "lt": f"Inférieur à la valeur pour {verbose_name}",
            "lte": f"Inférieur ou égal à la valeur pour {verbose_name}",
            "range": f"Valeur dans la plage pour {verbose_name}",
            "isnull": f"Vérifier si {verbose_name} est nul",
            "today": f"Filtrer pour la date d'aujourd'hui dans {verbose_name}",
            "yesterday": f"Filtrer pour la date d'hier dans {verbose_name}",
            "this_week": f"Filtrer pour les dates de cette semaine dans {verbose_name}",
            "this_month": f"Filtrer pour les dates de ce mois dans {verbose_name}",
            "this_year": f"Filtrer pour les dates de cette année dans {verbose_name}",
            "year": f"Filtrer par année pour {verbose_name}",
            "month": f"Filtrer par mois pour {verbose_name}",
            "day": f"Filtrer par jour pour {verbose_name}",
        }

        # Extract lookup expression from original text
        for lookup, french_text in translations.items():
            if lookup in original_text.lower():
                return french_text

        # Fallback: basic translation
        if "exact match" in original_text.lower():
            return f"Correspondance exacte pour {verbose_name}"
        elif "contains" in original_text.lower():
            return f"Contient le texte dans {verbose_name}"
        elif "greater than" in original_text.lower():
            return f"Supérieur à la valeur pour {verbose_name}"
        elif "less than" in original_text.lower():
            return f"Inférieur à la valeur pour {verbose_name}"
        else:
            return f"Filtre pour {verbose_name}"

    @cache_metadata(
        timeout=900, user_specific=False
    )  # 15 minutes cache for mutations metadata (not user-specific)
    def extract_mutations_metadata(
        self, model: Type[models.Model]
    ) -> List[MutationMetadata]:
        """
        Extract mutation metadata for a Django model.

        Args:
            model: Django model class

        Returns:
            List of MutationMetadata objects
        """
        try:
            from ..conf import get_mutation_generator_settings
            from ..generators.mutations import MutationGenerator
            from ..generators.types import TypeGenerator

            mutations = []
            model_name = model.__name__

            # Initialize mutation generator
            type_generator = TypeGenerator(schema_name=self.schema_name)
            mutation_settings = get_mutation_generator_settings(self.schema_name)
            mutation_generator = MutationGenerator(
                type_generator=type_generator,
                settings=mutation_settings,
                schema_name=self.schema_name,
            )

            # Generate CRUD mutations if enabled
            if mutation_settings.enable_create:
                create_mutation = self._extract_create_mutation_metadata(
                    model, mutation_generator
                )
                if create_mutation:
                    mutations.append(create_mutation)

            if mutation_settings.enable_update:
                update_mutation = self._extract_update_mutation_metadata(
                    model, mutation_generator
                )
                if update_mutation:
                    mutations.append(update_mutation)

            if mutation_settings.enable_delete:
                delete_mutation = self._extract_delete_mutation_metadata(
                    model, mutation_generator
                )
                if delete_mutation:
                    mutations.append(delete_mutation)

            # Generate bulk mutations if enabled
            if mutation_settings.enable_bulk_operations:
                bulk_mutations = self._extract_bulk_mutations_metadata(
                    model, mutation_generator
                )
                mutations.extend(bulk_mutations)

            # Generate method mutations if enabled
            if mutation_settings.enable_method_mutations:
                method_mutations = self._extract_method_mutations_metadata(
                    model, mutation_generator
                )
                mutations.extend(method_mutations)

            return mutations

        except Exception as e:
            logger.error(
                f"Error extracting mutations metadata for {model.__name__}: {e}"
            )
            return []

    def _extract_create_mutation_metadata(
        self, model: Type[models.Model], mutation_generator
    ) -> Optional[MutationMetadata]:
        """Extract metadata for create mutation."""
        try:
            model_name = model.__name__
            input_fields = self._extract_input_fields_from_model(model, "create")

            return MutationMetadata(
                name=f"create_{model_name.lower()}",
                description=f"Create a new {model_name} instance",
                input_fields=input_fields,
                return_type=f"{model_name}Type",
                requires_authentication=True,
                required_permissions=[
                    f"{model._meta.app_label}.add_{model._meta.model_name}"
                ],
                mutation_type="create",
                model_name=model_name,
                success_message=f"{model_name} created successfully",
                form_config={
                    "title": f"Create {model_name}",
                    "submit_text": "Create",
                    "cancel_text": "Cancel",
                },
            )
        except Exception as e:
            logger.error(f"Error extracting create mutation metadata: {e}")
            return None

    def _extract_update_mutation_metadata(
        self, model: Type[models.Model], mutation_generator
    ) -> Optional[MutationMetadata]:
        """Extract metadata for update mutation."""
        try:
            model_name = model.__name__
            input_fields = self._extract_input_fields_from_model(model, "update")

            # Add ID field for update
            id_field = InputFieldMetadata(
                name="id",
                field_type="ID",
                required=True,
                description=f"ID of the {model_name} to update",
                widget_type="hidden",
            )
            input_fields.insert(0, id_field)

            return MutationMetadata(
                name=f"update_{model_name.lower()}",
                description=f"Update an existing {model_name} instance",
                input_fields=input_fields,
                return_type=f"{model_name}Type",
                requires_authentication=True,
                required_permissions=[f"change_{model._meta.model_name}"],
                mutation_type="update",
                model_name=model_name,
                success_message=f"{model_name} updated successfully",
                form_config={
                    "title": f"Update {model_name}",
                    "submit_text": "Update",
                    "cancel_text": "Cancel",
                },
            )
        except Exception as e:
            logger.error(f"Error extracting update mutation metadata: {e}")
            return None

    def _extract_delete_mutation_metadata(
        self, model: Type[models.Model], mutation_generator
    ) -> Optional[MutationMetadata]:
        """Extract metadata for delete mutation."""
        try:
            model_name = model.__name__

            id_field = InputFieldMetadata(
                name="id",
                field_type="ID",
                required=True,
                description=f"ID of the {model_name} to delete",
                widget_type="hidden",
            )

            return MutationMetadata(
                name=f"delete_{model_name.lower()}",
                description=f"Delete a {model_name} instance",
                input_fields=[id_field],
                return_type="Boolean",
                requires_authentication=True,
                required_permissions=[f"delete_{model._meta.model_name}"],
                mutation_type="delete",
                model_name=model_name,
                success_message=f"{model_name} deleted successfully",
                form_config={
                    "title": f"Delete {model_name}",
                    "submit_text": "Delete",
                    "cancel_text": "Cancel",
                    "confirmation_required": True,
                    "confirmation_message": f"Are you sure you want to delete this {model_name}?",
                },
            )
        except Exception as e:
            logger.error(f"Error extracting delete mutation metadata: {e}")
            return None

    def _extract_bulk_mutations_metadata(
        self, model: Type[models.Model], mutation_generator
    ) -> List[MutationMetadata]:
        """Extract metadata for bulk mutations."""
        mutations = []
        model_name = model.__name__

        try:
            # Bulk create
            input_fields = self._extract_input_fields_from_model(model, "create")
            bulk_create = MutationMetadata(
                name=f"bulk_create_{model_name.lower()}",
                description=f"Create multiple {model_name} instances",
                input_fields=[
                    InputFieldMetadata(
                        name="objects",
                        field_type="List",
                        required=True,
                        description=f"List of {model_name} objects to create",
                        multiple=True,
                    )
                ],
                return_type=f"List[{model_name}Type]",
                requires_authentication=True,
                required_permissions=[f"add_{model._meta.model_name}"],
                mutation_type="bulk_create",
                model_name=model_name,
                success_message=f"Multiple {model_name} instances created successfully",
            )
            mutations.append(bulk_create)

            # Bulk update
            bulk_update = MutationMetadata(
                name=f"bulk_update_{model_name.lower()}",
                description=f"Update multiple {model_name} instances",
                input_fields=[
                    InputFieldMetadata(
                        name="objects",
                        field_type="List",
                        required=True,
                        description=f"List of {model_name} objects to update",
                        multiple=True,
                    )
                ],
                return_type=f"List[{model_name}Type]",
                requires_authentication=True,
                required_permissions=[f"change_{model._meta.model_name}"],
                mutation_type="bulk_update",
                model_name=model_name,
                success_message=f"Multiple {model_name} instances updated successfully",
            )
            mutations.append(bulk_update)

            # Bulk delete
            bulk_delete = MutationMetadata(
                name=f"bulk_delete_{model_name.lower()}",
                description=f"Delete multiple {model_name} instances",
                input_fields=[
                    InputFieldMetadata(
                        name="ids",
                        field_type="List[ID]",
                        required=True,
                        description=f"List of {model_name} IDs to delete",
                        multiple=True,
                    )
                ],
                return_type="Boolean",
                requires_authentication=True,
                required_permissions=[f"delete_{model._meta.model_name}"],
                mutation_type="bulk_delete",
                model_name=model_name,
                success_message=f"Multiple {model_name} instances deleted successfully",
            )
            mutations.append(bulk_delete)

        except Exception as e:
            logger.error(f"Error extracting bulk mutations metadata: {e}")

        return mutations

    def _extract_method_mutations_metadata(
        self, model: Type[models.Model], mutation_generator
    ) -> List[MutationMetadata]:
        """Extract metadata for method-based mutations."""
        mutations = []

        try:
            from ..generators.introspector import ModelIntrospector

            introspector = ModelIntrospector(model)
            model_methods = introspector.get_model_methods()

            for method_name, method_info in model_methods.items():
                if method_info.is_mutation and not method_info.is_private:
                    method_mutation = self._extract_method_mutation_metadata(
                        model, method_name, method_info
                    )
                    if method_mutation:
                        mutations.append(method_mutation)

        except Exception as e:
            logger.error(f"Error extracting method mutations metadata: {e}")

        return mutations

    def _extract_method_mutation_metadata(
        self, model: Type[models.Model], method_name: str, method_info
    ) -> Optional[MutationMetadata]:
        """Extract metadata for a specific method mutation."""
        try:
            model_name = model.__name__
            method = getattr(model, method_name)

            # Extract input fields from method signature
            input_fields = self._extract_input_fields_from_method(method)

            # Get custom attributes from decorators
            description = getattr(method, "_mutation_description", method.__doc__)
            custom_name = getattr(method, "_custom_mutation_name", None)
            requires_permission = getattr(method, "_requires_permission", None)

            mutation_name = custom_name or f"{model_name.lower()}_{method_name}"

            return MutationMetadata(
                name=mutation_name,
                description=description or f"Execute {method_name} on {model_name}",
                input_fields=input_fields,
                return_type="JSONString",
                requires_authentication=True,
                required_permissions=[requires_permission]
                if requires_permission
                else [],
                mutation_type="custom",
                model_name=model_name,
                success_message=f"{method_name} executed successfully",
            )

        except Exception as e:
            logger.error(f"Error extracting method mutation metadata: {e}")
            return None

    def _extract_input_fields_from_model(
        self, model: Type[models.Model], mutation_type: str
    ) -> List[InputFieldMetadata]:
        """Extract input fields from Django model fields."""
        input_fields = []

        for field in model._meta.fields:
            # Skip auto fields and primary keys for create mutations
            if field.primary_key and mutation_type == "create":
                continue

            # Skip auto-generated fields
            if hasattr(field, "auto_now") or hasattr(field, "auto_now_add"):
                continue

            input_field = self._convert_django_field_to_input_metadata(
                field, mutation_type
            )
            if input_field:
                input_fields.append(input_field)

        return input_fields

    def _convert_django_field_to_input_metadata(
        self, field, mutation_type: str
    ) -> Optional[InputFieldMetadata]:
        """Convert Django field to InputFieldMetadata."""
        try:
            from django.db import models

            field_name = field.name
            field_type = "String"  # Default
            required = (
                not field.null and not field.blank and not hasattr(field, "default")
            )

            # For update mutations, make fields optional
            if mutation_type == "update":
                required = False

            # Map Django field types to GraphQL types
            if isinstance(field, models.CharField):
                field_type = "String"
            elif isinstance(field, models.TextField):
                field_type = "String"
            elif isinstance(field, models.IntegerField):
                field_type = "Int"
            elif isinstance(field, models.FloatField):
                field_type = "Float"
            elif isinstance(field, models.BooleanField):
                field_type = "Boolean"
            elif isinstance(field, models.DateTimeField):
                field_type = "DateTime"
            elif isinstance(field, models.DateField):
                field_type = "Date"
            elif isinstance(field, models.EmailField):
                field_type = "String"
            elif isinstance(field, models.URLField):
                field_type = "String"
            elif isinstance(field, models.ForeignKey):
                field_type = "ID"
            elif isinstance(field, models.ManyToManyField):
                field_type = "List[ID]"

            # Get choices if available
            choices = None
            if hasattr(field, "choices") and field.choices:
                choices = [
                    {"value": choice[0], "label": choice[1]} for choice in field.choices
                ]

            # Determine widget type
            widget_type = self._get_widget_type_for_field(field)

            return InputFieldMetadata(
                name=field_name,
                field_type=field_type,
                required=required,
                description=str(field.verbose_name)
                if hasattr(field, "verbose_name")
                else None,
                choices=choices,
                widget_type=widget_type,
                help_text=str(field.help_text)
                if hasattr(field, "help_text") and field.help_text
                else None,
                max_length=getattr(field, "max_length", None),
                related_model=field.related_model.__name__
                if hasattr(field, "related_model") and field.related_model
                else None,
                multiple=isinstance(field, models.ManyToManyField),
            )

        except Exception as e:
            logger.error(f"Error converting field {field.name}: {e}")
            return None

    def _get_widget_type_for_field(self, field) -> str:
        """Determine the appropriate widget type for a Django field."""
        from django.db import models

        if isinstance(field, models.TextField):
            return "textarea"
        elif isinstance(field, models.EmailField):
            return "email"
        elif isinstance(field, models.URLField):
            return "url"
        elif isinstance(field, models.BooleanField):
            return "checkbox"
        elif isinstance(field, models.DateTimeField):
            return "datetime-local"
        elif isinstance(field, models.DateField):
            return "date"
        elif isinstance(field, models.IntegerField):
            return "number"
        elif isinstance(field, models.FloatField):
            return "number"
        elif isinstance(field, models.ForeignKey):
            return "select"
        elif isinstance(field, models.ManyToManyField):
            return "multiselect"
        elif hasattr(field, "choices") and field.choices:
            return "select"
        else:
            return "text"

    def _extract_input_fields_from_method(self, method) -> List[InputFieldMetadata]:
        """Extract input fields from method signature."""
        import inspect

        input_fields = []
        signature = inspect.signature(method)

        for param_name, param in signature.parameters.items():
            if param_name == "self":
                continue

            field_type = "String"  # Default
            required = param.default == inspect.Parameter.empty
            default_value = (
                param.default if param.default != inspect.Parameter.empty else None
            )

            # Try to infer type from annotation
            if param.annotation != inspect.Parameter.empty:
                annotation = param.annotation
                if annotation == int:
                    field_type = "Int"
                elif annotation == float:
                    field_type = "Float"
                elif annotation == bool:
                    field_type = "Boolean"
                elif hasattr(annotation, "__origin__"):
                    if annotation.__origin__ == list:
                        field_type = "List[String]"

            input_field = InputFieldMetadata(
                name=param_name,
                field_type=field_type,
                required=required,
                default_value=default_value,
                description=f"Parameter {param_name} for method execution",
            )
            input_fields.append(input_field)

        return input_fields


class ModelMetadataQuery(graphene.ObjectType):
    """GraphQL queries for model metadata."""

    model_metadata = graphene.Field(
        ModelMetadataType,
        app_name=graphene.String(required=True, description="Django app name"),
        model_name=graphene.String(required=True, description="Model class name"),
        nested_fields=graphene.Boolean(
            default_value=True, description="Include relationship metadata"
        ),
        permissions_included=graphene.Boolean(
            default_value=True, description="Include permission information"
        ),
        max_depth=graphene.Int(
            default_value=0,
            description="Maximum nesting depth for filters (default: 2)",
        ),
        description="Get comprehensive metadata for a Django model",
    )

    def resolve_model_metadata(
        self,
        info,
        app_name: str,
        model_name: str,
        nested_fields: bool = True,
        permissions_included: bool = True,
        max_depth: int = 2,
    ) -> Optional[ModelMetadataType]:
        """
        Resolve model metadata with permission checking and settings validation.

        Args:
            info: GraphQL resolve info
            app_name: Django app name
            model_name: Model name
            nested_fields: Include nested relationship metadata
            permissions_included: Include permission-based field filtering
            max_depth: Maximum nesting depth for filters

        Returns:
            ModelMetadataType or None if not accessible
        """
        # Check core schema settings gating
        # Get user from context and require authentication
        user = getattr(info.context, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            permissions_included = False

        # Extract metadata via extractor which handles model lookup
        extractor = ModelMetadataExtractor(max_depth=max_depth)
        metadata = extractor.extract_model_metadata(
            app_name=app_name,
            model_name=model_name,
            user=user,
            nested_fields=nested_fields,
            permissions_included=permissions_included,
        )
        # Handle extraction error returning None
        if metadata is None:
            return None

        # Return dataclass directly for Graphene to resolve attributes
        return metadata


# Cache invalidation signals - only invalidate when models actually change
@receiver(post_save, sender=None)
def invalidate_model_metadata_cache_on_save(sender, instance, created, **kwargs):
    """
    Invalidate metadata cache only when model structure changes.

    This is triggered when:
    - New models are created (migrations)
    - Model fields are added/removed (migrations)
    - Model relationships change (migrations)

    Args:
        sender: The model class that was saved
        instance: The model instance
        created: Whether this is a new instance
        **kwargs: Signal arguments
    """
    # Only invalidate cache for model structure changes, not data changes
    # We check if this is likely a migration or model structure change
    if sender and hasattr(sender, "_meta"):
        # Skip cache invalidation for regular data operations
        # Only invalidate during migrations or when model structure changes
        if _is_model_structure_change(sender, instance, created, **kwargs):
            app_name = sender._meta.app_label
            model_name = sender.__name__

            # Invalidate cache for this specific model
            invalidate_metadata_cache(model_name=model_name, app_name=app_name)
            logger.info(
                f"Invalidated metadata cache for {app_name}.{model_name} due to model structure change"
            )


@receiver(post_delete, sender=None)
def invalidate_model_metadata_cache_on_delete(sender, instance, **kwargs):
    """
    Invalidate metadata cache when models are deleted.

    This is more conservative and only invalidates when it's likely
    a model structure change rather than regular data deletion.

    Args:
        sender: The model class that was deleted
        instance: The model instance
        **kwargs: Signal arguments
    """
    if sender and hasattr(sender, "_meta"):
        # Only invalidate for structural changes, not regular deletions
        if _is_model_structure_change(sender, instance, False, **kwargs):
            app_name = sender._meta.app_label
            model_name = sender.__name__

            # Invalidate cache for this specific model
            invalidate_metadata_cache(model_name=model_name, app_name=app_name)
            logger.info(
                f"Invalidated metadata cache for {app_name}.{model_name} due to model deletion"
            )


@receiver(m2m_changed)
def invalidate_m2m_metadata_cache(sender, action, **kwargs):
    """
    Invalidate metadata cache when many-to-many relationships change structurally.

    Only invalidates on structural changes, not data changes.

    Args:
        sender: The through model for the m2m field
        action: The type of m2m change
        **kwargs: Signal arguments
    """
    # Only invalidate on structural changes, not data operations
    if (
        action in ["post_add", "post_remove", "post_clear"]
        and sender
        and hasattr(sender, "_meta")
    ):
        # Check if this is a structural change vs data change
        if _is_m2m_structure_change(sender, action, **kwargs):
            app_name = sender._meta.app_label
            model_name = sender.__name__

            # Invalidate cache for this specific model
            invalidate_metadata_cache(model_name=model_name, app_name=app_name)
            logger.info(
                f"Invalidated m2m metadata cache for {app_name}.{model_name} due to relationship structure change"
            )


def _is_model_structure_change(sender, instance, created, **kwargs):
    """
    Determine if this is a model structure change vs regular data operation.

    Args:
        sender: The model class
        instance: The model instance
        created: Whether this is a new instance
        **kwargs: Signal arguments

    Returns:
        bool: True if this is likely a structure change
    """
    # Check if we're in a migration context
    if _is_in_migration_context():
        return True

    # Check if this is a Django internal model that affects schema
    if sender._meta.app_label in ["contenttypes", "auth", "admin"]:
        # These apps can affect GraphQL schema structure
        return True

    # Check if this model has custom metadata that might affect schema
    if hasattr(sender, "_graphql_metadata_affects_schema"):
        return getattr(sender, "_graphql_metadata_affects_schema", False)

    # For now, be conservative and don't invalidate on regular data operations
    return False


def _is_m2m_structure_change(sender, action, **kwargs):
    """
    Determine if this is an M2M structure change vs regular data operation.

    Args:
        sender: The through model
        action: The M2M action
        **kwargs: Signal arguments

    Returns:
        bool: True if this is likely a structure change
    """
    # Check if we're in a migration context
    if _is_in_migration_context():
        return True

    # For now, be conservative and don't invalidate on regular M2M operations
    return False


def _is_in_migration_context():
    """
    Check if we're currently in a Django migration context.

    Returns:
        bool: True if in migration context
    """
    import sys

    # Check if we're running migrations
    if "migrate" in sys.argv:
        return True

    # Check if we're in a migration module
    for frame_info in __import__("inspect").stack():
        if "migrations" in frame_info.filename:
            return True

    return False


def invalidate_cache_on_startup():
    """
    Invalidate metadata cache on application startup.

    This ensures that cache is fresh when the application starts,
    which is useful for deployments and development.
    """
    try:
        logger.info("Invalidating metadata cache on application startup")
        invalidate_metadata_cache()  # Invalidate all metadata cache
        logger.info("Metadata cache invalidated successfully on startup")
    except Exception as e:
        logger.warning(f"Failed to invalidate metadata cache on startup: {e}")
        # Don't raise exception to avoid breaking app startup


# Cache warming functions
def warm_metadata_cache(app_name: str = None, model_name: str = None, user=None):
    """
    Pre-warm metadata cache for specified models.

    Args:
        app_name: Specific app to warm cache for (optional)
        model_name: Specific model to warm cache for (optional)
        user: User context for permission-based caching
    """
    extractor = ModelMetadataExtractor()

    if app_name and model_name:
        # Warm cache for specific model
        try:
            extractor.extract_model_metadata(app_name, model_name, user)
            logger.info(f"Warmed metadata cache for {app_name}.{model_name}")
        except Exception as e:
            logger.error(f"Failed to warm cache for {app_name}.{model_name}: {e}")
    elif app_name:
        # Warm cache for all models in app
        try:
            app_config = apps.get_app_config(app_name)
            for model in app_config.get_models():
                extractor.extract_model_metadata(app_name, model.__name__, user)
            logger.info(f"Warmed metadata cache for app {app_name}")
        except Exception as e:
            logger.error(f"Failed to warm cache for app {app_name}: {e}")
    else:
        # Warm cache for all models
        for app_config in apps.get_app_configs():
            for model in app_config.get_models():
                try:
                    extractor.extract_model_metadata(
                        app_config.label, model.__name__, user
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to warm cache for {app_config.label}.{model.__name__}: {e}"
                    )
        logger.info("Warmed metadata cache for all models")


def get_cache_stats() -> Dict[str, Any]:
    """
    Get metadata cache statistics.

    Returns:
        Dictionary with cache statistics
    """
    cache_manager = get_cache_manager()
    stats = cache_manager.get_stats()

    return {
        "enabled": METADATA_CACHE_CONFIG.enabled,
        "hit_rate": stats.hit_rate,
        "hits": stats.hits,
        "misses": stats.misses,
        "sets": stats.sets,
        "deletes": stats.deletes,
        "invalidations": stats.invalidations,
        "default_timeout": METADATA_CACHE_CONFIG.default_timeout,
        "schema_cache_timeout": METADATA_CACHE_CONFIG.schema_cache_timeout,
        "query_cache_timeout": METADATA_CACHE_CONFIG.query_cache_timeout,
        "field_cache_timeout": METADATA_CACHE_CONFIG.field_cache_timeout,
    }


# Use lazy import to avoid AppRegistryNotReady error

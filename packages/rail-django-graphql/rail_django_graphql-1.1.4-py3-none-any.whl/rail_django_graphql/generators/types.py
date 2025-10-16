"""
Type Generation System for Django GraphQL Auto-Generation

This module provides the TypeGenerator class, which is responsible for converting
Django model fields and relationships into GraphQL types.
"""

from typing import Any, Dict, List, Optional, Type, Union

import graphene
from django.db import models
from django.db.models.fields import Field
from django.db.models.fields.related import ForeignKey, ManyToManyField, OneToOneField
from graphene_django import DjangoObjectType

# Resilient import: DjangoFilterConnectionField may not exist in some graphene-django versions
try:
    from graphene_django.filter import DjangoFilterConnectionField  # type: ignore
except Exception:
    DjangoFilterConnectionField = None  # Not required unless Relay is explicitly used
from graphene_django.utils import DJANGO_FILTER_INSTALLED

if DJANGO_FILTER_INSTALLED:
    from django_filters import CharFilter
from datetime import date

from ..conf import get_mutation_generator_settings, get_type_generator_settings
from ..core.performance import get_query_optimizer
from ..core.scalars import get_custom_scalar, get_enabled_scalars
from ..core.settings import MutationGeneratorSettings, TypeGeneratorSettings
from .inheritance import inheritance_handler
from .introspector import FieldInfo, ModelIntrospector


class TypeGenerator:
    """
    Generates GraphQL types from Django models, including object types,
    input types, and filter types.

    This class supports:
    - Multi-schema type generation
    - Configurable field inclusion/exclusion
    - Custom naming conventions
    - Relationship handling with depth limits
    - Input type generation for mutations
    - Filter type generation for queries
    - Custom scalar types integration
    - Performance optimization
    """

    # Mapping of Django field types to GraphQL scalar types
    FIELD_TYPE_MAP = {
        models.AutoField: graphene.ID,
        models.BigAutoField: graphene.ID,
        models.BigIntegerField: graphene.Int,
        models.BooleanField: graphene.Boolean,
        models.CharField: graphene.String,
        models.DateField: graphene.Date,
        models.DateTimeField: graphene.DateTime,
        models.DecimalField: graphene.Decimal,
        models.EmailField: graphene.String,
        models.FileField: graphene.String,
        models.FloatField: graphene.Float,
        models.ImageField: graphene.String,
        models.IntegerField: graphene.Int,
        models.JSONField: graphene.JSONString,
        models.PositiveIntegerField: graphene.Int,
        models.PositiveSmallIntegerField: graphene.Int,
        models.SlugField: graphene.String,
        models.SmallIntegerField: graphene.Int,
        models.TextField: graphene.String,
        models.TimeField: graphene.Time,
        models.URLField: graphene.String,
        models.UUIDField: graphene.UUID,
    }

    # Mapping of Python types to GraphQL scalar types for @property methods
    PYTHON_TYPE_MAP = {
        str: graphene.String,
        int: graphene.Int,
        float: graphene.Float,
        bool: graphene.Boolean,
        list: graphene.List,
        dict: graphene.JSONString,
        date: graphene.Date,
        # Add more mappings as needed
    }

    def __init__(
        self,
        settings: Optional[TypeGeneratorSettings] = None,
        mutation_settings: Optional[MutationGeneratorSettings] = None,
        schema_name: str = "default",
    ):
        """
        Initialize the TypeGenerator.

        Args:
            settings: Type generator settings or None for defaults
            mutation_settings: Mutation generator settings or None for defaults
            schema_name: Name of the schema for multi-schema support
        """
        self.schema_name = schema_name

        # Use hierarchical settings if no explicit settings provided
        if settings is None:
            self.settings = TypeGeneratorSettings.from_schema(schema_name)
        else:
            self.settings = settings

        if mutation_settings is None:
            self.mutation_settings = MutationGeneratorSettings.from_schema(schema_name)
        else:
            self.mutation_settings = mutation_settings

        # Initialize performance optimizer
        self.query_optimizer = get_query_optimizer(schema_name)

        # Get enabled custom scalars for this schema
        self.custom_scalars = get_enabled_scalars(schema_name)

        # Update field type map with custom scalars
        self._update_field_type_map()

        # Type registries for caching generated types
        self._type_registry: Dict[Type[models.Model], Type[DjangoObjectType]] = {}
        self._input_type_registry: Dict[
            Type[models.Model], Type[graphene.InputObjectType]
        ] = {}
        self._filter_type_registry: Dict[Type[models.Model], Type] = {}
        self._union_registry: Dict[str, Type[graphene.Union]] = {}
        self._interface_registry: Dict[
            Type[models.Model], Type[graphene.Interface]
        ] = {}

    def _update_field_type_map(self) -> None:
        """Update field type map with custom scalars based on settings."""
        # Apply custom field mappings from settings
        if (
            hasattr(self.settings, "custom_field_mappings")
            and self.settings.custom_field_mappings
        ):
            for (
                django_field,
                graphql_type,
            ) in self.settings.custom_field_mappings.items():
                if isinstance(graphql_type, str):
                    # Try to get custom scalar
                    custom_scalar = get_custom_scalar(graphql_type)
                    if custom_scalar:
                        self.FIELD_TYPE_MAP[django_field] = custom_scalar
                else:
                    self.FIELD_TYPE_MAP[django_field] = graphql_type

        # Apply custom scalars based on field types
        if "Email" in self.custom_scalars:
            self.FIELD_TYPE_MAP[models.EmailField] = self.custom_scalars["Email"]

        if "URL" in self.custom_scalars:
            self.FIELD_TYPE_MAP[models.URLField] = self.custom_scalars["URL"]

        if "UUID" in self.custom_scalars:
            self.FIELD_TYPE_MAP[models.UUIDField] = self.custom_scalars["UUID"]

        if "DateTime" in self.custom_scalars:
            self.FIELD_TYPE_MAP[models.DateTimeField] = self.custom_scalars["DateTime"]

        if "Date" in self.custom_scalars:
            self.FIELD_TYPE_MAP[models.DateField] = self.custom_scalars["Date"]

        if "Time" in self.custom_scalars:
            self.FIELD_TYPE_MAP[models.TimeField] = self.custom_scalars["Time"]

        if "JSON" in self.custom_scalars:
            self.FIELD_TYPE_MAP[models.JSONField] = self.custom_scalars["JSON"]

        if "Decimal" in self.custom_scalars:
            self.FIELD_TYPE_MAP[models.DecimalField] = self.custom_scalars["Decimal"]

    def _get_excluded_fields(self, model: Type[models.Model]) -> List[str]:
        """Get excluded fields for a specific model."""
        model_name = model.__name__
        excluded = set()

        # Always exclude polymorphic model internal fields
        # These fields are automatically managed by django-polymorphic and should not be exposed
        polymorphic_fields = {"polymorphic_ctype"}
        excluded.update(polymorphic_fields)

        # Also exclude any field ending with '_ptr' which are typically OneToOneField pointers in inheritance
        from rail_django_graphql.generators.introspector import ModelIntrospector

        introspector = ModelIntrospector(model)
        all_fields = introspector.get_model_fields()
        for field_name in all_fields.keys():
            if field_name.endswith("_ptr"):
                excluded.add(field_name)

        # Check both exclude_fields and excluded_fields (alias)
        # Handle case where settings might be a list instead of dict

        if isinstance(self.settings.exclude_fields, dict):
            excluded.update(self.settings.exclude_fields.get(model_name, []))
        elif isinstance(self.settings.exclude_fields, list):
            excluded.update(self.settings.exclude_fields)

        if isinstance(self.settings.excluded_fields, dict):
            excluded.update(self.settings.excluded_fields.get(model_name, []))
        elif isinstance(self.settings.excluded_fields, list):
            excluded.update(self.settings.excluded_fields)
        return list(excluded)

    def _get_included_fields(self, model: Type[models.Model]) -> Optional[List[str]]:
        """Get included fields for a specific model."""
        if self.settings.include_fields is None:
            return None
        return self.settings.include_fields.get(model.__name__, None)

    def _should_field_be_required_for_create(
        self,
        field_info: "FieldInfo",
        field_name: str = None,
        model: Type[models.Model] = None,
    ) -> bool:
        """
        Determine if a field should be required for create mutations based on:
        - auto_now and auto_now_add fields are not required (automatically set)
        - fields with defaults are not required (Django will use the default)
        - fields with blank=True are not required (can be empty)
        - fields with blank=False AND no default ARE required
        - id/primary key fields are not required for create (auto-generated)
        - mandatory fields defined by _get_mandatory_fields are always required
        """
        # Check if this field is mandatory for this model
        if model and field_name:
            mandatory_fields = self._get_mandatory_fields(model)
            if field_name in mandatory_fields:
                return True

        # Primary key fields (id, pk) are not required for create
        if field_name and field_name in ("id", "pk"):
            return False

        # auto_now and auto_now_add fields are automatically set
        if field_info.has_auto_now or field_info.has_auto_now_add:
            return False

        # Fields with defaults don't need to be provided
        if field_info.has_default:
            return False

        # Fields with blank=True can be left empty, so not required
        if field_info.blank:
            return False

        # Fields with blank=False (default) and no default value are required
        return True

    def _should_field_be_required_for_update(
        self, field_name: str, field_info: Any, model: Type[models.Model] = None
    ) -> bool:
        """
        Determine if a field should be required for update mutations.
        - id is required for updates
        - mandatory fields defined by _get_mandatory_fields are always required
        """
        # Check if this field is mandatory for this model
        if model and field_name:
            mandatory_fields = self._get_mandatory_fields(model)
            if field_name in mandatory_fields:
                return True

        return field_name == "id"

    def _get_mandatory_fields(self, model: Type[models.Model]) -> List[str]:
        """
        Get list of mandatory fields for a specific model.
        These fields are always required in input types regardless of Django field settings.

        Args:
            model: The Django model to get mandatory fields for

        Returns:
            List of field names that are mandatory for this model
        """
        # Define mandatory fields per model
        if model.__name__ == "BlogPost":
            return ["category"]

        return []

    def _should_include_field(self, model: Type[models.Model], field_name: str) -> bool:
        # Exclude polymorphic model internal fields
        # These fields are automatically managed by django-polymorphic and should not be exposed in mutations
        polymorphic_fields = {"polymorphic_ctype"}
        # Also exclude any field ending with '_ptr' which are typically OneToOneField pointers in inheritance
        if field_name in polymorphic_fields or field_name.endswith("_ptr"):
            return False

        excluded_fields = self._get_excluded_fields(model)
        if field_name in excluded_fields:
            return False

        included_fields = self._get_included_fields(model)
        if included_fields is not None:
            return field_name in included_fields

        return True

    def _get_graphql_type_for_property(self, return_type: Any) -> graphene.Field:
        """
        Convert a Python return type annotation to a GraphQL field type.

        Args:
            return_type: The return type annotation from a @property method

        Returns:
            GraphQL field with appropriate type
        """
        # Handle typing.Any or no annotation
        if return_type is Any or return_type is None:
            return graphene.String()

        # Handle basic Python types
        if return_type in self.PYTHON_TYPE_MAP:
            graphql_type = self.PYTHON_TYPE_MAP[return_type]
            # Special handling for List type which requires of_type parameter
            if graphql_type == graphene.List:
                return graphene.List(graphene.String)
            return graphql_type()

        # Handle typing generics like List[str], Optional[int], etc.
        origin = getattr(return_type, "__origin__", None)
        if origin is not None:
            if origin is list or origin is List:
                # Handle List[SomeType]
                args = getattr(return_type, "__args__", ())
                if args:
                    inner_type = self._get_graphql_type_for_property(args[0])
                    # If inner_type is a Field, extract its type
                    if hasattr(inner_type, "_type"):
                        return graphene.List(inner_type._type)
                    return graphene.List(inner_type)
                return graphene.List(graphene.String)
            elif origin is Union:
                # Handle Optional[SomeType] which is Union[SomeType, None]
                args = getattr(return_type, "__args__", ())
                if len(args) == 2 and type(None) in args:
                    # This is Optional[SomeType]
                    non_none_type = args[0] if args[1] is type(None) else args[1]
                    return self._get_graphql_type_for_property(non_none_type)

        # Default to String for unknown types
        return graphene.String()

    def generate_object_type(self, model: Type[models.Model]) -> Type[DjangoObjectType]:
        """
        Generates a GraphQL object type for a Django model.
        Handles relationships and custom field mappings.
        """
        if model in self._type_registry:
            return self._type_registry[model]

        introspector = ModelIntrospector(model)
        fields = introspector.get_model_fields()
        relationships = introspector.get_model_relationships()

        # Get excluded fields for this model
        exclude_fields = self._get_excluded_fields(model)

        # Create the Meta class for the DjangoObjectType
        meta_attrs = {
            "model": model,
            "exclude_fields": exclude_fields,
            "interfaces": (graphene.relay.Node,)
            if self.settings.generate_filters
            else (),
        }
        meta_class = type("Meta", (), meta_attrs)

        # Create the object type class
        class_name = f"{model.__name__}Type"
        type_attrs = {
            "Meta": meta_class,
            "__doc__": f"GraphQL type for the {model.__name__} model.",
        }

        # Add pk field that resolves to the model's primary key
        type_attrs["pk"] = graphene.ID(description="Primary key of the model")
        type_attrs["resolve_pk"] = lambda self, info: getattr(self, self._meta.pk.name)

        # Add custom field resolvers
        for field_name, field_info in fields.items():
            if not self._should_include_field(model, field_name):
                continue
            resolver_name = f"resolve_{field_name}"
            if hasattr(self, resolver_name):
                type_attrs[resolver_name] = getattr(self, resolver_name)

        # Override ManyToMany fields to use direct lists instead of connections
        for field_name, rel_info in relationships.items():
            if not self._should_include_field(model, field_name):
                continue

            if rel_info.relationship_type == "ManyToManyField":
                # Get the related model
                related_model = rel_info.related_model

                # Use proper lazy type resolution to avoid recursion
                def make_lazy_type(model_ref):
                    def lazy_type():
                        # Check if type already exists to avoid infinite recursion
                        if model_ref in self._type_registry:
                            return self._type_registry[model_ref]
                        return self.generate_object_type(model_ref)

                    return lazy_type

                # Override the field as a direct list with filter arguments
                type_attrs[field_name] = graphene.List(
                    make_lazy_type(related_model),
                    filters=graphene.Argument(graphene.JSONString),
                    description=f"Related {related_model.__name__} objects",
                )

                # Add count field for ManyToMany relation
                count_field_name = f"{field_name}_count"
                type_attrs[count_field_name] = graphene.Int(
                    description=f"Count of related {related_model.__name__} objects"
                )

                # Add parameterized totalCount field with filters
                total_count_field_name = f"{field_name}_total_count"
                type_attrs[total_count_field_name] = graphene.Field(
                    graphene.Int,
                    filters=graphene.Argument(graphene.JSONString),
                    description=f"Count of related {related_model.__name__} objects with optional filters",
                )

                # Add resolver that handles different relationship types with filtering
                def make_resolver(field_name, rel_info, related_model):
                    def resolver(self, info, filters=None):
                        related_obj = getattr(self, field_name)
                        # For OneToOne fields, return the single object or None
                        if rel_info.relationship_type == "OneToOneField":
                            return related_obj
                        # For ForeignKey and ManyToMany, return queryset with optional filtering
                        else:
                            queryset = related_obj.all()

                            # Apply filters if provided
                            if filters:
                                from ..generators.filters import AdvancedFilterGenerator

                                filter_generator = AdvancedFilterGenerator()
                                filter_set_class = filter_generator.generate_filter_set(
                                    related_model
                                )
                                filter_set = filter_set_class(
                                    filters, queryset=queryset
                                )
                                queryset = filter_set.qs

                            return queryset

                    return resolver

                # Add count resolver for ManyToMany relation
                def make_count_resolver(field_name):
                    def count_resolver(self, info):
                        related_obj = getattr(self, field_name)
                        return related_obj.count()

                    return count_resolver

                # Add parameterized total count resolver with filters
                def make_total_count_resolver(field_name, related_model):
                    def total_count_resolver(self, info, filters=None):
                        related_obj = getattr(self, field_name)
                        queryset = related_obj.all()

                        # Apply filters if provided
                        if filters:
                            from ..generators.filters import AdvancedFilterGenerator

                            filter_generator = AdvancedFilterGenerator()
                            filter_set_class = filter_generator.generate_filter_set(
                                related_model
                            )
                            filter_set = filter_set_class(filters, queryset=queryset)
                            queryset = filter_set.qs

                        return queryset.count()

                    return total_count_resolver

                type_attrs[f"resolve_{field_name}"] = make_resolver(
                    field_name, rel_info, related_model
                )
                type_attrs[f"resolve_{count_field_name}"] = make_count_resolver(
                    field_name
                )

        # Add custom resolvers for ALL reverse relationships to return direct model lists
        # instead of relay connections (including Django's default _set relationships)
        reverse_relations = self._get_reverse_relations(model)
        for accessor_name, related_model in reverse_relations.items():
            if not self._should_include_field(model, accessor_name):
                continue

            # Use proper lazy type resolution to avoid recursion
            # Create a closure that captures the related_model
            def make_lazy_type(model_ref):
                def lazy_type():
                    # Check if type already exists to avoid infinite recursion
                    if model_ref in self._type_registry:
                        return self._type_registry[model_ref]
                    return self.generate_object_type(model_ref)

                return lazy_type

            # Check if this is a OneToOne reverse relationship
            is_one_to_one_reverse = False
            if hasattr(model._meta, "related_objects"):
                for rel in model._meta.related_objects:
                    if rel.get_accessor_name() == accessor_name:
                        # Import OneToOneRel to check relationship type
                        from django.db.models.fields.reverse_related import OneToOneRel

                        if isinstance(rel, OneToOneRel):
                            is_one_to_one_reverse = True
                            break

            # Add the field - single object for OneToOne, list for others
            if is_one_to_one_reverse:
                type_attrs[accessor_name] = graphene.Field(
                    make_lazy_type(related_model),
                    description=f"Related {related_model.__name__} object",
                )
            else:
                type_attrs[accessor_name] = graphene.List(
                    make_lazy_type(related_model),
                    filters=graphene.Argument(graphene.JSONString),
                    description=f"Related {related_model.__name__} objects",
                )

                # Add count field for reverse ManyToOne relations (e.g., posts_count for User)
                count_field_name = f"{accessor_name}_count"
                type_attrs[count_field_name] = graphene.Int(
                    description=f"Count of related {related_model.__name__} objects"
                )

            # Add resolver that handles different relationship types with filtering
            def make_resolver(accessor_name, is_one_to_one, related_model):
                def resolver(self, info, filters=None):
                    # For OneToOne reverse relationships, handle DoesNotExist exceptions
                    if is_one_to_one:
                        try:
                            related_obj = getattr(self, accessor_name)
                            return related_obj
                        except related_model.DoesNotExist:
                            return None
                    # For other relationships, return queryset with optional filtering
                    else:
                        related_obj = getattr(self, accessor_name)
                        queryset = related_obj.all()

                        # Apply filters if provided
                        if filters:
                            from ..generators.filters import AdvancedFilterGenerator

                            filter_generator = AdvancedFilterGenerator()
                            filter_set_class = filter_generator.generate_filter_set(
                                related_model
                            )
                            filter_set = filter_set_class(filters, queryset=queryset)
                            queryset = filter_set.qs

                        return queryset

                return resolver

            # Add count resolver for reverse ManyToOne relations
            def make_count_resolver(accessor_name, is_one_to_one):
                def count_resolver(self, info):
                    if is_one_to_one:
                        # For OneToOne, return 1 if exists, 0 if not
                        related_obj = getattr(self, accessor_name, None)
                        return 1 if related_obj else 0
                    else:
                        # For ManyToOne reverse relations, count the related objects
                        related_obj = getattr(self, accessor_name)
                        return related_obj.count()

                return count_resolver

            type_attrs[f"resolve_{accessor_name}"] = make_resolver(
                accessor_name, is_one_to_one_reverse, related_model
            )

            # Add count resolver only for non-OneToOne relationships
            if not is_one_to_one_reverse:
                count_field_name = f"{accessor_name}_count"
                type_attrs[f"resolve_{count_field_name}"] = make_count_resolver(
                    accessor_name, is_one_to_one_reverse
                )

            # Add the accessor name to excluded fields to prevent Django from
            # generating the default Connection field
            exclude_fields.append(accessor_name)

        # Add @property methods as GraphQL fields
        properties = introspector.properties
        for prop_name, prop_info in properties.items():
            if not self._should_include_field(model, prop_name):
                continue

            # Convert the property's return type to a GraphQL field
            graphql_field = self._get_graphql_type_for_property(prop_info.return_type)
            type_attrs[prop_name] = graphql_field

            # Add resolver that calls the property
            def make_property_resolver(property_name):
                def resolver(self, info):
                    return getattr(self, property_name)

                return resolver

            type_attrs[f"resolve_{prop_name}"] = make_property_resolver(prop_name)

        # Create the type class with Meta configuration
        meta_attrs = {
            "model": model,
        }

        # Use either fields or exclude, not both
        if exclude_fields:
            meta_attrs["exclude"] = exclude_fields
        else:
            meta_attrs["fields"] = "__all__"

        # Check if this model has polymorphic children
        analysis = inheritance_handler.analyze_model_inheritance(model)

        type_attrs["Meta"] = type("Meta", (), meta_attrs)

        # Add polymorphic type resolution for base models
        if analysis and analysis.get("child_models"):
            # This is a polymorphic base model, add custom type resolution
            def is_type_of(root, info):
                """
                Custom type resolution for polymorphic models.
                Returns True if the instance can be represented by this type.
                """
                # For polymorphic base types, accept both base and child instances
                return isinstance(root, model)

            type_attrs["is_type_of"] = staticmethod(is_type_of)

            # Add polymorphic_type field to indicate the actual class name
            type_attrs["polymorphic_type"] = graphene.String(
                description="The actual class name of this polymorphic instance"
            )

            def resolve_polymorphic_type(self, info):
                """
                Resolver for polymorphic_type field.
                Returns the actual class name of the instance.
                """
                return self.__class__.__name__

            type_attrs["resolve_polymorphic_type"] = resolve_polymorphic_type

        model_type = type(class_name, (DjangoObjectType,), type_attrs)

        # For polymorphic models, don't add interface logic here
        # Union types will be handled at the query level

        self._type_registry[model] = model_type
        return model_type

    def generate_input_type(
        self,
        model: Type[models.Model],
        partial: bool = False,
        mutation_type: str = "create",
        include_reverse_relations: bool = True,
    ) -> Type[graphene.InputObjectType]:
        """
        Generates a GraphQL input type for mutations.
        Handles nested inputs, validation, and reverse relationships.

        Args:
            model: The Django model to generate input type for
            partial: Whether this is a partial input (for updates)
            mutation_type: Type of mutation ('create' or 'update') to determine field requirements
            include_reverse_relations: Whether to include reverse relationship fields for nested creation
        """

        # Check if we already have this input type to prevent infinite recursion
        cache_key = (model, partial, mutation_type, include_reverse_relations)
        if cache_key in self._input_type_registry:
            return self._input_type_registry[cache_key]

        introspector = ModelIntrospector(model)
        fields = introspector.get_model_fields()
        relationships = introspector.get_model_relationships()

        # Create input fields
        input_fields = {}

        for field_name, field_info in fields.items():
            if not self._should_include_field(model, field_name):
                continue

            # Skip id field for create and update mutations (id is passed as separate argument for updates)
            if field_name == "id":
                continue

            # Get field type, fallback to handle_custom_fields if not in mapping
            field_type = self._get_input_field_type(field_info.field_type)
            if not field_type:
                # Handle custom fields that aren't in FIELD_TYPE_MAP
                field_type = self.handle_custom_fields(field_info.field_type)

            # Determine if field should be required based on mutation type
            if mutation_type == "create":
                is_required = (
                    self._should_field_be_required_for_create(
                        field_info, field_name, model
                    )
                    and not partial
                )
            else:  # update
                # For updates, only id is required regardless of partial flag
                # All other fields are optional for partial updates
                is_required = self._should_field_be_required_for_update(
                    field_name, field_info, model
                )

            # Create the field with proper required handling
            if is_required:
                input_fields[field_name] = graphene.InputField(
                    graphene.NonNull(field_type), description=field_info.help_text
                )
            else:
                input_fields[field_name] = field_type(description=field_info.help_text)

        # Add forward relationship fields with automatic dual field generation
        for field_name, rel_info in relationships.items():
            if not self._should_include_field(model, field_name):
                continue

            # Get the actual Django field to check its requirements
            django_field = model._meta.get_field(field_name)

            # Create a FieldInfo object for the relationship field to check requirements
            from .introspector import FieldInfo

            rel_field_info = FieldInfo(
                field_type=type(django_field),
                is_required=not django_field.null,
                default_value=django_field.default
                if django_field.default is not models.NOT_PROVIDED
                else None,
                help_text=str(django_field.help_text),
                has_auto_now=getattr(django_field, "auto_now", False),
                has_auto_now_add=getattr(django_field, "auto_now_add", False),
                blank=getattr(django_field, "blank", False),
                has_default=django_field.default is not models.NOT_PROVIDED,
            )

            # Apply field requirement logic to relationship fields
            # For ManyToMany fields, use blank attribute instead of null
            if rel_info.relationship_type == "ManyToManyField":
                if mutation_type == "create":
                    is_required = not django_field.blank and not partial
                else:  # update
                    is_required = (
                        False  # All relationship fields are optional for updates
                    )
            else:
                if mutation_type == "create":
                    is_required = (
                        self._should_field_be_required_for_create(
                            rel_field_info, field_name, model
                        )
                        and not partial
                    )
                else:  # update
                    is_required = self._should_field_be_required_for_update(
                        field_name, rel_field_info, model
                    )

            # Always generate both nested and direct ID fields for all relationships
            if rel_info.relationship_type in ("ForeignKey", "OneToOneField"):
                # Check if this field is part of a mandatory dual field pair
                mandatory_fields = self._get_mandatory_fields(model)
                is_mandatory_dual_field = field_name in mandatory_fields

                # 1. Add direct ID field: <field_name>
                # For mandatory dual fields, make the direct field optional in schema
                # but enforce requirement in mutation logic
                if is_required and is_mandatory_dual_field:
                    # Make mandatory dual fields optional in GraphQL schema
                    input_fields[field_name] = graphene.ID()
                elif is_required:
                    # Regular required fields remain NonNull
                    input_fields[field_name] = graphene.InputField(graphene.ID)
                else:
                    # Optional fields remain optional
                    input_fields[field_name] = graphene.ID()

                # 2. Add nested field: nested_<field_name>
                nested_field_name = f"nested_{field_name}"
                nested_input_type = self._get_or_create_nested_input_type(
                    rel_info.related_model, mutation_type, exclude_parent_field=model
                )
                input_fields[nested_field_name] = graphene.InputField(nested_input_type)

            elif rel_info.relationship_type == "ManyToManyField":
                # 1. Add direct ID list field: <field_name>
                list_type = graphene.List(graphene.ID)
                if is_required:
                    input_fields[field_name] = graphene.NonNull(list_type)
                else:
                    input_fields[field_name] = list_type

                # 2. Add nested field: nested_<field_name>
                nested_field_name = f"nested_{field_name}"
                nested_input_type = self._get_or_create_nested_input_type(
                    rel_info.related_model, mutation_type, exclude_parent_field=model
                )
                input_fields[nested_field_name] = graphene.InputField(
                    graphene.List(nested_input_type)
                )

        # Add reverse relationship fields with dual field generation for nested operations (e.g., comments for Post)
        if include_reverse_relations:
            reverse_relations = self._get_reverse_relations(model)
            for field_name, related_model in reverse_relations.items():
                if not self._should_include_field(model, field_name):
                    continue

                # Always generate both direct ID list and nested fields for reverse relations
                # 1. Add direct ID list field: <field_name>
                input_fields[field_name] = graphene.List(graphene.ID)

                # 2. Add nested field: nested_<field_name>
                nested_field_name = f"nested_{field_name}"
                # Use the appropriate mutation type for nested input generation
                nested_mutation_type = (
                    "create" if mutation_type == "create" else "update"
                )
                nested_input_type = self._get_or_create_nested_input_type(
                    related_model, nested_mutation_type, exclude_parent_field=model
                )
                input_fields[nested_field_name] = graphene.List(nested_input_type)

        # Create the input type class
        # Generate different class names for different mutation types
        if mutation_type == "update" and partial:
            class_name = f"Update{model.__name__}Input"
        elif mutation_type == "create":
            class_name = f"Create{model.__name__}Input"
        else:
            class_name = f"{model.__name__}Input"
        input_type = type(
            class_name,
            (graphene.InputObjectType,),
            {
                "__doc__": f"Input type for creating/updating {model.__name__} instances with nested relationships.",
                **input_fields,
            },
        )

        # Store in registry with comprehensive cache key
        cache_key = (model, partial, mutation_type, include_reverse_relations)
        self._input_type_registry[cache_key] = input_type
        return input_type

    def generate_filter_type(self, model: Type[models.Model]) -> Type:
        """
        Generates a filter type for the model if Django-filter is installed.
        Configures available filter operations based on field types.
        """
        if not DJANGO_FILTER_INSTALLED or not self.settings.generate_filters:
            return None

        if model in self._filter_type_registry:
            return self._filter_type_registry[model]

        from django_filters import FilterSet

        introspector = ModelIntrospector(model)
        fields = introspector.get_model_fields()

        # Define filter fields
        filter_fields = {}
        for field_name, field_info in fields.items():
            if not self._should_include_field(model, field_name):
                continue

            filter_type = self._get_filter_field_type(field_info.field_type)
            if filter_type:
                filter_fields[field_name] = filter_type

        # Create the filter set class
        class_name = f"{model.__name__}Filter"

        # Add filter overrides for file fields
        filter_overrides = {
            models.FileField: {
                "filter_class": CharFilter,
                "extra": lambda f: {"lookup_expr": "exact"},
            },
            models.ImageField: {
                "filter_class": CharFilter,
                "extra": lambda f: {"lookup_expr": "exact"},
            },
        }

        meta_class = type(
            "Meta",
            (),
            {
                "model": model,
                "fields": filter_fields,
                "filter_overrides": filter_overrides,
            },
        )

        filter_class = type(
            class_name,
            (FilterSet,),
            {
                "Meta": meta_class,
                "__doc__": f"Filter set for {model.__name__} queries.",
            },
        )

        self._filter_type_registry[model] = filter_class
        return filter_class

    def _get_input_field_type(
        self, django_field_type: Type[Field]
    ) -> Optional[Type[graphene.Scalar]]:
        """Maps Django field types to GraphQL input field types."""
        return self.FIELD_TYPE_MAP.get(django_field_type)

    def _get_filter_field_type(self, django_field_type: Type[Field]) -> List[str]:
        """Determines available filter operations for a field type."""
        base_filters = ["exact", "in", "isnull"]
        text_filters = [
            "contains",
            "icontains",
            "startswith",
            "istartswith",
            "endswith",
            "iendswith",
        ]
        number_filters = ["gt", "gte", "lt", "lte", "range"]

        if issubclass(django_field_type, (models.CharField, models.TextField)):
            return base_filters + text_filters
        elif issubclass(
            django_field_type,
            (models.IntegerField, models.FloatField, models.DecimalField),
        ):
            return base_filters + number_filters
        elif issubclass(django_field_type, (models.DateField, models.DateTimeField)):
            return base_filters + number_filters + ["year", "month", "day"]
        else:
            return base_filters

    def _get_filterable_fields(self, model: Type[models.Model]) -> Dict[str, List[str]]:
        """
        Determines which fields should be filterable and what operations are available.
        """
        introspector = ModelIntrospector(model)
        fields = introspector.get_model_fields()

        filterable_fields = {}
        for field_name, field_info in fields.items():
            if self._should_include_field(model, field_name):
                filter_ops = self._get_filter_field_type(field_info.field_type)
                if filter_ops:
                    filterable_fields[field_name] = filter_ops

        return filterable_fields

    def handle_custom_fields(self, field: Field) -> Type[graphene.Scalar]:
        """
        Handles custom field types by attempting to map them to appropriate GraphQL types.
        Falls back to String if no specific mapping is found.
        """
        # Check if there's a custom mapping defined in settings
        if self.settings.custom_field_mappings:
            field_type = type(field)
            if field_type in self.settings.custom_field_mappings:
                return self.settings.custom_field_mappings[field_type]

        # Default to String for unknown field types
        return graphene.String

    def _get_reverse_relations(
        self, model: Type[models.Model]
    ) -> Dict[str, Type[models.Model]]:
        """
        Get reverse relationships for a model (e.g., comments for Post).

        Returns:
            Dict mapping field names to related models
        """
        reverse_relations = {}

        # For modern Django versions, use related_objects
        if hasattr(model._meta, "related_objects"):
            for rel in model._meta.related_objects:
                # Get the accessor name (e.g., 'comments' for Comment.post -> Post)
                accessor_name = rel.get_accessor_name()

                # Skip if accessor name is in excluded fields
                if not self._should_include_field(model, accessor_name):
                    continue

                reverse_relations[accessor_name] = rel.related_model
        # Fallback for Django versions that use get_fields() with related fields
        elif hasattr(model._meta, "get_fields"):
            try:
                for field in model._meta.get_fields():
                    # Check if it's a reverse relation (ForeignKey, OneToOneField, ManyToManyField)
                    if hasattr(field, "related_model") and hasattr(
                        field, "get_accessor_name"
                    ):
                        accessor_name = field.get_accessor_name()

                        if self._should_include_field(model, accessor_name):
                            reverse_relations[accessor_name] = field.related_model
            except AttributeError:
                # If get_fields doesn't work as expected, continue without reverse relations
                pass
        else:
            # Final fallback for very old Django versions
            try:
                for rel in model._meta.get_all_related_objects():
                    if hasattr(rel, "get_accessor_name"):
                        accessor_name = rel.get_accessor_name()
                    else:
                        accessor_name = rel.name

                    if self._should_include_field(model, accessor_name):
                        reverse_relations[accessor_name] = rel.related_model
            except AttributeError:
                # If get_all_related_objects doesn't exist, skip reverse relations
                pass

        return reverse_relations

    def _get_or_create_nested_input_type(
        self,
        model: Type[models.Model],
        mutation_type: str = "create",
        exclude_parent_field: Optional[Type[models.Model]] = None,
    ) -> Type[graphene.InputObjectType]:
        """
        Get or create a nested input type for a model, avoiding circular references.

        Args:
            model: The model to create input type for
            mutation_type: Type of mutation ('create' or 'update')
            exclude_parent_field: Parent model to exclude from nested input to prevent circular refs

        Returns:
            GraphQL input type for the model
        """
        # Create a simplified input type to avoid infinite recursion
        # Include exclude_parent_field in cache key to ensure different types for different parents
        exclude_suffix = (
            f"_exclude_{exclude_parent_field.__name__}" if exclude_parent_field else ""
        )
        cache_key = (
            f"{model.__name__}Nested{mutation_type.title()}Input{exclude_suffix}"
        )

        if cache_key in self._input_type_registry:
            return self._input_type_registry[cache_key]

        introspector = ModelIntrospector(model)
        fields = introspector.get_model_fields()
        relationships = introspector.get_model_relationships()

        input_fields = {}

        # Add regular fields
        for field_name, field_info in fields.items():
            if not self._should_include_field(model, field_name):
                continue

            # Skip id field for create mutations
            if mutation_type == "create" and field_name == "id":
                continue

            field_type = self._get_input_field_type(field_info.field_type)
            if not field_type:
                field_type = self.handle_custom_fields(field_info.field_type)

            # For nested inputs, make most fields optional to allow partial data
            is_required = False
            if mutation_type == "create":
                is_required = self._should_field_be_required_for_create(
                    field_info, field_name, model
                )

            input_fields[field_name] = field_type(
                required=is_required, description=field_info.help_text
            )

        # Add only essential relationship fields (avoid deep nesting)
        for field_name, rel_info in relationships.items():
            if not self._should_include_field(model, field_name):
                continue

            # Skip the parent field to prevent circular references
            if exclude_parent_field and rel_info.related_model == exclude_parent_field:
                continue

            # For nested inputs, use only ID references for relationships
            if rel_info.relationship_type in ("ForeignKey", "OneToOneField"):
                input_fields[field_name] = graphene.ID(required=False)
            elif rel_info.relationship_type == "ManyToManyField":
                input_fields[field_name] = graphene.List(graphene.ID)

        # Create the nested input type
        nested_input_type = type(
            cache_key,
            (graphene.InputObjectType,),
            {
                "__doc__": f"Nested input type for {model.__name__} in {mutation_type} operations.",
                **input_fields,
            },
        )

        self._input_type_registry[cache_key] = nested_input_type
        return nested_input_type

    def _should_include_nested_relations(self, model: Type[models.Model]) -> bool:
        """
        Check if nested relations should be included for this model.

        Args:
            model: The Django model to check

        Returns:
            bool: True if nested relations should be included
        """
        model_name = model.__name__

        # Check global setting first
        if not self.mutation_settings.enable_nested_relations:
            return False

        # Check per-model configuration
        if model_name in self.mutation_settings.nested_relations_config:
            return self.mutation_settings.nested_relations_config[model_name]

        # Default to enabled if no specific configuration
        return True

    def _should_include_nested_field(
        self, model: Type[models.Model], field_name: str
    ) -> bool:
        """
        Check if a specific nested field should be included for this model.

        Args:
            model: The Django model
            field_name: The field name to check

        Returns:
            bool: True if the nested field should be included
        """
        model_name = model.__name__

        # Check per-field configuration
        if model_name in self.mutation_settings.nested_field_config:
            field_config = self.mutation_settings.nested_field_config[model_name]
            if field_name in field_config:
                return field_config[field_name]

        # Check per-model configuration
        if model_name in self.mutation_settings.nested_relations_config:
            return self.mutation_settings.nested_relations_config[model_name]

        # Check global configuration
        if hasattr(self.mutation_settings, "enable_nested_relations"):
            return self.mutation_settings.enable_nested_relations

        # Default to ID-based operations when no configuration is specified
        return False

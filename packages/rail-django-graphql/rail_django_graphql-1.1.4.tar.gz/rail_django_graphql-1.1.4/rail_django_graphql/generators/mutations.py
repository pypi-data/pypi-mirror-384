"""
Mutation Generation System for Django GraphQL Auto-Generation

This module provides the MutationGenerator class, which is responsible for creating
GraphQL mutations for Django models, including CRUD operations and custom method mutations.
"""

from .types import TypeGenerator
from .nested_operations import NestedOperationHandler
from .introspector import MethodInfo, ModelIntrospector
from ..core.settings import MutationGeneratorSettings
from ..core.security import get_auth_manager, get_authz_manager, get_input_validator
from ..core.performance import get_query_optimizer
from ..core.error_handling import get_error_handler
from ..conf import get_mutation_generator_settings
import inspect
from typing import Any, Callable, Dict, List, Optional, Type, Union

import graphene
from django.core.exceptions import ValidationError
from django.db import models, transaction
from graphene_django import DjangoObjectType


class MutationError(graphene.ObjectType):
    """
    Structured error type for GraphQL mutations.

    Attributes:
        field: The field name where the error occurred (optional)
        message: The error message describing what went wrong
    """

    field = graphene.String(description="Le nom du champ où l'erreur s'est produite")
    message = graphene.String(
        required=True,
        description="Le message d'erreur décrivant ce qui s'est mal passé",
    )


class MutationGenerator:
    """
    Creates GraphQL mutations for Django models, supporting CRUD operations
    and custom method-based mutations.

    This class supports:
    - CRUD operations (Create, Read, Update, Delete)
    - Bulk operations for multiple records
    - Nested operations for related models
    - Security and authorization integration
    - Input validation and error handling
    - Performance optimization
    """

    def __init__(
        self,
        type_generator: TypeGenerator,
        settings: Optional[MutationGeneratorSettings] = None,
        schema_name: str = "default",
    ):
        """
        Initialize the MutationGenerator.

        Args:
            type_generator: TypeGenerator instance for creating GraphQL types
            settings: Mutation generator settings or None for defaults
            schema_name: Name of the schema for multi-schema support
        """
        self.type_generator = type_generator
        self.schema_name = schema_name

        # Use hierarchical settings if no explicit settings provided
        if settings is None:
            self.settings = MutationGeneratorSettings.from_schema(schema_name)
        else:
            self.settings = settings

        # Initialize security and performance components
        self.authentication_manager = get_auth_manager(schema_name)
        self.authorization_manager = get_authz_manager(schema_name)
        self.input_validator = get_input_validator(schema_name)
        self.error_handler = get_error_handler(schema_name)
        self.query_optimizer = get_query_optimizer(schema_name)

        # Pass mutation settings to type generator for nested relations configuration
        self.type_generator.mutation_settings = self.settings
        self._mutation_classes: Dict[str, Type[graphene.Mutation]] = {}
        self.nested_handler = NestedOperationHandler(self.settings)

    def generate_create_mutation(
        self, model: Type[models.Model]
    ) -> Type[graphene.Mutation]:
        """
        Generates a mutation for creating a new model instance.
        Supports nested creates for related objects.
        """
        model_type = self.type_generator.generate_object_type(model)
        input_type = self.type_generator.generate_input_type(
            model, mutation_type="create"
        )
        model_name = model.__name__

        class CreateMutation(graphene.Mutation):
            class Arguments:
                input = input_type(required=True)

            # Standardized return type
            ok = graphene.Boolean()
            object = graphene.Field(model_type)
            errors = graphene.List(MutationError)

            @classmethod
            @transaction.atomic
            def mutate(
                cls, root: Any, info: graphene.ResolveInfo, input: Dict[str, Any]
            ) -> "CreateMutation":
                try:
                    # Handle double quotes in string fields
                    input = cls._sanitize_input_data(input)

                    # Process dual fields with automatic priority handling
                    input = cls._process_dual_fields(input, model)

                    # Use the nested operation handler for advanced nested operations
                    nested_handler = cls._get_nested_handler(info)

                    # Validate nested data before processing
                    validation_errors = nested_handler.validate_nested_data(
                        model, input, "create"
                    )
                    if validation_errors:
                        return cls(ok=False, object=None, errors=validation_errors)

                    # Handle nested create with comprehensive validation and transaction management
                    instance = nested_handler.handle_nested_create(model, input)

                    return cls(ok=True, object=instance, errors=None)

                except ValidationError as e:
                    # Create structured error objects for validation errors
                    error_objects = []
                    # Prefer Django's message_dict for field-specific errors
                    if hasattr(e, "message_dict") and isinstance(
                        getattr(e, "message_dict"), dict
                    ):
                        for field, messages in e.message_dict.items():
                            for message in messages:
                                error_objects.append(
                                    MutationError(field=field, message=str(message))
                                )
                    # Fallback to error_dict if present
                    elif hasattr(e, "error_dict") and isinstance(
                        getattr(e, "error_dict"), dict
                    ):
                        for field, errors in e.error_dict.items():
                            for error in errors:
                                error_objects.append(
                                    MutationError(field=field, message=str(error))
                                )
                    else:
                        # General validation error: collect messages if available
                        if hasattr(e, "messages") and isinstance(
                            getattr(e, "messages"), list
                        ):
                            for msg in e.messages:
                                error_objects.append(
                                    MutationError(field=None, message=str(msg))
                                )
                        else:
                            error_objects.append(
                                MutationError(field=None, message=str(e))
                            )
                    return cls(ok=False, object=None, errors=error_objects)
                except Exception as e:
                    transaction.set_rollback(True)
                    error_objects = [
                        MutationError(
                            field=None,
                            message=f"Failed to create {model_name}: {str(e)}",
                        )
                    ]
                    return cls(ok=False, object=None, errors=error_objects)

            @classmethod
            def _sanitize_input_data(cls, input_data: Dict[str, Any]) -> Dict[str, Any]:
                """
                Sanitize input data to handle double quotes and other special characters.

                Args:
                    input_data: The input data to sanitize

                Returns:
                    Dict with sanitized data
                """

                def sanitize_value(value):
                    if isinstance(value, str):
                        # Handle double quotes by escaping them properly
                        return value.replace('""', '"')
                    elif isinstance(value, dict):
                        return {k: sanitize_value(v) for k, v in value.items()}
                    elif isinstance(value, list):
                        return [sanitize_value(item) for item in value]
                    return value

                return {k: sanitize_value(v) for k, v in input_data.items()}

            @classmethod
            def _process_dual_fields(
                cls, input_data: Dict[str, Any], model: Type[models.Model]
            ) -> Dict[str, Any]:
                """
                Process dual fields with automatic priority handling and validation.

                For OneToManyRel (ForeignKey, OneToOneField):
                - Validates mutual exclusivity: only one of nested_<field_name> or <field_name> should be provided
                - Enforces mandatory fields: ensures required fields have either direct or nested value
                - If both nested_<field_name> and <field_name> are provided, raises ValidationError

                For ManyToManyRel:
                - If nested_<field_name> is provided, create nested objects first and merge their IDs
                  into the direct assign data (<field_name>: [ID])

                Args:
                    input_data: The input data to process
                    model: The Django model

                Returns:
                    Dict with processed dual fields

                Raises:
                    ValidationError: If mutual exclusivity is violated or mandatory fields are missing
                """
                processed_data = input_data.copy()

                # Get model relationships
                introspector = ModelIntrospector(model)
                relationships = introspector.get_model_relationships()

                # Define mandatory fields that require either direct or nested value
                mandatory_fields = cls._get_mandatory_fields(model)

                for field_name, rel_info in relationships.items():
                    nested_field_name = f"nested_{field_name}"

                    if rel_info.relationship_type in ["ForeignKey", "OneToOneField"]:
                        # Check for mutual exclusivity violation
                        if (
                            nested_field_name in processed_data
                            and field_name in processed_data
                        ):
                            raise ValidationError({
                                field_name: f"Cannot provide both '{field_name}' and '{nested_field_name}'. Please provide only one."
                            })

                        # Check if mandatory field is missing
                        if field_name in mandatory_fields:
                            if (
                                nested_field_name not in processed_data
                                and field_name not in processed_data
                            ):
                                raise ValidationError({
                                    field_name: f"Field '{field_name}' is mandatory. Please provide either '{field_name}' or '{nested_field_name}'."
                                })

                        # Transform nested field to direct field for processing
                        if nested_field_name in processed_data:
                            # Transform nested field name to direct field name
                            processed_data[field_name] = processed_data.pop(
                                nested_field_name
                            )

                    elif rel_info.relationship_type == "ManyToManyField":
                        # ManyToManyRel: Create nested objects first, then merge IDs
                        if nested_field_name in processed_data:
                            nested_data = processed_data.pop(nested_field_name)

                            # For now, transform nested field to direct field for processing
                            # The nested operation handler will handle the actual creation
                            processed_data[field_name] = nested_data

                # Handle reverse relationships (e.g., comments for Post)
                reverse_relations = introspector.get_reverse_relations()
                for field_name, related_model in reverse_relations.items():
                    nested_field_name = f"nested_{field_name}"

                    if nested_field_name in processed_data:
                        # Transform nested field name to direct field name
                        processed_data[field_name] = processed_data.pop(
                            nested_field_name
                        )

                return processed_data

            @classmethod
            def _get_mandatory_fields(cls, model: Type[models.Model]) -> List[str]:
                """
                Get list of mandatory fields for the given model.

                Args:
                    model: The Django model

                Returns:
                    List of field names that are mandatory
                """
                # Define mandatory fields per model
                # This can be extended to read from model metadata or configuration
                mandatory_fields_map = {
                    'BlogPost': ['category'],
                    # Add other models and their mandatory fields here
                }

                model_name = model.__name__
                return mandatory_fields_map.get(model_name, [])

            @classmethod
            def _get_nested_handler(
                cls, info: graphene.ResolveInfo
            ) -> NestedOperationHandler:
                """Get the nested operation handler from the mutation generator."""
                # Access the mutation generator through the schema context
                if hasattr(info.context, "mutation_generator"):
                    return info.context.mutation_generator.nested_handler
                # Fallback to creating a new handler
                return NestedOperationHandler()

        return type(
            f"Create{model_name}",
            (CreateMutation,),
            {"__doc__": f"Create a new {model_name} instance"},
        )

    def generate_update_mutation(
        self, model: Type[models.Model]
    ) -> Type[graphene.Mutation]:
        """
        Generates a mutation for updating an existing model instance.
        Supports partial updates and nested updates for related objects.
        """
        model_type = self.type_generator.generate_object_type(model)
        input_type = self.type_generator.generate_input_type(
            model, partial=True, mutation_type="update"
        )
        model_name = model.__name__

        class UpdateMutation(graphene.Mutation):
            class Arguments:
                id = graphene.ID(required=True)
                input = input_type(required=True)

            # Standardized return type
            ok = graphene.Boolean()
            object = graphene.Field(model_type)
            errors = graphene.List(MutationError)

            @classmethod
            @transaction.atomic
            def mutate(
                cls,
                root: Any,
                info: graphene.ResolveInfo,
                id: str,
                input: Dict[str, Any],
            ) -> "UpdateMutation":
                try:
                    # Handle double quotes in string fields
                    input = cls._sanitize_input_data(input)

                    # Process dual fields with automatic priority handling
                    input = cls._process_dual_fields(input, model)

                    # Decode GraphQL ID to database ID if needed
                    try:
                        # Try to use the ID as-is first (for integer IDs)
                        instance = model.objects.get(pk=id)
                    except (ValueError, model.DoesNotExist):
                        # If that fails, try to decode as GraphQL global ID
                        from graphql_relay import from_global_id

                        try:
                            decoded_type, decoded_id = from_global_id(id)
                            instance = model.objects.get(pk=decoded_id)
                        except Exception:
                            # If all else fails, raise the original error
                            instance = model.objects.get(pk=id)

                    # Use the nested operation handler for advanced nested operations
                    nested_handler = cls._get_nested_handler(info)

                    # Validate nested data before processing
                    validation_errors = nested_handler.validate_nested_data(
                        model, input, "update"
                    )
                    if validation_errors:
                        return cls(ok=False, object=None, errors=validation_errors)

                    # Handle nested update with comprehensive validation and transaction management
                    instance = nested_handler.handle_nested_update(
                        model, input, instance
                    )

                    return UpdateMutation(ok=True, object=instance, errors=[])

                except model.DoesNotExist:
                    error_objects = [
                        MutationError(
                            field=None,
                            message=f"{model_name} with id {id} does not exist",
                        )
                    ]
                    return UpdateMutation(ok=False, object=None, errors=error_objects)
                except ValidationError as e:
                    # Create structured error objects for validation errors
                    error_objects = []
                    # Prefer Django's message_dict for field-specific errors
                    if hasattr(e, "message_dict") and isinstance(
                        getattr(e, "message_dict"), dict
                    ):
                        for field, messages in e.message_dict.items():
                            for message in messages:
                                error_objects.append(
                                    MutationError(field=field, message=str(message))
                                )
                    # Fallback to error_dict if present
                    elif hasattr(e, "error_dict") and isinstance(
                        getattr(e, "error_dict"), dict
                    ):
                        for field, errors in e.error_dict.items():
                            for error in errors:
                                error_objects.append(
                                    MutationError(field=field, message=str(error))
                                )
                    else:
                        # General validation error: collect messages if available
                        if hasattr(e, "messages") and isinstance(
                            getattr(e, "messages"), list
                        ):
                            for msg in e.messages:
                                error_objects.append(
                                    MutationError(field=None, message=str(msg))
                                )
                        else:
                            error_objects.append(
                                MutationError(field=None, message=str(e))
                            )
                    return UpdateMutation(ok=False, object=None, errors=error_objects)
                except Exception as e:
                    transaction.set_rollback(True)
                    error_objects = [
                        MutationError(
                            field=None,
                            message=f"Failed to update {model_name}: {str(e)}",
                        )
                    ]
                    return UpdateMutation(ok=False, object=None, errors=error_objects)

            @classmethod
            def _sanitize_input_data(cls, input_data: Dict[str, Any]) -> Dict[str, Any]:
                """
                Sanitize input data to handle double quotes and other special characters.

                Args:
                    input_data: The input data to sanitize

                Returns:
                    Dict with sanitized data
                """

                def sanitize_value(value):
                    if isinstance(value, str):
                        # Handle double quotes by escaping them properly
                        return value.replace('""', '"')
                    elif isinstance(value, dict):
                        return {k: sanitize_value(v) for k, v in value.items()}
                    elif isinstance(value, list):
                        return [sanitize_value(item) for item in value]
                    return value

                return {k: sanitize_value(v) for k, v in input_data.items()}

            @classmethod
            def _process_dual_fields(
                cls, input_data: Dict[str, Any], model: Type[models.Model]
            ) -> Dict[str, Any]:
                """
                Process dual fields with automatic priority handling and validation.

                For OneToManyRel (ForeignKey, OneToOneField):
                - Validates mutual exclusivity: only one of field or nested_field should be provided
                - Validates mandatory fields: ensures required fields have either direct or nested value
                - If both nested_<field_name> and <field_name> are provided, raises ValidationError

                For ManyToManyRel:
                - If nested_<field_name> is provided, create nested objects first and merge their IDs
                  into the direct assign data (<field_name>: [ID])

                Args:
                    input_data: The input data to process
                    model: The Django model

                Returns:
                    Dict with processed dual fields

                Raises:
                    ValidationError: If mutual exclusivity or mandatory field rules are violated
                """
                processed_data = input_data.copy()

                # Get model relationships
                introspector = ModelIntrospector(model)
                relationships = introspector.get_model_relationships()

                # Get mandatory fields for this model
                mandatory_fields = cls._get_mandatory_fields(model)

                for field_name, rel_info in relationships.items():
                    nested_field_name = f"nested_{field_name}"

                    if rel_info.relationship_type in ["ForeignKey", "OneToOneField"]:
                        has_direct = field_name in processed_data and processed_data[field_name] is not None
                        has_nested = nested_field_name in processed_data and processed_data[
                            nested_field_name] is not None

                        # Validate mutual exclusivity
                        if has_direct and has_nested:
                            raise ValidationError({
                                field_name: f"Cannot provide both '{field_name}' and '{nested_field_name}'. Please provide only one."
                            })

                        # Validate mandatory fields
                        if field_name in mandatory_fields and not has_direct and not has_nested:
                            raise ValidationError({
                                field_name: f"Field '{field_name}' is mandatory. Please provide either '{field_name}' or '{nested_field_name}'."
                            })

                        # OneToManyRel: Prioritize nested field over direct ID field
                        if has_nested:
                            # Transform nested field name to direct field name
                            processed_data[field_name] = processed_data.pop(
                                nested_field_name
                            )

                    elif rel_info.relationship_type == "ManyToManyField":
                        # ManyToManyRel: Create nested objects first, then merge IDs
                        if nested_field_name in processed_data:
                            nested_data = processed_data.pop(nested_field_name)

                            # For now, transform nested field to direct field for processing
                            # The nested operation handler will handle the actual creation
                            processed_data[field_name] = nested_data

                # Handle reverse relationships (e.g., comments for Post)
                reverse_relations = introspector.get_reverse_relations()
                for field_name, related_model in reverse_relations.items():
                    nested_field_name = f"nested_{field_name}"

                    if nested_field_name in processed_data:
                        # Transform nested field name to direct field name
                        processed_data[field_name] = processed_data.pop(
                            nested_field_name
                        )

                return processed_data

            @classmethod
            def _get_mandatory_fields(cls, model: Type[models.Model]) -> List[str]:
                """
                Get list of mandatory fields for the given model.
                Override this method to customize mandatory field requirements.

                Args:
                    model: The Django model class

                Returns:
                    List of field names that are mandatory
                """
                # For now, hardcode BlogPost category as mandatory
                # This should be made configurable in the future
                if model.__name__ == 'BlogPost':
                    return ['category']
                return []

            @classmethod
            def _get_nested_handler(
                cls, info: graphene.ResolveInfo
            ) -> NestedOperationHandler:
                """Get the nested operation handler from the mutation generator."""
                # Access the mutation generator through the schema context
                if hasattr(info.context, "mutation_generator"):
                    return info.context.mutation_generator.nested_handler
                # Fallback to creating a new handler
                return NestedOperationHandler()

        return type(
            f"Update{model_name}",
            (UpdateMutation,),
            {"__doc__": f"Update an existing {model_name} instance"},
        )

    def generate_delete_mutation(
        self, model: Type[models.Model]
    ) -> Type[graphene.Mutation]:
        """
        Generates a mutation for deleting a model instance.
        Supports cascade delete configuration.
        """
        model_type = self.type_generator.generate_object_type(model)
        model_name = model.__name__

        class DeleteMutation(graphene.Mutation):
            class Arguments:
                id = graphene.ID(required=True)

            # Standardized return type
            ok = graphene.Boolean()
            object = graphene.Field(model_type)
            errors = graphene.List(MutationError)

            @classmethod
            @transaction.atomic
            def mutate(
                cls, root: Any, info: graphene.ResolveInfo, id: str
            ) -> "DeleteMutation":
                try:
                    instance = model.objects.get(pk=id)
                    deleted_instance = instance  # Store reference before deletion
                    instance.delete()
                    return cls(ok=True, object=deleted_instance, errors=[])

                except model.DoesNotExist:
                    error_objects = [
                        MutationError(
                            field=None,
                            message=f"{model_name} with id {id} does not exist",
                        )
                    ]
                    return cls(ok=False, object=None, errors=error_objects)
                except Exception as e:
                    transaction.set_rollback(True)
                    error_objects = [
                        MutationError(
                            field=None,
                            message=f"Failed to delete {model_name}: {str(e)}",
                        )
                    ]
                    return cls(ok=False, object=None, errors=error_objects)

        return type(
            f"Delete{model_name}",
            (DeleteMutation,),
            {"__doc__": f"Delete a {model_name} instance"},
        )

    def generate_bulk_create_mutation(
        self, model: Type[models.Model]
    ) -> Type[graphene.Mutation]:
        """
        Generates a mutation for creating multiple model instances in bulk.
        """
        model_type = self.type_generator.generate_object_type(model)
        input_type = self.type_generator.generate_input_type(
            model, mutation_type="create"
        )
        model_name = model.__name__

        class BulkCreateMutation(graphene.Mutation):
            class Arguments:
                inputs = graphene.List(input_type, required=True)

            # Standardized return type
            ok = graphene.Boolean()
            objects = graphene.List(model_type)  # Using 'objects' for multiple items
            errors = graphene.List(MutationError)

            @classmethod
            @transaction.atomic
            def mutate(
                cls, root: Any, info: graphene.ResolveInfo, inputs: List[Dict[str, Any]]
            ) -> "BulkCreateMutation":
                try:
                    instances = []
                    for input_data in inputs:
                        instance = model.objects.create(**input_data)
                        instances.append(instance)

                    return cls(ok=True, objects=instances, errors=[])

                except ValidationError as e:
                    # Create structured error objects for validation errors
                    error_objects = []
                    if hasattr(e, "error_dict"):
                        # Field-specific validation errors
                        for field, errors in e.error_dict.items():
                            for error in errors:
                                error_objects.append(
                                    MutationError(field=field, message=str(error))
                                )
                    else:
                        # General validation error
                        error_objects.append(MutationError(field=None, message=str(e)))
                    return cls(ok=False, objects=[], errors=error_objects)
                except Exception as e:
                    transaction.set_rollback(True)
                    error_objects = [
                        MutationError(
                            field=None,
                            message=f"Failed to bulk create {model_name}s: {str(e)}",
                        )
                    ]
                    return cls(ok=False, objects=[], errors=error_objects)

        return type(
            f"BulkCreate{model_name}",
            (BulkCreateMutation,),
            {"__doc__": f"Create multiple {model_name} instances"},
        )

    def generate_bulk_update_mutation(
        self, model: Type[models.Model]
    ) -> Type[graphene.Mutation]:
        """
        Generates a mutation for updating multiple model instances in bulk.
        """
        model_type = self.type_generator.generate_object_type(model)
        input_type = self.type_generator.generate_input_type(
            model, partial=True, mutation_type="update"
        )
        model_name = model.__name__

        class BulkUpdateInput(graphene.InputObjectType):
            id = graphene.ID(required=True)
            data = input_type(required=True)

        class BulkUpdateMutation(graphene.Mutation):
            class Arguments:
                inputs = graphene.List(BulkUpdateInput, required=True)

            # Standardized return type
            ok = graphene.Boolean()
            objects = graphene.List(model_type)  # Using 'objects' for multiple items
            errors = graphene.List(MutationError)

            @classmethod
            @transaction.atomic
            def mutate(
                cls, root: Any, info: graphene.ResolveInfo, inputs: List[Dict[str, Any]]
            ) -> "BulkUpdateMutation":
                try:
                    instances = []
                    for input_data in inputs:
                        instance = model.objects.get(pk=input_data["id"])
                        for field, value in input_data["data"].items():
                            setattr(instance, field, value)
                        instance.full_clean()
                        instance.save()
                        instances.append(instance)

                    return cls(ok=True, objects=instances, errors=[])

                except model.DoesNotExist as e:
                    return cls(
                        ok=False,
                        objects=[],
                        errors=[f"{model_name} not found: {str(e)}"],
                    )
                except ValidationError as e:
                    return cls(ok=False, objects=[], errors=[str(e)])
                except Exception as e:
                    transaction.set_rollback(True)
                    return cls(
                        ok=False,
                        objects=[],
                        errors=[f"Failed to bulk update {model_name}s: {str(e)}"],
                    )

        return type(
            f"BulkUpdate{model_name}",
            (BulkUpdateMutation,),
            {"__doc__": f"Update multiple {model_name} instances"},
        )

    def generate_bulk_delete_mutation(
        self, model: Type[models.Model]
    ) -> Type[graphene.Mutation]:
        """
        Generates a mutation for deleting multiple model instances in bulk.
        """
        model_type = self.type_generator.generate_object_type(model)
        model_name = model.__name__

        class BulkDeleteMutation(graphene.Mutation):
            class Arguments:
                ids = graphene.List(graphene.ID, required=True)

            # Standardized return type
            ok = graphene.Boolean()
            objects = graphene.List(model_type)  # Return deleted objects
            errors = graphene.List(MutationError)

            @classmethod
            @transaction.atomic
            def mutate(
                cls, root: Any, info: graphene.ResolveInfo, ids: List[str]
            ) -> "BulkDeleteMutation":
                try:
                    instances = model.objects.filter(pk__in=ids)
                    if len(instances) != len(ids):
                        found_ids = set(str(instance.pk) for instance in instances)
                        missing_ids = set(ids) - found_ids
                        return cls(
                            ok=False,
                            objects=[],
                            errors=[
                                f"Some {model_name} instances not found: {', '.join(missing_ids)}"
                            ],
                        )

                    deleted_instances = list(instances)  # Store before deletion
                    instances.delete()
                    return cls(ok=True, objects=deleted_instances, errors=[])

                except model.DoesNotExist as e:
                    return cls(ok=False, objects=[], errors=[str(e)])
                except Exception as e:
                    transaction.set_rollback(True)
                    return cls(
                        ok=False,
                        objects=[],
                        errors=[f"Failed to bulk delete {model_name}s: {str(e)}"],
                    )

        return type(
            f"BulkDelete{model_name}",
            (BulkDeleteMutation,),
            {"__doc__": f"Delete multiple {model_name} instances"},
        )

    def convert_method_to_mutation(
        self,
        model: Type[models.Model],
        method_name: str,
        custom_input_type: Optional[Type[graphene.InputObjectType]] = None,
        custom_output_type: Optional[Type[graphene.ObjectType]] = None,
    ) -> Optional[Type[graphene.Mutation]]:
        """
        Converts a model method to a GraphQL mutation with enhanced capabilities.

        Args:
            model: The Django model class
            method_name: Name of the method to convert
            custom_input_type: Optional custom input type
            custom_output_type: Optional custom output type

        Returns:
            GraphQL mutation class or None if method not found
        """
        if not hasattr(model, method_name):
            return None

        method = getattr(model, method_name)
        if not callable(method):
            return None

        signature = inspect.signature(method)
        model_name = model.__name__

        # Create input type
        if custom_input_type:
            input_type = custom_input_type
        else:
            input_fields = {}
            for param_name, param in signature.parameters.items():
                if param_name == "self":
                    continue

                param_type = (
                    param.annotation
                    if param.annotation != inspect.Parameter.empty
                    else Any
                )
                graphql_type = self._convert_python_type_to_graphql(param_type)

                if param.default == inspect.Parameter.empty:
                    input_fields[param_name] = graphql_type(required=True)
                else:
                    input_fields[param_name] = graphql_type(default_value=param.default)

            input_type = (
                type(
                    f"{model_name}{method_name.title()}Input",
                    (graphene.InputObjectType,),
                    input_fields,
                )
                if input_fields
                else None
            )

        # Determine output type
        if custom_output_type:
            output_type = custom_output_type
        else:
            return_type = signature.return_annotation
            if return_type == inspect.Parameter.empty:
                output_type = graphene.Boolean
            else:
                output_type = self._convert_python_type_to_graphql(return_type)

        class ConvertedMethodMutation(graphene.Mutation):
            class Arguments:
                id = graphene.ID(required=True)

            # Standardized return format
            ok = graphene.Boolean()
            result = output_type()
            errors = graphene.List(MutationError)

            @classmethod
            @transaction.atomic
            def mutate(cls, root: Any, info: graphene.ResolveInfo, id: str, **kwargs):
                try:
                    # Check permissions if required
                    if hasattr(method, "_requires_permission"):
                        permission = method._requires_permission
                        if hasattr(info, "context") and hasattr(info.context, "user"):
                            if not info.context.user.has_perm(permission):
                                return cls(
                                    ok=False, result=None, errors=["Permission denied"]
                                )
                        else:
                            return cls(
                                ok=False,
                                result=None,
                                errors=["Authentication required"],
                            )

                    instance = model.objects.get(pk=id)
                    method_func = getattr(instance, method_name)

                    # Filter kwargs to only include method parameters
                    method_params = set(signature.parameters.keys()) - {"self"}
                    filtered_kwargs = {
                        k: v for k, v in kwargs.items() if k in method_params
                    }

                    # Execute method with filtered arguments
                    result = method_func(**filtered_kwargs)

                    # Handle model instance results
                    if isinstance(result, models.Model):
                        result.save()

                    return cls(ok=True, result=result, errors=[])

                except model.DoesNotExist:
                    return cls(
                        ok=False,
                        result=None,
                        errors=[f"{model_name} with id {id} does not exist"],
                    )
                except Exception as e:
                    transaction.set_rollback(True)
                    return cls(
                        ok=False,
                        result=None,
                        errors=[f"Failed to execute {method_name}: {str(e)}"],
                    )

        # Add method parameters as individual arguments
        for param_name, param in signature.parameters.items():
            if param_name == "self":
                continue

            param_type = (
                param.annotation if param.annotation != inspect.Parameter.empty else Any
            )
            graphql_type = self._convert_python_type_to_graphql(param_type)

            if param.default == inspect.Parameter.empty:
                setattr(
                    ConvertedMethodMutation.Arguments,
                    param_name,
                    graphql_type(required=True),
                )
            else:
                setattr(
                    ConvertedMethodMutation.Arguments,
                    param_name,
                    graphql_type(default_value=param.default),
                )

        # Preserve decorator metadata
        mutation_attrs = {
            "__doc__": method.__doc__ or f"Execute {method_name} on {model_name}"
        }

        # Check for business_logic decorator metadata
        if hasattr(method, "_business_logic_category"):
            mutation_attrs["_business_logic_category"] = method._business_logic_category
        if hasattr(method, "_requires_permission"):
            mutation_attrs["_requires_permission"] = method._requires_permission
        if hasattr(method, "_custom_mutation_name"):
            mutation_attrs["_custom_mutation_name"] = method._custom_mutation_name

        return type(
            f"{model_name}{method_name.title()}Mutation",
            (ConvertedMethodMutation,),
            mutation_attrs,
        )

    def _convert_python_type_to_graphql(
        self, python_type: Any
    ) -> Type[graphene.Scalar]:
        """
        Converts Python types to GraphQL types with enhanced mapping.

        Args:
            python_type: Python type annotation

        Returns:
            Corresponding GraphQL type
        """
        type_mapping = {
            str: graphene.String,
            int: graphene.Int,
            float: graphene.Float,
            bool: graphene.Boolean,
            Any: graphene.String,
            type(None): graphene.String,
        }

        # Handle Union types (e.g., Optional[str])
        if hasattr(python_type, "__origin__"):
            if python_type.__origin__ is Union:
                # For Optional types, use the non-None type
                args = python_type.__args__
                non_none_types = [arg for arg in args if arg is not type(None)]
                if non_none_types:
                    return self._convert_python_type_to_graphql(non_none_types[0])

        return type_mapping.get(python_type, graphene.String)

    def generate_method_mutation(
        self, model: Type[models.Model], method_info: MethodInfo
    ) -> Optional[Type[graphene.Mutation]]:
        """
        Generates a mutation from a model method.
        Analyzes method signature and return type to create appropriate mutation.
        Supports custom business logic and decorator-enhanced methods.
        """
        if not self.settings.enable_method_mutations:
            return None
        method_name = method_info.name
        method = getattr(model, method_name)
        signature = inspect.signature(method)
        model_name = model.__name__

        # Check for custom input/output types from decorators
        custom_input_type = getattr(method, "_mutation_input_type", None)
        custom_output_type = getattr(method, "_mutation_output_type", None)
        custom_name = getattr(method, "_custom_mutation_name", None)
        description = getattr(method, "_mutation_description", method.__doc__)
        is_business_logic = getattr(method, "_is_business_logic", False)
        requires_permission = getattr(method, "_requires_permission", None)
        atomic = getattr(method, "_atomic", True)

        # Create input type for method arguments
        if custom_input_type:
            input_type = custom_input_type
        else:
            input_fields = {}
            for param_name, param in signature.parameters.items():
                if param_name == "self":
                    continue

                param_type = (
                    param.annotation
                    if param.annotation != inspect.Parameter.empty
                    else Any
                )
                graphql_type = self._convert_python_type_to_graphql(param_type)

                if param.default == inspect.Parameter.empty:
                    input_fields[param_name] = graphql_type(required=True)
                else:
                    input_fields[param_name] = graphql_type(default_value=param.default)

            input_type = (
                type(
                    f"{model_name}{method_name.title()}Input",
                    (graphene.InputObjectType,),
                    input_fields,
                )
                if input_fields
                else None
            )

        # Determine return type
        if custom_output_type:
            output_type = custom_output_type
        else:
            return_type = signature.return_annotation
            if return_type == inspect.Parameter.empty:
                output_type = graphene.Boolean
            else:
                output_type = self._convert_python_type_to_graphql(return_type)

        class MethodMutation(graphene.Mutation):
            class Arguments:
                id = graphene.ID(required=True)
                if input_type:
                    input = input_type(required=True)

            # Standardized return format
            ok = graphene.Boolean()
            result = output_type()
            errors = graphene.List(MutationError)

            @classmethod
            def mutate(
                cls,
                root: Any,
                info: graphene.ResolveInfo,
                id: str,
                input: Dict[str, Any] = None,
            ):
                # Permission check if required
                if requires_permission and hasattr(info.context, "user"):
                    if not info.context.user.has_perm(requires_permission):
                        return cls(ok=False, result=None, errors=["Permission denied"])

                # Wrap in transaction if atomic is True
                if atomic:
                    return cls._atomic_mutate(model, method_name, id, input)
                else:
                    return cls._non_atomic_mutate(model, method_name, id, input)

            @classmethod
            @transaction.atomic
            def _atomic_mutate(cls, model, method_name, id, input):
                return cls._execute_method(model, method_name, id, input)

            @classmethod
            def _non_atomic_mutate(cls, model, method_name, id, input):
                return cls._execute_method(model, method_name, id, input)

            @classmethod
            def _execute_method(cls, model, method_name, id, input):
                try:
                    instance = model.objects.get(pk=id)
                    method_func = getattr(instance, method_name)

                    if input:
                        result = method_func(**input)
                    else:
                        result = method_func()

                    if isinstance(result, models.Model):
                        result.save()

                    return cls(ok=True, result=result, errors=[])

                except model.DoesNotExist:
                    return cls(
                        ok=False,
                        result=None,
                        errors=[f"{model.__name__} with id {id} does not exist"],
                    )
                except Exception as e:
                    if atomic:
                        transaction.set_rollback(True)
                    return cls(
                        ok=False,
                        result=None,
                        errors=[f"Failed to execute {method_name}: {str(e)}"],
                    )

        # Use custom name if provided
        mutation_name = custom_name or f"{model_name}{method_name.title()}"

        mutation_class = type(
            mutation_name,
            (MethodMutation,),
            {"__doc__": description or f"Execute {method_name} on {model_name}"},
        )

        # Add business logic metadata
        if is_business_logic:
            mutation_class._is_business_logic = True
            mutation_class._business_logic_category = getattr(
                method, "_business_logic_category", "general"
            )

        return mutation_class

    def generate_all_mutations(
        self, model: Type[models.Model]
    ) -> Dict[str, graphene.Field]:
        """
        Generates all mutations for a model, including CRUD operations and method mutations.
        """
        mutations = {}
        model_name = model.__name__.lower()
        # Generate CRUD mutations if enabled
        if self.settings.enable_create:
            mutation_class = self.generate_create_mutation(model)
            mutations[f"create_{model_name}"] = mutation_class.Field()

        if self.settings.enable_update:
            mutation_class = self.generate_update_mutation(model)
            mutations[f"update_{model_name}"] = mutation_class.Field()

        if self.settings.enable_delete:
            mutation_class = self.generate_delete_mutation(model)
            mutations[f"delete_{model_name}"] = mutation_class.Field()

        # Generate bulk mutations if enabled
        if self.settings.enable_bulk_operations:
            bulk_create_class = self.generate_bulk_create_mutation(model)
            mutations[f"bulk_create_{model_name}"] = bulk_create_class.Field()

            bulk_update_class = self.generate_bulk_update_mutation(model)
            mutations[f"bulk_update_{model_name}"] = bulk_update_class.Field()

            bulk_delete_class = self.generate_bulk_delete_mutation(model)
            mutations[f"bulk_delete_{model_name}"] = bulk_delete_class.Field()

        # Generate method mutations if enabled

        introspector = ModelIntrospector(model)
        for method_name, method_info in introspector.get_model_methods().items():
            if method_info.is_mutation and not method_info.is_private:
                mutation = self.generate_method_mutation(model, method_info)
                if mutation:
                    mutations[f"{model_name}_{method_name}"] = mutation.Field()
        return mutations

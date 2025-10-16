"""
GraphQL Meta utilities for Rail Django GraphQL.

This module provides utilities for working with GraphQL metadata
from Django models, including extracting GraphqlMeta configurations.
"""

from typing import Any, Dict, List, Optional, Type

from django.db import models


def get_model_graphql_meta(model: Type[models.Model]) -> Dict[str, Any]:
    """
    Extract GraphQL metadata from a Django model's GraphqlMeta class.

    Args:
        model: Django model class to extract metadata from

    Returns:
        Dictionary containing GraphQL metadata configuration

    Example:
        >>> meta = get_model_graphql_meta(MyModel)
        >>> print(meta.get('custom_filters', {}))
    """
    # Check if model has GraphqlMeta inner class
    if hasattr(model, 'GraphqlMeta'):
        graphql_meta = model.GraphqlMeta

        # Extract all attributes from GraphqlMeta
        meta_dict = {}

        # Common GraphqlMeta attributes
        for attr_name in dir(graphql_meta):
            if not attr_name.startswith('_'):
                attr_value = getattr(graphql_meta, attr_name)
                if not callable(attr_value):
                    meta_dict[attr_name] = attr_value

        return meta_dict

    # Return empty dict if no GraphqlMeta found
    return {}


def get_custom_filters(model: Type[models.Model]) -> Dict[str, Any]:
    """
    Get custom filters from model's GraphqlMeta.

    Args:
        model: Django model class

    Returns:
        Dictionary of custom filters
    """
    meta = get_model_graphql_meta(model)
    return meta.get('custom_filters', {})


def get_quick_filter_fields(model: Type[models.Model]) -> List[str]:
    """
    Get quick filter fields from model's GraphqlMeta.

    Args:
        model: Django model class

    Returns:
        List of quick filter field names
    """
    meta = get_model_graphql_meta(model)
    return meta.get('quick_filter_fields', [])


def get_filter_fields(model: Type[models.Model]) -> Dict[str, Any]:
    """
    Get filter fields configuration from model's GraphqlMeta.

    Args:
        model: Django model class

    Returns:
        Dictionary of filter fields configuration
    """
    meta = get_model_graphql_meta(model)
    return meta.get('filters', {})

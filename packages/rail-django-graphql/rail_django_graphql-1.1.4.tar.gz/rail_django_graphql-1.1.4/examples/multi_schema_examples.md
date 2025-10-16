# Multi-Schema Examples

This document provides runnable snippets and patterns for registering and using multiple GraphQL schemas.

## Register Schemas

```python
from rail_django_graphql.core.registry import schema_registry

schema_registry.register_schema(
    name="public_api",
    description="Public API",
    enabled=True,
    settings={"enable_graphiql": True, "authentication_required": False},
)

schema_registry.register_schema(
    name="admin_api",
    description="Admin API",
    enabled=True,
    settings={"enable_graphiql": True, "authentication_required": True},
)
```

## URLs

```python
from django.urls import path
from rail_django_graphql.views.graphql_views import MultiSchemaGraphQLView, SchemaListView, GraphQLPlaygroundView

urlpatterns = [
    path('graphql/<str:schema_name>/', MultiSchemaGraphQLView.as_view()),
    path('schemas/', SchemaListView.as_view()),
    path('playground/<str:schema_name>/', GraphQLPlaygroundView.as_view()),
]
```

## Try It

- POST GraphQL queries to `/graphql/public_api/`
- Open Playground at `/playground/admin_api/` (if enabled)
- List schemas at `/schemas/`

For a deeper guide, see `rail-django-graphql/docs/usage/multi-schema-setup.md`.
# Views and Schema Registry

## MultiSchemaGraphQLView

- Route: `GET/POST /graphql/<schema_name>/`
- Dynamically selects the GraphQL schema by `schema_name`
- Respects per-schema settings: `authentication_required`, `enable_graphiql`
- Returns appropriate status codes for missing or disabled schemas

See implementation: `rail_django_graphql/views/graphql_views.py`.

## SchemaListView

- Route: `GET /schemas/`
- Lists registered schemas with metadata (name, description, version, enabled, graphiql status, auth requirement)

## GraphQLPlaygroundView

- Route: `GET /playground/<schema_name>/`
- Renders a schema-specific GraphQL Playground when enabled

## Schema Registry

Use `schema_registry` to register and retrieve schemas.

```python
from rail_django_graphql.core.registry import schema_registry

schema_registry.register_schema(
    name="example_api",
    description="Example API",
    version="1.0.0",
    apps=["app1"],
    models=["ModelA"],
    enabled=True,
    settings={
        "authentication_required": False,
        "enable_graphiql": True,
    },
)

info = schema_registry.get_schema("example_api")
```

Integration tests: `rail_django_graphql/tests/integration/test_multi_schema.py`.
# Basic Usage

This guide covers the fundamental usage patterns of the Rail Django GraphQL library, including auto-generated types, queries, and mutations.

## Overview

- Object types generated from Django models
- Queries: single, list, paginated
- Mutations: create, update, delete
- Filters and input types

See practical examples in `rail-django-graphql/examples/basic_usage.py` and in the project docs `docs/usage/basic-usage.md`.

## Quick Example

```python
from rail_django_graphql import TypeGenerator, QueryGenerator, MutationGenerator

# Generate types
# UserType = TypeGenerator.from_model(User)

# Queries
# users = QueryGenerator.list_field(User)

# Mutations
# create_user = MutationGenerator.create_mutation(User)
```
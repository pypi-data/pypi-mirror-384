# Multiple Django Model Managers Support

The `rail-django-graphql` library now supports multiple Django model managers, automatically generating GraphQL queries for each manager with appropriate naming conventions.

## Overview

Django models can have multiple managers to provide different views of the same data. For example, you might have:
- A default `objects` manager that returns all records
- A `published` manager that returns only published records  
- A `featured` manager that returns only featured records

This library now automatically detects all managers on your Django models and generates corresponding GraphQL queries for each one.

## Features

- **Automatic Manager Detection**: Discovers all managers defined on Django models
- **Smart Naming Conventions**: Uses consistent naming patterns for generated queries
- **Full Query Support**: Generates single, list, and paginated queries for each manager
- **Backward Compatibility**: Default manager queries maintain existing naming conventions

## Naming Conventions

### Default Manager (usually `objects`)

The default manager maintains the existing naming conventions:

- **Single object**: `modelname` (e.g., `article`)
- **List query**: `modelnames` (e.g., `articles`)  
- **Paginated query**: `modelnames_pages` (e.g., `articles_pages`)

### Custom Managers

Custom managers use a new naming convention to avoid conflicts:

- **Single object**: `modelname__managername` (e.g., `article__published`)
- **List query**: `modelnames__managername` (e.g., `articles__published`)
- **Paginated query**: `modelnames_pages_managername` (e.g., `articles_pages_published`)

## Example Usage

### Django Model Definition

```python
from django.db import models

class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_published=True)

class FeaturedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_featured=True)

class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Default manager
    objects = models.Manager()
    
    # Custom managers
    published = PublishedManager()
    featured = FeaturedManager()
```

### Generated GraphQL Queries

The library will automatically generate the following GraphQL queries:

#### Default Manager Queries

```graphql
# Single article (any article)
query {
  article(id: 1) {
    id
    title
    content
    isPublished
    isFeatured
  }
}

# All articles
query {
  articles {
    id
    title
    isPublished
    isFeatured
  }
}

# Paginated articles
query {
  articles_pages(page: 1, perPage: 10) {
    items {
      id
      title
    }
    pageInfo {
      currentPage
      totalPages
      hasNextPage
    }
  }
}
```

#### Published Manager Queries

```graphql
# Single published article
query {
  article__published(id: 1) {
    id
    title
    content
  }
}

# All published articles
query {
  articles__published {
    id
    title
    content
  }
}

# Paginated published articles
query {
  articles_pages_published(page: 1, perPage: 10) {
    items {
      id
      title
      content
    }
    pageInfo {
      currentPage
      totalPages
      hasNextPage
    }
  }
}
```

#### Featured Manager Queries

```graphql
# Single featured article
query {
  article__featured(id: 1) {
    id
    title
    content
  }
}

# All featured articles
query {
  articles__featured {
    id
    title
    content
  }
}

# Paginated featured articles
query {
  articles_pages_featured(page: 1, perPage: 10) {
    items {
      id
      title
      content
    }
    pageInfo {
      currentPage
      totalPages
      hasNextPage
    }
  }
}
```

## Implementation Details

### Manager Detection

The library uses the `ModelIntrospector` class to detect managers:

```python
from rail_django_graphql.generators.introspector import ModelIntrospector

introspector = ModelIntrospector(Article)
managers = introspector.get_model_managers()

# Returns a dictionary like:
# {
#     'objects': ManagerInfo(name='objects', is_default=True, manager_class=Manager),
#     'published': ManagerInfo(name='published', is_default=False, manager_class=PublishedManager),
#     'featured': ManagerInfo(name='featured', is_default=False, manager_class=FeaturedManager)
# }
```

### Query Generation

The `QueryGenerator` class has been updated to accept manager names:

```python
# Generate queries for a specific manager
single_query = query_generator.generate_single_query(Article, 'published')
list_query = query_generator.generate_list_query(Article, 'published')
paginated_query = query_generator.generate_paginated_query(Article, 'published')
```

### Schema Building

The `SchemaBuilder` automatically generates queries for all detected managers:

```python
from rail_django_graphql.core.schema import SchemaBuilder

schema_builder = SchemaBuilder()
schema = schema_builder.get_schema()

# The schema will include queries for all managers
```

## Configuration

### Excluding Managers

You can exclude specific managers from GraphQL generation by configuring the introspector:

```python
# This feature may be added in future versions
# Currently, all detected managers are included
```

### Custom Naming

The naming conventions are currently fixed, but future versions may allow customization:

```python
# Future feature - custom naming patterns
# MANAGER_NAMING = {
#     'single': '{model}__{manager}',
#     'list': '{model}s__{manager}',
#     'paginated': '{model}s_pages_{manager}'
# }
```

## Best Practices

1. **Manager Naming**: Use descriptive manager names that clearly indicate their purpose
2. **Default Manager**: Always define a default manager (usually `objects`) first
3. **Performance**: Custom managers should include appropriate database optimizations
4. **Documentation**: Document what each manager returns in your model docstrings

## Troubleshooting

### Common Issues

1. **Manager Not Detected**: Ensure the manager is properly defined as a class attribute
2. **Naming Conflicts**: Avoid manager names that conflict with existing GraphQL field names
3. **Query Errors**: Verify that custom managers return valid querysets

### Debug Information

Enable debug logging to see manager detection:

```python
import logging
logging.getLogger('rail_django_graphql').setLevel(logging.DEBUG)
```

## Migration Guide

### From Previous Versions

This feature is backward compatible. Existing GraphQL queries will continue to work unchanged. New queries for custom managers will be automatically available.

### Testing Your Implementation

Use the provided test script to verify manager detection:

```bash
python test_custom_managers.py
```

## Examples

See the `examples/multiple_managers_example.py` file for a complete working example.

## Future Enhancements

- Custom naming pattern configuration
- Manager-specific filtering and ordering
- Manager exclusion configuration
- Advanced manager introspection features
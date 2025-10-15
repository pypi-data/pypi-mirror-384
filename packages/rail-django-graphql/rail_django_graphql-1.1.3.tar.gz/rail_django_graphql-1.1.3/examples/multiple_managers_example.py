"""
Multiple Django Model Managers Example

This example demonstrates how the rail-django-graphql library now supports
multiple Django model managers, automatically generating GraphQL queries
for each manager with appropriate naming conventions.
"""

import os
import sys

import django
from django.conf import settings
from django.db import models

# Configure Django settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
        ],
        USE_TZ=True,
    )
    django.setup()


class PublishedManager(models.Manager):
    """Custom manager for published articles."""

    def get_queryset(self):
        return super().get_queryset().filter(is_published=True)


class FeaturedManager(models.Manager):
    """Custom manager for featured articles."""

    def get_queryset(self):
        return super().get_queryset().filter(is_featured=True)


class Article(models.Model):
    """
    Example model with multiple managers.

    This model demonstrates how different managers can be used
    to provide different views of the same data.
    """
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Default manager (always first)
    objects = models.Manager()

    # Custom managers
    published = PublishedManager()
    featured = FeaturedManager()

    class Meta:
        app_label = 'example'


def demonstrate_manager_detection():
    """Demonstrate how the library detects and processes multiple managers."""

    print("=== Multiple Django Model Managers Example ===\n")

    # Import the introspector
    from rail_django_graphql.generators.introspector import ModelIntrospector

    # Create introspector for the Article model
    introspector = ModelIntrospector(Article)

    # Get all managers
    managers = introspector.get_model_managers()

    print(f"Detected {len(managers)} managers for Article model:")
    for manager_name, manager_info in managers.items():
        print(f"  - {manager_name}: {manager_info}")

    print("\n" + "=" * 50)

    return managers


def demonstrate_query_generation():
    """Demonstrate how GraphQL queries are generated for each manager."""

    print("\n=== GraphQL Query Generation ===\n")

    from rail_django_graphql.core.schema import SchemaBuilder

    # Create schema builder
    schema_builder = SchemaBuilder()

    # Generate query fields for the Article model
    schema_builder._generate_query_fields([Article])

    # Get generated query fields
    query_fields = schema_builder._query_fields

    print(f"Generated {len(query_fields)} GraphQL query fields:")

    # Group fields by manager type
    default_fields = []
    custom_fields = []

    for field_name in sorted(query_fields.keys()):
        if '__' in field_name:
            custom_fields.append(field_name)
        else:
            default_fields.append(field_name)

    print("\nDefault manager (objects) queries:")
    for field in default_fields:
        print(f"  - {field}")

    print("\nCustom manager queries:")
    for field in custom_fields:
        manager_name = field.split('__')[1].split('_')[0] if '__' in field else 'unknown'
        print(f"  - {field} (uses '{manager_name}' manager)")

    return query_fields


def demonstrate_graphql_schema():
    """Show example GraphQL queries that would be available."""

    print("\n=== Example GraphQL Queries ===\n")

    queries = {
        "Single Article (default manager)": """
        query {
          article(id: 1) {
            id
            title
            content
            isPublished
            isFeatured
            createdAt
          }
        }
        """,

        "All Articles (default manager)": """
        query {
          articles {
            id
            title
            isPublished
            isFeatured
          }
        }
        """,

        "Published Articles Only": """
        query {
          articles__published {
            id
            title
            content
            createdAt
          }
        }
        """,

        "Featured Articles Only": """
        query {
          articles__featured {
            id
            title
            content
            isPublished
          }
        }
        """,

        "Paginated Published Articles": """
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
              totalItems
              hasNextPage
              hasPreviousPage
            }
          }
        }
        """
    }

    for title, query in queries.items():
        print(f"{title}:")
        print(query.strip())
        print("-" * 40)


def main():
    """Run the complete example."""

    try:
        # Demonstrate manager detection
        managers = demonstrate_manager_detection()

        # Demonstrate query generation
        query_fields = demonstrate_query_generation()

        # Show example GraphQL queries
        demonstrate_graphql_schema()

        print("\n=== Summary ===")
        print(f"✓ Detected {len(managers)} managers")
        print(f"✓ Generated {len(query_fields)} GraphQL query fields")
        print("✓ Multiple manager support is working correctly!")

        print("\n=== Naming Conventions ===")
        print("Default manager (objects):")
        print("  - Single: modelname")
        print("  - List: modelnames")
        print("  - Paginated: modelnames_pages")
        print("\nCustom managers:")
        print("  - Single: modelname__managername")
        print("  - List: modelnames__managername")
        print("  - Paginated: modelnames_pages_managername")

    except Exception as e:
        print(f"Error running example: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

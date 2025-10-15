# GraphQLMeta Configuration Guide

This guide covers the `GraphQLMeta` class, which provides advanced configuration options for customizing GraphQL schema generation, filtering, and query behavior for Django models.

## 📚 Table of Contents

- [Overview](#overview)
- [GraphQLMeta Field Reference](#graphqlmeta-field-reference)
  - [Core Configuration](#core-configuration)
  - [Filtering & Search](#filtering--search)
  - [Performance Optimization](#performance-optimization)
  - [Field Management](#field-management)
  - [Query Customization](#query-customization)
  - [Ordering & Pagination](#ordering--pagination)
- [Basic Configuration](#basic-configuration)
- [Custom Resolvers](#custom-resolvers)
- [Custom Filters](#custom-filters)
- [Quick Filter](#quick-filter)
- [Date/DateTime Filters](#datetime-filters)
- [Field Configuration](#field-configuration)
- [Complete Examples](#complete-examples)
- [Best Practices](#best-practices)

## 🔍 Overview

The `GraphQLMeta` class allows you to extend and customize the GraphQL schema generation for your Django models. It provides fine-grained control over:

- **Custom Resolvers**: Intercept and modify model queries
- **Custom Filters**: Define specialized filtering logic
- **Quick Filter**: Enable cross-field search functionality
- **Field Configuration**: Control field inclusion, exclusion, and behavior
- **Date/DateTime Filters**: Built-in time-based filtering options
- **Performance Optimization**: Query optimization with select_related and prefetch_related
- **Ordering & Pagination**: Control sorting and pagination behavior

## 📋 GraphQLMeta Field Reference

This section provides a comprehensive reference of all available `GraphQLMeta` configuration fields, organized by category and utility.

### Core Configuration

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `include_fields` | `list[str]` | Explicitly include only these fields in the GraphQL schema | `['title', 'content', 'author']` |
| `exclude_fields` | `list[str]` | Exclude these fields from the GraphQL schema | `['internal_notes', 'password']` |
| `field_config` | `dict` | Advanced field-specific configuration | `{'title': {'max_length': 200}}` |
| `relationship_config` | `dict` | Configuration for relationship fields | `{'author': {'select_related': True}}` |

### Filtering & Search

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `filter_fields` | `dict` | Define filterable fields and their lookup types | `{'title': ['exact', 'icontains'], 'date': ['gt', 'lt']}` |
| `quick_filter_fields` | `list[str]` | Fields to include in quick search functionality | `['title', 'content', 'author__username']` |
| `custom_filters` | `dict` | Custom filter methods for complex filtering logic | `{'published': 'filter_published_posts'}` |
| `filters` | `dict` | Alternative way to define filters with quick search | `{'quick': ['title', 'content']}` |

### Performance Optimization

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `select_related` | `list[str]` | Fields to select_related for query optimization | `['author', 'category']` |
| `prefetch_related` | `list[str]` | Fields to prefetch_related for query optimization | `['tags', 'comments']` |

### Field Management

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `nested_field_config` | `dict` | Configuration for nested relationship fields | `{'author': {'include_fields': ['username', 'email']}}` |

### Query Customization

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `custom_resolvers` | `dict` | Custom resolver methods for specialized queries | `{'popular_posts': 'get_popular_posts'}` |

### Ordering & Pagination

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `ordering_fields` | `list[str]` | Fields available for ordering results | `['title', 'created_at', 'author__username']` |

### Field Details and Usage Examples

#### Core Configuration Fields

**`include_fields`** - Whitelist Approach
```python
class GraphQLMeta(GraphQLMeta):
    include_fields = ['title', 'content', 'author', 'published_date']
    # Only these fields will be available in GraphQL
```

**`exclude_fields`** - Blacklist Approach
```python
class GraphQLMeta(GraphQLMeta):
    exclude_fields = ['internal_notes', 'password_hash', 'secret_key']
    # All fields except these will be available
```

**`field_config`** - Advanced Field Configuration
```python
class GraphQLMeta(GraphQLMeta):
    field_config = {
        'title': {
            'description': 'The blog post title',
            'max_length': 200,
            'required': True
        },
        'content': {
            'description': 'The main content of the blog post',
            'strip_html': True
        }
    }
```

**`relationship_config`** - Relationship Field Configuration
```python
class GraphQLMeta(GraphQLMeta):
    relationship_config = {
        'author': {
            'select_related': True,
            'include_fields': ['username', 'email', 'first_name']
        },
        'category': {
            'select_related': True,
            'exclude_fields': ['internal_code']
        }
    }
```

#### Filtering & Search Fields

**`filter_fields`** - Standard Filtering
```python
class GraphQLMeta(GraphQLMeta):
    filter_fields = {
        'title': ['exact', 'icontains', 'startswith', 'endswith'],
        'is_published': ['exact'],
        'published_date': ['exact', 'gt', 'gte', 'lt', 'lte', 'range'],
        'author': ['exact', 'in'],
        'category': ['exact', 'in'],
        'tags': ['exact', 'in', 'isnull'],
        'view_count': ['exact', 'gt', 'gte', 'lt', 'lte', 'range']
    }
```

**`quick_filter_fields`** - Cross-Field Search
```python
class GraphQLMeta(GraphQLMeta):
    quick_filter_fields = [
        'title',           # Search in title
        'content',         # Search in content
        'author__username', # Search in related author username
        'author__email',   # Search in related author email
        'tags__name'       # Search in related tag names
    ]
```

**`custom_filters`** - Advanced Custom Filtering
```python
class GraphQLMeta(GraphQLMeta):
    custom_filters = {
        'published': 'filter_published_posts',
        'popular': 'filter_popular_posts',
        'recent': 'filter_recent_posts',
        'by_author_type': 'filter_by_author_type'
    }

@classmethod
def filter_published_posts(cls, queryset, info, value=None, **kwargs):
    """Filter for published posts only."""
    if value:
        return queryset.filter(is_published=True, published_date__lte=timezone.now())
    return queryset

@classmethod
def filter_popular_posts(cls, queryset, info, min_views=100, **kwargs):
    """Filter posts by minimum view count."""
    return queryset.filter(view_count__gte=min_views)
```

**`filters`** - Alternative Filter Configuration
```python
class GraphQLMeta(GraphQLMeta):
    filters = {
        'quick': ['title', 'content', 'author__username'],  # Quick search fields
        'advanced': {
            'title': ['exact', 'icontains'],
            'published_date': ['gt', 'lt', 'range']
        }
    }
```

#### Performance Optimization Fields

**`select_related`** - Optimize Foreign Key Queries
```python
class GraphQLMeta(GraphQLMeta):
    select_related = [
        'author',          # ForeignKey to User
        'category',        # ForeignKey to Category
        'author__profile'  # Nested relationship
    ]
```

**`prefetch_related`** - Optimize Many-to-Many and Reverse Foreign Key Queries
```python
class GraphQLMeta(GraphQLMeta):
    prefetch_related = [
        'tags',                    # ManyToManyField
        'comments',                # Reverse ForeignKey
        'comments__author',        # Nested prefetch
        'tags__category'           # Nested prefetch through M2M
    ]
```

#### Query Customization Fields

**`custom_resolvers`** - Custom Query Logic
```python
class GraphQLMeta(GraphQLMeta):
    custom_resolvers = {
        'trending': 'get_trending_posts',
        'featured': 'get_featured_posts',
        'by_category': 'get_posts_by_category',
        'author_favorites': 'get_author_favorite_posts'
    }

@classmethod
def get_trending_posts(cls, queryset, info, days=7, **kwargs):
    """Get trending posts based on recent activity."""
    from datetime import datetime, timedelta
    cutoff_date = datetime.now() - timedelta(days=days)
    
    return queryset.annotate(
        recent_views=Count('views', filter=Q(views__created_at__gte=cutoff_date)),
        recent_comments=Count('comments', filter=Q(comments__created_at__gte=cutoff_date))
    ).filter(
        Q(recent_views__gte=10) | Q(recent_comments__gte=5)
    ).order_by('-recent_views', '-recent_comments')

@classmethod
def get_posts_by_category(cls, queryset, info, category_slug=None, **kwargs):
    """Get posts filtered by category slug."""
    if category_slug:
        return queryset.filter(category__slug=category_slug)
    return queryset
```

#### Ordering & Pagination Fields

**`ordering_fields`** - Available Sorting Options
```python
class GraphQLMeta(GraphQLMeta):
    ordering_fields = [
        'title',                   # Sort by title
        'published_date',          # Sort by publication date
        'view_count',              # Sort by view count
        'author__username',        # Sort by author username
        'category__name',          # Sort by category name
        'comments_count',          # Sort by comment count (if annotated)
        '-published_date'          # Descending sort (optional, handled by GraphQL)
    ]
```

## 🚀 Basic Configuration

### Adding GraphQLMeta to Your Model

```python
from django.db import models
from rail_django_graphql.core.meta import GraphQLMeta

class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    published_date = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=False)
    tags = models.ManyToManyField('Tag', blank=True)

    class GraphQLMeta(GraphQLMeta):
        # Basic field configuration
        exclude_fields = ['internal_notes']
        include_fields = ['title', 'content', 'author', 'published_date']
        
        # Enable filtering and ordering
        filter_fields = {
            'title': ['exact', 'icontains', 'startswith'],
            'is_published': ['exact'],
            'published_date': ['exact', 'gt', 'lt', 'range'],
            'author': ['exact'],
            'category': ['exact', 'in'],
        }
        
        ordering_fields = ['title', 'published_date', 'author__username']
```

## 🔧 Custom Resolvers

Custom resolvers allow you to intercept and modify queries before they're executed:

```python
from django.db.models import Q, Count
from django_filters import CharFilter

class BlogPost(models.Model):
    # ... model fields ...

    class GraphQLMeta(GraphQLMeta):
        custom_resolvers = {
            'popular_posts': 'get_popular_posts',
            'recent_posts': 'get_recent_posts',
            'author_posts': 'get_posts_by_author',
        }

    @classmethod
    def get_popular_posts(cls, queryset, info, **kwargs):
        """Get posts with high engagement."""
        return queryset.annotate(
            comment_count=Count('comments')
        ).filter(
            comment_count__gte=10,
            is_published=True
        ).order_by('-comment_count')

    @classmethod
    def get_recent_posts(cls, queryset, info, **kwargs):
        """Get posts from the last 30 days."""
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.now() - timedelta(days=30)
        return queryset.filter(
            published_date__gte=thirty_days_ago,
            is_published=True
        ).order_by('-published_date')

    @classmethod
    def get_posts_by_author(cls, queryset, info, author_id=None, **kwargs):
        """Get posts by specific author."""
        if author_id:
            return queryset.filter(author_id=author_id, is_published=True)
        return queryset.filter(is_published=True)
```

### Using Custom Resolvers in GraphQL

```graphql
query {
  # Using custom resolvers
  popularPosts {
    edges {
      node {
        title
        commentCount
        author {
          username
        }
      }
    }
  }
  
  recentPosts {
    edges {
      node {
        title
        publishedDate
      }
    }
  }
  
  authorPosts(authorId: 1) {
    edges {
      node {
        title
        author {
          username
        }
      }
    }
  }
}
```

## 🎯 Custom Filters

Define specialized filtering logic for complex use cases:

```python
from django_filters import CharFilter, NumberFilter, BooleanFilter

class BlogPost(models.Model):
    # ... model fields ...

    class GraphQLMeta(GraphQLMeta):
        custom_filters = {
            'content_length': CharFilter(method='filter_by_content_length'),
            'has_tags': BooleanFilter(method='filter_has_tags'),
            'tag_count': NumberFilter(method='filter_by_tag_count'),
            'author_active': BooleanFilter(method='filter_by_author_active'),
        }

    @classmethod
    def filter_by_content_length(cls, queryset, name, value):
        """Filter by content length (short, medium, long)."""
        if value == 'short':
            return queryset.extra(where=["LENGTH(content) < 500"])
        elif value == 'medium':
            return queryset.extra(where=["LENGTH(content) BETWEEN 500 AND 2000"])
        elif value == 'long':
            return queryset.extra(where=["LENGTH(content) > 2000"])
        return queryset

    @classmethod
    def filter_has_tags(cls, queryset, name, value):
        """Filter posts that have or don't have tags."""
        if value:
            return queryset.filter(tags__isnull=False).distinct()
        return queryset.filter(tags__isnull=True)

    @classmethod
    def filter_by_tag_count(cls, queryset, name, value):
        """Filter by number of tags."""
        return queryset.annotate(
            tag_count=Count('tags')
        ).filter(tag_count=value)

    @classmethod
    def filter_by_author_active(cls, queryset, name, value):
        """Filter by author's active status."""
        return queryset.filter(author__is_active=value)
```

### Using Custom Filters in GraphQL

```graphql
query {
  blogPosts(
    contentLength: "medium"
    hasTags: true
    tagCount: 3
    authorActive: true
  ) {
    edges {
      node {
        title
        content
        tags {
          edges {
            node {
              name
            }
          }
        }
        author {
          username
          isActive
        }
      }
    }
  }
}
```

## ⚡ Quick Filter

The quick filter enables cross-field search functionality:

```python
class BlogPost(models.Model):
    # ... model fields ...

    class GraphQLMeta(GraphQLMeta):
        # Enable quick filter across multiple fields
        quick_filter_fields = [
            'title',
            'content',
            'author__username',
            'author__first_name',
            'author__last_name',
            'category__name',
            'tags__name',
        ]
        
        # Additional filter configuration
        filter_fields = {
            'quick': ['icontains'],  # This enables the quick filter
            'title': ['exact', 'icontains'],
            'is_published': ['exact'],
        }
```

### Using Quick Filter in GraphQL

```graphql
query {
  # Search across title, content, author name, category, and tags
  blogPosts(quick: "django tutorial") {
    edges {
      node {
        title
        content
        author {
          username
          firstName
          lastName
        }
        category {
          name
        }
        tags {
          edges {
            node {
              name
            }
          }
        }
      }
    }
  }
}
```

## 📅 Date/DateTime Filters

Built-in time-based filtering options are automatically generated for date and datetime fields:

```python
class BlogPost(models.Model):
    published_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    scheduled_date = models.DateField(null=True, blank=True)

    class GraphQLMeta(GraphQLMeta):
        filter_fields = {
            'published_date': ['exact', 'gt', 'lt', 'range'],
            'updated_date': ['exact', 'gt', 'lt'],
            'scheduled_date': ['exact', 'gt', 'lt'],
        }
```

### Available Date/DateTime Filters

For each date/datetime field, the following filters are automatically generated:

- `fieldname_today` - Filter for today's date
- `fieldname_yesterday` - Filter for yesterday's date
- `fieldname_this_week` - Filter for this week (Monday to Sunday)
- `fieldname_past_week` - Filter for past week
- `fieldname_this_month` - Filter for current month
- `fieldname_past_month` - Filter for previous month
- `fieldname_this_year` - Filter for current year
- `fieldname_past_year` - Filter for previous year

### Using Date/DateTime Filters in GraphQL

```graphql
query {
  # Posts published today
  todayPosts: blogPosts(publishedDateToday: true) {
    edges {
      node {
        title
        publishedDate
      }
    }
  }
  
  # Posts published this week
  thisWeekPosts: blogPosts(publishedDateThisWeek: true) {
    edges {
      node {
        title
        publishedDate
      }
    }
  }
  
  # Posts updated this month
  recentlyUpdated: blogPosts(updatedDateThisMonth: true) {
    edges {
      node {
        title
        updatedDate
      }
    }
  }
  
  # Posts scheduled for this year
  scheduledPosts: blogPosts(scheduledDateThisYear: true) {
    edges {
      node {
        title
        scheduledDate
      }
    }
  }
}
```

## ⚙️ Field Configuration

Control field behavior and inclusion:

```python
class BlogPost(models.Model):
    # ... model fields ...

    class GraphQLMeta(GraphQLMeta):
        # Field inclusion/exclusion
        include_fields = ['title', 'content', 'author', 'published_date']
        exclude_fields = ['internal_notes', 'admin_comments']
        
        # Field-specific configuration
        field_config = {
            'content': {
                'description': 'The main content of the blog post',
                'deprecation_reason': None,
            },
            'author': {
                'description': 'The author of this blog post',
                'required': True,
            },
        }
        
        # Relationship configuration
        relationship_config = {
            'comments': {
                'max_depth': 2,
                'enable_filtering': True,
                'enable_ordering': True,
            },
            'tags': {
                'enable_filtering': True,
                'prefetch_related': True,
            },
        }
```

## 📋 Complete Examples

### E-commerce Product Model

```python
from django.db import models
from rail_django_graphql.core.meta import GraphQLMeta

class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    brand = models.ForeignKey('Brand', on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    stock_quantity = models.IntegerField(default=0)
    tags = models.ManyToManyField('Tag', blank=True)

    class GraphQLMeta(GraphQLMeta):
        # Quick search across multiple fields
        quick_filter_fields = [
            'name',
            'description',
            'category__name',
            'brand__name',
            'tags__name',
        ]
        
        # Custom resolvers
        custom_resolvers = {
            'featured_products': 'get_featured_products',
            'on_sale_products': 'get_on_sale_products',
            'low_stock_products': 'get_low_stock_products',
        }
        
        # Custom filters
        custom_filters = {
            'price_range': 'filter_by_price_range',
            'in_stock': 'filter_in_stock',
            'popular': 'filter_popular_products',
        }
        
        # Standard filters
        filter_fields = {
            'name': ['exact', 'icontains', 'startswith'],
            'price': ['exact', 'gt', 'lt', 'range'],
            'category': ['exact', 'in'],
            'brand': ['exact', 'in'],
            'is_active': ['exact'],
            'stock_quantity': ['exact', 'gt', 'lt'],
            'created_date': ['exact', 'gt', 'lt', 'range'],
        }
        
        ordering_fields = ['name', 'price', 'created_date', 'stock_quantity']

    @classmethod
    def get_featured_products(cls, queryset, info, **kwargs):
        """Get featured products."""
        return queryset.filter(
            is_active=True,
            stock_quantity__gt=0,
            tags__name='featured'
        ).distinct()

    @classmethod
    def get_on_sale_products(cls, queryset, info, **kwargs):
        """Get products on sale."""
        return queryset.filter(
            is_active=True,
            tags__name='sale'
        ).distinct()

    @classmethod
    def get_low_stock_products(cls, queryset, info, **kwargs):
        """Get products with low stock."""
        return queryset.filter(
            is_active=True,
            stock_quantity__lt=10,
            stock_quantity__gt=0
        )

    @classmethod
    def filter_by_price_range(cls, queryset, name, value):
        """Filter by price range (budget, mid, premium)."""
        if value == 'budget':
            return queryset.filter(price__lt=50)
        elif value == 'mid':
            return queryset.filter(price__gte=50, price__lt=200)
        elif value == 'premium':
            return queryset.filter(price__gt=200)
        return queryset

## 🎯 Complete Real-World Examples

### E-commerce Product Model

```python
from django.db import models
from django.db.models import Q, Count, Avg
from rail_django_graphql.core.meta import GraphQLMeta

class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    brand = models.ForeignKey('Brand', on_delete=models.CASCADE)
    tags = models.ManyToManyField('Tag', blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Internal fields we don't want to expose
    internal_code = models.CharField(max_length=50, blank=True)
    supplier_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    class GraphQLMeta(GraphQLMeta):
        # Core Configuration
        exclude_fields = ['internal_code', 'supplier_cost']
        
        # Performance Optimization
        select_related = ['category', 'brand']
        prefetch_related = ['tags', 'reviews', 'reviews__user']
        
        # Filtering & Search
        filter_fields = {
            'name': ['exact', 'icontains', 'startswith'],
            'price': ['exact', 'gt', 'gte', 'lt', 'lte', 'range'],
            'stock_quantity': ['exact', 'gt', 'gte', 'lt', 'lte'],
            'category': ['exact', 'in'],
            'brand': ['exact', 'in'],
            'tags': ['exact', 'in'],
            'is_active': ['exact'],
            'created_at': ['exact', 'gt', 'gte', 'lt', 'lte', 'range'],
        }
        
        quick_filter_fields = [
            'name',
            'description',
            'category__name',
            'brand__name',
            'tags__name'
        ]
        
        # Custom Filters
        custom_filters = {
            'featured': 'filter_featured_products',
            'on_sale': 'filter_on_sale_products',
            'low_stock': 'filter_low_stock_products',
            'price_range': 'filter_by_price_range',
            'highly_rated': 'filter_highly_rated_products'
        }
        
        # Custom Resolvers
        custom_resolvers = {
            'bestsellers': 'get_bestselling_products',
            'new_arrivals': 'get_new_arrivals',
            'recommended': 'get_recommended_products'
        }
        
        # Ordering
        ordering_fields = [
            'name',
            'price',
            'created_at',
            'stock_quantity',
            'category__name',
            'brand__name'
        ]
        
        # Field Configuration
        field_config = {
            'price': {
                'description': 'Product price in USD',
                'decimal_places': 2
            },
            'stock_quantity': {
                'description': 'Available stock quantity'
            }
        }
        
        # Relationship Configuration
        relationship_config = {
            'category': {
                'include_fields': ['name', 'slug', 'description']
            },
            'brand': {
                'include_fields': ['name', 'logo_url', 'website']
            }
        }

    @classmethod
    def filter_featured_products(cls, queryset, info, value=True, **kwargs):
        """Filter for featured products."""
        if value:
            return queryset.filter(tags__name='featured', is_active=True).distinct()
        return queryset.exclude(tags__name='featured')

    @classmethod
    def filter_highly_rated_products(cls, queryset, info, min_rating=4.0, **kwargs):
        """Filter products with high ratings."""
        return queryset.annotate(
            avg_rating=Avg('reviews__rating')
        ).filter(avg_rating__gte=min_rating)

    @classmethod
    def get_bestselling_products(cls, queryset, info, limit=10, **kwargs):
        """Get bestselling products based on order count."""
        return queryset.annotate(
            order_count=Count('orderitem')
        ).filter(
            is_active=True,
            order_count__gt=0
        ).order_by('-order_count')[:limit]

    @classmethod
    def get_recommended_products(cls, queryset, info, user_id=None, **kwargs):
        """Get recommended products for a user."""
        if user_id:
            # Complex recommendation logic based on user history
            user_categories = cls.objects.filter(
                orderitem__order__user_id=user_id
            ).values_list('category', flat=True).distinct()
            
            return queryset.filter(
                category__in=user_categories,
                is_active=True
            ).exclude(
                orderitem__order__user_id=user_id
            ).annotate(
                popularity=Count('orderitem')
            ).order_by('-popularity')
        
        # Default recommendations for anonymous users
        return queryset.filter(
            is_active=True,
            tags__name='popular'
        ).distinct()
```

### Blog Management System

```python
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from rail_django_graphql.core.meta import GraphQLMeta

class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    excerpt = models.TextField(max_length=500, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    tags = models.ManyToManyField('Tag', blank=True)
    
    # Status and visibility
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived')
    ], default='draft')
    is_featured = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # SEO and metadata
    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    
    # Analytics
    view_count = models.PositiveIntegerField(default=0)
    
    # Internal fields
    internal_notes = models.TextField(blank=True)
    editor_notes = models.TextField(blank=True)

    class GraphQLMeta(GraphQLMeta):
        # Core Configuration
        exclude_fields = ['internal_notes', 'editor_notes']
        
        # Performance Optimization
        select_related = ['author', 'category', 'author__profile']
        prefetch_related = [
            'tags',
            'comments',
            'comments__author',
            'comments__replies'
        ]
        
        # Filtering & Search
        filter_fields = {
            'title': ['exact', 'icontains', 'startswith'],
            'status': ['exact', 'in'],
            'is_featured': ['exact'],
            'author': ['exact', 'in'],
            'category': ['exact', 'in'],
            'tags': ['exact', 'in'],
            'created_at': ['exact', 'gt', 'gte', 'lt', 'lte', 'range'],
            'published_at': ['exact', 'gt', 'gte', 'lt', 'lte', 'range', 'isnull'],
            'view_count': ['exact', 'gt', 'gte', 'lt', 'lte', 'range']
        }
        
        quick_filter_fields = [
            'title',
            'content',
            'excerpt',
            'author__username',
            'author__first_name',
            'author__last_name',
            'category__name',
            'tags__name'
        ]
        
        # Custom Filters
        custom_filters = {
            'published': 'filter_published_posts',
            'trending': 'filter_trending_posts',
            'recent': 'filter_recent_posts',
            'popular': 'filter_popular_posts',
            'by_author_type': 'filter_by_author_type'
        }
        
        # Custom Resolvers
        custom_resolvers = {
            'featured_posts': 'get_featured_posts',
            'related_posts': 'get_related_posts',
            'author_posts': 'get_author_posts',
            'category_posts': 'get_category_posts'
        }
        
        # Ordering
        ordering_fields = [
            'title',
            'created_at',
            'updated_at',
            'published_at',
            'view_count',
            'author__username',
            'category__name'
        ]
        
        # Field Configuration
        field_config = {
            'title': {
                'description': 'The blog post title',
                'max_length': 200
            },
            'content': {
                'description': 'The main content of the blog post'
            },
            'view_count': {
                'description': 'Number of times this post has been viewed'
            }
        }
        
        # Relationship Configuration
        relationship_config = {
            'author': {
                'include_fields': ['username', 'first_name', 'last_name', 'email'],
                'exclude_fields': ['password', 'is_staff', 'is_superuser']
            },
            'category': {
                'include_fields': ['name', 'slug', 'description', 'color']
            }
        }

    @classmethod
    def filter_published_posts(cls, queryset, info, value=True, **kwargs):
        """Filter for published posts."""
        if value:
            return queryset.filter(
                status='published',
                published_at__lte=timezone.now()
            )
        return queryset.exclude(status='published')

    @classmethod
    def filter_trending_posts(cls, queryset, info, days=7, min_views=50, **kwargs):
        """Filter trending posts based on recent views."""
        cutoff_date = timezone.now() - timedelta(days=days)
        return queryset.filter(
            status='published',
            published_at__gte=cutoff_date,
            view_count__gte=min_views
        ).order_by('-view_count')

    @classmethod
    def get_related_posts(cls, queryset, info, post_id=None, limit=5, **kwargs):
        """Get posts related to a specific post."""
        if not post_id:
            return queryset.none()
        
        try:
            post = cls.objects.get(id=post_id)
            return queryset.filter(
                Q(category=post.category) | Q(tags__in=post.tags.all()),
                status='published'
            ).exclude(id=post_id).distinct()[:limit]
        except cls.DoesNotExist:
            return queryset.none()
```

## 🏆 Best Practices and Tips

### 1. Performance Optimization

**Always use `select_related` and `prefetch_related`:**
```python
class GraphQLMeta(GraphQLMeta):
    # For ForeignKey relationships
    select_related = ['author', 'category', 'author__profile']
    
    # For ManyToMany and reverse ForeignKey relationships
    prefetch_related = ['tags', 'comments', 'comments__author']
```

### 2. Security Considerations

**Exclude sensitive fields:**
```python
class GraphQLMeta(GraphQLMeta):
    exclude_fields = [
        'password',
        'secret_key',
        'internal_notes',
        'api_tokens',
        'private_data'
    ]
```

### 3. Filtering Best Practices

**Provide comprehensive filtering options:**
```python
class GraphQLMeta(GraphQLMeta):
    filter_fields = {
        # Text fields - provide multiple lookup options
        'title': ['exact', 'icontains', 'startswith', 'endswith'],
        
        # Numeric fields - provide range options
        'price': ['exact', 'gt', 'gte', 'lt', 'lte', 'range'],
        
        # Boolean fields - simple exact match
        'is_active': ['exact'],
        
        # Date fields - comprehensive date filtering
        'created_at': ['exact', 'gt', 'gte', 'lt', 'lte', 'range', 'year', 'month', 'day'],
        
        # Relationship fields - exact and in lookups
        'category': ['exact', 'in'],
        'tags': ['exact', 'in', 'isnull']
    }
```

### 4. Custom Resolver Patterns

**Follow consistent naming and documentation:**
```python
@classmethod
def get_featured_items(cls, queryset, info, limit=10, **kwargs):
    """
    Get featured items with proper filtering and ordering.
    
    Args:
        queryset: Base queryset to filter
        info: GraphQL resolve info
        limit: Maximum number of items to return
        **kwargs: Additional filter parameters
    
    Returns:
        QuerySet: Filtered and ordered queryset
    """
    return queryset.filter(
        is_featured=True,
        is_active=True
    ).order_by('-created_at')[:limit]
```

### 5. Error Handling in Custom Methods

**Always handle edge cases:**
```python
@classmethod
def get_user_posts(cls, queryset, info, user_id=None, **kwargs):
    """Get posts for a specific user with error handling."""
    if not user_id:
        return queryset.none()
    
    try:
        # Validate user exists
        from django.contrib.auth.models import User
        User.objects.get(id=user_id)
        
        return queryset.filter(
            author_id=user_id,
            status='published'
        ).order_by('-published_at')
        
    except User.DoesNotExist:
        return queryset.none()
    except Exception as e:
        # Log error and return empty queryset
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in get_user_posts: {e}")
        return queryset.none()
```

### 6. Testing GraphQLMeta Configuration

**Create comprehensive tests:**
```python
# tests/test_graphql_meta.py
from django.test import TestCase
from graphene.test import Client
from your_app.schema import schema

class GraphQLMetaTestCase(TestCase):
    def setUp(self):
        self.client = Client(schema)
    
    def test_excluded_fields_not_accessible(self):
        """Test that excluded fields are not accessible via GraphQL."""
        query = '''
        query {
            blogPosts {
                edges {
                    node {
                        title
                        internalNotes  # This should fail
                    }
                }
            }
        }
        '''
        result = self.client.execute(query)
        self.assertIn('errors', result)
    
    def test_custom_filter_works(self):
        """Test custom filters work correctly."""
        query = '''
        query {
            blogPosts(published: true) {
                edges {
                    node {
                        title
                        status
                    }
                }
            }
        }
        '''
        result = self.client.execute(query)
        self.assertNotIn('errors', result)
        
        # Verify all returned posts are published
        posts = result['data']['blogPosts']['edges']
        for post in posts:
            self.assertEqual(post['node']['status'], 'published')
```

### 7. Documentation Standards

**Always document your GraphQLMeta configuration:**
```python
class BlogPost(models.Model):
    # ... model fields ...

    class GraphQLMeta(GraphQLMeta):
        """
        GraphQL configuration for BlogPost model.
        
        Features:
        - Excludes sensitive internal fields
        - Optimizes queries with select_related/prefetch_related
        - Provides comprehensive filtering options
        - Includes custom resolvers for common use cases
        - Supports quick search across multiple fields
        """
        
        # Core configuration
        exclude_fields = ['internal_notes', 'editor_notes']  # Hide internal fields
        
        # Performance optimization
        select_related = ['author', 'category']  # Reduce database queries
        prefetch_related = ['tags', 'comments']  # Optimize M2M queries
        
        # ... rest of configuration
```

This comprehensive guide should help you leverage all the powerful features of `GraphQLMeta` to create efficient, secure, and feature-rich GraphQL APIs for your Django applications.

    @classmethod
    def filter_in_stock(cls, queryset, name, value):
        """Filter products in stock."""
        if value:
            return queryset.filter(stock_quantity__gt=0)
        return queryset.filter(stock_quantity=0)

    @classmethod
    def filter_popular_products(cls, queryset, name, value):
        """Filter popular products based on order count."""
        if value:
            return queryset.annotate(
                order_count=Count('orderitem')
            ).filter(order_count__gte=10)
        return queryset
```

### User Profile Model

```python
class UserProfile(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    birth_date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=True)

    class GraphQLMeta(GraphQLMeta):
        # Quick search
        quick_filter_fields = [
            'user__username',
            'user__first_name',
            'user__last_name',
            'user__email',
            'bio',
            'location',
        ]
        
        # Custom resolvers
        custom_resolvers = {
            'active_users': 'get_active_users',
            'recent_joiners': 'get_recent_joiners',
        }
        
        # Custom filters
        custom_filters = {
            'age_range': 'filter_by_age_range',
            'has_website': 'filter_has_website',
        }
        
        # Standard filters
        filter_fields = {
            'user__username': ['exact', 'icontains'],
            'user__is_active': ['exact'],
            'location': ['exact', 'icontains'],
            'is_public': ['exact'],
            'birth_date': ['exact', 'gt', 'lt'],
            'created_date': ['exact', 'gt', 'lt'],
        }

    @classmethod
    def get_active_users(cls, queryset, info, **kwargs):
        """Get profiles of active users."""
        return queryset.filter(
            user__is_active=True,
            is_public=True
        )

    @classmethod
    def get_recent_joiners(cls, queryset, info, **kwargs):
        """Get profiles of users who joined recently."""
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.now() - timedelta(days=30)
        return queryset.filter(
            created_date__gte=thirty_days_ago,
            is_public=True
        )

    @classmethod
    def filter_by_age_range(cls, queryset, name, value):
        """Filter by age range."""
        from datetime import date, timedelta
        today = date.today()
        
        if value == 'teen':
            start_date = today - timedelta(days=365*19)
            end_date = today - timedelta(days=365*13)
        elif value == 'young_adult':
            start_date = today - timedelta(days=365*35)
            end_date = today - timedelta(days=365*20)
        elif value == 'adult':
            start_date = today - timedelta(days=365*65)
            end_date = today - timedelta(days=365*36)
        else:
            return queryset
            
        return queryset.filter(
            birth_date__gte=start_date,
            birth_date__lte=end_date
        )

    @classmethod
    def filter_has_website(cls, queryset, name, value):
        """Filter profiles with or without website."""
        if value:
            return queryset.exclude(website='')
        return queryset.filter(website='')
```

## 🎯 Best Practices

### 1. Performance Considerations

```python
class GraphQLMeta(GraphQLMeta):
    # Use select_related for foreign keys
    select_related = ['author', 'category']
    
    # Use prefetch_related for many-to-many and reverse foreign keys
    prefetch_related = ['tags', 'comments']
    
    # Limit quick filter fields to essential ones
    quick_filter_fields = ['title', 'content']  # Don't include too many
    
    # Use database indexes for filtered fields
    filter_fields = {
        'published_date': ['exact', 'gt', 'lt'],  # Ensure DB index exists
        'is_published': ['exact'],  # Boolean fields are usually indexed
    }
```

### 2. Security Considerations

```python
class GraphQLMeta(GraphQLMeta):
    # Exclude sensitive fields
    exclude_fields = ['internal_notes', 'admin_comments', 'secret_key']
    
    # Implement permission checks in custom resolvers
    @classmethod
    def get_admin_posts(cls, queryset, info, **kwargs):
        """Only allow admin users to access this resolver."""
        if not info.context.user.is_staff:
            return queryset.none()
        return queryset.filter(is_admin_post=True)
```

### 3. Maintainability

```python
class GraphQLMeta(GraphQLMeta):
    # Group related configurations
    quick_filter_fields = [
        # User-related fields
        'author__username',
        'author__first_name',
        'author__last_name',
        
        # Content fields
        'title',
        'content',
        
        # Category fields
        'category__name',
    ]
    
    # Use descriptive method names
    custom_resolvers = {
        'published_posts': 'get_published_posts',
        'draft_posts': 'get_draft_posts',
        'featured_posts': 'get_featured_posts',
    }
    
    # Document complex filters
    custom_filters = {
        'engagement_level': 'filter_by_engagement_level',  # High/Medium/Low engagement
        'content_type': 'filter_by_content_type',  # Article/Tutorial/News
    }
```

### 4. Testing Custom Logic

```python
# tests/test_graphql_meta.py
from django.test import TestCase
from myapp.models import BlogPost

class GraphQLMetaTest(TestCase):
    def test_popular_posts_resolver(self):
        """Test the popular posts custom resolver."""
        # Create test data
        post1 = BlogPost.objects.create(title="Popular Post", is_published=True)
        post2 = BlogPost.objects.create(title="Unpopular Post", is_published=True)
        
        # Add comments to make post1 popular
        for i in range(15):
            post1.comments.create(content=f"Comment {i}")
        
        # Test the resolver
        queryset = BlogPost.objects.all()
        popular_posts = BlogPost.get_popular_posts(queryset, None)
        
        self.assertIn(post1, popular_posts)
        self.assertNotIn(post2, popular_posts)

    def test_quick_filter(self):
        """Test the quick filter functionality."""
        post1 = BlogPost.objects.create(title="Django Tutorial", content="Learn Django")
        post2 = BlogPost.objects.create(title="Python Guide", content="Learn Python")
        
        # Test quick filter
        # This would be tested through GraphQL queries in integration tests
        pass
```

## 🔗 Related Documentation

- [Basic Usage Guide](basic-usage.md) - Learn the fundamentals
- [Advanced Usage Guide](advanced-usage.md) - Advanced patterns and API reference
- [Filtering Guide](../features/filtering.md) - Detailed filtering documentation
- [Performance Guide](../development/performance.md) - Performance optimization tips
- [Security Guide](../features/security.md) - Security best practices

---

**Next Steps:**
1. Try implementing `GraphQLMeta` in your models
2. Experiment with custom resolvers and filters
3. Test the quick filter functionality
4. Explore the date/datetime filters
5. Check out the [Advanced Usage Guide](advanced-usage.md) for more patterns
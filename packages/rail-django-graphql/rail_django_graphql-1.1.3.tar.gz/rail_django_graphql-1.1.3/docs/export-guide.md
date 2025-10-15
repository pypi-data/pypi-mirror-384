# Django Model Export Extension

The Django Model Export Extension provides a powerful and flexible way to export Django model data to Excel or CSV formats through both HTTP endpoints and programmatic interfaces. **All export endpoints are protected by JWT authentication for security.**

## Table of Contents

1. [🔐 Security & Authentication](#security--authentication)
2. [Features](#features)
3. [Installation](#installation)
4. [Quick Start](#quick-start)
5. [HTTP API Usage](#http-api-usage)
6. [Programmatic Usage](#programmatic-usage)
7. [Field Configuration](#field-configuration)
8. [Filtering and Ordering](#filtering-and-ordering)
9. [Advanced Examples](#advanced-examples)
10. [Error Handling](#error-handling)
11. [Best Practices](#best-practices)

## 🔐 Security & Authentication

### JWT Token Protection

All export endpoints are protected by JWT authentication, similar to GraphQL project schemas:

```bash
# Required Authorization header
Authorization: Bearer <your_jwt_token>
```

**Authentication Requirements:**
- Valid JWT token must be provided in the Authorization header
- Token format: `Bearer <token>`
- Both GET (API docs) and POST (export) endpoints require authentication
- Expired or invalid tokens will return 401 Unauthorized

### Getting JWT Tokens

```python
from rail_django_graphql.extensions.auth import JWTManager
from django.contrib.auth.models import User

# Generate token for authenticated user
jwt_manager = JWTManager()
user = User.objects.get(username='your_username')
token = jwt_manager.generate_token(user)
```

### Authentication Errors

```json
// 401 Unauthorized responses
{
    "error": "Authentication required",
    "detail": "No authentication token provided"
}

{
    "error": "Invalid token", 
    "detail": "Token has expired or is invalid"
}
```

## Features

- **Dynamic Model Loading**: Export any Django model by specifying app and model names
- **Flexible Field Selection**: Choose specific fields with custom display names
- **Nested Field Access**: Access related model fields and properties
- **Method Calls**: Execute model methods during export
- **Multiple Formats**: Support for Excel (.xlsx) and CSV formats
- **Advanced Filtering**: Use Django ORM filter expressions
- **Custom Ordering**: Sort data using Django ordering syntax
- **Proper Formatting**: Automatic formatting for dates, booleans, decimals, etc.
- **HTTP Endpoint**: Ready-to-use REST API endpoint
- **Programmatic Interface**: Use directly in Python code

## Installation

### Prerequisites

```bash
# Required for CSV support (included in Python standard library)
# No additional packages needed for CSV

# Required for Excel support
pip install openpyxl
```

### Django Setup

1. **Add to URLs**: Include the export URLs in your Django project:

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('rail_django_graphql.extensions.urls')),
    # ... other patterns
]
```

2. **Optional Settings**: Add to your Django settings if needed:

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'export.log',
        },
    },
    'loggers': {
        'rail_django_graphql.extensions.exporting': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

## Quick Start

### HTTP API Example

```bash
curl -X POST http://localhost:8000/api/export/ \
  -H "Authorization: Bearer your_jwt_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "app_name": "blog",
    "model_name": "Post",
    "file_extension": "excel",
    "filename": "blog_posts",
    "fields": [
      {"accessor": "title", "value": "Post Title"},
      {"accessor": "author.username", "value": "Author"},
      {"accessor": "created_at", "value": "Created Date"}
    ],
    "ordering": "-created_at",
    "variables": {
      "is_published": true
    }
  }' \
  --output blog_posts.xlsx
```

### Python Code Example

```python
from rail_django_graphql.extensions import export_model_to_excel

# Define fields to export
fields = [
    {'accessor': 'title', 'value': 'Post Title'},
    {'accessor': 'author.username', 'value': 'Author'},
    {'accessor': 'created_at', 'value': 'Created Date'}
]

# Export to Excel
excel_content = export_model_to_excel(
    app_name='blog',
    model_name='Post',
    fields=fields,
    variables={'is_published': True},
    ordering='-created_at'
)

# Save to file
with open('posts.xlsx', 'wb') as f:
    f.write(excel_content)
```

## HTTP API Usage

### Endpoint

```
POST /api/export/
```

### Request Format

```json
{
  "app_name": "string",           // Required: Django app name
  "model_name": "string",         // Required: Model name
  "file_extension": "string",     // Required: "excel" or "csv"
  "filename": "string",           // Optional: Custom filename
  "fields": [                     // Required: Field definitions
    {
      "accessor": "string",       // Field path or method
      "value": "string"           // Display name (optional)
    }
  ],
  "ordering": "string",           // Optional: Django ordering expression
  "variables": {                  // Optional: Filter parameters
    "field__lookup": "value"
  }
}
```

### Response

- **Success (200)**: File download with appropriate headers
- **Error (400)**: JSON error response with details
- **Error (500)**: Internal server error

### Example Requests

#### Basic Export

```json
{
  "app_name": "auth",
  "model_name": "User",
  "file_extension": "csv",
  "fields": [
    {"accessor": "username", "value": "Username"},
    {"accessor": "email", "value": "Email"},
    {"accessor": "date_joined", "value": "Registration Date"}
  ]
}
```

#### Advanced Export with Filtering

```json
{
  "app_name": "ecommerce",
  "model_name": "Order",
  "file_extension": "excel",
  "filename": "monthly_orders",
  "fields": [
    {"accessor": "order_number", "value": "Order #"},
    {"accessor": "customer.email", "value": "Customer"},
    {"accessor": "total_amount", "value": "Total ($)"},
    {"accessor": "status", "value": "Status"},
    {"accessor": "created_at", "value": "Order Date"}
  ],
  "ordering": "-created_at",
  "variables": {
    "status": "completed",
    "created_at__gte": "2024-01-01",
    "total_amount__gte": 100.00
  }
}
```

## Programmatic Usage

### Import Functions

```python
from rail_django_graphql.extensions import (
    export_model_to_csv,
    export_model_to_excel,
    ModelExporter
)
```

### Quick Export Functions

#### CSV Export

```python
csv_content = export_model_to_csv(
    app_name='blog',
    model_name='Post',
    fields=[
        {'accessor': 'title', 'value': 'Title'},
        {'accessor': 'author.username', 'value': 'Author'}
    ],
    variables={'is_published': True},
    ordering='-created_at'
)

# Save to file
with open('posts.csv', 'w', encoding='utf-8') as f:
    f.write(csv_content)
```

#### Excel Export

```python
excel_content = export_model_to_excel(
    app_name='blog',
    model_name='Post',
    fields=[
        {'accessor': 'title', 'value': 'Title'},
        {'accessor': 'author.username', 'value': 'Author'}
    ],
    variables={'is_published': True},
    ordering='-created_at'
)

# Save to file
with open('posts.xlsx', 'wb') as f:
    f.write(excel_content)
```

### ModelExporter Class

For more control, use the `ModelExporter` class directly:

```python
from rail_django_graphql.extensions import ModelExporter

# Create exporter
exporter = ModelExporter('blog', 'Post')

# Get queryset for inspection
queryset = exporter.get_queryset(
    variables={'is_published': True},
    ordering='-created_at'
)
print(f"Found {queryset.count()} posts")

# Define fields
fields = [
    {'accessor': 'title', 'value': 'Post Title'},
    {'accessor': 'author.username', 'value': 'Author'},
    {'accessor': 'created_at', 'value': 'Created Date'}
]

# Export to both formats
csv_data = exporter.export_to_csv(fields, {'is_published': True}, '-created_at')
excel_data = exporter.export_to_excel(fields, {'is_published': True}, '-created_at')
```

## Field Configuration

### Basic Field Access

```python
fields = [
    {'accessor': 'title', 'value': 'Post Title'},
    {'accessor': 'content', 'value': 'Content'},
    {'accessor': 'created_at', 'value': 'Created Date'}
]
```

### Nested Field Access

Access related model fields using dot notation:

```python
fields = [
    {'accessor': 'author.username', 'value': 'Author Username'},
    {'accessor': 'author.email', 'value': 'Author Email'},
    {'accessor': 'author.profile.bio', 'value': 'Author Bio'},
    {'accessor': 'category.name', 'value': 'Category'},
    {'accessor': 'category.parent.name', 'value': 'Parent Category'}
]
```

### Method Calls

Execute model methods during export:

```python
fields = [
    {'accessor': 'get_absolute_url()', 'value': 'URL'},
    {'accessor': 'get_status_display()', 'value': 'Status'},
    {'accessor': 'author.get_full_name()', 'value': 'Author Name'}
]
```

### Many-to-Many Fields

```python
fields = [
    {'accessor': 'tags.all', 'value': 'Tags'},           # All related objects
    {'accessor': 'categories.count()', 'value': 'Category Count'}  # Count
]
```

### Automatic Display Names

If you don't provide a `value`, the system will try to use the field's `verbose_name`:

```python
fields = [
    {'accessor': 'title'},        # Uses field's verbose_name
    {'accessor': 'created_at'}    # Uses field's verbose_name
]
```

## Filtering and Ordering

### Basic Filtering

Use Django ORM filter expressions:

```python
variables = {
    'is_published': True,
    'author__is_active': True,
    'created_at__gte': '2024-01-01'
}
```

### Advanced Filtering

```python
variables = {
    # Exact matches
    'status': 'published',
    'is_featured': True,
    
    # Text searches
    'title__icontains': 'django',
    'content__search': 'tutorial',
    
    # Date ranges
    'created_at__gte': '2024-01-01',
    'created_at__lt': '2024-12-31',
    'created_at__year': 2024,
    
    # Numeric comparisons
    'view_count__gte': 100,
    'price__range': [10, 100],
    
    # Related field filtering
    'author__username__startswith': 'admin',
    'category__name__in': ['Tech', 'Science'],
    
    # Null checks
    'featured_image__isnull': False
}
```

### Ordering

Use Django ordering expressions:

```python
# Single field ordering
ordering = 'created_at'        # Ascending
ordering = '-created_at'       # Descending

# Multiple field ordering
ordering = ['category', '-created_at']  # Category ASC, then Created DESC
```

## Advanced Examples

### E-commerce Order Export

```python
fields = [
    {'accessor': 'order_number', 'value': 'Order #'},
    {'accessor': 'customer.email', 'value': 'Customer Email'},
    {'accessor': 'customer.profile.full_name', 'value': 'Customer Name'},
    {'accessor': 'customer.profile.phone', 'value': 'Phone'},
    {'accessor': 'total_amount', 'value': 'Total ($)'},
    {'accessor': 'tax_amount', 'value': 'Tax ($)'},
    {'accessor': 'shipping_cost', 'value': 'Shipping ($)'},
    {'accessor': 'status', 'value': 'Status'},
    {'accessor': 'get_status_display()', 'value': 'Status Display'},
    {'accessor': 'payment_method', 'value': 'Payment Method'},
    {'accessor': 'shipping_address.street', 'value': 'Street'},
    {'accessor': 'shipping_address.city', 'value': 'City'},
    {'accessor': 'shipping_address.state', 'value': 'State'},
    {'accessor': 'shipping_address.zip_code', 'value': 'ZIP'},
    {'accessor': 'created_at', 'value': 'Order Date'},
    {'accessor': 'shipped_at', 'value': 'Shipped Date'},
    {'accessor': 'items.count()', 'value': 'Item Count'}
]

variables = {
    'status__in': ['completed', 'shipped'],
    'created_at__gte': '2024-01-01',
    'total_amount__gte': 50.00,
    'customer__is_active': True
}

excel_content = export_model_to_excel(
    app_name='ecommerce',
    model_name='Order',
    fields=fields,
    variables=variables,
    ordering=['-created_at', 'customer__email']
)
```

### User Analytics Export

```python
fields = [
    {'accessor': 'username', 'value': 'Username'},
    {'accessor': 'email', 'value': 'Email'},
    {'accessor': 'first_name', 'value': 'First Name'},
    {'accessor': 'last_name', 'value': 'Last Name'},
    {'accessor': 'date_joined', 'value': 'Registration Date'},
    {'accessor': 'last_login', 'value': 'Last Login'},
    {'accessor': 'is_active', 'value': 'Active'},
    {'accessor': 'is_staff', 'value': 'Staff'},
    {'accessor': 'profile.bio', 'value': 'Bio'},
    {'accessor': 'profile.birth_date', 'value': 'Birth Date'},
    {'accessor': 'profile.location', 'value': 'Location'},
    {'accessor': 'posts.count()', 'value': 'Post Count'},
    {'accessor': 'comments.count()', 'value': 'Comment Count'},
    {'accessor': 'groups.all', 'value': 'Groups'}
]

# Export active users from the last year
variables = {
    'is_active': True,
    'date_joined__gte': '2023-01-01',
    'last_login__isnull': False
}

csv_content = export_model_to_csv(
    app_name='auth',
    model_name='User',
    fields=fields,
    variables=variables,
    ordering='date_joined'
)
```

### Inventory Report

```python
fields = [
    {'accessor': 'sku', 'value': 'SKU'},
    {'accessor': 'name', 'value': 'Product Name'},
    {'accessor': 'description', 'value': 'Description'},
    {'accessor': 'category.name', 'value': 'Category'},
    {'accessor': 'category.parent.name', 'value': 'Parent Category'},
    {'accessor': 'brand.name', 'value': 'Brand'},
    {'accessor': 'price', 'value': 'Price ($)'},
    {'accessor': 'cost', 'value': 'Cost ($)'},
    {'accessor': 'stock_quantity', 'value': 'Stock'},
    {'accessor': 'reserved_quantity', 'value': 'Reserved'},
    {'accessor': 'available_quantity', 'value': 'Available'},
    {'accessor': 'reorder_level', 'value': 'Reorder Level'},
    {'accessor': 'supplier.company_name', 'value': 'Supplier'},
    {'accessor': 'supplier.contact_email', 'value': 'Supplier Email'},
    {'accessor': 'is_active', 'value': 'Active'},
    {'accessor': 'created_at', 'value': 'Added Date'},
    {'accessor': 'updated_at', 'value': 'Last Updated'}
]

# Low stock report
variables = {
    'is_active': True,
    'stock_quantity__lte': models.F('reorder_level'),  # Note: F expressions need special handling
    'supplier__is_active': True
}

# Alternative without F expressions
variables = {
    'is_active': True,
    'stock_quantity__lt': 10,  # Fixed threshold
    'supplier__is_active': True
}

excel_content = export_model_to_excel(
    app_name='inventory',
    model_name='Product',
    fields=fields,
    variables=variables,
    ordering=['category__name', 'name']
)
```

## Error Handling

### Common Errors and Solutions

#### Model Not Found

```python
# Error: Model 'Post' not found in app 'blog'
# Solution: Check app_name and model_name spelling

try:
    content = export_model_to_csv('blog', 'Post', fields)
except ExportError as e:
    print(f"Export failed: {e}")
```

#### Invalid Field Access

```python
# Error: Field 'nonexistent_field' not found
# Solution: Check field names and relationships

fields = [
    {'accessor': 'title', 'value': 'Title'},
    # {'accessor': 'nonexistent_field', 'value': 'Bad Field'},  # This will cause issues
]
```

#### Filter Errors

```python
# Error: Invalid filter expression
# Solution: Use valid Django ORM filters

variables = {
    'created_at__gte': '2024-01-01',  # Valid date format
    # 'created_at__gte': 'invalid-date',  # This would cause an error
}
```

### Error Response Format

HTTP API errors return JSON responses:

```json
{
  "error": "Model 'Post' not found in app 'blog': No installed app with label 'blog'."
}
```

### Exception Handling in Code

```python
from rail_django_graphql.extensions.exporting import ExportError

try:
    content = export_model_to_excel(
        app_name='blog',
        model_name='Post',
        fields=fields,
        variables=variables
    )
except ExportError as e:
    print(f"Export error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Best Practices

### Performance Optimization

1. **Use select_related and prefetch_related** in your model's default manager:

```python
class PostManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'author', 'category'
        ).prefetch_related('tags')

class Post(models.Model):
    objects = PostManager()
    # ... fields
```

2. **Limit field selection** to only what you need:

```python
# Good: Only export necessary fields
fields = [
    {'accessor': 'title', 'value': 'Title'},
    {'accessor': 'author.username', 'value': 'Author'}
]

# Avoid: Exporting large text fields unnecessarily
# {'accessor': 'content', 'value': 'Full Content'}  # Large field
```

3. **Use efficient filtering**:

```python
# Good: Use indexed fields for filtering
variables = {
    'is_published': True,  # Indexed boolean
    'created_at__gte': '2024-01-01'  # Indexed date
}

# Avoid: Complex text searches on large datasets
# variables = {'content__icontains': 'search term'}  # Slow on large tables
```

### Security Considerations

1. **Validate user permissions** before allowing exports:

```python
# In your view or API
def export_view(request):
    if not request.user.has_perm('blog.view_post'):
        return HttpResponseForbidden()
    
    # Proceed with export
```

2. **Sanitize file names**:

```python
import re

def sanitize_filename(filename):
    # Remove or replace invalid characters
    return re.sub(r'[^\w\-_\.]', '_', filename)
```

3. **Limit export size** to prevent resource exhaustion:

```python
# Add pagination or limits
MAX_EXPORT_ROWS = 10000

queryset = exporter.get_queryset(variables, ordering)
if queryset.count() > MAX_EXPORT_ROWS:
    raise ExportError(f"Export too large. Maximum {MAX_EXPORT_ROWS} rows allowed.")
```

### Data Formatting

1. **Handle sensitive data**:

```python
fields = [
    {'accessor': 'username', 'value': 'Username'},
    # Don't export sensitive fields directly
    # {'accessor': 'password', 'value': 'Password'},  # Never do this
    {'accessor': 'email', 'value': 'Email'}
]
```

2. **Format currency and numbers**:

```python
# The exporter automatically formats Decimal fields
# For custom formatting, use model methods:

class Order(models.Model):
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    def get_formatted_total(self):
        return f"${self.total_amount:.2f}"

# In export fields:
fields = [
    {'accessor': 'get_formatted_total()', 'value': 'Total'}
]
```

3. **Handle None values gracefully**:

```python
# The exporter automatically converts None to empty strings
# For custom handling, use model properties:

class Profile(models.Model):
    bio = models.TextField(blank=True, null=True)
    
    @property
    def bio_display(self):
        return self.bio or "No bio provided"

# In export:
fields = [
    {'accessor': 'bio_display', 'value': 'Biography'}
]
```

### File Management

1. **Use appropriate file names**:

```python
from datetime import datetime

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
filename = f"users_export_{timestamp}"
```

2. **Consider file size limits**:

```python
# For large exports, consider pagination or streaming
# Excel files can become large with many rows
# CSV is generally more efficient for large datasets
```

3. **Clean up temporary files** if generating them:

```python
import tempfile
import os

# If you need temporary files
with tempfile.NamedTemporaryFile(delete=False) as tmp:
    tmp.write(excel_content)
    tmp_path = tmp.name

try:
    # Process file
    pass
finally:
    os.unlink(tmp_path)  # Clean up
```

### Testing

Create tests for your export functionality:

```python
from django.test import TestCase
from rail_django_graphql.extensions import export_model_to_csv

class ExportTestCase(TestCase):
    def setUp(self):
        # Create test data
        pass
    
    def test_csv_export(self):
        fields = [
            {'accessor': 'title', 'value': 'Title'},
            {'accessor': 'author.username', 'value': 'Author'}
        ]
        
        csv_content = export_model_to_csv(
            'blog', 'Post', fields
        )
        
        self.assertIn('Title,Author', csv_content)
        # Add more assertions
```

This completes the comprehensive documentation for the Django Model Export Extension. The system provides a robust, flexible solution for exporting Django model data with extensive customization options and proper error handling.
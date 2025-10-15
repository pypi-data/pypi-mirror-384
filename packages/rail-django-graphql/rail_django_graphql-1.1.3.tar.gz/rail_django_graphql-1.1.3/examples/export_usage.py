"""
Example Usage of Django Model Export Extension

This file demonstrates various ways to use the model export functionality
provided by the rail-django-graphql extensions package.
"""

import json

import requests

from rail_django_graphql.extensions import ModelExporter, export_model_to_csv, export_model_to_excel


def example_programmatic_csv_export():
    """
    Example of programmatic CSV export using the utility function.
    """
    # Define the fields to export
    fields = [
        {'accessor': 'title', 'value': 'Post Title'},
        {'accessor': 'author.username', 'value': 'Author Username'},
        {'accessor': 'author.email', 'value': 'Author Email'},
        {'accessor': 'created_at', 'value': 'Created Date'},
        {'accessor': 'is_published', 'value': 'Published'},
        {'accessor': 'category.name', 'value': 'Category'},
        {'accessor': 'tags.all', 'value': 'Tags'},  # Many-to-many field
        {'accessor': 'get_absolute_url()', 'value': 'URL'}  # Method call
    ]

    # Define filters
    variables = {
        'is_published': True,
        'created_at__gte': '2024-01-01',
        'title__icontains': 'django'
    }

    # Export to CSV
    csv_content = export_model_to_csv(
        app_name='blog',
        model_name='Post',
        fields=fields,
        variables=variables,
        ordering='-created_at'
    )

    # Save to file
    with open('blog_posts_export.csv', 'w', encoding='utf-8') as f:
        f.write(csv_content)

    print("CSV export completed: blog_posts_export.csv")


def example_programmatic_excel_export():
    """
    Example of programmatic Excel export using the utility function.
    """
    # Define fields for user export
    fields = [
        {'accessor': 'username', 'value': 'Username'},
        {'accessor': 'email', 'value': 'Email Address'},
        {'accessor': 'first_name', 'value': 'First Name'},
        {'accessor': 'last_name', 'value': 'Last Name'},
        {'accessor': 'date_joined', 'value': 'Registration Date'},
        {'accessor': 'is_active', 'value': 'Active Status'},
        {'accessor': 'profile.bio', 'value': 'Biography'},  # Related field
        {'accessor': 'profile.phone_number', 'value': 'Phone'}
    ]

    # Filter for active users only
    variables = {
        'is_active': True,
        'date_joined__gte': '2023-01-01'
    }

    # Export to Excel
    excel_content = export_model_to_excel(
        app_name='auth',
        model_name='User',
        fields=fields,
        variables=variables,
        ordering='date_joined'
    )

    # Save to file
    with open('users_export.xlsx', 'wb') as f:
        f.write(excel_content)

    print("Excel export completed: users_export.xlsx")


def example_model_exporter_class():
    """
    Example using the ModelExporter class directly for more control.
    """
    # Create exporter instance
    exporter = ModelExporter('inventory', 'Product')

    # Define complex field mappings
    fields = [
        {'accessor': 'sku', 'value': 'Product SKU'},
        {'accessor': 'name', 'value': 'Product Name'},
        {'accessor': 'category.name', 'value': 'Category'},
        {'accessor': 'category.parent.name', 'value': 'Parent Category'},
        {'accessor': 'price', 'value': 'Price ($)'},
        {'accessor': 'stock_quantity', 'value': 'Stock'},
        {'accessor': 'supplier.company_name', 'value': 'Supplier'},
        {'accessor': 'supplier.contact_email', 'value': 'Supplier Email'},
        {'accessor': 'created_at', 'value': 'Added Date'},
        {'accessor': 'is_active', 'value': 'Active'}
    ]

    # Complex filtering
    variables = {
        'is_active': True,
        'stock_quantity__gt': 0,
        'price__range': [10, 1000],
        'category__name__in': ['Electronics', 'Books', 'Clothing']
    }

    # Get the queryset for inspection
    queryset = exporter.get_queryset(variables, '-created_at')
    print(f"Found {queryset.count()} products matching criteria")

    # Export to both formats
    csv_data = exporter.export_to_csv(fields, variables, '-created_at')
    excel_data = exporter.export_to_excel(fields, variables, '-created_at')

    # Save files
    with open('products_export.csv', 'w', encoding='utf-8') as f:
        f.write(csv_data)

    with open('products_export.xlsx', 'wb') as f:
        f.write(excel_data)

    print("Product exports completed")


def example_http_api_usage():
    """
    Example of using the HTTP API endpoint for export.
    """
    # API endpoint URL (adjust based on your Django setup)
    api_url = 'http://localhost:8000/api/export/'

    # Prepare the export request payload
    payload = {
        'app_name': 'blog',
        'model_name': 'Post',
        'file_extension': 'excel',
        'filename': 'blog_posts_filtered',
        'fields': [
            {'accessor': 'title', 'value': 'Post Title'},
            {'accessor': 'author.username', 'value': 'Author'},
            {'accessor': 'author.profile.full_name', 'value': 'Author Full Name'},
            {'accessor': 'created_at', 'value': 'Created Date'},
            {'accessor': 'updated_at', 'value': 'Last Updated'},
            {'accessor': 'is_published', 'value': 'Published'},
            {'accessor': 'view_count', 'value': 'Views'},
            {'accessor': 'category.name', 'value': 'Category'},
            {'accessor': 'tags.count()', 'value': 'Tag Count'}
        ],
        'ordering': '-created_at',
        'variables': {
            'is_published': True,
            'created_at__year': 2024,
            'author__is_active': True
        }
    }

    # Make the API request
    try:
        response = requests.post(
            api_url,
            json=payload,
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code == 200:
            # Save the downloaded file
            filename = 'api_export.xlsx'
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"API export completed: {filename}")
        else:
            print(f"API request failed: {response.status_code}")
            print(response.json())

    except requests.RequestException as e:
        print(f"Request error: {e}")


def example_csv_api_request():
    """
    Example of requesting CSV export via HTTP API.
    """
    api_url = 'http://localhost:8000/api/export/'

    payload = {
        'app_name': 'ecommerce',
        'model_name': 'Order',
        'file_extension': 'csv',
        'filename': 'orders_report',
        'fields': [
            {'accessor': 'order_number', 'value': 'Order #'},
            {'accessor': 'customer.email', 'value': 'Customer Email'},
            {'accessor': 'customer.profile.full_name', 'value': 'Customer Name'},
            {'accessor': 'total_amount', 'value': 'Total ($)'},
            {'accessor': 'status', 'value': 'Status'},
            {'accessor': 'created_at', 'value': 'Order Date'},
            {'accessor': 'shipping_address.city', 'value': 'Shipping City'},
            {'accessor': 'payment_method', 'value': 'Payment Method'}
        ],
        'ordering': '-created_at',
        'variables': {
            'status__in': ['completed', 'shipped'],
            'created_at__gte': '2024-01-01',
            'total_amount__gte': 50.00
        }
    }

    try:
        response = requests.post(api_url, json=payload)

        if response.status_code == 200:
            with open('orders_report.csv', 'wb') as f:
                f.write(response.content)
            print("CSV export completed: orders_report.csv")
        else:
            print(f"Export failed: {response.json()}")

    except Exception as e:
        print(f"Error: {e}")


def example_complex_nested_fields():
    """
    Example demonstrating complex nested field access and method calls.
    """
    fields = [
        # Basic fields
        {'accessor': 'id', 'value': 'ID'},
        {'accessor': 'name', 'value': 'Name'},

        # Nested model fields
        {'accessor': 'author.profile.bio', 'value': 'Author Bio'},
        {'accessor': 'category.parent.name', 'value': 'Parent Category'},

        # Method calls
        {'accessor': 'get_absolute_url()', 'value': 'URL'},
        {'accessor': 'get_status_display()', 'value': 'Status Display'},

        # Many-to-many relationships
        {'accessor': 'tags.all', 'value': 'All Tags'},

        # Computed properties
        {'accessor': 'author.profile.get_full_name()', 'value': 'Author Full Name'},

        # Date formatting (handled automatically)
        {'accessor': 'created_at', 'value': 'Created Date'},
        {'accessor': 'updated_at', 'value': 'Updated Date'},

        # Boolean fields (formatted as Yes/No)
        {'accessor': 'is_featured', 'value': 'Featured'},
        {'accessor': 'is_published', 'value': 'Published'}
    ]

    # Export with complex nested access
    csv_content = export_model_to_csv(
        app_name='blog',
        model_name='Article',
        fields=fields,
        ordering='-created_at'
    )

    with open('complex_export.csv', 'w', encoding='utf-8') as f:
        f.write(csv_content)

    print("Complex nested field export completed")


if __name__ == '__main__':
    """
    Run examples (uncomment the ones you want to test).

    Note: Make sure your Django environment is properly set up
    and the models exist before running these examples.
    """

    print("Django Model Export Examples")
    print("=" * 40)

    # Uncomment the examples you want to run:

    # example_programmatic_csv_export()
    # example_programmatic_excel_export()
    # example_model_exporter_class()
    # example_http_api_usage()
    # example_csv_api_request()
    # example_complex_nested_fields()

    print("\nTo run examples, uncomment the function calls in the __main__ section.")


# Django management command example
"""
You can also create a Django management command for exports:

# management/commands/export_model.py
from django.core.management.base import BaseCommand
from rail_django_graphql.extensions import export_model_to_excel

class Command(BaseCommand):
    help = 'Export model data to Excel file'
    
    def add_arguments(self, parser):
        parser.add_argument('app_name', type=str)
        parser.add_argument('model_name', type=str)
        parser.add_argument('--output', type=str, default='export.xlsx')
    
    def handle(self, *args, **options):
        fields = [
            {'accessor': 'id', 'value': 'ID'},
            {'accessor': 'name', 'value': 'Name'},
            # Add more fields as needed
        ]
        
        content = export_model_to_excel(
            options['app_name'],
            options['model_name'],
            fields
        )
        
        with open(options['output'], 'wb') as f:
            f.write(content)
        
        self.stdout.write(f"Export completed: {options['output']}")

# Usage: python manage.py export_model blog Post --output posts.xlsx
"""

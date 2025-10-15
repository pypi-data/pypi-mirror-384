# Rail Django GraphQL - Examples

This directory contains comprehensive examples demonstrating how to use the Rail Django GraphQL library in various scenarios.

## 📁 Available Examples

### 1. `basic_usage.py`
**Perfect for beginners** - Shows the fundamental usage of the library:
- Basic Django setup and configuration
- Simple model definitions (Category, Post, Comment)
- Basic GraphQL type, query, and mutation generation
- Schema creation and URL configuration
- Simple GraphQL queries and mutations

**When to use**: Start here if you're new to the library or GraphQL in Django.

### 2. `advanced_usage.py`
**For experienced developers** - Demonstrates advanced features:
- Complex permission systems (role-based, rate limiting)
- Custom type generation with complex field mappings
- Query optimization techniques with DataLoader
- Custom middleware and extensions
- Bulk operations and complex mutations
- Performance monitoring and metrics
- Full-text search capabilities
- Advanced security features

**When to use**: When you need sophisticated GraphQL functionality with custom business logic.

### 3. `github_installation.py`
**For contributors and developers** - Shows development setup:
- Installing from GitHub repository
- Development environment setup
- Testing the library installation
- Contributing workflow and guidelines
- Code quality checks and testing procedures

**When to use**: When you want to contribute to the library or use the latest development version.

## 🚀 Quick Start

1. **Choose your starting point**:
   - New to GraphQL? → Start with `basic_usage.py`
   - Need advanced features? → Check `advanced_usage.py`
   - Want to contribute? → See `github_installation.py`

2. **Install the library**:
   ```bash
   # From PyPI (stable)
   pip install rail-django-graphql
   
   # From GitHub (latest)
   pip install git+https://github.com/raillogistic/rail-django-graphql.git
   ```

3. **Run an example**:
   ```bash
   cd examples/
   python basic_usage.py
   ```

## 📋 Prerequisites

Before running the examples, make sure you have:

- Python 3.8+ installed
- Django 4.2+ installed
- Basic understanding of Django models and views
- Basic understanding of GraphQL concepts (optional but helpful)

## 🛠️ Setup Instructions

### Option 1: Quick Setup (Recommended)
```bash
# Clone or download the examples
git clone https://github.com/raillogistic/rail-django-graphql.git
cd rail-django-graphql/examples/

# Install dependencies
pip install -r requirements.txt

# Run basic example
python basic_usage.py
```

### Option 2: Manual Setup
```bash
# Install the library
pip install rail-django-graphql

# Install additional dependencies for examples
pip install django graphene-django

# Download example files
# Run the examples
```

## 📖 Example Descriptions

### Basic Usage Example
```python
# Shows how to:
from rail_django_graphql import TypeGenerator, QueryGenerator, MutationGenerator

# Generate GraphQL types from Django models
CategoryType = TypeGenerator.from_model(Category)

# Create queries and mutations
queries = QueryGenerator.from_model(Category)
mutations = MutationGenerator.from_model(Category)

# Build complete schema
schema = SchemaBuilder.build(query=Query, mutation=Mutation)
```

### Advanced Usage Example
```python
# Demonstrates:
from rail_django_graphql.permissions import BasePermission
from rail_django_graphql.middleware import BaseMiddleware

# Custom permissions
class IsOwnerOrReadOnly(BasePermission):
    def has_permission(self, info, obj=None):
        # Custom permission logic
        pass

# Advanced type generation with custom fields
UserType = TypeGenerator.from_model(
    User,
    custom_fields={'full_name': graphene.String()},
    custom_resolvers={'full_name': lambda user, info: f"{user.first_name} {user.last_name}"},
    permission_classes=[IsOwnerOrReadOnly]
)
```

### GitHub Installation Example
```python
# Shows how to:
# 1. Install from GitHub
pip install git+https://github.com/raillogistic/rail-django-graphql.git

# 2. Set up development environment
git clone https://github.com/raillogistic/rail-django-graphql.git
pip install -e ".[dev]"

# 3. Run tests and contribute
pytest
flake8 rail_django_graphql/
```

## 🔧 Configuration Examples

### Basic Configuration
```python
# settings.py
RAIL_DJANGO_GRAPHQL = {
    'SCHEMA_SETTINGS': {
        'auto_generate_schema': True,
        'enable_introspection': True,
    },
    'SECURITY': {
        'max_query_depth': 10,
    },
}

GRAPHENE = {
    'SCHEMA': 'myproject.schema.schema',
}
```

### Advanced Configuration
```python
# settings.py
RAIL_DJANGO_GRAPHQL = {
    # Schema Generation
    'SCHEMA_SETTINGS': {
        'auto_generate_schema': True,
        'auto_discover_models': True,
        'enable_introspection': False,  # Production
    },
    
    # Security
    'SECURITY': {
        'max_query_depth': 15,
        'max_query_complexity': 2000,
        'enable_query_whitelist': True,
    },
    
    # Performance
    'PERFORMANCE': {
        'enable_query_optimization': True,
        'enable_dataloader': True,
        'cache_timeout': 600,
    
    # Permissions
    'DEFAULT_PERMISSION_CLASSES': [
        'myapp.permissions.IsAuthenticatedAndActive',
    ],
}
```

## 🧪 Testing the Examples

Each example includes test functions to verify functionality:

```bash
# Test basic usage
python basic_usage.py
# Output: ✅ All basic tests passed!

# Test advanced features
python advanced_usage.py
# Output: ✅ Advanced features working correctly!

# Test GitHub installation
python github_installation.py
# Output: ✅ GitHub installation successful!
```

## 🐛 Troubleshooting

### Common Issues

1. **ModuleNotFoundError: No module named 'rail_django_graphql'**
   ```bash
   # Solution: Install the library
   pip install rail-django-graphql
   ```

2. **ImproperlyConfigured: Django settings not configured**
   ```python
   # Solution: Configure Django before importing
   import django
   from django.conf import settings
   
   settings.configure(
       DEBUG=True,
       SECRET_KEY='your-secret-key',
       # ... other settings
   )
   django.setup()
   ```

3. **GraphQL execution errors**
   ```python
   # Solution: Check your schema and query syntax
   result = schema.execute(query)
   if result.errors:
       for error in result.errors:
           print(f"Error: {error}")
   ```

### Getting Help

- 📚 Check the [main documentation](../README.md)
- 🐛 Report issues on [GitHub Issues](https://github.com/raillogistic/rail-django-graphql/issues)
- 💬 Ask questions in [Discussions](https://github.com/raillogistic/rail-django-graphql/discussions)
- 📧 Contact maintainers (see [CONTRIBUTING.md](../CONTRIBUTING.md))

## 🤝 Contributing Examples

We welcome contributions to improve these examples! Here's how:

1. **Improve existing examples**:
   - Add more detailed comments
   - Fix bugs or issues
   - Add error handling
   - Improve code style

2. **Add new examples**:
   - Real-world use cases
   - Integration with other libraries
   - Performance optimization techniques
   - Security best practices

3. **Update documentation**:
   - Fix typos or unclear explanations
   - Add more detailed setup instructions
   - Include troubleshooting tips

### Example Contribution Process
```bash
# 1. Fork the repository
# 2. Create a feature branch
git checkout -b feature/improve-basic-example

# 3. Make your changes
# Edit examples/basic_usage.py

# 4. Test your changes
python basic_usage.py

# 5. Commit and push
git commit -m "feat: improve basic usage example with better error handling"
git push origin feature/improve-basic-example

# 6. Create a Pull Request
```

## 📝 License

These examples are part of the Rail Django GraphQL project and are licensed under the MIT License. See the [LICENSE](../LICENSE) file for details.

---

**Happy coding! 🚀**

If you find these examples helpful, please consider:
- ⭐ Starring the repository
- 🐛 Reporting issues
- 🤝 Contributing improvements
- 📢 Sharing with others
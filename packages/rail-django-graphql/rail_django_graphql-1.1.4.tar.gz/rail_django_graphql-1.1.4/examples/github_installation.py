"""
GitHub Installation and Development Setup Example

This example shows how to install rail-django-graphql from GitHub
and set up a development environment.
"""

# Installation from GitHub
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
import django
import os
GITHUB_INSTALLATION = """
# Install from GitHub (latest development version)
pip install git+https://github.com/raillogistic/rail-django-graphql.git

# Install specific branch
pip install git+https://github.com/raillogistic/rail-django-graphql.git@develop

# Install specific tag/version
pip install git+https://github.com/raillogistic/rail-django-graphql.git@v1.0.0

# Install in editable mode for development
git clone https://github.com/raillogistic/rail-django-graphql.git
cd rail-django-graphql
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
"""

# Development Environment Setup
DEVELOPMENT_SETUP = """
# 1. Clone the repository
git clone https://github.com/raillogistic/rail-django-graphql.git
cd rail-django-graphql

# 2. Create virtual environment
python -m venv venv

# Windows
venv\\Scripts\\activate

# Linux/Mac
source venv/bin/activate

# 3. Install development dependencies
pip install -e ".[dev]"

# 4. Install pre-commit hooks
pre-commit install

# 5. Run tests to verify setup
pytest

# 6. Run linting
flake8 rail_django_graphql/
black --check rail_django_graphql/
isort --check-only rail_django_graphql/

# 7. Generate documentation
cd docs/
make html
"""

# Example Django Project Setup with GitHub Version


# Configure Django settings for testing
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY="development-key-not-for-production",
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        INSTALLED_APPS=[
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.messages",
            "django.contrib.staticfiles",
            "graphene_django",
            "rail_django_graphql",
            "myapp",  # Your app
        ],
        MIDDLEWARE=[
            "django.middleware.security.SecurityMiddleware",
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.middleware.common.CommonMiddleware",
            "django.middleware.csrf.CsrfViewMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
            "django.middleware.clickjacking.XFrameOptionsMiddleware",
        ],
        ROOT_URLCONF="myproject.urls",
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "DIRS": [],
                "APP_DIRS": True,
                "OPTIONS": {
                    "context_processors": [
                        "django.template.context_processors.debug",
                        "django.template.context_processors.request",
                        "django.contrib.auth.context_processors.auth",
                        "django.contrib.messages.context_processors.messages",
                    ],
                },
            },
        ],
        # Rail Django GraphQL Configuration
        RAIL_DJANGO_GRAPHQL={
            "schema_settings": {
                "auto_generate_schema": True,
                "enable_introspection": True,  # Enable for development
            },
            "SECURITY": {
                "max_query_depth": 10,
            },
            "PERFORMANCE": {
                "enable_query_optimization": True,
                "enable_dataloader": True,
            },
            "DEVELOPMENT": {
                "enable_debugging": True,  # Enable for development
            },
        },
        GRAPHENE={
            "SCHEMA": "myproject.schema.schema",
            "MIDDLEWARE": [
                "rail_django_graphql.middleware.AuthenticationMiddleware",
                "rail_django_graphql.middleware.DebuggingMiddleware",
            ],
        },
        USE_TZ=True,
        LOGGING={
            "version": 1,
            "disable_existing_loggers": False,
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                },
            },
            "loggers": {
                "rail_django_graphql": {
                    "handlers": ["console"],
                    "level": "DEBUG",
                    "propagate": True,
                },
                "graphql": {
                    "handlers": ["console"],
                    "level": "DEBUG",
                    "propagate": True,
                },
            },
        },
    )

django.setup()

# Example models for testing


class Category(models.Model):
    nom_categorie = models.CharField(max_length=100, verbose_name="Nom de la catégorie")
    description_categorie = models.TextField(blank=True, verbose_name="Description")
    date_creation = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de création"
    )

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"

    def __str__(self):
        return self.nom_categorie


class Post(models.Model):
    titre_article = models.CharField(max_length=200, verbose_name="Titre de l'article")
    contenu_article = models.TextField(verbose_name="Contenu de l'article")
    auteur_article = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="posts", verbose_name="Auteur"
    )
    categorie_article = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
        verbose_name="Catégorie",
    )
    date_publication = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de publication"
    )
    date_modification = models.DateTimeField(
        auto_now=True, verbose_name="Date de modification"
    )
    est_publie = models.BooleanField(default=False, verbose_name="Est publié")

    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        ordering = ["-date_publication"]

    def __str__(self):
        return self.titre_article


# GitHub Development Workflow Example
def github_development_workflow():
    """
    Example of a typical development workflow with GitHub.
    """

    workflow_steps = """
    # GitHub Development Workflow
    
    ## 1. Fork and Clone
    # Fork the repository on GitHub
    # Clone your fork
    git clone https://github.com/raillogistic/rail-django-graphql.git
    cd rail-django-graphql
    
    # Add upstream remote
    git remote add upstream https://github.com/original/rail-django-graphql.git
    
    ## 2. Create Feature Branch
    git checkout -b feature/new-awesome-feature
    
    ## 3. Make Changes
    # Edit files, add features, fix bugs
    
    ## 4. Test Changes
    # Run tests
    pytest
    
    # Run linting
    flake8 rail_django_graphql/
    black rail_django_graphql/
    isort rail_django_graphql/
    
    # Test with different Django versions
    tox
    
    ## 5. Commit Changes
    git add .
    git commit -m "feat: add awesome new feature
    
    - Add new TypeGenerator method
    - Improve query optimization
    - Add comprehensive tests
    - Update documentation
    
    Closes #123"
    
    ## 6. Push and Create PR
    git push origin feature/new-awesome-feature
    # Create Pull Request on GitHub
    
    ## 7. Keep Branch Updated
    git fetch upstream
    git rebase upstream/main
    
    ## 8. After PR is Merged
    git checkout main
    git pull upstream main
    git branch -d feature/new-awesome-feature
    """

    return workflow_steps


# Testing with GitHub Version
def test_github_installation():
    """
    Test the GitHub installation of rail-django-graphql.
    """

    try:
        # Import the library
        import rail_django_graphql

        print(
            f"✅ Successfully imported rail_django_graphql version {rail_django_graphql.__version__}"
        )

        # Test basic functionality
        from rail_django_graphql import MutationGenerator, QueryGenerator, TypeGenerator

        # Generate types from models
        CategoryType = TypeGenerator.from_model(Category)
        PostType = TypeGenerator.from_model(Post)

        print("✅ Successfully generated GraphQL types")

        # Test query generation
        category_queries = QueryGenerator.from_model(Category)
        post_queries = QueryGenerator.from_model(Post)

        print("✅ Successfully generated GraphQL queries")

        # Test mutation generation
        category_mutations = MutationGenerator.from_model(Category)
        post_mutations = MutationGenerator.from_model(Post)

        print("✅ Successfully generated GraphQL mutations")

        # Test schema building
        import graphene

        from rail_django_graphql import SchemaBuilder

        class Query(graphene.ObjectType):
            categories = category_queries["list"]
            category = category_queries["detail"]
            posts = post_queries["list"]
            post = post_queries["detail"]

        class Mutation(graphene.ObjectType):
            create_category = category_mutations["create"]
            update_category = category_mutations["update"]
            delete_category = category_mutations["delete"]
            create_post = post_mutations["create"]
            update_post = post_mutations["update"]
            delete_post = post_mutations["delete"]

        schema = SchemaBuilder.build(query=Query, mutation=Mutation)

        print("✅ Successfully built GraphQL schema")

        # Test introspection
        introspection_query = """
        query IntrospectionQuery {
            __schema {
                types {
                    name
                    kind
                }
            }
        }
        """

        result = schema.execute(introspection_query)
        if not result.errors:
            print("✅ Schema introspection successful")
            print(f"   Found {len(result.data['__schema']['types'])} types")
        else:
            print("❌ Schema introspection failed")
            for error in result.errors:
                print(f"   Error: {error}")

        return True

    except ImportError as e:
        print(f"❌ Failed to import rail_django_graphql: {e}")
        print("   Make sure you have installed it from GitHub:")
        print(
            "   pip install git+https://github.com/raillogistic/rail-django-graphql.git"
        )
        return False

    except Exception as e:
        print(f"❌ Error testing GitHub installation: {e}")
        return False


# Contributing Guidelines Example
CONTRIBUTING_EXAMPLE = """
# Contributing to Rail Django GraphQL

## Development Setup from GitHub

1. **Fork the Repository**
   ```bash
   # Go to https://github.com/original/rail-django-graphql
   # Click "Fork" button
   ```

2. **Clone Your Fork**
   ```bash
   git clone https://github.com/raillogistic/rail-django-graphql.git
   cd rail-django-graphql
   ```

3. **Set Up Development Environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\\Scripts\\activate  # Windows
   
   # Install in development mode
   pip install -e ".[dev]"
   
   # Install pre-commit hooks
   pre-commit install
   ```

4. **Run Tests**
   ```bash
   # Run all tests
   pytest
   
   # Run with coverage
   pytest --cov=rail_django_graphql
   
   # Run specific test file
   pytest tests/test_type_generator.py
   
   # Run with different Django versions
   tox
   ```

5. **Code Quality Checks**
   ```bash
   # Format code
   black rail_django_graphql/
   isort rail_django_graphql/
   
   # Check formatting
   black --check rail_django_graphql/
   isort --check-only rail_django_graphql/
   
   # Lint code
   flake8 rail_django_graphql/
   
   # Type checking
   mypy rail_django_graphql/
   ```

6. **Make Changes**
   ```bash
   # Create feature branch
   git checkout -b feature/your-feature-name
   
   # Make your changes
   # Add tests for new functionality
   # Update documentation if needed
   ```

7. **Submit Pull Request**
   ```bash
   # Commit changes
   git add .
   git commit -m "feat: add your feature description"
   
   # Push to your fork
   git push origin feature/your-feature-name
   
   # Create Pull Request on GitHub
   ```

## Testing Your Changes

Before submitting a PR, make sure:

- [ ] All tests pass
- [ ] Code coverage is maintained
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated
- [ ] No breaking changes (or properly documented)
"""

if __name__ == "__main__":
    print("Rail Django GraphQL - GitHub Installation Example")
    print("=" * 55)

    print("\n📦 Installation Options:")
    print(GITHUB_INSTALLATION)

    print("\n🛠️ Development Setup:")
    print(DEVELOPMENT_SETUP)

    print("\n🔄 Development Workflow:")
    print(github_development_workflow())

    print("\n🧪 Testing Installation:")
    success = test_github_installation()

    if success:
        print("\n✅ All tests passed! GitHub installation is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the installation.")

    print("\n📝 Contributing Guidelines:")
    print(CONTRIBUTING_EXAMPLE)

"""
Setup script for rail-django-graphql library.

This file provides backward compatibility for older pip versions
and build systems that don't support pyproject.toml.
"""

import os

from setuptools import find_packages, setup


# Read the README file
def read_readme():
    """Read README.md file for long description."""
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Automatic GraphQL schema generation for Django with advanced features"

# Read version from __init__.py


def get_version():
    """Extract version from rail_django_graphql/__init__.py."""
    version_file = os.path.join(os.path.dirname(__file__), 'rail_django_graphql', '__init__.py')
    if os.path.exists(version_file):
        with open(version_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('__version__'):
                    return line.split('=')[1].strip().strip('"\'')
    return "1.0.0"


setup(
    name="rail-django-graphql",
    version=get_version(),
    description="Automatic GraphQL schema generation for Django with advanced features",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="Rail Logistic",
    author_email="contact@raillogistic.com",
    url="https://github.com/raillogistic/rail-django-graphql",
    project_urls={
        "Documentation": "https://rail-django-graphql.readthedocs.io",
        "Repository": "https://github.com/raillogistic/rail-django-graphql",
        "Issues": "https://github.com/raillogistic/rail-django-graphql/issues",
        "Changelog": "https://github.com/raillogistic/rail-django-graphql/blob/main/CHANGELOG.md",
    },
    packages=find_packages(exclude=["tests*", "test_app*", "docs*", "examples*"]),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "Django>=4.2.0",
        "graphene>=3.4.0",
        "graphene-django>=3.2.0",
        "django-filter>=24.0.0",
        "graphene-file-upload>=1.3.0",
        "django-cors-headers>=4.0.0",
    ],
    extras_require={
        "auth": ["PyJWT>=2.9.0"],
        "performance": ["psutil>=7.0.0", "redis>=4.0.0", "django-redis>=5.0.0"],
        "media": ["Pillow>=10.0.0"],
        "monitoring": ["sentry-sdk>=1.0.0", "prometheus-client>=0.15.0"],
        "dev": [
            "pytest>=8.0.0",
            "pytest-django>=4.0.0",
            "pytest-cov>=5.0.0",
            "factory-boy>=3.3.0",
            "coverage>=7.0.0",
            "black>=23.0.0",
            "isort>=5.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "djlint>=1.35.0",
        ],
        "all": [
            "PyJWT>=2.9.0",
            "psutil>=7.0.0",
            "redis>=4.0.0",
            "django-redis>=5.0.0",
            "Pillow>=10.0.0",
            "sentry-sdk>=1.0.0",
            "prometheus-client>=0.15.0",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Django",
        "Framework :: Django :: 4.2",
        "Framework :: Django :: 5.0",
        "Framework :: Django :: 5.1",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Code Generators",
    ],
    keywords="django graphql schema generation api graphene",
    license="MIT",
    zip_safe=False,
    package_data={
        "rail_django_graphql": [
            "templates/**/*",
            "static/**/*",
            "management/commands/*.py",
        ],
    },
)

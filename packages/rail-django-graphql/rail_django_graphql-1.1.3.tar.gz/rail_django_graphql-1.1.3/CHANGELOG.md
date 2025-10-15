# Changelog

## [1.1.3] - 2025-10-14

### Changed
- Automated version bump and build


All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.2] - 2024-12-20

### Fixed
- **Critical Bug Fix**: Fixed dual field logic in GraphQL mutations where mandatory dual fields (e.g., `category`/`nested_category`) were incorrectly required
- Corrected inverted logic in `rail_django_graphql/generators/types.py` that made required fields NonNull instead of making mandatory dual fields optional
- Enhanced mutual exclusivity handling between direct ID fields and nested object fields in GraphQL input types

### Improved
- Better error handling and validation for dual field scenarios
- Comprehensive test coverage for dual field functionality
- Production-ready dual field implementation with runtime validation

### Technical Details
- Modified `_should_be_required` method in TypeGenerator to properly handle mandatory dual fields
- Ensured mandatory dual fields are made optional in GraphQL schema while maintaining runtime validation
- Added extensive debugging and testing infrastructure for dual field logic

## [1.1.1] - 2024-12-19

### Added
- Initial library structure and packaging
- GitHub Actions CI/CD pipeline
- Comprehensive documentation and contributing guidelines

## [1.0.0] - 2024-01-XX

### Added
- **Core Features**
  - Automatic GraphQL schema generation from Django models
  - TypeGenerator for creating GraphQL types with customizable field mappings
  - QueryGenerator for automatic query generation with filtering and pagination
  - MutationGenerator for CRUD operations with validation
  - SchemaBuilder for comprehensive schema construction

- **Advanced Functionality**
  - Query optimization and N+1 problem prevention
  - Field-level permission system with customizable access control
  - Comprehensive debugging and introspection tools
  - Performance monitoring and metrics collection
  - Plugin system for extensible architecture

- **Developer Experience**
  - Enhanced GraphiQL interface with custom tools
  - Automatic API documentation generation
  - Comprehensive error handling and validation
  - Type hints and comprehensive docstrings
  - Extensive test coverage (>90%)

- **Security Features**
  - Built-in security measures and input validation
  - Query depth and complexity limiting
  - Authentication and authorization middleware
  - CSRF protection for mutations

- **Performance Optimizations**
  - DataLoader integration for efficient data fetching
  - Query caching and optimization
  - Lazy loading and selective field resolution
  - Database query optimization

- **Configuration & Extensibility**
  - Flexible configuration system
  - Custom scalar types support
  - Middleware system for request/response processing
  - Plugin architecture for custom extensions

- **Development Tools**
  - Management commands for schema generation and validation
  - Health check endpoints
  - Debugging middleware with query analysis
  - Performance profiling tools

### Dependencies
- Django >= 4.2
- graphene-django >= 3.0
- django-filter >= 23.0
- graphene-file-upload >= 1.3
- django-cors-headers >= 4.0

### Optional Dependencies
- PyJWT >= 2.8 (for authentication features)
- psutil >= 5.9 (for performance monitoring)
- redis >= 4.5 (for caching)
- django-redis >= 5.3 (for Django cache backend)
- Pillow >= 10.0 (for media handling)
- sentry-sdk >= 1.32 (for error monitoring)
- prometheus-client >= 0.17 (for metrics collection)

### Documentation
- Comprehensive README with installation and usage examples
- API reference documentation
- Contributing guidelines and development setup
- Security best practices guide
- Performance optimization guide

### Testing & Quality Assurance
- Unit tests for all core functionality
- Integration tests for complex workflows
- End-to-end tests for complete user scenarios
- Code coverage reporting
- Automated linting and formatting
- Type checking with mypy
- Security scanning with bandit

### CI/CD Pipeline
- Automated testing across Python 3.8-3.12 and Django 4.2-5.1
- Code quality checks (Black, isort, flake8, mypy)
- Security vulnerability scanning
- Automated PyPI publishing on releases
- Documentation building and deployment

[Unreleased]: https://github.com/raillogistic/rail-django-graphql/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/raillogistic/rail-django-graphql/releases/tag/v1.0.0
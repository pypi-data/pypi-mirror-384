# Django GraphQL Auto-Generation Documentation

Welcome to the comprehensive documentation for Django GraphQL Auto-Generation, a powerful package that provides automated GraphQL schema generation, advanced security features, and performance monitoring for Django applications.

## 📚 Documentation Overview

This documentation is organized into several key sections to help you understand, implement, and maintain secure GraphQL APIs with Django.

### 🔧 [Middleware Documentation](middleware/README.md)
Complete guide to the middleware components that provide:
- **Performance Monitoring**: Query execution tracking and optimization
- **Authentication & Security**: JWT validation and user context management  
- **Rate Limiting**: Protection against abuse and brute force attacks
- **Security Headers**: HTTP security headers management

### 🛡️ [Extensions Documentation](extensions/README.md)
Comprehensive coverage of security and monitoring extensions:
- **Audit Logging**: Security event tracking and compliance
- **Multi-Factor Authentication (MFA)**: TOTP, SMS, and backup code support
- **Security Configuration**: Centralized security settings management

### ⚙️ [Management Commands Documentation](management/README.md)
Essential tools for security validation and configuration:
- **Security Check**: Automated security validation and recommendations
- **Security Setup**: Streamlined security feature configuration
- **Maintenance Utilities**: Database cleanup and monitoring tools

## 🚀 Quick Start Guide

### 1. Installation

```bash
pip install django-graphql-auto-generation
```

### 2. Basic Configuration

Add to your Django `settings.py`:

```python
INSTALLED_APPS = [
    # ... your apps
    'rail_django_graphql',
    'graphene_django',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    
    # GraphQL Security Middleware
    'rail_django_graphql.middleware.GraphQLAuthenticationMiddleware',
    'rail_django_graphql.middleware.GraphQLRateLimitMiddleware',
    'rail_django_graphql.middleware.GraphQLPerformanceMiddleware',
    
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# GraphQL Configuration
GRAPHENE = {
    'SCHEMA': 'your_project.schema.schema'
}
```

### 3. Security Setup

Run the automated security setup:

```bash
# Basic setup
python manage.py setup_security

# Production setup
python manage.py setup_security --environment production

# Verify configuration
python manage.py security_check
```

### 4. Database Migration

```bash
python manage.py makemigrations
python manage.py migrate
```

## 🏗️ Architecture Overview

```
Django GraphQL Auto-Generation
├── Middleware Layer
│   ├── Authentication Middleware    # JWT validation & user context
│   ├── Rate Limiting Middleware     # Request throttling & abuse protection
│   └── Performance Middleware       # Query monitoring & optimization
├── Extensions Layer
│   ├── Audit System               # Security event logging
│   ├── MFA System                  # Multi-factor authentication
│   └── Security Configuration      # Centralized security management
└── Management Layer
    ├── Security Check Command      # Configuration validation
    ├── Security Setup Command      # Automated configuration
    └── Maintenance Utilities       # Database & monitoring tools
```

## 🔐 Security Features

### Authentication & Authorization
- **JWT Token Validation**: Secure token-based authentication
- **User Context Injection**: Automatic user context in GraphQL resolvers
- **Security Headers**: Comprehensive HTTP security headers
- **Session Management**: Secure session handling

### Multi-Factor Authentication
- **TOTP Support**: Time-based one-time passwords
- **SMS Verification**: Phone-based authentication
- **Backup Codes**: Account recovery mechanisms
- **Trusted Devices**: Device registration and management

### Rate Limiting & Protection
- **IP-based Rate Limiting**: Protection against brute force attacks
- **User-based Rate Limiting**: Per-user request throttling
- **GraphQL-specific Limits**: Query complexity and depth limits
- **Configurable Windows**: Flexible time-based limiting

### Audit & Monitoring
- **Security Event Logging**: Comprehensive audit trail
- **Real-time Alerting**: Immediate notification of security events
- **Compliance Reporting**: Automated security reports
- **Performance Metrics**: Query performance monitoring

## 📊 Performance Features

### Query Monitoring
- **Execution Time Tracking**: Detailed performance metrics
- **Memory Usage Monitoring**: Resource consumption analysis
- **Database Query Analysis**: N+1 query detection
- **Slow Query Detection**: Performance bottleneck identification

### Optimization Tools
- **User Caching**: Reduced database queries for authentication
- **Query Complexity Analysis**: Prevention of expensive operations
- **Performance Dashboards**: Real-time monitoring interfaces
- **Automated Recommendations**: Performance improvement suggestions

## 🛠️ Configuration Examples

### Development Environment

```python
# settings/development.py
DEBUG = True

# Relaxed security for development
GRAPHQL_ENABLE_AUTH_RATE_LIMITING = False
MFA_SETTINGS = {'ENABLED': False}

# Performance monitoring enabled
GRAPHQL_PERFORMANCE_MONITORING = {
    'ENABLED': True,
    'SLOW_QUERY_THRESHOLD': 2.0
}
```

### Production Environment

```python
# settings/production.py
DEBUG = False

# Strict security for production
GRAPHQL_ENABLE_AUTH_RATE_LIMITING = True
AUTH_LOGIN_ATTEMPTS_LIMIT = 3
AUTH_LOGIN_ATTEMPTS_WINDOW = 1800

# MFA required
MFA_SETTINGS = {'ENABLED': True}

# Comprehensive audit logging
AUDIT_LOGGING = {
    'ENABLED': True,
    'STORAGE_BACKEND': 'database',
    'RETENTION_DAYS': 365
}

# Performance monitoring with database storage
GRAPHQL_PERFORMANCE_MONITORING = {
    'ENABLED': True,
    'STORE_IN_DATABASE': True,
    'SLOW_QUERY_THRESHOLD': 0.5
}
```

## 🔍 Monitoring & Maintenance

### Security Monitoring

```bash
# Daily security check
python manage.py security_check --verbose

# Generate security report
python manage.py security_check --format json --output-file security-report.json

# Automated fixing
python manage.py security_check --fix
```

### Performance Monitoring

```python
from rail_django_graphql.middleware import get_performance_aggregator

# Get current metrics
aggregator = get_performance_aggregator()
metrics = aggregator.get_current_metrics()

print(f"Average query time: {metrics['avg_execution_time']}ms")
print(f"Slow queries: {metrics['slow_queries_count']}")
```

### Audit Log Analysis

```python
from rail_django_graphql.extensions.audit import audit_logger

# Generate security report
report = audit_logger.generate_security_report(
    start_date=datetime.now() - timedelta(days=7),
    end_date=datetime.now()
)

print(f"Failed logins: {report['failed_logins']}")
print(f"Suspicious activities: {report['suspicious_activities']}")
```

## 🚨 Troubleshooting

### Common Issues

1. **Middleware Order**: Ensure proper middleware ordering in `MIDDLEWARE` setting
2. **Cache Configuration**: Configure cache backend for rate limiting
3. **Database Migrations**: Run migrations for audit and MFA models
4. **Security Headers**: Verify HTTPS configuration for production

### Debug Mode

Enable debug logging:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'loggers': {
        'rail_django_graphql': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

## 📈 Best Practices

### Security
1. **Enable all security features** in production environments
2. **Regularly run security checks** as part of CI/CD pipeline
3. **Monitor audit logs** for suspicious activities
4. **Keep security configurations updated** based on threat landscape
5. **Use HTTPS** and proper SSL/TLS configuration

### Performance
1. **Monitor query performance** regularly
2. **Set appropriate rate limits** based on usage patterns
3. **Use caching** for frequently accessed data
4. **Optimize database queries** in GraphQL resolvers
5. **Profile memory usage** in production environments

### Maintenance
1. **Schedule regular security audits** using management commands
2. **Clean up old audit logs** based on retention policies
3. **Update dependencies** regularly for security patches
4. **Test configurations** in staging before production deployment
5. **Document custom configurations** and security decisions

## 🔗 Integration Examples

### CI/CD Pipeline

```yaml
# .github/workflows/security.yml
name: Security Check
on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run security check
        run: python manage.py security_check --format json
      - name: Validate security score
        run: |
          python -c "
          import json
          with open('security-report.json') as f:
              report = json.load(f)
          assert report['security_score'] >= 8, 'Security score too low'
          "
```

### Docker Integration

```dockerfile
FROM python:3.9

COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt
RUN python manage.py setup_security --environment production --config-only
RUN python manage.py security_check

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

## 📚 Additional Resources

### API Reference
- [Middleware API Reference](middleware/README.md#api-reference)
- [Extensions API Reference](extensions/README.md#api-reference)
- [Management Commands API](management/README.md#command-options)

### Security Guides
- [Security Configuration Guide](extensions/README.md#security-configuration)
- [MFA Implementation Guide](extensions/README.md#multi-factor-authentication-mfa)
- [Audit Logging Guide](extensions/README.md#audit-logging-system)

### Performance Guides
- [Performance Monitoring Guide](middleware/README.md#graphqlperformancemiddleware)
- [Optimization Best Practices](middleware/README.md#performance-considerations)
- [Caching Strategies](middleware/README.md#caching-strategy)

## 🤝 Contributing

We welcome contributions to improve Django GraphQL Auto-Generation! Please refer to our contributing guidelines and ensure all security features are properly tested.

### Development Setup

```bash
# Clone repository
git clone https://github.com/your-org/django-graphql-auto-generation.git
cd django-graphql-auto-generation

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest

# Run security check
python manage.py security_check --verbose
```

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.

## 🆘 Support

For support, questions, or feature requests:
- 📧 Email: support@django-graphql.com
- 🐛 Issues: [GitHub Issues](https://github.com/your-org/django-graphql-auto-generation/issues)
- 📖 Documentation: [Full Documentation](https://docs.django-graphql.com)
- 💬 Community: [Discord Server](https://discord.gg/django-graphql)

---

**Django GraphQL Auto-Generation** - Secure, performant, and scalable GraphQL APIs for Django applications.
# Management Commands Documentation

This document provides comprehensive documentation for the Django GraphQL Auto-Generation management commands, which include security validation, configuration setup, and maintenance utilities.

## Overview

The management commands package provides essential tools for:
- **Security Configuration Validation**: Automated security checks and recommendations
- **Security Setup Automation**: Streamlined security feature configuration
- **Maintenance Utilities**: Database cleanup, migration helpers, and monitoring tools
- **Development Assistance**: Configuration generation and debugging utilities

## Available Commands

### 1. security_check

**Purpose**: Validates current security configuration and provides detailed recommendations for improving application security.

**Location**: `rail_django_graphql.management.commands.security_check`

**Features**:
- Comprehensive security configuration analysis
- Middleware validation and recommendations
- Database security settings verification
- Django security settings audit
- Customizable output formats (text, JSON, verbose)
- Automatic issue detection and fixing capabilities
- Security scoring system

#### Usage

```bash
# Basic security check
python manage.py security_check

# Verbose output with detailed explanations
python manage.py security_check --verbose

# Output results in JSON format
python manage.py security_check --format json

# Automatically fix issues where possible
python manage.py security_check --fix

# Check specific security categories
python manage.py security_check --category middleware
python manage.py security_check --category django
python manage.py security_check --category database
```

#### Command Options

| Option | Description | Default |
|--------|-------------|---------|
| `--verbose` | Enable detailed output with explanations | False |
| `--format` | Output format: `text`, `json`, `yaml` | text |
| `--fix` | Automatically fix issues where possible | False |
| `--category` | Check specific category: `all`, `middleware`, `django`, `database`, `mfa`, `audit` | all |
| `--output-file` | Save results to file | None |
| `--no-color` | Disable colored output | False |

#### Example Output

```
Django GraphQL Security Configuration Check
==========================================

Checking Middleware Configuration...
✓ GraphQLAuthenticationMiddleware is properly configured
✓ GraphQLRateLimitMiddleware is enabled
✓ GraphQLPerformanceMiddleware is active
✗ SecurityMiddleware should be first in MIDDLEWARE list

Checking Audit & Logging Configuration...
✓ Audit logging is enabled
✓ Database backend is configured
✗ Log retention policy not set (Recommendation: Set AUDIT_RETENTION_DAYS)

Checking MFA Configuration...
✗ MFA is not enabled (Critical for production environments)
✗ No MFA devices configured

Checking Rate Limiting Configuration...
✓ Rate limiting is enabled
✓ Cache backend is properly configured
⚠ Login attempt limits may be too permissive (Current: 10, Recommended: 5)

Checking Django Security Settings...
✗ DEBUG is True (Critical: Set to False in production)
✗ SECRET_KEY appears to be default (Critical: Use unique secret key)
✓ ALLOWED_HOSTS is configured
✗ SECURE_SSL_REDIRECT is False (Recommendation: Enable for HTTPS)
✗ SESSION_COOKIE_SECURE is False (Recommendation: Enable for HTTPS)

Security Score: 6/10

Critical Issues (Must Fix):
1. Disable DEBUG in production
2. Use unique SECRET_KEY
3. Enable MFA for production

Recommendations:
1. Set AUDIT_RETENTION_DAYS = 365
2. Reduce login attempt limits to 5
3. Enable HTTPS enforcement
4. Configure session security settings

Auto-fixable Issues: 3
Run with --fix to automatically resolve fixable issues.
```

#### JSON Output Format

```json
{
  "security_score": 6,
  "total_checks": 15,
  "passed_checks": 9,
  "failed_checks": 6,
  "categories": {
    "middleware": {
      "score": 8,
      "checks": [
        {
          "name": "GraphQLAuthenticationMiddleware Configuration",
          "status": "passed",
          "severity": "medium",
          "message": "Middleware is properly configured"
        },
        {
          "name": "SecurityMiddleware Order",
          "status": "failed",
          "severity": "high",
          "message": "SecurityMiddleware should be first in MIDDLEWARE list",
          "recommendation": "Move 'django.middleware.security.SecurityMiddleware' to the top of MIDDLEWARE",
          "auto_fixable": true
        }
      ]
    },
    "audit": {
      "score": 7,
      "checks": [
        {
          "name": "Audit Logging Enabled",
          "status": "passed",
          "severity": "high",
          "message": "Audit logging is properly configured"
        }
      ]
    }
  },
  "recommendations": [
    "Enable MFA for production environments",
    "Set up log retention policy",
    "Configure HTTPS enforcement"
  ],
  "critical_issues": [
    "DEBUG is enabled in production",
    "Default SECRET_KEY detected"
  ]
}
```

### 2. setup_security

**Purpose**: Automates the setup and configuration of security features for Django GraphQL applications.

**Location**: `rail_django_graphql.management.commands.setup_security`

**Features**:
- Automated security middleware configuration
- Database migration generation and execution
- Security settings file generation
- Environment-specific configuration templates
- MFA setup and initialization
- Audit logging configuration
- Cache backend setup assistance

#### Usage

```bash
# Basic security setup
python manage.py setup_security

# Setup for specific environment
python manage.py setup_security --environment production
python manage.py setup_security --environment development
python manage.py setup_security --environment staging

# Generate configuration files only (no database changes)
python manage.py setup_security --config-only

# Skip database migrations
python manage.py setup_security --no-migrate

# Force overwrite existing configurations
python manage.py setup_security --force

# Interactive setup with prompts
python manage.py setup_security --interactive
```

#### Command Options

| Option | Description | Default |
|--------|-------------|---------|
| `--environment` | Target environment: `development`, `staging`, `production` | development |
| `--config-only` | Generate configuration files without database changes | False |
| `--no-migrate` | Skip database migrations | False |
| `--force` | Overwrite existing configuration files | False |
| `--interactive` | Enable interactive prompts for configuration | False |
| `--dry-run` | Show what would be done without making changes | False |

#### Setup Process

The command performs the following steps:

1. **Environment Detection**
   ```
   Detecting current environment...
   ✓ Environment: development
   ✓ Django version: 4.2.7
   ✓ Database: PostgreSQL
   ```

2. **Middleware Configuration**
   ```
   Configuring security middleware...
   ✓ Added GraphQLAuthenticationMiddleware to MIDDLEWARE
   ✓ Added GraphQLRateLimitMiddleware to MIDDLEWARE
   ✓ Added GraphQLPerformanceMiddleware to MIDDLEWARE
   ✓ Configured middleware order
   ```

3. **Database Setup**
   ```
   Setting up database models...
   ✓ Generated migration for audit events
   ✓ Generated migration for MFA devices
   ✓ Generated migration for trusted devices
   ✓ Applied migrations successfully
   ```

4. **Configuration Files**
   ```
   Generating configuration files...
   ✓ Created security_settings.py
   ✓ Created audit_config.py
   ✓ Created mfa_config.py
   ✓ Updated main settings.py
   ```

5. **Cache Configuration**
   ```
   Configuring cache backend...
   ✓ Redis connection tested successfully
   ✓ Cache configuration added to settings
   ✓ Rate limiting cache keys initialized
   ```

#### Generated Configuration Files

**security_settings.py**
```python
"""
Security settings for Django GraphQL Auto-Generation
Generated by setup_security command
Environment: production
"""

# Middleware Configuration
MIDDLEWARE_SECURITY_CONFIG = {
    'authentication': {
        'enabled': True,
        'jwt_header_prefix': 'Bearer',
        'user_cache_timeout': 300,
        'security_headers': True
    },
    'rate_limiting': {
        'enabled': True,
        'login_attempts_limit': 3,
        'login_attempts_window': 1800,  # 30 minutes
        'graphql_requests_limit': 50,
        'graphql_requests_window': 3600  # 1 hour
    }
}

# Audit Logging Configuration
AUDIT_LOGGING = {
    'ENABLED': True,
    'STORAGE_BACKEND': 'database',
    'RETENTION_DAYS': 365,
    'ALERT_THRESHOLDS': {
        'FAILED_LOGINS_PER_HOUR': 10,
        'SUSPICIOUS_ACTIVITY_PER_DAY': 5,
        'RATE_LIMIT_HITS_PER_HOUR': 50
    }
}

# MFA Configuration
MFA_SETTINGS = {
    'ENABLED': True,
    'TOTP_ISSUER': 'Your App Name',
    'BACKUP_CODES_COUNT': 10,
    'TRUSTED_DEVICE_DURATION_DAYS': 30
}

# Django Security Settings
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

#### Interactive Setup

When using `--interactive` flag, the command prompts for configuration options:

```
Django GraphQL Security Setup
============================

Environment Configuration:
? Select target environment: (Use arrow keys)
  > production
    staging  
    development

Middleware Configuration:
? Enable authentication middleware? (Y/n): Y
? Enable rate limiting? (Y/n): Y
? Enable performance monitoring? (Y/n): Y

Rate Limiting Configuration:
? Login attempts limit (1-20): 5
? Login attempts window (minutes): 15
? GraphQL requests limit (10-1000): 100
? GraphQL requests window (minutes): 60

MFA Configuration:
? Enable Multi-Factor Authentication? (Y/n): Y
? TOTP issuer name: My Django App
? Number of backup codes (5-20): 10

Audit Logging Configuration:
? Enable audit logging? (Y/n): Y
? Storage backend (file/database/webhook): database
? Log retention days (30-365): 365

Cache Configuration:
? Cache backend (redis/memcached/database): redis
? Redis host: localhost
? Redis port: 6379
? Redis database: 1

Generating configuration...
✓ All configurations generated successfully!
```

## Configuration Templates

### Development Environment Template

```python
# Development security configuration
DEVELOPMENT_CONFIG = {
    'middleware': {
        'authentication': {'enabled': True},
        'rate_limiting': {'enabled': False},  # Disabled for development
        'performance': {'enabled': True}
    },
    'audit': {
        'enabled': True,
        'storage_backend': 'file',
        'retention_days': 30
    },
    'mfa': {'enabled': False},  # Disabled for development
    'django_security': {
        'DEBUG': True,
        'SECURE_SSL_REDIRECT': False,
        'SESSION_COOKIE_SECURE': False
    }
}
```

### Production Environment Template

```python
# Production security configuration
PRODUCTION_CONFIG = {
    'middleware': {
        'authentication': {'enabled': True},
        'rate_limiting': {
            'enabled': True,
            'login_attempts_limit': 3,
            'login_attempts_window': 1800
        },
        'performance': {'enabled': True}
    },
    'audit': {
        'enabled': True,
        'storage_backend': 'database',
        'retention_days': 365,
        'webhook_url': 'https://siem.company.com/webhook'
    },
    'mfa': {'enabled': True},
    'django_security': {
        'DEBUG': False,
        'SECURE_SSL_REDIRECT': True,
        'SESSION_COOKIE_SECURE': True,
        'CSRF_COOKIE_SECURE': True
    }
}
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Security Check

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  security-check:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run security check
      run: |
        python manage.py security_check --format json --output-file security-report.json
    
    - name: Upload security report
      uses: actions/upload-artifact@v3
      with:
        name: security-report
        path: security-report.json
    
    - name: Fail on critical issues
      run: |
        python -c "
        import json
        with open('security-report.json') as f:
            report = json.load(f)
        if report['security_score'] < 8:
            exit(1)
        "
```

### Docker Integration

```dockerfile
# Dockerfile
FROM python:3.9

COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt

# Run security setup during build
RUN python manage.py setup_security --environment production --config-only

# Run security check
RUN python manage.py security_check --format json > security-report.json

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

## Monitoring and Maintenance

### Automated Security Monitoring

```python
# monitoring/security_monitor.py
from django.core.management import call_command
from django.core.mail import send_mail
import json
import logging

def run_security_check():
    """Run automated security check and send alerts"""
    
    try:
        # Run security check
        call_command('security_check', format='json', output_file='security-check.json')
        
        # Load results
        with open('security-check.json') as f:
            report = json.load(f)
        
        # Check security score
        if report['security_score'] < 8:
            send_security_alert(report)
        
        # Log results
        logging.info(f"Security check completed. Score: {report['security_score']}/10")
        
    except Exception as e:
        logging.error(f"Security check failed: {e}")
        send_error_alert(str(e))

def send_security_alert(report):
    """Send security alert email"""
    
    subject = f"Security Alert: Score {report['security_score']}/10"
    message = f"""
    Security check completed with issues:
    
    Critical Issues: {len(report['critical_issues'])}
    Failed Checks: {report['failed_checks']}
    
    Critical Issues:
    {chr(10).join(report['critical_issues'])}
    
    Please review and address these issues immediately.
    """
    
    send_mail(
        subject=subject,
        message=message,
        from_email='security@company.com',
        recipient_list=['admin@company.com', 'security-team@company.com']
    )
```

### Scheduled Security Checks

```python
# celery_tasks.py
from celery import shared_task
from django.core.management import call_command

@shared_task
def daily_security_check():
    """Daily automated security check"""
    call_command('security_check', format='json', output_file='daily-security-check.json')

@shared_task
def weekly_security_report():
    """Weekly comprehensive security report"""
    call_command('security_check', verbose=True, output_file='weekly-security-report.txt')

# Schedule in celery beat
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'daily-security-check': {
        'task': 'myapp.tasks.daily_security_check',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    'weekly-security-report': {
        'task': 'myapp.tasks.weekly_security_report',
        'schedule': crontab(hour=3, minute=0, day_of_week=1),  # Weekly on Monday at 3 AM
    },
}
```

## Troubleshooting

### Common Issues

1. **Command Not Found**
   ```
   Error: Unknown command: 'security_check'
   ```
   **Solution**: Ensure the app is in `INSTALLED_APPS`:
   ```python
   INSTALLED_APPS = [
       # ... other apps
       'rail_django_graphql',
   ]
   ```

2. **Migration Errors During Setup**
   ```
   Error: Migration failed for audit events
   ```
   **Solution**: 
   - Check database permissions
   - Ensure database is running
   - Run migrations manually: `python manage.py migrate`

3. **Cache Configuration Issues**
   ```
   Error: Cache backend not configured
   ```
   **Solution**: Configure cache in settings:
   ```python
   CACHES = {
       'default': {
           'BACKEND': 'django.core.cache.backends.redis.RedisCache',
           'LOCATION': 'redis://127.0.0.1:6379/1',
       }
   }
   ```

4. **Permission Denied for Configuration Files**
   ```
   Error: Permission denied writing to security_settings.py
   ```
   **Solution**: 
   - Check file permissions
   - Run with appropriate user privileges
   - Use `--dry-run` to test first

### Debug Mode

Enable debug logging for management commands:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'rail_django_graphql.management': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

## Best Practices

### Security Validation
1. **Run security checks regularly** as part of CI/CD pipeline
2. **Set minimum security score thresholds** for deployments
3. **Address critical issues immediately** before production deployment
4. **Review security recommendations** and implement where appropriate
5. **Monitor security scores over time** to track improvements

### Configuration Management
1. **Use environment-specific configurations** for different deployment stages
2. **Version control configuration templates** for consistency
3. **Test configurations in staging** before production deployment
4. **Document custom security settings** and their rationale
5. **Regularly update security configurations** based on new threats

### Automation
1. **Integrate security checks into CI/CD** for continuous validation
2. **Automate security setup** for new environments
3. **Schedule regular security audits** using management commands
4. **Set up alerting for security issues** detected by automated checks
5. **Use configuration management tools** for consistent deployments

This management commands package provides essential tools for maintaining secure Django GraphQL applications. Regular use of these commands helps ensure consistent security posture and compliance with best practices.
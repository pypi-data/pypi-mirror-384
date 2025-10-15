# Extensions Documentation

This document provides comprehensive documentation for the Django GraphQL Auto-Generation extensions package, which includes audit logging, multi-factor authentication (MFA), and security configuration components.

## Overview

The extensions package provides advanced security and monitoring features:
- **Audit Logging**: Comprehensive security event tracking and compliance
- **Multi-Factor Authentication (MFA)**: TOTP, SMS, and backup code support
- **Security Configuration**: Centralized security settings management

## Available Extensions

### 1. Audit Logging System

**Purpose**: Provides comprehensive audit logging for security events, compliance tracking, and security monitoring.

**Location**: `rail_django_graphql.extensions.audit`

**Features**:
- Authentication event logging (login, logout, failures)
- Security event tracking (suspicious activity, rate limits)
- Token lifecycle management logging
- Configurable severity levels and event types
- Multiple storage backends (file, database, webhook)
- Security report generation
- Real-time alerting for critical events

#### Event Types

```python
class AuditEventType(Enum):
    # Authentication Events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    
    # Token Events
    TOKEN_CREATED = "token_created"
    TOKEN_REFRESHED = "token_refreshed"
    TOKEN_EXPIRED = "token_expired"
    TOKEN_REVOKED = "token_revoked"
    
    # Security Events
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    
    # MFA Events
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    MFA_SUCCESS = "mfa_success"
    MFA_FAILED = "mfa_failed"
```

#### Severity Levels

```python
class AuditSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
```

#### Configuration

```python
# settings.py
AUDIT_LOGGING = {
    'ENABLED': True,
    'STORAGE_BACKEND': 'database',  # 'file', 'database', 'webhook'
    'LOG_FILE_PATH': '/var/log/django/audit.log',
    'DATABASE_TABLE': 'audit_events',
    'WEBHOOK_URL': 'https://your-siem.com/webhook',
    'WEBHOOK_HEADERS': {
        'Authorization': 'Bearer your-token',
        'Content-Type': 'application/json'
    },
    'RETENTION_DAYS': 365,
    'ALERT_THRESHOLDS': {
        'FAILED_LOGINS_PER_HOUR': 10,
        'SUSPICIOUS_ACTIVITY_PER_DAY': 5,
        'RATE_LIMIT_HITS_PER_HOUR': 50
    }
}
```

#### Usage Examples

```python
from rail_django_graphql.extensions.audit import audit_logger

# Log authentication success
audit_logger.log_authentication_success(
    user=user,
    client_ip='192.168.1.1',
    user_agent='Mozilla/5.0...',
    additional_data={'login_method': 'password'}
)

# Log authentication failure
audit_logger.log_authentication_failure(
    username='john_doe',
    client_ip='192.168.1.1',
    user_agent='Mozilla/5.0...',
    reason='Invalid password'
)

# Log suspicious activity
audit_logger.log_suspicious_activity(
    user=user,
    client_ip='192.168.1.1',
    activity_type='Multiple failed login attempts',
    details={'attempts': 5, 'time_window': '5 minutes'}
)

# Log rate limit exceeded
audit_logger.log_rate_limit_exceeded(
    identifier='192.168.1.1',
    limit_type='login_attempts',
    current_count=10,
    limit=5,
    window_seconds=900
)

# Generate security report
report = audit_logger.generate_security_report(
    start_date=datetime.now() - timedelta(days=7),
    end_date=datetime.now()
)
print(f"Failed logins: {report['failed_logins']}")
print(f"Suspicious activities: {report['suspicious_activities']}")
```

#### Database Model

```python
class AuditEventModel(models.Model):
    """Database model for storing audit events"""
    
    event_type = models.CharField(max_length=50)
    severity = models.CharField(max_length=20)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    client_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    details = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'audit_events'
        indexes = [
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['client_ip', 'timestamp']),
        ]
```

### 2. Multi-Factor Authentication (MFA)

**Purpose**: Provides comprehensive MFA support including TOTP, SMS, and backup codes for enhanced security.

**Location**: `rail_django_graphql.extensions.mfa`

**Features**:
- TOTP (Time-based One-Time Password) support
- SMS-based verification
- Backup codes for account recovery
- Trusted device management
- GraphQL mutations for MFA setup and verification
- QR code generation for authenticator apps
- Device registration and management

#### MFA Device Types

```python
class MFADeviceType(models.TextChoices):
    TOTP = 'totp', 'TOTP Authenticator'
    SMS = 'sms', 'SMS'
    BACKUP_CODES = 'backup_codes', 'Backup Codes'
```

#### Database Models

```python
class MFADevice(models.Model):
    """Model for storing MFA devices"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mfa_devices')
    device_type = models.CharField(max_length=20, choices=MFADeviceType.choices)
    name = models.CharField(max_length=100)
    secret_key = models.CharField(max_length=255)  # Encrypted
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)

class MFABackupCode(models.Model):
    """Model for storing backup codes"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='backup_codes')
    code = models.CharField(max_length=20, unique=True)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)

class TrustedDevice(models.Model):
    """Model for storing trusted devices"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trusted_devices')
    device_id = models.CharField(max_length=255, unique=True)
    device_name = models.CharField(max_length=100)
    user_agent = models.TextField()
    ip_address = models.GenericIPAddressField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
```

#### Configuration

```python
# settings.py
MFA_SETTINGS = {
    'ENABLED': True,
    'TOTP_ISSUER': 'Your App Name',
    'TOTP_DIGITS': 6,
    'TOTP_PERIOD': 30,
    'BACKUP_CODES_COUNT': 10,
    'BACKUP_CODE_LENGTH': 8,
    'TRUSTED_DEVICE_DURATION_DAYS': 30,
    'SMS_PROVIDER': 'twilio',  # 'twilio', 'aws_sns', 'custom'
    'SMS_SETTINGS': {
        'TWILIO_ACCOUNT_SID': 'your_account_sid',
        'TWILIO_AUTH_TOKEN': 'your_auth_token',
        'TWILIO_PHONE_NUMBER': '+1234567890'
    }
}
```

#### Usage Examples

```python
from rail_django_graphql.extensions.mfa import MFAManager

mfa_manager = MFAManager()

# Check if MFA is required for user
if mfa_manager.is_mfa_required(user):
    print("MFA verification required")

# Setup TOTP device
totp_secret = mfa_manager.setup_totp_device(
    user=user,
    device_name="My Phone"
)
qr_code_url = mfa_manager.generate_qr_code(user, totp_secret)

# Verify TOTP code
is_valid = mfa_manager.verify_totp_code(
    user=user,
    code="123456"
)

# Setup SMS device
mfa_manager.setup_sms_device(
    user=user,
    phone_number="+1234567890",
    device_name="My Phone"
)

# Send SMS code
mfa_manager.send_sms_code(user=user)

# Verify SMS code
is_valid = mfa_manager.verify_sms_code(
    user=user,
    code="123456"
)

# Generate backup codes
backup_codes = mfa_manager.generate_backup_codes(user=user)

# Verify backup code
is_valid = mfa_manager.verify_backup_code(
    user=user,
    code="ABCD1234"
)

# Register trusted device
device_id = mfa_manager.register_trusted_device(
    user=user,
    device_name="My Laptop",
    user_agent="Mozilla/5.0...",
    ip_address="192.168.1.1"
)
```

#### GraphQL Integration

```python
# GraphQL Types
class MFADeviceType(DjangoObjectType):
    class Meta:
        model = MFADevice
        fields = ('id', 'device_type', 'name', 'is_active', 'is_primary', 'created_at', 'last_used')

class SetupTOTPMutation(graphene.Mutation):
    class Arguments:
        device_name = graphene.String(required=True)
    
    success = graphene.Boolean()
    secret_key = graphene.String()
    qr_code_url = graphene.String()
    backup_codes = graphene.List(graphene.String)
    
    def mutate(self, info, device_name):
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("Authentication required")
        
        mfa_manager = MFAManager()
        secret_key = mfa_manager.setup_totp_device(user, device_name)
        qr_code_url = mfa_manager.generate_qr_code(user, secret_key)
        backup_codes = mfa_manager.generate_backup_codes(user)
        
        return SetupTOTPMutation(
            success=True,
            secret_key=secret_key,
            qr_code_url=qr_code_url,
            backup_codes=backup_codes
        )

class VerifyTOTPMutation(graphene.Mutation):
    class Arguments:
        code = graphene.String(required=True)
        trust_device = graphene.Boolean(default_value=False)
    
    success = graphene.Boolean()
    device_id = graphene.String()
    
    def mutate(self, info, code, trust_device=False):
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("Authentication required")
        
        mfa_manager = MFAManager()
        is_valid = mfa_manager.verify_totp_code(user, code)
        
        device_id = None
        if is_valid and trust_device:
            device_id = mfa_manager.register_trusted_device(
                user=user,
                device_name="Trusted Device",
                user_agent=info.context.META.get('HTTP_USER_AGENT', ''),
                ip_address=get_client_ip(info.context)
            )
        
        return VerifyTOTPMutation(success=is_valid, device_id=device_id)
```

### 3. Security Configuration

**Purpose**: Centralized management of security settings and configurations across the application.

**Location**: `rail_django_graphql.extensions.security_config`

**Features**:
- Centralized security configuration management
- Environment-specific settings
- Security validation and recommendations
- Configuration templates for different environments
- Integration with Django security settings

#### Configuration Structure

```python
class SecurityConfig:
    """Centralized security configuration management"""
    
    @classmethod
    def get_middleware_config(cls):
        """Get middleware configuration"""
        return {
            'authentication': {
                'enabled': True,
                'jwt_header_prefix': 'Bearer',
                'user_cache_timeout': 300,
                'security_headers': True
            },
            'rate_limiting': {
                'enabled': True,
                'login_attempts_limit': 5,
                'login_attempts_window': 900,
                'graphql_requests_limit': 100,
                'graphql_requests_window': 3600
            },
            'performance': {
                'enabled': True,
                'slow_query_threshold': 1.0,
                'track_memory_usage': True
            }
        }
    
    @classmethod
    def get_audit_config(cls):
        """Get audit logging configuration"""
        return {
            'enabled': True,
            'storage_backend': 'database',
            'retention_days': 365,
            'alert_thresholds': {
                'failed_logins_per_hour': 10,
                'suspicious_activity_per_day': 5
            }
        }
    
    @classmethod
    def get_mfa_config(cls):
        """Get MFA configuration"""
        return {
            'enabled': True,
            'totp_issuer': 'Django GraphQL App',
            'backup_codes_count': 10,
            'trusted_device_duration_days': 30
        }
```

#### Environment-Specific Configurations

```python
# Development Configuration
DEVELOPMENT_SECURITY_CONFIG = {
    'middleware': {
        'rate_limiting': {'enabled': False},
        'performance': {'enabled': True}
    },
    'audit': {
        'storage_backend': 'file',
        'retention_days': 30
    },
    'mfa': {'enabled': False}
}

# Production Configuration
PRODUCTION_SECURITY_CONFIG = {
    'middleware': {
        'rate_limiting': {
            'enabled': True,
            'login_attempts_limit': 3,
            'login_attempts_window': 1800
        }
    },
    'audit': {
        'storage_backend': 'database',
        'retention_days': 365,
        'webhook_url': 'https://siem.company.com/webhook'
    },
    'mfa': {'enabled': True}
}
```

## Management Commands

### Security Check Command

**Purpose**: Validates current security configuration and provides recommendations.

**Usage**:
```bash
# Basic security check
python manage.py security_check

# Verbose output with detailed recommendations
python manage.py security_check --verbose

# Output in JSON format
python manage.py security_check --format json

# Auto-fix issues where possible
python manage.py security_check --fix
```

**Example Output**:
```
Django GraphQL Security Configuration Check
==========================================

✓ Authentication middleware is properly configured
✓ Rate limiting is enabled and configured
✗ MFA is not enabled (Recommendation: Enable for production)
✓ Audit logging is configured
✗ HTTPS is not enforced (Critical: Enable SECURE_SSL_REDIRECT)

Security Score: 7/10

Recommendations:
1. Enable MFA for enhanced security
2. Configure HTTPS enforcement
3. Set up security headers middleware
4. Configure session security settings
```

### Security Setup Command

**Purpose**: Automates security configuration setup and initialization.

**Usage**:
```bash
# Setup basic security configuration
python manage.py setup_security

# Setup for production environment
python manage.py setup_security --environment production

# Generate configuration files only
python manage.py setup_security --config-only

# Skip database migrations
python manage.py setup_security --no-migrate
```

**Features**:
- Generates security configuration files
- Creates necessary database migrations
- Sets up audit logging
- Configures MFA settings
- Provides environment-specific recommendations

## Integration Examples

### Complete Security Setup

```python
# settings.py
from rail_django_graphql.extensions.security_config import SecurityConfig

# Load security configuration
security_config = SecurityConfig()

# Middleware configuration
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'rail_django_graphql.middleware.GraphQLAuthenticationMiddleware',
    'rail_django_graphql.middleware.GraphQLRateLimitMiddleware',
    'rail_django_graphql.middleware.GraphQLPerformanceMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Apply security configurations
middleware_config = security_config.get_middleware_config()
GRAPHQL_ENABLE_AUTH_RATE_LIMITING = middleware_config['rate_limiting']['enabled']
AUTH_LOGIN_ATTEMPTS_LIMIT = middleware_config['rate_limiting']['login_attempts_limit']

# Audit configuration
audit_config = security_config.get_audit_config()
AUDIT_LOGGING = audit_config

# MFA configuration
mfa_config = security_config.get_mfa_config()
MFA_SETTINGS = mfa_config
```

### GraphQL Schema Integration

```python
import graphene
from rail_django_graphql.extensions.mfa import (
    MFADeviceType, SetupTOTPMutation, VerifyTOTPMutation,
    SetupSMSMutation, VerifySMSMutation
)

class Query(graphene.ObjectType):
    mfa_devices = graphene.List(MFADeviceType)
    
    def resolve_mfa_devices(self, info):
        user = info.context.user
        if not user.is_authenticated:
            return []
        return user.mfa_devices.filter(is_active=True)

class Mutation(graphene.ObjectType):
    setup_totp = SetupTOTPMutation.Field()
    verify_totp = VerifyTOTPMutation.Field()
    setup_sms = SetupSMSMutation.Field()
    verify_sms = VerifySMSMutation.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)
```

## Monitoring and Alerting

### Security Metrics Dashboard

```python
from rail_django_graphql.extensions.audit import audit_logger
from datetime import datetime, timedelta

def get_security_dashboard_data():
    """Generate security dashboard data"""
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    # Generate security report
    report = audit_logger.generate_security_report(start_date, end_date)
    
    return {
        'failed_logins': report['failed_logins'],
        'successful_logins': report['successful_logins'],
        'suspicious_activities': report['suspicious_activities'],
        'rate_limit_hits': report['rate_limit_hits'],
        'mfa_usage': report['mfa_events'],
        'security_score': calculate_security_score(report)
    }

def calculate_security_score(report):
    """Calculate security score based on events"""
    score = 100
    
    # Deduct points for security issues
    score -= min(report['failed_logins'] * 0.1, 20)
    score -= min(report['suspicious_activities'] * 2, 30)
    score -= min(report['rate_limit_hits'] * 0.05, 10)
    
    return max(score, 0)
```

### Real-time Alerting

```python
from rail_django_graphql.extensions.audit import audit_logger

# Set up alert handlers
def security_alert_handler(event):
    """Handle security alerts"""
    
    if event.severity == 'CRITICAL':
        # Send immediate notification
        send_security_alert(
            subject=f"Critical Security Event: {event.event_type}",
            message=f"Event: {event.event_type}\nUser: {event.user}\nIP: {event.client_ip}",
            recipients=['security@company.com']
        )
    
    elif event.severity == 'HIGH':
        # Log to security monitoring system
        log_to_siem(event)

# Register alert handler
audit_logger.register_alert_handler(security_alert_handler)
```

## Best Practices

### Security Configuration
1. **Use environment-specific configurations** for different deployment stages
2. **Enable all security features** in production environments
3. **Regularly review and update** security settings
4. **Monitor security metrics** and set up appropriate alerts
5. **Keep audit logs** for compliance and forensic analysis

### MFA Implementation
1. **Require MFA for privileged accounts** and sensitive operations
2. **Provide multiple MFA options** (TOTP, SMS, backup codes)
3. **Implement trusted device management** for better user experience
4. **Regularly rotate backup codes** and remind users to update them
5. **Monitor MFA usage patterns** for anomaly detection

### Audit Logging
1. **Log all security-relevant events** including successes and failures
2. **Use structured logging** with consistent event formats
3. **Implement log retention policies** based on compliance requirements
4. **Set up real-time monitoring** for critical security events
5. **Regularly review audit logs** for security analysis

## Troubleshooting

### Common Issues

1. **MFA Setup Fails**
   ```
   Error: Unable to generate TOTP secret
   ```
   **Solution**: Check that `cryptography` package is installed and `SECRET_KEY` is properly configured

2. **Audit Logging Not Working**
   ```
   Error: Unable to write to audit log
   ```
   **Solution**: 
   - Check file permissions for log directory
   - Verify database configuration for database backend
   - Test webhook URL for webhook backend

3. **SMS MFA Not Sending**
   ```
   Error: SMS delivery failed
   ```
   **Solution**: 
   - Verify SMS provider credentials
   - Check phone number format
   - Ensure SMS provider account has sufficient credits

### Debug Configuration

```python
# Enable debug logging for extensions
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
        },
    },
    'loggers': {
        'rail_django_graphql.extensions': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

This extensions package provides comprehensive security features for Django GraphQL applications. For additional configuration options and advanced usage, refer to the individual component documentation and security best practices guide.
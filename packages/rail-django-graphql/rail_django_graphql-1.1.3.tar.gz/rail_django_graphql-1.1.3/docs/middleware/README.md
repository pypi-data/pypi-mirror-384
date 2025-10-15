# Middleware Documentation

This document provides comprehensive documentation for the Django GraphQL Auto-Generation middleware package, which includes performance monitoring, security, authentication, and rate limiting components.

## Overview

The middleware package provides essential components for:
- **Performance Monitoring**: Query execution tracking and optimization
- **Authentication & Security**: JWT validation and user context management
- **Rate Limiting**: Protection against abuse and brute force attacks
- **Audit Logging**: Security event tracking and compliance

## Available Middleware Components

### 1. GraphQLPerformanceMiddleware

**Purpose**: Monitors and tracks GraphQL query performance, providing detailed metrics and optimization insights.

**Location**: `rail_django_graphql.middleware.performance`

**Features**:
- Query execution time tracking
- Memory usage monitoring
- Database query analysis
- Slow query detection
- Performance metrics aggregation
- Real-time performance dashboard

**Configuration**:
```python
MIDDLEWARE = [
    # ... other middleware
    'rail_django_graphql.middleware.GraphQLPerformanceMiddleware',
    # ... other middleware
]

# Performance settings
GRAPHQL_PERFORMANCE_MONITORING = {
    'ENABLED': True,
    'SLOW_QUERY_THRESHOLD': 1.0,  # seconds
    'TRACK_MEMORY_USAGE': True,
    'TRACK_DATABASE_QUERIES': True,
    'AGGREGATION_WINDOW': 300,  # 5 minutes
}
```

**Usage Example**:
```python
from rail_django_graphql.middleware import get_performance_aggregator

# Get performance metrics
aggregator = get_performance_aggregator()
metrics = aggregator.get_metrics()
print(f"Average query time: {metrics['avg_execution_time']}ms")
```

### 2. GraphQLAuthenticationMiddleware

**Purpose**: Handles JWT token validation, user authentication, and security headers for GraphQL requests.

**Location**: `rail_django_graphql.middleware.auth_middleware`

**Features**:
- JWT token validation and parsing
- User context injection into GraphQL resolvers
- HTTP security headers management
- Authentication event logging
- User caching for performance optimization
- Support for multiple authentication methods

**Configuration**:
```python
MIDDLEWARE = [
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'rail_django_graphql.middleware.GraphQLAuthenticationMiddleware',
    # ... other middleware
]

# Authentication settings
JWT_AUTH_HEADER_PREFIX = 'Bearer'
JWT_AUTH_HEADER_NAME = 'HTTP_AUTHORIZATION'
JWT_USER_CACHE_TIMEOUT = 300  # 5 minutes
GRAPHQL_ENDPOINTS = ['/graphql/', '/graphql']
```

**Security Headers Applied**:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `Content-Security-Policy: default-src 'self'`
- `Referrer-Policy: strict-origin-when-cross-origin`

**Usage in GraphQL Resolvers**:
```python
def resolve_user_profile(self, info):
    # User is automatically available in context
    user = info.context.user
    if user.is_authenticated:
        return user.profile
    return None
```

### 3. GraphQLRateLimitMiddleware

**Purpose**: Implements rate limiting to protect against abuse, brute force attacks, and excessive API usage.

**Location**: `rail_django_graphql.middleware.auth_middleware`

**Features**:
- IP-based rate limiting
- User-based rate limiting
- Different limits for login attempts vs general queries
- Configurable time windows
- Integration with Django cache backends
- Automatic rate limit response generation

**Configuration**:
```python
MIDDLEWARE = [
    # ... authentication middleware
    'rail_django_graphql.middleware.GraphQLRateLimitMiddleware',
    # ... other middleware
]

# Rate limiting settings
GRAPHQL_ENABLE_AUTH_RATE_LIMITING = True
AUTH_LOGIN_ATTEMPTS_LIMIT = 5
AUTH_LOGIN_ATTEMPTS_WINDOW = 900  # 15 minutes
GRAPHQL_REQUESTS_LIMIT = 100
GRAPHQL_REQUESTS_WINDOW = 3600  # 1 hour

# Cache configuration (required)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

**Rate Limit Response**:
```json
{
  "errors": [
    {
      "message": "Rate limit exceeded. Try again in 847 seconds.",
      "extensions": {
        "code": "RATE_LIMIT_EXCEEDED",
        "retry_after": 847
      }
    }
  ]
}
```

## Middleware Order and Dependencies

**Recommended Middleware Order**:
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    
    # GraphQL Security Middleware (order matters)
    'rail_django_graphql.middleware.GraphQLAuthenticationMiddleware',
    'rail_django_graphql.middleware.GraphQLRateLimitMiddleware',
    
    # GraphQL Performance Middleware
    'rail_django_graphql.middleware.GraphQLPerformanceMiddleware',
    
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

**Dependencies**:
- **Authentication Middleware**: Requires Django's `AuthenticationMiddleware`
- **Rate Limiting**: Requires configured cache backend
- **Performance Monitoring**: No external dependencies
- **All Middleware**: Requires `graphene-django` and `PyJWT`

## Integration with Extensions

The middleware integrates seamlessly with the extensions package:

### Audit Logging Integration
```python
from rail_django_graphql.extensions.audit import audit_logger

# Middleware automatically logs to audit system
# Manual logging example:
audit_logger.log_authentication_success(
    user=user,
    client_ip='192.168.1.1',
    user_agent='Mozilla/5.0...'
)
```

### MFA Integration
```python
from rail_django_graphql.extensions.mfa import MFAManager

# Middleware respects MFA requirements
mfa_manager = MFAManager()
if mfa_manager.is_mfa_required(user):
    # Handle MFA verification
    pass
```

## Performance Considerations

### Caching Strategy
- **User Caching**: Authenticated users are cached for 5 minutes by default
- **Rate Limit Caching**: Uses sliding window algorithm with Redis/Memcached
- **Performance Metrics**: Aggregated in memory with periodic persistence

### Memory Usage
- **Performance Middleware**: ~1-2MB for metrics storage
- **Authentication Middleware**: ~100KB for user cache
- **Rate Limiting**: ~50KB per active IP/user

### Database Impact
- **Authentication**: Reduces user queries by 80-90% with caching
- **Audit Logging**: Asynchronous writes to minimize impact
- **Performance Tracking**: Optional database storage for historical data

## Configuration Examples

### Development Configuration
```python
# settings/development.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'rail_django_graphql.middleware.GraphQLAuthenticationMiddleware',
    'rail_django_graphql.middleware.GraphQLPerformanceMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Relaxed rate limiting for development
GRAPHQL_ENABLE_AUTH_RATE_LIMITING = False
GRAPHQL_PERFORMANCE_MONITORING = {'ENABLED': True}
```

### Production Configuration
```python
# settings/production.py
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

# Strict rate limiting for production
GRAPHQL_ENABLE_AUTH_RATE_LIMITING = True
AUTH_LOGIN_ATTEMPTS_LIMIT = 3
AUTH_LOGIN_ATTEMPTS_WINDOW = 1800  # 30 minutes
GRAPHQL_REQUESTS_LIMIT = 50
GRAPHQL_REQUESTS_WINDOW = 3600  # 1 hour

# Performance monitoring with database storage
GRAPHQL_PERFORMANCE_MONITORING = {
    'ENABLED': True,
    'STORE_IN_DATABASE': True,
    'SLOW_QUERY_THRESHOLD': 0.5,  # 500ms
}
```

## Monitoring and Debugging

### Performance Monitoring
```python
# Access performance metrics
from rail_django_graphql.middleware import get_performance_aggregator

aggregator = get_performance_aggregator()
metrics = aggregator.get_current_metrics()

print(f"Total queries: {metrics['total_queries']}")
print(f"Average execution time: {metrics['avg_execution_time']}ms")
print(f"Slow queries: {metrics['slow_queries_count']}")
```

### Security Monitoring
```python
# Check authentication events
from rail_django_graphql.extensions.audit import audit_logger

# Get recent security events
events = audit_logger.get_recent_events(hours=24)
failed_logins = [e for e in events if e.event_type == 'LOGIN_FAILED']

print(f"Failed login attempts in last 24h: {len(failed_logins)}")
```

### Rate Limiting Status
```python
from django.core.cache import cache

# Check rate limit status for an IP
ip = '192.168.1.1'
key = f"rate_limit_graphql_{ip}"
current_count = cache.get(key, 0)
print(f"Current requests for {ip}: {current_count}")
```

## Troubleshooting

### Common Issues

1. **Cache Not Configured**
   ```
   Error: 'default' cache not configured
   ```
   **Solution**: Configure a cache backend in `CACHES` setting

2. **Middleware Order Issues**
   ```
   Error: User not authenticated in GraphQL context
   ```
   **Solution**: Ensure `GraphQLAuthenticationMiddleware` comes after Django's `AuthenticationMiddleware`

3. **Performance Impact**
   ```
   Issue: Slow GraphQL responses
   ```
   **Solution**: 
   - Enable user caching: `JWT_USER_CACHE_TIMEOUT = 300`
   - Use Redis for caching instead of database
   - Optimize database queries in resolvers

4. **Rate Limiting Too Strict**
   ```
   Issue: Legitimate users getting rate limited
   ```
   **Solution**: Adjust limits in settings:
   ```python
   GRAPHQL_REQUESTS_LIMIT = 200  # Increase limit
   GRAPHQL_REQUESTS_WINDOW = 3600  # Keep window same
   ```

### Debug Mode

Enable debug logging for middleware:
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
        'rail_django_graphql.middleware': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

## API Reference

### GraphQLPerformanceMiddleware

**Methods**:
- `process_request(request)`: Initialize performance tracking
- `process_response(request, response)`: Finalize metrics collection
- `get_metrics()`: Return current performance metrics

**Metrics Collected**:
- `execution_time`: Query execution duration
- `memory_usage`: Peak memory usage during query
- `database_queries`: Number of database queries executed
- `cache_hits`: Number of cache hits/misses

### GraphQLAuthenticationMiddleware

**Methods**:
- `process_request(request)`: Authenticate user and set context
- `_extract_jwt_token(request)`: Extract JWT from request headers
- `_authenticate_user(token)`: Validate token and get user
- `_log_authentication_event(event_type, user, request)`: Log auth events

**Context Variables Set**:
- `request.user`: Authenticated user object
- `request.auth_token`: JWT token information
- `request.client_ip`: Client IP address

### GraphQLRateLimitMiddleware

**Methods**:
- `process_request(request)`: Check and enforce rate limits
- `_is_rate_limited(identifier, limit, window)`: Check rate limit status
- `_create_rate_limit_response(retry_after)`: Generate rate limit response

**Rate Limit Keys**:
- `rate_limit_login_{ip}`: Login attempts per IP
- `rate_limit_graphql_{ip}`: GraphQL requests per IP
- `rate_limit_user_{user_id}`: Requests per authenticated user

## Best Practices

### Security
1. **Always use HTTPS** in production with security middleware
2. **Configure strong rate limits** to prevent abuse
3. **Monitor authentication events** for suspicious activity
4. **Use Redis/Memcached** for production caching
5. **Regularly review audit logs** for security incidents

### Performance
1. **Enable user caching** to reduce database queries
2. **Monitor slow queries** and optimize resolvers
3. **Use database connection pooling** for better performance
4. **Set appropriate cache timeouts** based on your use case
5. **Profile memory usage** in production environments

### Monitoring
1. **Set up alerts** for high error rates or slow queries
2. **Monitor rate limit hits** to adjust limits appropriately
3. **Track authentication failures** for security monitoring
4. **Use performance metrics** to identify bottlenecks
5. **Regularly clean up old audit logs** to manage storage

## Migration Guide

### From Basic Setup to Full Security

1. **Add Authentication Middleware**:
   ```python
   # Add to MIDDLEWARE
   'rail_django_graphql.middleware.GraphQLAuthenticationMiddleware',
   ```

2. **Enable Rate Limiting**:
   ```python
   # Add to MIDDLEWARE
   'rail_django_graphql.middleware.GraphQLRateLimitMiddleware',
   
   # Configure settings
   GRAPHQL_ENABLE_AUTH_RATE_LIMITING = True
   ```

3. **Configure Cache Backend**:
   ```python
   CACHES = {
       'default': {
           'BACKEND': 'django.core.cache.backends.redis.RedisCache',
           'LOCATION': 'redis://127.0.0.1:6379/1',
       }
   }
   ```

4. **Run Security Check**:
   ```bash
   python manage.py security_check
   ```

This middleware package provides a comprehensive foundation for secure, performant GraphQL APIs with Django. For additional configuration options and advanced usage, refer to the individual component documentation and the security guide.
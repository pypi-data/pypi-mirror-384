# Recommandations de Sécurité pour rail-django-graphql

## Vue d'ensemble

Ce document fournit des recommandations détaillées pour améliorer et maintenir la sécurité du système `rail-django-graphql`. Il couvre les bonnes pratiques, les configurations recommandées, et les mesures de sécurité avancées.

## 🔒 Architecture de Sécurité Recommandée

### Couches de Sécurité

```
┌─────────────────────────────────────────────────────────────┐
│                    Client (Frontend)                        │
├─────────────────────────────────────────────────────────────┤
│                 Reverse Proxy (Nginx)                      │
│              • Rate Limiting                               │
│              • SSL Termination                             │
│              • Request Filtering                           │
├─────────────────────────────────────────────────────────────┤
│                Django Middleware Stack                      │
│              • CORS                                        │
│              • CSRF Protection                             │
│              • Security Headers                            │
├─────────────────────────────────────────────────────────────┤
│              GraphQL Security Middleware                    │
│              • Query Complexity Analysis                   │
│              • Depth Limiting                              │
│              • Rate Limiting                               │
│              • Introspection Control                       │
├─────────────────────────────────────────────────────────────┤
│                Authentication Layer                         │
│              • JWT Validation                              │
│              • MFA Verification                            │
│              • Session Management                          │
├─────────────────────────────────────────────────────────────┤
│                Authorization Layer                          │
│              • RBAC (Role-Based Access Control)           │
│              • Field-Level Permissions                     │
│              • Contextual Permissions                      │
├─────────────────────────────────────────────────────────────┤
│                Input Validation Layer                       │
│              • Schema Validation                           │
│              • Input Sanitization                          │
│              • Business Logic Validation                   │
├─────────────────────────────────────────────────────────────┤
│                   Data Access Layer                         │
│              • ORM Security                                │
│              • Query Filtering                             │
│              • Data Masking                                │
├─────────────────────────────────────────────────────────────┤
│                    Audit Layer                              │
│              • Operation Logging                           │
│              • Security Event Monitoring                   │
│              • Anomaly Detection                           │
└─────────────────────────────────────────────────────────────┘
```

## 🛡️ Recommandations par Catégorie

### 1. Authentification et Autorisation

#### Configuration JWT Recommandée

```python
# settings.py
JWT_AUTH = {
    'JWT_SECRET_KEY': os.environ.get('JWT_SECRET_KEY'),  # Clé forte, unique
    'JWT_ALGORITHM': 'HS256',
    'JWT_EXPIRATION_DELTA': timedelta(minutes=15),      # Token court
    'JWT_REFRESH_EXPIRATION_DELTA': timedelta(days=7),  # Refresh plus long
    'JWT_ALLOW_REFRESH': True,
    'JWT_AUTH_HEADER_PREFIX': 'Bearer',
    'JWT_VERIFY_EXPIRATION': True,
    'JWT_LEEWAY': 0,  # Pas de tolérance sur l'expiration
    'JWT_AUDIENCE': 'your-app-name',
    'JWT_ISSUER': 'your-domain.com',
}

# Rotation automatique des clés JWT
JWT_KEY_ROTATION = {
    'ENABLE_ROTATION': True,
    'ROTATION_INTERVAL': timedelta(days=30),
    'KEEP_OLD_KEYS': 2,  # Garder 2 anciennes clés pour la transition
}
```

#### Configuration MFA Renforcée

```python
# Configuration MFA
MFA_CONFIG = {
    'TOTP': {
        'ISSUER_NAME': 'VotreApp',
        'DIGITS': 6,
        'PERIOD': 30,
        'ALGORITHM': 'SHA1',
        'BACKUP_TOKENS': 10,
    },
    'SMS': {
        'PROVIDER': 'twilio',
        'FROM_NUMBER': '+1234567890',
        'MESSAGE_TEMPLATE': 'Votre code de vérification: {code}',
        'CODE_LENGTH': 6,
        'CODE_EXPIRY': 300,  # 5 minutes
    },
    'EMAIL': {
        'ENABLED': True,
        'TEMPLATE': 'mfa/email_code.html',
        'SUBJECT': 'Code de vérification',
    },
    'TRUSTED_DEVICES': {
        'ENABLED': True,
        'EXPIRY_DAYS': 30,
        'MAX_DEVICES': 5,
    }
}

# Politiques MFA
MFA_POLICIES = {
    'REQUIRE_FOR_ADMIN': True,
    'REQUIRE_FOR_SENSITIVE_OPS': True,
    'GRACE_PERIOD_HOURS': 1,  # Période de grâce après authentification
    'BACKUP_CODES_MIN': 3,    # Minimum de codes de sauvegarde
}
```

### 2. Contrôle d'Accès Basé sur les Rôles (RBAC)

#### Hiérarchie de Rôles Recommandée

```python
# Configuration des rôles hiérarchiques
ROLE_HIERARCHY = {
    'super_admin': {
        'inherits_from': [],
        'permissions': ['*'],  # Toutes les permissions
        'description': 'Administrateur système complet'
    },
    'admin': {
        'inherits_from': ['manager'],
        'permissions': [
            'user.create', 'user.read', 'user.update', 'user.delete',
            'role.assign', 'role.revoke',
            'system.configure', 'audit.read'
        ],
        'description': 'Administrateur de l\'application'
    },
    'manager': {
        'inherits_from': ['team_lead'],
        'permissions': [
            'employee.create', 'employee.read', 'employee.update',
            'report.generate', 'budget.approve'
        ],
        'description': 'Manager avec permissions étendues'
    },
    'team_lead': {
        'inherits_from': ['employee'],
        'permissions': [
            'team.read', 'team.update',
            'task.assign', 'task.review'
        ],
        'description': 'Chef d\'équipe'
    },
    'employee': {
        'inherits_from': ['user'],
        'permissions': [
            'profile.read', 'profile.update',
            'task.read', 'task.update'
        ],
        'description': 'Employé standard'
    },
    'user': {
        'inherits_from': [],
        'permissions': [
            'auth.login', 'auth.logout',
            'profile.read'
        ],
        'description': 'Utilisateur de base'
    }
}
```

#### Permissions Contextuelles

```python
# Exemple de permissions contextuelles
CONTEXTUAL_PERMISSIONS = {
    'employee.salary.read': {
        'conditions': [
            'user.is_hr_manager',
            'user.is_finance_manager',
            'user.is_employee_manager',  # Manager de l'employé
            'user.is_self'  # L'employé lui-même
        ]
    },
    'document.read': {
        'conditions': [
            'document.is_public',
            'user.is_document_owner',
            'user.has_department_access',
            'document.is_shared_with_user'
        ]
    }
}
```

### 3. Sécurité GraphQL

#### Configuration de Sécurité Stricte

```python
# Configuration GraphQL sécurisée
GRAPHQL_SECURITY = {
    'MAX_QUERY_COMPLEXITY': 100,      # Complexité maximale
    'MAX_QUERY_DEPTH': 7,             # Profondeur maximale
    'MAX_FIELD_COUNT': 30,            # Nombre de champs max
    'QUERY_TIMEOUT': 10,              # Timeout en secondes
    'ENABLE_INTROSPECTION': False,    # Désactiver en production
    'INTROSPECTION_ROLES': ['developer', 'admin'],
    
    # Rate limiting spécifique à GraphQL
    'RATE_LIMIT': {
        'REQUESTS_PER_MINUTE': 60,
        'REQUESTS_PER_HOUR': 1000,
        'COMPLEXITY_PER_MINUTE': 1000,
        'BURST_ALLOWANCE': 10
    },
    
    # Analyse des coûts de requête
    'COST_ANALYSIS': {
        'ENABLED': True,
        'MAX_COST': 1000,
        'SCALAR_COST': 1,
        'OBJECT_COST': 2,
        'LIST_FACTOR': 10,
        'INTROSPECTION_COST': 1000
    }
}
```

#### Règles de Validation Personnalisées

```python
from graphql.validation import ValidationRule
from graphql.error import GraphQLError

class SecurityValidationRule(ValidationRule):
    """Règle de validation personnalisée pour la sécurité."""
    
    def enter_field(self, node, *args):
        # Vérifier les champs sensibles
        if node.name.value in ['password', 'token', 'secret']:
            if not self.context.user.has_perm('admin'):
                raise GraphQLError(
                    f"Accès refusé au champ sensible: {node.name.value}",
                    nodes=[node]
                )
    
    def enter_argument(self, node, *args):
        # Valider les arguments
        if node.name.value == 'id' and not node.value.value.isdigit():
            raise GraphQLError(
                "L'ID doit être numérique",
                nodes=[node]
            )

# Ajouter la règle au schéma
GRAPHQL_VALIDATION_RULES = [
    SecurityValidationRule,
    # Autres règles...
]
```

### 4. Validation et Sanitisation des Entrées

#### Validateurs Personnalisés

```python
# Validateurs métier spécifiques
CUSTOM_VALIDATORS = {
    'employee_id': {
        'pattern': r'^EMP\d{6}$',
        'message': 'L\'ID employé doit suivre le format EMP123456'
    },
    'phone_number': {
        'pattern': r'^\+?1?\d{9,15}$',
        'message': 'Numéro de téléphone invalide'
    },
    'ssn': {
        'pattern': r'^\d{3}-\d{2}-\d{4}$',
        'message': 'Le SSN doit suivre le format XXX-XX-XXXX',
        'encrypt': True  # Chiffrer automatiquement
    },
    'bank_account': {
        'pattern': r'^\d{10,12}$',
        'message': 'Numéro de compte bancaire invalide',
        'encrypt': True
    }
}

# Configuration de sanitisation
SANITIZATION_CONFIG = {
    'HTML_SANITIZER': {
        'ALLOWED_TAGS': ['b', 'i', 'u', 'em', 'strong'],
        'ALLOWED_ATTRIBUTES': {},
        'STRIP_DISALLOWED': True
    },
    'SQL_INJECTION_PATTERNS': [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\b)',
        r'(UNION\s+SELECT)',
        r'(--|\#|\/\*)',
        r'(\bOR\b.*=.*\bOR\b)',
        r'(\bAND\b.*=.*\bAND\b)'
    ],
    'XSS_PATTERNS': [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>.*?</iframe>'
    ]
}
```

### 5. Audit et Monitoring

#### Configuration d'Audit Complète

```python
# Configuration des logs d'audit
AUDIT_CONFIG = {
    'ENABLED': True,
    'LOG_LEVEL': 'INFO',
    'LOG_FORMAT': 'json',
    'RETENTION_DAYS': 365,
    
    # Événements à auditer
    'EVENTS': {
        'AUTHENTICATION': {
            'login_success': True,
            'login_failure': True,
            'logout': True,
            'password_change': True,
            'mfa_setup': True,
            'mfa_verification': True
        },
        'AUTHORIZATION': {
            'permission_granted': True,
            'permission_denied': True,
            'role_assigned': True,
            'role_revoked': True
        },
        'DATA_ACCESS': {
            'read_sensitive_data': True,
            'bulk_export': True,
            'admin_access': True
        },
        'DATA_MODIFICATION': {
            'create': True,
            'update': True,
            'delete': True,
            'bulk_operations': True
        },
        'SYSTEM': {
            'configuration_change': True,
            'security_policy_change': True,
            'user_management': True
        }
    },
    
    # Détection d'anomalies
    'ANOMALY_DETECTION': {
        'ENABLED': True,
        'BRUTE_FORCE_THRESHOLD': 5,
        'UNUSUAL_ACCESS_PATTERN': True,
        'BULK_DATA_ACCESS_THRESHOLD': 100,
        'OFF_HOURS_ACCESS': True,
        'GEOGRAPHIC_ANOMALIES': True
    }
}

# Alertes de sécurité
SECURITY_ALERTS = {
    'EMAIL_NOTIFICATIONS': {
        'ENABLED': True,
        'RECIPIENTS': ['security@yourcompany.com'],
        'SEVERITY_THRESHOLD': 'HIGH'
    },
    'SLACK_INTEGRATION': {
        'ENABLED': True,
        'WEBHOOK_URL': os.environ.get('SLACK_SECURITY_WEBHOOK'),
        'CHANNEL': '#security-alerts'
    },
    'SIEM_INTEGRATION': {
        'ENABLED': True,
        'ENDPOINT': 'https://your-siem.com/api/events',
        'API_KEY': os.environ.get('SIEM_API_KEY')
    }
}
```

### 6. Chiffrement et Protection des Données

#### Configuration de Chiffrement

```python
# Configuration du chiffrement
ENCRYPTION_CONFIG = {
    'ALGORITHM': 'AES-256-GCM',
    'KEY_DERIVATION': 'PBKDF2',
    'KEY_ITERATIONS': 100000,
    'SALT_LENGTH': 32,
    
    # Champs à chiffrer automatiquement
    'ENCRYPTED_FIELDS': [
        'Employee.ssn',
        'Employee.bank_account',
        'User.phone_number',
        'Company.tax_id'
    ],
    
    # Rotation des clés
    'KEY_ROTATION': {
        'ENABLED': True,
        'ROTATION_INTERVAL': timedelta(days=90),
        'KEEP_OLD_KEYS': 3
    }
}

# Configuration de hachage des mots de passe
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
]

# Politique de mots de passe
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 12}
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    {
        'NAME': 'myapp.validators.CustomPasswordValidator',
        'OPTIONS': {
            'require_uppercase': True,
            'require_lowercase': True,
            'require_digits': True,
            'require_symbols': True,
            'max_age_days': 90
        }
    }
]
```

### 7. Sécurité de l'Infrastructure

#### Configuration Nginx Recommandée

```nginx
# Configuration Nginx sécurisée
server {
    listen 443 ssl http2;
    server_name yourapp.com;
    
    # SSL Configuration
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;
    
    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=graphql:10m rate=5r/s;
    
    location /graphql {
        limit_req zone=graphql burst=20 nodelay;
        proxy_pass http://django_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Block common attack patterns
    location ~* \.(php|asp|aspx|jsp)$ {
        return 444;
    }
    
    location ~* /(wp-admin|wp-login|phpmyadmin) {
        return 444;
    }
}
```

#### Configuration Docker Sécurisée

```dockerfile
# Dockerfile sécurisé
FROM python:3.11-slim

# Créer un utilisateur non-root
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer les dépendances Python
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copier le code de l'application
COPY --chown=appuser:appuser . /app
WORKDIR /app

# Passer à l'utilisateur non-root
USER appuser

# Exposer le port
EXPOSE 8000

# Commande de démarrage
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "myproject.wsgi:application"]
```

## 🔍 Tests de Sécurité Recommandés

### Tests Automatisés

```python
# tests/test_security.py
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from graphene.test import Client
from myapp.schema import schema

User = get_user_model()

class SecurityTestCase(TestCase):
    """Tests de sécurité pour GraphQL."""
    
    def setUp(self):
        self.client = Client(schema)
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_query_depth_limiting(self):
        """Test de limitation de profondeur des requêtes."""
        deep_query = """
        query {
            users {
                company {
                    employees {
                        user {
                            company {
                                employees {
                                    user {
                                        id
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        result = self.client.execute(deep_query)
        self.assertIsNotNone(result.errors)
        self.assertIn("Query depth limit exceeded", str(result.errors))
    
    def test_query_complexity_limiting(self):
        """Test de limitation de complexité des requêtes."""
        complex_query = """
        query {
            users {
                id
                username
                email
                company {
                    id
                    name
                    employees {
                        id
                        salary
                        user {
                            id
                            username
                        }
                    }
                }
            }
        }
        """
        
        result = self.client.execute(complex_query)
        self.assertIsNotNone(result.errors)
        self.assertIn("Query complexity limit exceeded", str(result.errors))
    
    def test_unauthorized_access(self):
        """Test d'accès non autorisé."""
        query = """
        query {
            employees {
                salary
                ssn
            }
        }
        """
        
        # Sans authentification
        result = self.client.execute(query)
        self.assertIsNotNone(result.errors)
        self.assertIn("Authentication required", str(result.errors))
    
    def test_field_level_permissions(self):
        """Test des permissions au niveau des champs."""
        query = """
        query {
            employees {
                id
                salary
            }
        }
        """
        
        # Avec utilisateur sans permissions
        result = self.client.execute(query, context={'user': self.user})
        self.assertIsNotNone(result.data)
        
        # Vérifier que le salaire est masqué
        for employee in result.data['employees']:
            self.assertIn('***', employee.get('salary', ''))
    
    def test_input_validation(self):
        """Test de validation des entrées."""
        mutation = """
        mutation {
            createEmployee(
                employeeId: "<script>alert('xss')</script>",
                salary: -1000
            ) {
                employee {
                    id
                }
            }
        }
        """
        
        result = self.client.execute(mutation, context={'user': self.user})
        self.assertIsNotNone(result.errors)
        self.assertIn("Invalid input", str(result.errors))
```

### Tests de Pénétration

```bash
#!/bin/bash
# Script de tests de sécurité automatisés

echo "🔍 Tests de sécurité GraphQL"

# Test d'injection GraphQL
echo "Testing GraphQL injection..."
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "query { users { id } } { __schema { types { name } } }"}'

# Test de déni de service
echo "Testing DoS protection..."
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "query { users { company { employees { user { company { employees { id } } } } } } }"}'

# Test de rate limiting
echo "Testing rate limiting..."
for i in {1..100}; do
  curl -X POST http://localhost:8000/graphql \
    -H "Content-Type: application/json" \
    -d '{"query": "query { users { id } }"}' &
done
wait

# Test d'introspection
echo "Testing introspection security..."
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "query IntrospectionQuery { __schema { queryType { name } } }"}'

echo "✅ Tests de sécurité terminés"
```

## 📋 Checklist de Sécurité

### Déploiement en Production

- [ ] **Authentification**
  - [ ] JWT configuré avec clés fortes
  - [ ] MFA activé pour les comptes privilégiés
  - [ ] Rotation des clés implémentée
  - [ ] Sessions sécurisées configurées

- [ ] **Autorisation**
  - [ ] RBAC configuré et testé
  - [ ] Permissions de champs implémentées
  - [ ] Permissions contextuelles validées
  - [ ] Principe du moindre privilège appliqué

- [ ] **GraphQL Security**
  - [ ] Limitation de profondeur activée
  - [ ] Analyse de complexité configurée
  - [ ] Introspection désactivée en production
  - [ ] Rate limiting implémenté
  - [ ] Timeout des requêtes configuré

- [ ] **Validation des Entrées**
  - [ ] Validation de schéma activée
  - [ ] Sanitisation des entrées implémentée
  - [ ] Protection contre l'injection SQL
  - [ ] Protection contre XSS

- [ ] **Chiffrement**
  - [ ] HTTPS/TLS configuré
  - [ ] Champs sensibles chiffrés
  - [ ] Clés de chiffrement sécurisées
  - [ ] Rotation des clés planifiée

- [ ] **Audit et Monitoring**
  - [ ] Logs d'audit configurés
  - [ ] Monitoring de sécurité actif
  - [ ] Alertes configurées
  - [ ] Détection d'anomalies activée

- [ ] **Infrastructure**
  - [ ] Reverse proxy configuré
  - [ ] Firewall configuré
  - [ ] Conteneurs sécurisés
  - [ ] Secrets management implémenté

### Maintenance Continue

- [ ] **Mises à jour**
  - [ ] Dépendances régulièrement mises à jour
  - [ ] Patches de sécurité appliqués
  - [ ] Vulnérabilités scannées

- [ ] **Tests**
  - [ ] Tests de sécurité automatisés
  - [ ] Tests de pénétration réguliers
  - [ ] Audit de code sécurisé

- [ ] **Formation**
  - [ ] Équipe formée aux bonnes pratiques
  - [ ] Procédures de sécurité documentées
  - [ ] Plan de réponse aux incidents

## 🚨 Plan de Réponse aux Incidents

### Procédure d'Urgence

1. **Détection**
   - Monitoring automatique
   - Alertes en temps réel
   - Rapports d'utilisateurs

2. **Évaluation**
   - Gravité de l'incident
   - Impact sur les données
   - Nombre d'utilisateurs affectés

3. **Confinement**
   - Isolation des systèmes compromis
   - Révocation des accès suspects
   - Sauvegarde des preuves

4. **Éradication**
   - Correction des vulnérabilités
   - Nettoyage des systèmes
   - Mise à jour des configurations

5. **Récupération**
   - Restauration des services
   - Validation de la sécurité
   - Monitoring renforcé

6. **Leçons Apprises**
   - Analyse post-incident
   - Amélioration des processus
   - Mise à jour de la documentation

## 📞 Contacts d'Urgence

- **Équipe Sécurité**: security@yourcompany.com
- **Administrateur Système**: admin@yourcompany.com
- **Responsable Technique**: cto@yourcompany.com
- **CERT National**: cert@cert.fr

---

*Ce document doit être régulièrement mis à jour et adapté aux besoins spécifiques de votre organisation.*
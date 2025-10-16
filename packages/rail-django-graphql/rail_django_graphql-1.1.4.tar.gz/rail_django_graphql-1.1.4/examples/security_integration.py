"""
Exemple d'intégration complète du système de sécurité Django GraphQL.

Ce fichier montre comment :
- Configurer le système RBAC
- Implémenter les permissions de champs
- Utiliser la validation d'entrée
- Configurer la sécurité GraphQL
- Mettre en place l'audit logging
"""

import graphene
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import models
from graphene_django import DjangoObjectType

# Imports du système de sécurité
from rail_django_graphql.security import (  # RBAC; Field Permissions; Input Validation; GraphQL Security; Audit Logging
    AuditEventType,
    AuditSeverity,
    FieldAccessLevel,
    FieldPermissionRule,
    FieldVisibility,
    InputValidator,
    PermissionContext,
    RoleDefinition,
    RoleType,
    SecurityConfig,
    audit_data_modification,
    audit_graphql_operation,
    create_security_middleware,
    field_permission_manager,
    field_permission_required,
    mask_sensitive_fields,
    require_introspection_permission,
    require_permission,
    require_role,
    role_manager,
    validate_input,
)

User = get_user_model()


# ============================================================================
# MODÈLES D'EXEMPLE
# ============================================================================

class Company(models.Model):
    """Modèle d'entreprise avec données sensibles."""
    name = models.CharField(max_length=200, verbose_name="Nom de l'entreprise")
    email = models.EmailField(verbose_name="Email de contact")
    phone = models.CharField(max_length=20, verbose_name="Téléphone")
    revenue = models.DecimalField(max_digits=15, decimal_places=2,
                                  verbose_name="Chiffre d'affaires")
    tax_id = models.CharField(max_length=50, verbose_name="Numéro fiscal")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Créé par")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        verbose_name = "Entreprise"
        verbose_name_plural = "Entreprises"


class Employee(models.Model):
    """Modèle d'employé avec informations personnelles."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Utilisateur")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name="Entreprise")
    employee_id = models.CharField(max_length=20, unique=True, verbose_name="ID employé")
    salary = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Salaire")
    ssn = models.CharField(max_length=11, verbose_name="Numéro de sécurité sociale")
    bank_account = models.CharField(max_length=30, verbose_name="Compte bancaire")
    manager = models.ForeignKey('self', null=True, blank=True,
                                on_delete=models.SET_NULL, verbose_name="Manager")

    class Meta:
        verbose_name = "Employé"
        verbose_name_plural = "Employés"


# ============================================================================
# CONFIGURATION DU SYSTÈME DE SÉCURITÉ
# ============================================================================

def setup_security_system():
    """Configure le système de sécurité complet."""

    # 1. Configuration des rôles RBAC
    setup_rbac_roles()

    # 2. Configuration des permissions de champs
    setup_field_permissions()

    # 3. Configuration de la sécurité GraphQL
    security_config = SecurityConfig(
        max_query_complexity=500,
        max_query_depth=10,
        max_field_count=50,
        enable_introspection=False,
        introspection_roles=['admin', 'developer'],
        query_timeout=15,
        rate_limit_per_minute=30
    )

    return security_config


def setup_rbac_roles():
    """Configure les rôles et permissions RBAC."""

    # Rôles métier personnalisés
    hr_manager_role = RoleDefinition(
        name='hr_manager',
        description='Gestionnaire des ressources humaines',
        role_type=RoleType.BUSINESS,
        permissions=[
            'employee.create', 'employee.read', 'employee.update', 'employee.delete',
            'employee.salary.read', 'employee.ssn.read', 'employee.bank_account.read',
            'company.read', 'company.update',
            'user.read', 'user.update'
        ]
    )

    finance_manager_role = RoleDefinition(
        name='finance_manager',
        description='Gestionnaire financier',
        role_type=RoleType.BUSINESS,
        permissions=[
            'company.revenue.read', 'company.tax_id.read',
            'employee.salary.read', 'employee.bank_account.read',
            'financial_report.create', 'financial_report.read'
        ]
    )

    team_lead_role = RoleDefinition(
        name='team_lead',
        description='Chef d\'équipe',
        role_type=RoleType.BUSINESS,
        permissions=[
            'employee.read_team', 'employee.update_team',
            'project.create', 'project.read', 'project.update', 'project.delete',
            'task.assign', 'task.review'
        ]
    )

    # Enregistrer les rôles
    role_manager.register_role(hr_manager_role)
    role_manager.register_role(finance_manager_role)
    role_manager.register_role(team_lead_role)


def setup_field_permissions():
    """Configure les permissions au niveau des champs."""

    # Permissions pour les données financières
    field_permission_manager.register_field_rule(FieldPermissionRule(
        field_name="salary",
        model_name="Employee",
        access_level=FieldAccessLevel.READ,
        visibility=FieldVisibility.VISIBLE,
        roles=["hr_manager", "finance_manager", "admin"]
    ))

    field_permission_manager.register_field_rule(FieldPermissionRule(
        field_name="salary",
        model_name="Employee",
        access_level=FieldAccessLevel.READ,
        visibility=FieldVisibility.MASKED,
        mask_value="***CONFIDENTIEL***",
        condition=lambda ctx: ctx.instance.manager == ctx.user.employee if hasattr(
            ctx.user, 'employee') else False
    ))

    # Permissions pour les données personnelles sensibles
    field_permission_manager.register_field_rule(FieldPermissionRule(
        field_name="ssn",
        model_name="Employee",
        access_level=FieldAccessLevel.READ,
        visibility=FieldVisibility.REDACTED,
        roles=["hr_manager", "admin"]
    ))

    field_permission_manager.register_field_rule(FieldPermissionRule(
        field_name="bank_account",
        model_name="Employee",
        access_level=FieldAccessLevel.READ,
        visibility=FieldVisibility.MASKED,
        mask_value="***MASQUÉ***",
        roles=["hr_manager", "finance_manager", "admin"]
    ))

    # Permissions pour les données d'entreprise
    field_permission_manager.register_field_rule(FieldPermissionRule(
        field_name="revenue",
        model_name="Company",
        access_level=FieldAccessLevel.READ,
        visibility=FieldVisibility.VISIBLE,
        roles=["finance_manager", "admin"]
    ))

    field_permission_manager.register_field_rule(FieldPermissionRule(
        field_name="tax_id",
        model_name="Company",
        access_level=FieldAccessLevel.READ,
        visibility=FieldVisibility.VISIBLE,
        roles=["finance_manager", "admin"]
    ))


# ============================================================================
# TYPES GRAPHQL AVEC SÉCURITÉ
# ============================================================================

class UserType(DjangoObjectType):
    """Type GraphQL pour les utilisateurs avec sécurité."""

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_active')

    @field_permission_required('email', FieldAccessLevel.READ)
    def resolve_email(self, info):
        """Résolveur sécurisé pour l'email."""
        return self.email


class CompanyType(DjangoObjectType):
    """Type GraphQL pour les entreprises avec sécurité."""

    class Meta:
        model = Company
        fields = '__all__'

    @field_permission_required('revenue', FieldAccessLevel.READ)
    def resolve_revenue(self, info):
        """Résolveur sécurisé pour le chiffre d'affaires."""
        return self.revenue

    @field_permission_required('tax_id', FieldAccessLevel.READ)
    def resolve_tax_id(self, info):
        """Résolveur sécurisé pour le numéro fiscal."""
        return self.tax_id


class EmployeeType(DjangoObjectType):
    """Type GraphQL pour les employés avec sécurité."""

    class Meta:
        model = Employee
        fields = '__all__'

    @field_permission_required('salary', FieldAccessLevel.READ)
    def resolve_salary(self, info):
        """Résolveur sécurisé pour le salaire."""
        return self.salary

    @field_permission_required('ssn', FieldAccessLevel.READ)
    def resolve_ssn(self, info):
        """Résolveur sécurisé pour le SSN."""
        return self.ssn

    @field_permission_required('bank_account', FieldAccessLevel.READ)
    def resolve_bank_account(self, info):
        """Résolveur sécurisé pour le compte bancaire."""
        return self.bank_account


# ============================================================================
# REQUÊTES AVEC SÉCURITÉ
# ============================================================================

class Query(graphene.ObjectType):
    """Requêtes GraphQL avec sécurité."""

    # Requêtes utilisateur
    me = graphene.Field(UserType)
    users = graphene.List(UserType)
    user = graphene.Field(UserType, id=graphene.ID(required=True))

    # Requêtes entreprise
    companies = graphene.List(CompanyType)
    company = graphene.Field(CompanyType, id=graphene.ID(required=True))

    # Requêtes employé
    employees = graphene.List(EmployeeType)
    employee = graphene.Field(EmployeeType, id=graphene.ID(required=True))
    my_team = graphene.List(EmployeeType)

    @audit_graphql_operation("query")
    def resolve_me(self, info):
        """Récupère l'utilisateur actuel."""
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentification requise")
        return user

    @require_role(['admin', 'hr_manager'])
    @audit_graphql_operation("query")
    def resolve_users(self, info):
        """Liste tous les utilisateurs (admin/RH seulement)."""
        return User.objects.all()

    @require_permission('user.read')
    @audit_graphql_operation("query")
    def resolve_user(self, info, id):
        """Récupère un utilisateur spécifique."""
        return User.objects.get(pk=id)

    @require_permission('company.read')
    @audit_graphql_operation("query")
    def resolve_companies(self, info):
        """Liste toutes les entreprises."""
        return Company.objects.all()

    @require_permission('company.read')
    @audit_graphql_operation("query")
    def resolve_company(self, info, id):
        """Récupère une entreprise spécifique."""
        return Company.objects.get(pk=id)

    @require_role(['admin', 'hr_manager', 'finance_manager'])
    @audit_graphql_operation("query")
    def resolve_employees(self, info):
        """Liste tous les employés."""
        return Employee.objects.all()

    @require_permission('employee.read')
    @audit_graphql_operation("query")
    def resolve_employee(self, info, id):
        """Récupère un employé spécifique."""
        return Employee.objects.get(pk=id)

    @require_role(['team_lead', 'manager'])
    @audit_graphql_operation("query")
    def resolve_my_team(self, info):
        """Récupère l'équipe de l'utilisateur."""
        user = info.context.user
        if hasattr(user, 'employee'):
            return Employee.objects.filter(manager=user.employee)
        return []


# ============================================================================
# MUTATIONS AVEC SÉCURITÉ
# ============================================================================

class CreateEmployee(graphene.Mutation):
    """Mutation pour créer un employé avec validation et audit."""

    class Arguments:
        user_id = graphene.ID(required=True)
        company_id = graphene.ID(required=True)
        employee_id = graphene.String(required=True)
        salary = graphene.Decimal(required=True)
        ssn = graphene.String(required=True)
        bank_account = graphene.String(required=True)

    employee = graphene.Field(EmployeeType)

    @require_role(['admin', 'hr_manager'])
    @validate_input({
        'employee_id': {'type': 'string', 'min_length': 3, 'max_length': 20},
        'salary': {'type': 'decimal', 'min_value': 0},
        'ssn': {'type': 'string', 'pattern': r'^\d{3}-\d{2}-\d{4}$'},
        'bank_account': {'type': 'string', 'min_length': 10}
    })
    @audit_data_modification(Employee, 'create')
    def mutate(self, info, **kwargs):
        """Crée un nouvel employé."""
        user = User.objects.get(pk=kwargs['user_id'])
        company = Company.objects.get(pk=kwargs['company_id'])

        employee = Employee.objects.create(
            user=user,
            company=company,
            employee_id=kwargs['employee_id'],
            salary=kwargs['salary'],
            ssn=kwargs['ssn'],
            bank_account=kwargs['bank_account']
        )

        return CreateEmployee(employee=employee)


class UpdateEmployeeSalary(graphene.Mutation):
    """Mutation pour mettre à jour le salaire d'un employé."""

    class Arguments:
        employee_id = graphene.ID(required=True)
        new_salary = graphene.Decimal(required=True)

    employee = graphene.Field(EmployeeType)

    @require_permission('employee.salary.update')
    @validate_input({
        'new_salary': {'type': 'decimal', 'min_value': 0, 'max_value': 1000000}
    })
    @audit_data_modification(Employee, 'update')
    def mutate(self, info, employee_id, new_salary):
        """Met à jour le salaire d'un employé."""
        employee = Employee.objects.get(pk=employee_id)
        employee.salary = new_salary
        employee.save()

        return UpdateEmployeeSalary(employee=employee)


class Mutation(graphene.ObjectType):
    """Mutations GraphQL avec sécurité."""

    create_employee = CreateEmployee.Field()
    update_employee_salary = UpdateEmployeeSalary.Field()


# ============================================================================
# SCHÉMA AVEC MIDDLEWARE DE SÉCURITÉ
# ============================================================================

def create_secure_schema():
    """Crée un schéma GraphQL avec toutes les sécurités activées."""

    # Configuration de la sécurité
    security_config = setup_security_system()

    # Middleware de sécurité
    security_middleware = create_security_middleware(security_config)

    # Création du schéma
    schema = graphene.Schema(
        query=Query,
        mutation=Mutation
    )

    return schema, security_middleware


# ============================================================================
# EXEMPLE D'UTILISATION DANS DJANGO SETTINGS
# ============================================================================

EXAMPLE_DJANGO_SETTINGS = """
# settings.py

# Configuration GraphQL avec sécurité
GRAPHENE = {
    'SCHEMA': 'myapp.schema.schema',
    'MIDDLEWARE': [
        'rail_django_graphql.security.create_security_middleware',
        'graphene_django.debug.DjangoDebugMiddleware',
    ],
}

# Configuration de sécurité GraphQL
GRAPHQL_MAX_QUERY_COMPLEXITY = 500
GRAPHQL_MAX_QUERY_DEPTH = 10
GRAPHQL_MAX_FIELD_COUNT = 50
GRAPHQL_ENABLE_INTROSPECTION = False
GRAPHQL_QUERY_TIMEOUT = 15
GRAPHQL_RATE_LIMIT_PER_MINUTE = 30

# Configuration des logs d'audit
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'audit': {
            'format': '{asctime} {levelname} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'audit_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/audit.log',
            'formatter': 'audit',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': 'logs/security.log',
            'formatter': 'audit',
        },
    },
    'loggers': {
        'audit': {
            'handlers': ['audit_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'security': {
            'handlers': ['security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# Configuration des permissions de champs
FIELD_PERMISSIONS = {
    'Employee.salary': ['hr_manager', 'finance_manager', 'admin'],
    'Employee.ssn': ['hr_manager', 'admin'],
    'Employee.bank_account': ['hr_manager', 'finance_manager', 'admin'],
    'Company.revenue': ['finance_manager', 'admin'],
    'Company.tax_id': ['finance_manager', 'admin'],
}
"""

# ============================================================================
# EXEMPLE D'UTILISATION DANS UNE VUE DJANGO
# ============================================================================

EXAMPLE_DJANGO_VIEW = """
# views.py

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from graphene_django.views import GraphQLView
from .schema import create_secure_schema
from rail_django_graphql.security import audit_logger, AuditEvent, AuditEventType, AuditSeverity

class SecureGraphQLView(GraphQLView):
    '''Vue GraphQL sécurisée avec audit.'''
    
    def __init__(self, **kwargs):
        schema, middleware = create_secure_schema()
        super().__init__(schema=schema, middleware=[middleware], **kwargs)
    
    def dispatch(self, request, *args, **kwargs):
        '''Dispatch avec audit des requêtes.'''
        
        # Auditer la requête entrante
        audit_event = AuditEvent(
            event_type=AuditEventType.DATA_ACCESS,
            severity=AuditSeverity.INFO,
            user_id=request.user.id if request.user.is_authenticated else None,
            username=request.user.username if request.user.is_authenticated else None,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            operation_type='graphql_request',
            details={
                'method': request.method,
                'path': request.path,
                'content_type': request.content_type
            }
        )
        
        audit_logger.log_event(audit_event)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_client_ip(self, request):
        '''Récupère l'IP du client.'''
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
"""

if __name__ == "__main__":
    # Exemple d'initialisation du système de sécurité
    print("Configuration du système de sécurité Django GraphQL...")

    # Configurer le système
    security_config = setup_security_system()

    # Créer le schéma sécurisé
    schema, middleware = create_secure_schema()

    print("✅ Système de sécurité configuré avec succès!")
    print(f"✅ Configuration: {security_config}")
    print("✅ Schéma GraphQL créé avec middleware de sécurité")
    print("✅ Rôles RBAC configurés")
    print("✅ Permissions de champs configurées")
    print("✅ Audit logging activé")

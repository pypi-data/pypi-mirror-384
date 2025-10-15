"""
Advanced Usage Example for Rail Django GraphQL

This example demonstrates advanced features including:
- Custom type generation with complex field mappings
- Advanced permission systems
- Query optimization techniques
- Custom middleware and extensions
- Performance monitoring
"""

from datetime import timedelta
from typing import Any, Dict, List, Optional

import graphene
from django.contrib.auth.models import User
from django.utils import timezone

from rail_django_graphql import MutationGenerator, QueryGenerator, SchemaBuilder, TypeGenerator
from rail_django_graphql.extensions import BaseExtension
from rail_django_graphql.middleware import BaseMiddleware
from rail_django_graphql.optimization import QueryOptimizer
from rail_django_graphql.permissions import BasePermission

# Advanced Django Settings Configuration
ADVANCED_SETTINGS = """
# settings.py - Advanced Configuration
RAIL_DJANGO_GRAPHQL = {
    # Schema Generation
    'schema_settings': {
        'auto_generate_schema': True,
        'auto_discover_models': True,
        'schema_output_path': 'schema.json',
        'enable_introspection': False,  # Disabled in production
    },
    
    # Security
    'SECURITY': {
        'max_query_depth': 15,
        'max_query_complexity': 2000,
        'enable_query_whitelist': True,
        'allowed_query_hashes': [
            'hash1', 'hash2'  # Pre-approved query hashes
        ],
    },
    
    # Performance
    'PERFORMANCE': {
        'enable_query_optimization': True,
        'enable_dataloader': True,
        'cache_timeout': 600,
        'enable_query_caching': True,
        'cache_key_prefix': 'graphql:',
        'enable_performance_monitoring': True,
    },
    
    # Development & Debugging
    'DEVELOPMENT': {
        'enable_debugging': False,  # Disabled in production
        'log_queries': True,
        'log_slow_queries': True,
        'slow_query_threshold': 0.5,  # seconds
    },
    
    # Permissions
    'DEFAULT_PERMISSION_CLASSES': [
        'myapp.permissions.IsAuthenticatedAndActive',
        'myapp.permissions.RateLimitPermission',
    ],
    'ENABLE_FIELD_PERMISSIONS': True,
    'PERMISSION_CACHE_TIMEOUT': 300,
    
    # Extensions
    'ENABLE_EXTENSIONS': True,
    'EXTENSION_CLASSES': [
        'rail_django_graphql.extensions.QueryComplexityExtension',
        'rail_django_graphql.extensions.PerformanceExtension',
        'rail_django_graphql.extensions.SecurityExtension',
        'myapp.extensions.CustomMetricsExtension',
    ],
    
    # Custom Scalars
    'CUSTOM_SCALARS': {
        'DateTime': 'graphene.DateTime',
        'JSON': 'graphene_django.extras.DjangoJSONType',
        'Upload': 'graphene_file_upload.scalars.Upload',
    },
}

# Middleware Configuration
GRAPHENE = {
    'SCHEMA': 'myproject.schema.schema',
    'MIDDLEWARE': [
        'rail_django_graphql.middleware.AuthenticationMiddleware',
        'rail_django_graphql.middleware.PermissionMiddleware',
        'rail_django_graphql.middleware.QueryOptimizationMiddleware',
        'rail_django_graphql.middleware.CachingMiddleware',
        'rail_django_graphql.middleware.RateLimitMiddleware',
        'rail_django_graphql.middleware.SecurityMiddleware',
        'rail_django_graphql.middleware.PerformanceMiddleware',
        'rail_django_graphql.middleware.DebuggingMiddleware',
        'myapp.middleware.CustomLoggingMiddleware',
    ],
}
"""


# Advanced Permission Classes
class IsOwnerOrReadOnly(BasePermission):
    """
    Permission that allows read access to everyone,
    but write access only to the owner of the object.
    """

    def has_permission(self, info, obj=None):
        # Read permissions for any request
        if info.context.method in ["GET", "HEAD", "OPTIONS"]:
            return True

        # Write permissions only for authenticated users
        if not info.context.user.is_authenticated:
            return False

        # For object-level permissions
        if obj:
            return self.has_object_permission(info, obj)

        return True

    def has_object_permission(self, info, obj):
        # Check if user is the owner
        if hasattr(obj, "auteur_article"):
            return obj.auteur_article == info.context.user
        elif hasattr(obj, "owner"):
            return obj.owner == info.context.user
        elif hasattr(obj, "user"):
            return obj.user == info.context.user

        return False


class RoleBasedPermission(BasePermission):
    """
    Permission based on user roles and groups.
    """

    def __init__(
        self, required_roles: List[str] = None, required_groups: List[str] = None
    ):
        self.required_roles = required_roles or []
        self.required_groups = required_groups or []

    def has_permission(self, info, obj=None):
        user = info.context.user

        if not user.is_authenticated:
            return False

        # Check user roles (assuming a role field or method)
        if self.required_roles:
            user_roles = getattr(user, "roles", []) or []
            if not any(role in user_roles for role in self.required_roles):
                return False

        # Check user groups
        if self.required_groups:
            user_groups = user.groups.values_list("name", flat=True)
            if not any(group in user_groups for group in self.required_groups):
                return False

        return True


class RateLimitPermission(BasePermission):
    """
    Rate limiting permission using Redis or cache backend.
    """

    def __init__(self, max_requests: int = 100, time_window: int = 3600):
        self.max_requests = max_requests
        self.time_window = time_window

    def has_permission(self, info, obj=None):
        from django.core.cache import cache

        user = info.context.user
        if not user.is_authenticated:
            return True  # Apply different limits for anonymous users

        cache_key = f"rate_limit:{user.id}:{info.field_name}"
        current_requests = cache.get(cache_key, 0)

        if current_requests >= self.max_requests:
            return False

        # Increment counter
        cache.set(cache_key, current_requests + 1, self.time_window)
        return True


# Advanced Type Generation
def create_advanced_user_type():
    """
    Create an advanced User type with custom fields and resolvers.
    """

    UserType = TypeGenerator.from_model(
        User,
        fields=[
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "date_joined",
            "last_login",
            "is_active",
        ],
        exclude_fields=["password", "user_permissions"],
        custom_fields={
            "full_name": graphene.String(description="Nom complet de l'utilisateur"),
            "initials": graphene.String(description="Initiales de l'utilisateur"),
            "post_count": graphene.Int(description="Nombre d'articles publiés"),
            "comment_count": graphene.Int(description="Nombre de commentaires"),
            "is_recent_user": graphene.Boolean(
                description="Utilisateur récent (moins de 30 jours)"
            ),
            "avatar_url": graphene.String(description="URL de l'avatar"),
            "last_activity": graphene.DateTime(description="Dernière activité"),
            "reputation_score": graphene.Int(description="Score de réputation"),
        },
        custom_resolvers={
            "full_name": lambda user,
            info: f"{user.first_name} {user.last_name}".strip(),
            "initials": lambda user,
            info: f"{user.first_name[:1]}{user.last_name[:1]}".upper(),
            "post_count": lambda user, info: user.post_set.filter(
                est_publie=True
            ).count(),
            "comment_count": lambda user, info: user.comment_set.count(),
            "is_recent_user": lambda user, info: (
                timezone.now() - user.date_joined
            ).days
            < 30,
            "avatar_url": lambda user,
            info: f"https://api.dicebear.com/7.x/initials/svg?seed={user.username}",
            "last_activity": lambda user, info: getattr(
                user, "last_activity", user.last_login
            ),
            "reputation_score": lambda user, info: calculate_reputation_score(user),
        },
        permission_classes=[IsOwnerOrReadOnly],
        description="Type utilisateur avancé avec champs personnalisés",
    )

    return UserType


def calculate_reputation_score(user):
    """
    Calculate user reputation based on posts, comments, and other factors.
    """
    score = 0

    # Points for published posts
    score += user.post_set.filter(est_publie=True).count() * 10

    # Points for comments
    score += user.comment_set.count() * 2

    # Bonus for recent activity
    if user.last_login and (timezone.now() - user.last_login).days < 7:
        score += 5

    # Penalty for inactive users
    if user.last_login and (timezone.now() - user.last_login).days > 90:
        score -= 10

    return max(0, score)


# Advanced Query Generation with Optimization
class AdvancedQuery(graphene.ObjectType):
    """
    Advanced GraphQL queries with optimization and custom logic.
    """

    # Optimized queries with DataLoader
    users = QueryGenerator.list_field(
        User,
        permission_classes=[RoleBasedPermission(["admin", "moderator"])],
        filterset_fields={
            "username": ["exact", "icontains"],
            "email": ["exact", "icontains"],
            "is_active": ["exact"],
            "date_joined": ["gte", "lte"],
        },
        ordering_fields=["username", "date_joined", "last_login"],
        pagination_class="relay",  # Use Relay-style pagination
        max_limit=50,
    )

    user = QueryGenerator.detail_field(
        User,
        permission_classes=[IsOwnerOrReadOnly],
    )

    # Custom complex queries
    trending_posts = graphene.List(
        "PostType",
        time_range=graphene.String(default_value="week"),
        limit=graphene.Int(default_value=10),
        description="Articles tendance basés sur les vues et commentaires",
    )

    user_statistics = graphene.Field(
        "UserStatisticsType",
        user_id=graphene.ID(required=True),
        description="Statistiques détaillées d'un utilisateur",
    )

    search_content = graphene.List(
        "SearchResultType",
        query=graphene.String(required=True),
        content_types=graphene.List(graphene.String),
        limit=graphene.Int(default_value=20),
        description="Recherche dans le contenu avec filtres",
    )

    @QueryOptimizer.optimize(["auteur_article", "categorie_article", "comments"])
    def resolve_trending_posts(self, info, time_range="week", limit=10):
        """
        Resolve trending posts with query optimization.
        """
        from datetime import timedelta

        from django.db.models import Count, Q

        # Calculate time range
        time_ranges = {
            "day": timedelta(days=1),
            "week": timedelta(weeks=1),
            "month": timedelta(days=30),
            "year": timedelta(days=365),
        }

        since = timezone.now() - time_ranges.get(time_range, timedelta(weeks=1))

        # Complex query with annotations
        return (
            Post.objects.filter(est_publie=True, date_publication__gte=since)
            .annotate(
                comment_count=Count("comments"),
                recent_comments=Count(
                    "comments", filter=Q(comments__date_commentaire__gte=since)
                ),
            )
            .order_by("-recent_comments", "-comment_count", "-date_publication")[:limit]
        )

    def resolve_user_statistics(self, info, user_id):
        """
        Resolve detailed user statistics.
        """
        try:
            user = User.objects.get(id=user_id)

            # Check permissions
            if not IsOwnerOrReadOnly().has_object_permission(info, user):
                raise PermissionError("Accès non autorisé aux statistiques")

            return {
                "user": user,
                "total_posts": user.post_set.count(),
                "published_posts": user.post_set.filter(est_publie=True).count(),
                "total_comments": user.comment_set.count(),
                "posts_this_month": user.post_set.filter(
                    date_publication__gte=timezone.now() - timedelta(days=30)
                ).count(),
                "average_comments_per_post": user.post_set.aggregate(
                    avg_comments=models.Avg("comments__count")
                )["avg_comments"]
                or 0,
                "most_popular_post": user.post_set.annotate(
                    comment_count=Count("comments")
                )
                .order_by("-comment_count")
                .first(),
                "recent_activity": user.comment_set.order_by("-date_commentaire")[:5],
            }
        except User.DoesNotExist:
            return None

    def resolve_search_content(self, info, query, content_types=None, limit=20):
        """
        Advanced content search with full-text search capabilities.
        """
        from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector

        results = []

        # Search in posts
        if not content_types or "posts" in content_types:
            post_results = (
                Post.objects.annotate(
                    search=SearchVector("titre_article", "contenu_article"),
                    rank=SearchRank(
                        SearchVector("titre_article", "contenu_article"),
                        SearchQuery(query),
                    ),
                )
                .filter(search=SearchQuery(query), est_publie=True)
                .order_by("-rank")[: limit // 2]
            )

            results.extend(
                [
                    {"type": "post", "object": post, "rank": post.rank}
                    for post in post_results
                ]
            )

        # Search in comments
        if not content_types or "comments" in content_types:
            comment_results = (
                Comment.objects.annotate(
                    search=SearchVector("contenu_commentaire"),
                    rank=SearchRank(
                        SearchVector("contenu_commentaire"), SearchQuery(query)
                    ),
                )
                .filter(search=SearchQuery(query))
                .order_by("-rank")[: limit // 2]
            )

            results.extend(
                [
                    {"type": "comment", "object": comment, "rank": comment.rank}
                    for comment in comment_results
                ]
            )

        # Sort by relevance
        results.sort(key=lambda x: x["rank"], reverse=True)

        return results[:limit]


# Advanced Mutations with Validation
class AdvancedMutation(graphene.ObjectType):
    """
    Advanced mutations with complex validation and business logic.
    """

    # Bulk operations
    bulk_create_posts = graphene.Field(
        "BulkCreatePostsPayload",
        input=graphene.List("CreatePostInput", required=True),
        description="Création en lot d'articles",
    )

    bulk_update_posts = graphene.Field(
        "BulkUpdatePostsPayload",
        updates=graphene.List("BulkUpdatePostInput", required=True),
        description="Mise à jour en lot d'articles",
    )

    # Complex business logic mutations
    publish_post = graphene.Field(
        "PublishPostPayload",
        post_id=graphene.ID(required=True),
        scheduled_date=graphene.DateTime(),
        description="Publication d'un article avec planification optionnelle",
    )

    transfer_post_ownership = graphene.Field(
        "TransferOwnershipPayload",
        post_id=graphene.ID(required=True),
        new_owner_id=graphene.ID(required=True),
        reason=graphene.String(),
        description="Transfert de propriété d'un article",
    )

    def resolve_bulk_create_posts(self, info, input):
        """
        Create multiple posts with validation and transaction handling.
        """
        from django.db import transaction

        user = info.context.user
        if not user.is_authenticated:
            return {
                "success": False,
                "errors": ["Authentification requise"],
                "posts": [],
            }

        created_posts = []
        errors = []

        try:
            with transaction.atomic():
                for i, post_data in enumerate(input):
                    try:
                        # Validate each post
                        if not post_data.get("titre_article"):
                            errors.append(f"Post {i+1}: Titre requis")
                            continue

                        if len(post_data.get("titre_article", "")) > 200:
                            errors.append(f"Post {i+1}: Titre trop long")
                            continue

                        # Create post
                        post = Post.objects.create(
                            titre_article=post_data["titre_article"],
                            contenu_article=post_data.get("contenu_article", ""),
                            auteur_article=user,
                            categorie_article_id=post_data.get("categorie_id"),
                            est_publie=post_data.get("est_publie", False),
                        )
                        created_posts.append(post)

                    except Exception as e:
                        errors.append(f"Post {i+1}: {str(e)}")

                if errors:
                    transaction.set_rollback(True)
                    return {"success": False, "errors": errors, "posts": []}

        except Exception as e:
            return {
                "success": False,
                "errors": [f"Erreur de transaction: {str(e)}"],
                "posts": [],
            }

        return {"success": True, "errors": [], "posts": created_posts}

    def resolve_publish_post(self, info, post_id, scheduled_date=None):
        """
        Publish a post with optional scheduling.
        """
        from django.utils import timezone

        user = info.context.user

        try:
            post = Post.objects.get(id=post_id)

            # Check permissions
            if post.auteur_article != user and not user.is_staff:
                return {
                    "success": False,
                    "errors": ["Permission refusée"],
                    "post": None,
                }

            # Validate scheduling
            if scheduled_date and scheduled_date <= timezone.now():
                return {
                    "success": False,
                    "errors": ["La date de planification doit être dans le futur"],
                    "post": None,
                }

            # Update post
            if scheduled_date:
                # Schedule for later (would need a task queue like Celery)
                post.scheduled_publication = scheduled_date
                post.save()

                # Here you would typically create a scheduled task
                # schedule_post_publication.apply_async(
                #     args=[post.id],
                #     eta=scheduled_date
                # )

                return {
                    "success": True,
                    "errors": [],
                    "post": post,
                    "message": f"Article planifié pour publication le {scheduled_date}",
                }
            else:
                # Publish immediately
                post.est_publie = True
                post.date_publication = timezone.now()
                post.save()

                return {
                    "success": True,
                    "errors": [],
                    "post": post,
                    "message": "Article publié avec succès",
                }

        except Post.DoesNotExist:
            return {"success": False, "errors": ["Article non trouvé"], "post": None}


# Custom Middleware
class CustomLoggingMiddleware(BaseMiddleware):
    """
    Custom middleware for detailed logging and monitoring.
    """

    def resolve(self, next, root, info, **args):
        import logging
        import time

        logger = logging.getLogger("graphql.queries")

        # Log query start
        start_time = time.time()
        query_name = info.field_name
        user = getattr(info.context, "user", None)

        logger.info(f"GraphQL Query Started: {query_name} by {user}")

        try:
            # Execute query
            result = next(root, info, **args)

            # Log successful completion
            execution_time = time.time() - start_time
            logger.info(
                f"GraphQL Query Completed: {query_name} in {execution_time:.3f}s"
            )

            # Log slow queries
            if execution_time > 1.0:
                logger.warning(
                    f"Slow GraphQL Query: {query_name} took {execution_time:.3f}s"
                )

            return result

        except Exception as e:
            # Log errors
            execution_time = time.time() - start_time
            logger.error(
                f"GraphQL Query Failed: {query_name} after {execution_time:.3f}s - {str(e)}"
            )
            raise


# Custom Extension
class CustomMetricsExtension(BaseExtension):
    """
    Custom extension for collecting detailed metrics.
    """

    def __init__(self):
        self.query_count = 0
        self.total_execution_time = 0
        self.error_count = 0

    def request_started(self, request, query_string, variables, operation_name):
        """Called when a GraphQL request starts."""
        self.start_time = time.time()
        self.query_count += 1

    def request_finished(self, request, response):
        """Called when a GraphQL request finishes."""
        execution_time = time.time() - self.start_time
        self.total_execution_time += execution_time

        # Send metrics to monitoring system
        self.send_metrics(
            {
                "query_count": self.query_count,
                "execution_time": execution_time,
                "average_execution_time": self.total_execution_time / self.query_count,
                "error_count": self.error_count,
            }
        )

    def send_metrics(self, metrics):
        """Send metrics to external monitoring system."""
        # Implementation would depend on your monitoring system
        # e.g., Prometheus, StatsD, CloudWatch, etc.
        pass


# Schema Builder with Advanced Configuration
def create_advanced_schema():
    """
    Create an advanced GraphQL schema with all features enabled.
    """

    schema = SchemaBuilder.build(
        query=AdvancedQuery,
        mutation=AdvancedMutation,
        auto_discover=True,
        enable_subscriptions=True,  # Enable real-time subscriptions
        custom_scalars={
            "DateTime": "graphene.DateTime",
            "JSON": "graphene_django.extras.DjangoJSONType",
            "Upload": "graphene_file_upload.scalars.Upload",
        },
        middleware=[
            CustomLoggingMiddleware(),
        ],
        extensions=[
            CustomMetricsExtension(),
        ],
        introspection=False,  # Disabled in production
        max_depth=15,
        max_complexity=2000,
    )

    return schema


if __name__ == "__main__":
    print("Rail Django GraphQL Advanced Usage Example")
    print("=" * 50)
    print("\nThis example demonstrates:")
    print("- Advanced permission systems")
    print("- Complex type generation with custom fields")
    print("- Query optimization techniques")
    print("- Custom middleware and extensions")
    print("- Bulk operations and complex mutations")
    print("- Performance monitoring and metrics")
    print("- Full-text search capabilities")
    print("- Rate limiting and security features")
    print("\nSee the code above for detailed implementations.")

"""
Basic Usage Example for Rail Django GraphQL

This example demonstrates how to install and use rail-django-graphql
to create a GraphQL API from Django models.
"""

# Installation:
# pip install rail-django-graphql
# or from GitHub:
# pip install git+https://github.com/raillogistic/rail-django-graphql.git

# 1. Django Settings Configuration
from rail_django_graphql import MutationGenerator, QueryGenerator, SchemaBuilder, TypeGenerator
import graphene
DJANGO_SETTINGS_EXAMPLE = """
# settings.py
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # GraphQL dependencies
    'graphene_django',
    'django_filters',
    'corsheaders',
    
    # Rail Django GraphQL
    'rail_django_graphql',
    
    # Your apps
    'blog',  # Example app
]

# GraphQL Configuration
GRAPHENE = {
    'SCHEMA': 'myproject.schema.schema',
    'MIDDLEWARE': [
        'rail_django_graphql.middleware.QueryOptimizationMiddleware',
        'rail_django_graphql.middleware.PermissionMiddleware',
        'rail_django_graphql.middleware.DebuggingMiddleware',
    ],
}

# Rail Django GraphQL Settings
RAIL_DJANGO_GRAPHQL = {
    'schema_settings': {
        'auto_generate_schema': True,
        'enable_introspection': True,
    },
    'SECURITY': {
        'max_query_depth': 10,
    },
    'PERFORMANCE': {
        'enable_query_optimization': True,
    },
    'DEVELOPMENT': {
        'enable_debugging': True,
    },
}
"""

# 2. Example Django Models
"""
# blog/models.py
from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    nom_categorie = models.CharField(max_length=100, verbose_name="Nom de la catégorie")
    description_categorie = models.TextField(verbose_name="Description de la catégorie")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    
    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"

class Post(models.Model):
    titre_article = models.CharField(max_length=200, verbose_name="Titre de l'article")
    contenu_article = models.TextField(verbose_name="Contenu de l'article")
    auteur_article = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Auteur")
    categorie_article = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Catégorie")
    date_publication = models.DateTimeField(auto_now_add=True, verbose_name="Date de publication")
    est_publie = models.BooleanField(default=False, verbose_name="Est publié")
    
    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"

class Comment(models.Model):
    contenu_commentaire = models.TextField(verbose_name="Contenu du commentaire")
    auteur_commentaire = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Auteur")
    article_commentaire = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', verbose_name="Article")
    date_commentaire = models.DateTimeField(auto_now_add=True, verbose_name="Date du commentaire")
    
    class Meta:
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"
"""

# 3. GraphQL Schema Creation


# Assuming we have the models imported
# from blog.models import Category, Post, Comment
# from django.contrib.auth.models import User


def create_basic_schema():
    """
    Create a basic GraphQL schema using rail-django-graphql
    """

    # Generate GraphQL types automatically from Django models
    # UserType = TypeGenerator.from_model(User)
    # CategoryType = TypeGenerator.from_model(Category)
    # PostType = TypeGenerator.from_model(Post)
    # CommentType = TypeGenerator.from_model(Comment)

    class Query(graphene.ObjectType):
        """
        GraphQL Query root with auto-generated queries
        """

        # Auto-generated list and detail queries
        # users = QueryGenerator.list_field(User)
        # user = QueryGenerator.detail_field(User)
        # categories = QueryGenerator.list_field(Category)
        # category = QueryGenerator.detail_field(Category)
        # posts = QueryGenerator.list_field(Post)
        # post = QueryGenerator.detail_field(Post)
        # comments = QueryGenerator.list_field(Comment)
        # comment = QueryGenerator.detail_field(Comment)

        # Custom queries
        # published_posts = graphene.List(PostType)
        # my_posts = graphene.List(PostType)

        # def resolve_published_posts(self, info):
        #     return Post.objects.filter(est_publie=True)

        # def resolve_my_posts(self, info):
        #     if info.context.user.is_authenticated:
        #         return Post.objects.filter(auteur_article=info.context.user)
        #     return Post.objects.none()
        pass

    class Mutation(graphene.ObjectType):
        """
        GraphQL Mutation root with auto-generated mutations
        """

        # Auto-generated CRUD mutations
        # create_category = MutationGenerator.create_mutation(Category)
        # update_category = MutationGenerator.update_mutation(Category)
        # delete_category = MutationGenerator.delete_mutation(Category)

        # create_post = MutationGenerator.create_mutation(Post)
        # update_post = MutationGenerator.update_mutation(Post)
        # delete_post = MutationGenerator.delete_mutation(Post)

        # create_comment = MutationGenerator.create_mutation(Comment)
        # update_comment = MutationGenerator.update_mutation(Comment)
        # delete_comment = MutationGenerator.delete_mutation(Comment)
        pass

    # Build the complete schema
    schema = SchemaBuilder.build(
        query=Query,
        mutation=Mutation,
        auto_discover=True,  # Automatically discover and include all models
    )

    return schema


# 4. URL Configuration
URL_CONFIGURATION = """
# myproject/urls.py
from django.contrib import admin
from django.urls import path, include
from rail_django_graphql.views import GraphQLView
from rail_django_graphql.health_urls import health_urlpatterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('graphql/', GraphQLView.as_view(graphiql=True)),
    path('health/', include(health_urlpatterns)),
]
"""

# 5. Example GraphQL Queries
EXAMPLE_QUERIES = """
# Query all published posts with their categories and authors
query GetPublishedPosts {
  publishedPosts {
    id
    titreArticle
    contenuArticle
    datePublication
    auteurArticle {
      id
      username
      firstName
      lastName
    }
    categorieArticle {
      id
      nomCategorie
      descriptionCategorie
    }
    comments {
      id
      contenuCommentaire
      dateCommentaire
      auteurCommentaire {
        username
      }
    }
  }
}

# Query specific post by ID
query GetPost($id: ID!) {
  post(id: $id) {
    id
    titreArticle
    contenuArticle
    datePublication
    estPublie
    auteurArticle {
      username
    }
    categorieArticle {
      nomCategorie
    }
  }
}

# Query all categories with post counts
query GetCategories {
  categories {
    id
    nomCategorie
    descriptionCategorie
    dateCreation
    postSet {
      id
      titreArticle
    }
  }
}

# Create a new post
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    success
    errors
    post {
      id
      titreArticle
      contenuArticle
      datePublication
    }
  }
}

# Update an existing post
mutation UpdatePost($id: ID!, $input: UpdatePostInput!) {
  updatePost(id: $id, input: $input) {
    success
    errors
    post {
      id
      titreArticle
      contenuArticle
      estPublie
    }
  }
}

# Delete a post
mutation DeletePost($id: ID!) {
  deletePost(id: $id) {
    success
    errors
  }
}
"""

# 6. Advanced Usage with Custom Fields and Permissions
ADVANCED_USAGE = """
from rail_django_graphql import TypeGenerator
from rail_django_graphql.permissions import BasePermission

# Custom permission class
class IsOwnerOrReadOnly(BasePermission):
    def has_permission(self, info, obj=None):
        if info.context.method == 'GET':
            return True
        return obj and obj.auteur_article == info.context.user

# Advanced type generation with custom fields
PostType = TypeGenerator.from_model(
    Post,
    fields=['id', 'titre_article', 'contenu_article', 'date_publication'],
    exclude_fields=['est_publie'],  # Hide from non-owners
    custom_fields={
        'comment_count': graphene.Int(),
        'is_recent': graphene.Boolean(),
        'author_name': graphene.String(),
    },
    custom_resolvers={
        'comment_count': lambda post, info: post.comments.count(),
        'is_recent': lambda post, info: (timezone.now() - post.date_publication).days < 7,
        'author_name': lambda post, info: f"{post.auteur_article.first_name} {post.auteur_article.last_name}",
    }
)

# Apply permissions to queries
posts = QueryGenerator.list_field(
    Post,
    permission_classes=[IsOwnerOrReadOnly],
    filterset_fields=['categorie_article', 'auteur_article', 'est_publie'],
    ordering_fields=['date_publication', 'titre_article'],
)
"""

if __name__ == "__main__":
    print("Rail Django GraphQL Basic Usage Example")
    print("=" * 50)
    print("\n1. Install the library:")
    print("   pip install rail-django-graphql")
    print("\n2. Configure Django settings (see DJANGO_SETTINGS_EXAMPLE)")
    print("\n3. Create your models with French verbose names")
    print("\n4. Generate GraphQL schema (see create_basic_schema function)")
    print("\n5. Configure URLs (see URL_CONFIGURATION)")
    print("\n6. Run server and visit http://localhost:8000/graphql/")
    print("\n7. Try example queries (see EXAMPLE_QUERIES)")
    print("\nFor advanced usage, see ADVANCED_USAGE section")

# django-directory-api

Reusable Django REST API framework with auto-discovery and bearer token authentication.

## Features

- 🔐 **Bearer Token Authentication** - Secure API access with per-user tokens
- 🔌 **Auto-Discovery** - Automatically discovers and registers API routers from `api.py` files
- 📚 **Django Shinobi** - Built on Django Shinobi (Django Ninja fork) for type-safe APIs
- 🤖 **LLM-Optimized** - Rich OpenAPI documentation designed for AI agent consumption
- 🎯 **Zero Config** - Just create an `api.py` file and start building

## Installation

```bash
pip install django-directory-api
```

## Quick Start

### 1. Add to INSTALLED_APPS

```python
# settings.py
INSTALLED_APPS = [
    # ...
    "django_directory_api",  # Must come before apps that define API endpoints
    # ...
]
```

### 2. Include API URLs

```python
# urls.py
from django_directory_api import api

urlpatterns = [
    path("api/", api.urls),
    # ...
]
```

### 3. Create API Endpoints

Create an `api.py` file in any Django app:

```python
# myapp/api.py
from ninja import Router
from .models import MyModel

router = Router(tags=["My App"])

@router.get("/items/")
def list_items(request):
    return {"items": list(MyModel.objects.values())}
```

That's it! The router is automatically discovered and registered.

## Authentication

### Creating API Tokens

1. Log into Django admin
2. Navigate to "API Tokens"
3. Click "Add API Token"
4. Give it a name (e.g., "Production Bot")
5. Copy the token value (shown only once)

### Using Tokens

```bash
curl -H "Authorization: Bearer <your-token>" \
     https://example.com/api/items/
```

```python
import requests

headers = {"Authorization": "Bearer <your-token>"}
response = requests.get("https://example.com/api/items/", headers=headers)
```

## Auto-Discovery

The package automatically discovers `api.py` files in all installed Django apps:

- ✅ Looks for `router` attribute (single router)
- ✅ Looks for `routers` attribute (list of routers)
- ✅ Skips apps without `api.py` files
- ✅ No explicit registration required

### Example with Multiple Routers

```python
# myapp/api.py
from ninja import Router

public_router = Router(tags=["Public"])
admin_router = Router(tags=["Admin"])

@public_router.get("/public/")
def public_endpoint(request):
    return {"message": "Hello world"}

@admin_router.get("/admin/")
def admin_endpoint(request):
    return {"message": "Admin only"}

# Export multiple routers
routers = [public_router, admin_router]
```

## Advanced Patterns

### Production-Ready CRUD API

Here's a complete example showing best practices for a production API:

```python
# myapp/api.py
from django.shortcuts import get_object_or_404
from ninja import Router
from django_directory_api.schemas import PaginatedResponse

from .models import Article
from .schemas import ArticleListSchema, ArticleDetailSchema, ArticleCreateSchema, ArticleUpdateSchema

router = Router(tags=["Articles"])

@router.get("/articles/", response=PaginatedResponse[ArticleListSchema])
def list_articles(request, page: int = 1, page_size: int = 50, is_published: bool | None = None):
    """List articles with pagination and filtering."""
    queryset = Article.objects.all()

    if is_published is not None:
        queryset = queryset.filter(is_published=is_published)

    # Enforce max page size
    page_size = min(page_size, 100)

    # Calculate pagination
    total = queryset.count()
    offset = (page - 1) * page_size
    items = list(queryset[offset:offset + page_size])

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }

@router.get("/articles/{slug}/", response=ArticleDetailSchema)
def get_article(request, slug: str):
    """Get detailed information for a specific article."""
    return get_object_or_404(Article, slug=slug)

@router.post("/articles/", response={201: ArticleDetailSchema})
def create_article(request, data: ArticleCreateSchema):
    """Create a new article."""
    article = Article.objects.create(**data.dict(exclude_unset=True))
    return 201, article

@router.patch("/articles/{slug}/", response=ArticleDetailSchema)
def update_article(request, slug: str, data: ArticleUpdateSchema):
    """Update an article (partial update)."""
    article = get_object_or_404(Article, slug=slug)

    update_data = data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(article, field, value)
    article.save()

    return article

@router.delete("/articles/{slug}/", response={204: None})
def delete_article(request, slug: str):
    """Delete an article permanently."""
    article = get_object_or_404(Article, slug=slug)
    article.delete()
    return 204, None
```

### Nested Resources

Handle parent-child relationships elegantly:

```python
# myapp/api.py
from ninja import Router

router = Router(tags=["Articles"])

@router.get("/articles/{article_slug}/comments/", response=list[CommentSchema])
def list_comments(request, article_slug: str):
    """Get all comments for an article."""
    article = get_object_or_404(Article, slug=article_slug)
    return list(article.comments.all().order_by("-created_at"))

@router.post("/articles/{article_slug}/comments/", response={201: CommentSchema})
def create_comment(request, article_slug: str, data: CommentCreateSchema):
    """Add a comment to an article."""
    article = get_object_or_404(Article, slug=article_slug)
    comment = Comment.objects.create(article=article, **data.dict(exclude_unset=True))
    return 201, comment
```

## Schema Best Practices

### Organizing Schemas

Create a separate `schemas.py` file in your app:

```python
# myapp/schemas.py
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class ArticleListSchema(BaseModel):
    """Lightweight schema for list views."""
    model_config = ConfigDict(from_attributes=True)

    slug: str
    title: str
    excerpt: str
    is_published: bool
    created_at: datetime

class ArticleDetailSchema(BaseModel):
    """Complete schema with all fields."""
    model_config = ConfigDict(from_attributes=True)

    slug: str
    title: str
    content: str
    excerpt: str
    is_published: bool
    author_name: str
    created_at: datetime
    updated_at: datetime

    # Computed properties from Django model
    word_count: int
    reading_time: int

class ArticleCreateSchema(BaseModel):
    """Schema for creating articles."""
    title: str
    content: str
    excerpt: str | None = None
    is_published: bool = False

class ArticleUpdateSchema(BaseModel):
    """Schema for partial updates (all fields optional)."""
    title: str | None = None
    content: str | None = None
    excerpt: str | None = None
    is_published: bool | None = None
```

### Using Computed Properties

Django model methods work automatically with `from_attributes=True`:

```python
# myapp/models.py
class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()

    @property
    def word_count(self):
        """Computed property available in API responses."""
        return len(self.content.split())

    @property
    def reading_time(self):
        """Estimated reading time in minutes."""
        return max(1, self.word_count // 200)

# myapp/schemas.py
class ArticleDetailSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str
    content: str
    word_count: int  # ← Automatically calls model property
    reading_time: int  # ← Automatically calls model property
```

## Common Schemas Reference

The package provides reusable schemas in `django_directory_api.schemas`:

### PaginatedResponse[T]

Generic pagination wrapper for list endpoints:

```python
from django_directory_api.schemas import PaginatedResponse
from .schemas import ArticleListSchema

@router.get("/articles/", response=PaginatedResponse[ArticleListSchema])
def list_articles(request, page: int = 1, page_size: int = 50):
    # ... pagination logic ...
    return {
        "items": items,        # List of items
        "total": total,        # Total count
        "page": page,          # Current page
        "page_size": page_size,  # Items per page
        "pages": total_pages,  # Total pages
    }
```

### Enums

Standard enums for common patterns:

```python
from django_directory_api.schemas import (
    BackfillStatusEnum,      # pending, done, error, no_backfill
    PublishStatusEnum,       # draft, published, archived
    ExperienceLevelEnum,     # beginner, intermediate, advanced, expert
)

class ArticleSchema(BaseModel):
    status: PublishStatusEnum
    level: ExperienceLevelEnum
```

### Response Schemas

```python
from django_directory_api.schemas import MessageResponse, ErrorResponse

@router.post("/articles/{slug}/publish/", response=MessageResponse)
def publish_article(request, slug: str):
    article = get_object_or_404(Article, slug=slug)
    article.is_published = True
    article.save()
    return {"message": f"Article '{article.title}' published successfully"}
```

## Real-World Examples

Complete implementations you can reference:

### Pages API (django-directory-cms)
Full-featured CMS pages API with SEO fields:
- **File**: `django-directory-cms/src/django_directory_cms/api.py`
- **Schemas**: `django-directory-cms/src/django_directory_cms/schemas.py`
- **Features**: CRUD operations, SEO management, auto-slug generation
- **GitHub**: [django-directory-cms](https://github.com/heysamtexas/django-directory-cms)

### Categories API
Complex hierarchical data with nested subpages:
- **File**: `categories/api.py` in directory-builder
- **Schemas**: `categories/schemas.py`
- **Features**: Parent-child relationships, pagination, filtering, nested resources
- **Pattern**: `/categories/{slug}/subpages/` for nested resources

### Entities API
Many-to-many relationships and linking:
- **File**: `entities/api.py` in directory-builder
- **Schemas**: `entities/schemas.py`
- **Features**: Link management, relationship endpoints, bulk operations

## Testing

### Basic Test Pattern

```python
# myapp/tests/test_api.py
from django.test import TestCase
from django_directory_api.models import APIToken
from django.contrib.auth import get_user_model

User = get_user_model()

class ArticleAPITest(TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(email="test@example.com", password="test123")
        self.token = APIToken.objects.create(user=self.user, name="Test Token")
        self.auth_headers = {"HTTP_AUTHORIZATION": f"Bearer {self.token.key}"}

    def test_list_articles(self):
        """Test article listing endpoint."""
        response = self.client.get("/api/articles/", **self.auth_headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("items", data)
        self.assertIn("total", data)

    def test_create_article(self):
        """Test article creation."""
        payload = {
            "title": "Test Article",
            "content": "Test content",
            "is_published": True,
        }
        response = self.client.post(
            "/api/articles/",
            data=payload,
            content_type="application/json",
            **self.auth_headers
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["title"], "Test Article")

    def test_authentication_required(self):
        """Test that endpoints require authentication."""
        response = self.client.get("/api/articles/")  # No auth header
        self.assertEqual(response.status_code, 401)
```

### Testing with Fixtures

```python
from django.test import TestCase
from myapp.models import Article

class ArticleAPITest(TestCase):
    fixtures = ["articles.json"]  # Load test data

    def test_get_article(self):
        """Test retrieving a specific article."""
        response = self.client.get("/api/articles/test-article/", **self.auth_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["slug"], "test-article")
```

## API Documentation

Once installed, automatic documentation is available at:

- **Swagger UI**: `/api/docs`
- **OpenAPI Schema**: `/api/openapi.json`
- **ReDoc**: `/api/redoc`

## Architecture

The package provides:

1. **APIToken Model** - Database-backed authentication tokens
2. **APIKeyAuth** - Bearer token authentication handler
3. **Auto-Discovery System** - Scans apps for `api.py` files at startup
4. **Common Schemas** - Shared Pydantic schemas (e.g., PaginatedResponse)
5. **Django System Checks** - Validates configuration at startup
6. **Management Command** - `api_discover` for debugging and validation

## Troubleshooting

### Discovery and Validation Commands

List all discovered API routers:
```bash
python manage.py api_discover --list-routers
```

Show all registered endpoints:
```bash
python manage.py api_discover --list-endpoints
```

Validate api.py files for common issues:
```bash
python manage.py api_discover --validate
```

Run Django system checks:
```bash
python manage.py check
```

### Common Issues

#### "My endpoints aren't showing up!"

**Problem**: Created `api.py` but endpoints don't appear in `/api/docs`

**Solutions**:

1. **Check INSTALLED_APPS ordering**:
   ```python
   INSTALLED_APPS = [
       # ...
       "django_directory_api",  # Must come BEFORE your app
       "myapp",  # Your app with api.py
       # ...
   ]
   ```

2. **Verify router export**:
   ```python
   # myapp/api.py
   from ninja import Router

   router = Router(tags=["My App"])  # ← Must be named 'router'

   @router.get("/items/")
   def list_items(request):
       return {"items": []}
   ```

3. **Check for syntax errors**:
   ```bash
   python manage.py api_discover --validate
   ```

4. **Restart Django server** - Changes to `api.py` require restart

#### "ImportError" or "Circular Import"

**Problem**: Getting import errors when Django starts

**Solution**: Use local imports in endpoint functions:
```python
# myapp/api.py
from ninja import Router

router = Router(tags=["My App"])

@router.get("/items/")
def list_items(request):
    from .models import MyModel  # ← Import inside function
    return {"items": list(MyModel.objects.values())}
```

#### "Router has no tags warning"

**Problem**: System check warns about missing tags

**Solution**: Add tags to your router:
```python
router = Router(tags=["My App"])  # ← Helps organize OpenAPI docs
```

#### "APIToken table does not exist"

**Problem**: Database error on startup

**Solution**: Run migrations:
```bash
python manage.py migrate django_directory_api
```

### Debug Output

The package prints discovery information on startup:
```
[django-directory-api] Auto-discovered and registered 3 API routers
```

If you see `0 API routers`, check:
- INSTALLED_APPS ordering
- Router export names (`router` or `routers`)
- Syntax errors in api.py files

## Development

```bash
# Install dependencies
uv sync --extra dev

# Run tests
python tests/manage.py test

# Format code
ruff format .

# Lint
ruff check .
```

## License

MIT License - see LICENSE file for details.

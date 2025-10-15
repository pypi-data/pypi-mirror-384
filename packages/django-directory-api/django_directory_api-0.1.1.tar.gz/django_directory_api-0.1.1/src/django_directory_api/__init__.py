"""Django Directory API - REST API framework with auto-discovery.

This package provides a reusable Django REST API infrastructure with:
- Bearer token authentication via APIToken model
- Auto-discovery of API routers from installed apps
- Built on Django Shinobi (Django Ninja fork)
- LLM-optimized OpenAPI documentation

API instance will be created when Django apps are ready (in apps.py).
"""

# API instance will be created during Django startup
api = None

__version__ = "0.1.1"
__all__ = ["api", "__version__"]

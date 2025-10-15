"""Django app configuration for django_directory_api with auto-discovery."""

from importlib import import_module

from django.apps import AppConfig


class DjangoDirectoryApiConfig(AppConfig):
    """Configuration for the django_directory_api Django app.

    Features:
    - Auto-discovers and registers API routers from installed apps
    - Each app can define an api.py file with a `router` or `routers` attribute
    - Routers are automatically added to the main API instance
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "django_directory_api"
    verbose_name = "Directory REST API"

    def ready(self):
        """Initialize API when Django apps are ready (avoids import cycles).

        Auto-discovers api.py files in all installed apps and registers their routers.
        """
        # Import checks to register them with Django's check framework
        from django_directory_api import checks  # noqa: F401

        # Only initialize once (ready() can be called multiple times)
        import django_directory_api

        if django_directory_api.api is not None:
            return  # Already initialized

        # Import here to avoid AppRegistryNotReady errors
        from django.apps import apps
        from ninja import NinjaAPI

        from django_directory_api.auth import api_key_auth

        # Initialize the API instance
        api_instance = NinjaAPI(
            title="Directory Builder API",
            version="1.0.0",
            description=(
                "REST API for managing directory platform resources.\n\n"
                "**Authentication:** Use Bearer token authentication with your API key:\n"
                "```\n"
                "Authorization: Bearer <your-api-token>\n"
                "```\n\n"
                "**For LLM Agents:** This API is designed with rich descriptions, examples, and validation rules "
                "to facilitate programmatic access by AI agents. See the OpenAPI schema at `/api/openapi.json` "
                "for complete machine-readable documentation.\n\n"
                "**Auto-Discovery:** This API automatically discovers and registers routers from all installed "
                "Django apps that define an `api.py` file with a `router` or `routers` attribute."
            ),
            auth=api_key_auth,
            docs_url="/docs",  # Swagger UI at /api/docs
            openapi_url="/openapi.json",  # OpenAPI schema at /api/openapi.json
        )

        # Auto-discover and register routers from all installed apps
        registered_count = 0
        registered_apps = []  # Track which apps contributed routers

        for app_config in apps.get_app_configs():
            # Skip django_directory_api itself to avoid circular import
            if app_config.name == self.name:
                continue

            try:
                # Try to import api.py from each app
                api_module = import_module(f"{app_config.name}.api")

                app_router_count = 0

                # Register single router if it exists
                if hasattr(api_module, "router"):
                    router = api_module.router
                    api_instance.add_router("", router)
                    app_router_count += 1

                # Support multiple routers
                if hasattr(api_module, "routers"):
                    routers = api_module.routers
                    if isinstance(routers, (list, tuple)):
                        for router in routers:
                            api_instance.add_router("", router)
                            app_router_count += 1

                # Track this app if it contributed routers
                if app_router_count > 0:
                    registered_count += app_router_count
                    registered_apps.append(app_config.name)

            except (ImportError, AttributeError):
                # App doesn't have api.py or router - that's ok, skip silently
                pass

        # Make API available at module level
        django_directory_api.api = api_instance

        # Optional: Log discovery results in debug mode
        if apps.is_installed("django.contrib.admin"):  # Proxy for debug mode check
            if registered_apps:
                apps_list = ", ".join(registered_apps)
                print(f"[django-directory-api] Auto-discovered and registered {registered_count} API routers from: {apps_list}")
            else:
                print("[django-directory-api] No API routers discovered")

"""Django system checks for django-directory-api configuration validation.

These checks run automatically with `python manage.py check` to catch common
configuration issues before they cause runtime problems.
"""

from django.apps import apps
from django.conf import settings
from django.core.checks import Error, Tags, Warning, register


@register(Tags.compatibility)
def check_installed_apps_order(app_configs, **kwargs):
    """Check that django_directory_api comes before apps with api.py files.

    If django_directory_api is listed after apps that define API endpoints,
    those endpoints won't be auto-discovered.
    """
    errors = []

    if not hasattr(settings, "INSTALLED_APPS"):
        return errors

    installed_apps = list(settings.INSTALLED_APPS)

    try:
        api_index = installed_apps.index("django_directory_api")
    except ValueError:
        # django_directory_api not in INSTALLED_APPS - Django will handle this error
        return errors

    # Check each app that comes before django_directory_api
    for app_name in installed_apps[:api_index]:
        try:
            app_config = apps.get_app_config(app_name.split(".")[-1])

            # Skip Django built-in apps
            if app_config.name.startswith("django."):
                continue

            # Try to import api module
            api_module = __import__(f"{app_config.name}.api", fromlist=[""])

            # Check if it actually has router/routers (not just any api module)
            has_router = hasattr(api_module, "router") or hasattr(api_module, "routers")

            if has_router:
                # This app has an api.py file with routers but comes before django_directory_api
                errors.append(
                    Warning(
                        f"App '{app_name}' has an api.py file but is listed before 'django_directory_api' in INSTALLED_APPS.",
                        hint=(
                            "Move 'django_directory_api' before apps that define API endpoints in INSTALLED_APPS. "
                            f"The API endpoints in {app_name}/api.py will not be auto-discovered in the current configuration."
                        ),
                        id="django_directory_api.W001",
                    )
                )
        except (LookupError, ImportError, AttributeError):
            # App doesn't exist or doesn't have api.py - that's fine
            continue

    return errors


@register(Tags.database)
def check_apitoken_migrations(app_configs, **kwargs):
    """Check that django_directory_api migrations have been applied.

    This check verifies that migrations are up-to-date without querying
    the database, which would block the migrate command itself.
    """
    errors = []

    # Only check if django_directory_api is in app_configs
    if app_configs and not any(app.name == "django_directory_api" for app in app_configs):
        return errors

    try:
        from django.db import DEFAULT_DB_ALIAS, connections
        from django.db.migrations.executor import MigrationExecutor

        # Get migration executor for default database
        executor = MigrationExecutor(connections[DEFAULT_DB_ALIAS])

        # Get migration plan - if it's not empty, there are unapplied migrations
        targets = executor.loader.graph.leaf_nodes()
        plan = executor.migration_plan(targets)

        # Check if any migrations are for django_directory_api
        unapplied_migrations = [migration for migration, _backwards in plan if migration[0] == "django_directory_api"]

        if unapplied_migrations:
            migration_names = ", ".join([f"{app}.{name}" for app, name in unapplied_migrations])
            errors.append(
                Error(
                    f"django_directory_api has unapplied migrations: {migration_names}",
                    hint=(
                        "Run migrations to create the APIToken table:\n"
                        "  python manage.py migrate django_directory_api"
                    ),
                    id="django_directory_api.E001",
                )
            )

    except Exception:
        # If we can't check migrations (e.g., database not configured),
        # don't block - let Django handle that error
        pass

    return errors


@register(Tags.compatibility)
def check_api_module_exports(app_configs, **kwargs):
    """Check that api.py files export 'router' or 'routers'.

    This catches common mistakes where developers create api.py files
    but forget to export the router with the correct variable name.
    """
    errors = []

    for app_config in apps.get_app_configs():
        # Skip django_directory_api itself
        if app_config.name == "django_directory_api":
            continue

        # Skip Django built-in apps
        if app_config.name.startswith("django."):
            continue

        try:
            # Try to import api module
            api_module = __import__(f"{app_config.name}.api", fromlist=[""])

            # Check if it has router or routers
            has_router = hasattr(api_module, "router")
            has_routers = hasattr(api_module, "routers")

            if not has_router and not has_routers:
                errors.append(
                    Warning(
                        f"App '{app_config.name}' has an api.py file but doesn't export 'router' or 'routers'.",
                        hint=(
                            f"In {app_config.name}/api.py, ensure you export your router:\n"
                            "  router = Router(tags=['YourApp'])\n"
                            "or for multiple routers:\n"
                            "  routers = [router1, router2]"
                        ),
                        id="django_directory_api.W002",
                    )
                )

            # Validate routers is a list/tuple if it exists
            if has_routers:
                routers = getattr(api_module, "routers")
                if not isinstance(routers, (list, tuple)):
                    errors.append(
                        Warning(
                            f"App '{app_config.name}' exports 'routers' but it's not a list or tuple.",
                            hint=f"In {app_config.name}/api.py, change 'routers' to a list: routers = [router1, router2]",
                            id="django_directory_api.W003",
                        )
                    )

        except ImportError:
            # App doesn't have api.py - that's fine
            continue
        except Exception:
            # Other errors - let them surface during actual import
            continue

    return errors


@register(Tags.compatibility)
def check_router_configuration(app_configs, **kwargs):
    """Check that routers are properly configured with tags.

    Routers without tags will appear in OpenAPI docs without proper categorization.
    """
    warnings = []

    for app_config in apps.get_app_configs():
        if app_config.name == "django_directory_api":
            continue

        try:
            api_module = __import__(f"{app_config.name}.api", fromlist=[""])

            routers_to_check = []

            if hasattr(api_module, "router"):
                routers_to_check.append(("router", getattr(api_module, "router")))

            if hasattr(api_module, "routers"):
                routers = getattr(api_module, "routers")
                if isinstance(routers, (list, tuple)):
                    for i, router in enumerate(routers):
                        routers_to_check.append((f"routers[{i}]", router))

            for router_name, router in routers_to_check:
                # Check if router has tags
                if hasattr(router, "tags") and not router.tags:
                    warnings.append(
                        Warning(
                            f"Router '{router_name}' in '{app_config.name}' has no tags.",
                            hint=(
                                "Add tags to your router for better OpenAPI documentation:\n"
                                f"  router = Router(tags=['{app_config.verbose_name}'])"
                            ),
                            id="django_directory_api.W004",
                        )
                    )

        except (ImportError, AttributeError):
            continue
        except Exception:
            continue

    return warnings

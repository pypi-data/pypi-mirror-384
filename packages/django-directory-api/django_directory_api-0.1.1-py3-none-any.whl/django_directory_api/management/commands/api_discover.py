"""Management command to discover and validate API routers.

Usage:
    # List all discovered routers
    python manage.py api_discover --list-routers

    # List all endpoints with details
    python manage.py api_discover --list-endpoints

    # Validate api.py files
    python manage.py api_discover --validate

    # Focus on specific app
    python manage.py api_discover --app myapp --list-endpoints

This command helps debug auto-discovery issues and provides visibility
into which API endpoints are registered.
"""

from importlib import import_module

from django.apps import apps
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Management command for API router discovery and validation."""

    help = "Discover and validate API routers from installed Django apps"

    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            "--list-routers",
            action="store_true",
            help="List all discovered API routers by app",
        )
        parser.add_argument(
            "--list-endpoints",
            action="store_true",
            help="List all registered API endpoints",
        )
        parser.add_argument(
            "--validate",
            action="store_true",
            help="Validate api.py files and show common issues",
        )
        parser.add_argument(
            "--app",
            type=str,
            help="Focus on specific app (app label)",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed output",
        )

    def handle(self, *args, **options):
        """Execute the command."""
        # Default to listing routers if no specific action specified
        if not any([options["list_routers"], options["list_endpoints"], options["validate"]]):
            options["list_routers"] = True

        if options["list_routers"]:
            self._list_routers(options)

        if options["list_endpoints"]:
            self._list_endpoints(options)

        if options["validate"]:
            self._validate_apis(options)

    def _list_routers(self, options):
        """List all discovered API routers."""
        self.stdout.write(self.style.SUCCESS("\n📡 Discovered API Routers"))
        self.stdout.write("=" * 60)

        discovered = self._discover_routers(options.get("app"))

        if not discovered:
            self.stdout.write(self.style.WARNING("\nNo API routers found."))
            self._show_discovery_help()
            return

        for app_name, router_info in discovered.items():
            self.stdout.write(f"\n📦 {app_name}")
            self.stdout.write("-" * 60)

            for info in router_info:
                router_type = info["type"]
                tags = info.get("tags", [])
                endpoint_count = info.get("endpoint_count", 0)

                if tags:
                    tags_str = f" (tags: {', '.join(tags)})"
                else:
                    tags_str = self.style.WARNING(" (no tags)")

                self.stdout.write(f"  • {router_type}: {endpoint_count} endpoints{tags_str}")

        total_routers = sum(len(routers) for routers in discovered.values())
        total_endpoints = sum(
            info["endpoint_count"] for routers in discovered.values() for info in routers
        )

        self.stdout.write(f"\n📊 Total: {total_routers} routers, {total_endpoints} endpoints\n")

    def _list_endpoints(self, options):
        """List all registered API endpoints."""
        self.stdout.write(self.style.SUCCESS("\n🔌 Registered API Endpoints"))
        self.stdout.write("=" * 60)

        app_filter = options.get("app")

        # Discover routers and list their endpoints
        discovered = self._discover_routers(app_filter)

        if not discovered:
            self.stdout.write(self.style.WARNING("\nNo endpoints found."))
            return

        total_endpoints = 0

        for app_name, router_info in discovered.items():
            for info in router_info:
                tags = info.get("tags", ["Untagged"])
                tag_name = tags[0] if tags else "Untagged"

                self.stdout.write(f"\n🏷️  {tag_name} (from {app_name})")
                self.stdout.write("-" * 60)

                # Note: Individual endpoint paths would require introspecting the router
                # which is complex. For now, just show the count.
                count = info.get("endpoint_count", 0)
                self.stdout.write(f"  {count} endpoints registered")
                total_endpoints += count

        self.stdout.write(f"\n📊 Total: {total_endpoints} endpoints")
        self.stdout.write("\n💡 Visit /api/docs to see detailed endpoint documentation\n")

    def _validate_apis(self, options):
        """Validate api.py files and show common issues."""
        self.stdout.write(self.style.SUCCESS("\n🔍 Validating API Configuration"))
        self.stdout.write("=" * 60)

        app_filter = options.get("app")
        issues_found = []

        for app_config in apps.get_app_configs():
            if app_config.name == "django_directory_api":
                continue

            if app_filter and app_config.label != app_filter:
                continue

            try:
                api_module = import_module(f"{app_config.name}.api")

                # Check for router/routers export
                has_router = hasattr(api_module, "router")
                has_routers = hasattr(api_module, "routers")

                if not has_router and not has_routers:
                    issues_found.append({
                        "app": app_config.name,
                        "issue": "api.py exists but doesn't export 'router' or 'routers'",
                        "fix": "Add: router = Router(tags=['YourApp'])",
                    })
                    continue

                # Check router tags
                if has_router:
                    router = getattr(api_module, "router")
                    if not getattr(router, "tags", None):
                        issues_found.append({
                            "app": app_config.name,
                            "issue": "Router has no tags (affects OpenAPI docs)",
                            "fix": f"Add tags: router = Router(tags=['{app_config.verbose_name}'])",
                        })

                # Check routers is a list
                if has_routers:
                    routers = getattr(api_module, "routers")
                    if not isinstance(routers, (list, tuple)):
                        issues_found.append({
                            "app": app_config.name,
                            "issue": "'routers' export is not a list or tuple",
                            "fix": "Change to: routers = [router1, router2]",
                        })

            except ImportError:
                # No api.py - that's fine
                continue
            except Exception as e:
                issues_found.append({
                    "app": app_config.name,
                    "issue": f"Error loading api.py: {e!s}",
                    "fix": "Check for syntax errors or circular imports",
                })

        if not issues_found:
            self.stdout.write(self.style.SUCCESS("\n✅ No issues found!\n"))
            return

        self.stdout.write(self.style.WARNING(f"\n⚠️  Found {len(issues_found)} issue(s):\n"))

        for issue in issues_found:
            self.stdout.write(f"\n📦 {issue['app']}")
            self.stdout.write(f"   Issue: {issue['issue']}")
            self.stdout.write(self.style.SUCCESS(f"   Fix: {issue['fix']}"))

        self.stdout.write("")

    def _discover_routers(self, app_filter=None):
        """Discover routers from installed apps."""
        discovered = {}

        for app_config in apps.get_app_configs():
            if app_config.name == "django_directory_api":
                continue

            if app_filter and app_config.label != app_filter:
                continue

            try:
                api_module = import_module(f"{app_config.name}.api")
                app_routers = []

                if hasattr(api_module, "router"):
                    router = getattr(api_module, "router")
                    app_routers.append({
                        "type": "router",
                        "tags": getattr(router, "tags", []),
                        "endpoint_count": self._count_router_endpoints(router),
                    })

                if hasattr(api_module, "routers"):
                    routers = getattr(api_module, "routers")
                    if isinstance(routers, (list, tuple)):
                        for i, router in enumerate(routers):
                            app_routers.append({
                                "type": f"routers[{i}]",
                                "tags": getattr(router, "tags", []),
                                "endpoint_count": self._count_router_endpoints(router),
                            })

                if app_routers:
                    discovered[app_config.name] = app_routers

            except (ImportError, AttributeError):
                continue

        return discovered

    def _count_router_endpoints(self, router):
        """Count endpoints in a router."""
        try:
            if hasattr(router, "path_operations"):
                return len(router.path_operations)
            return 0
        except Exception:
            return 0

    def _show_discovery_help(self):
        """Show help for creating API endpoints."""
        self.stdout.write("\nTo create API endpoints:")
        self.stdout.write("\n1. Create api.py in your Django app:")
        self.stdout.write("   " + self.style.SUCCESS("myapp/api.py"))
        self.stdout.write("\n2. Define a router and endpoints:")
        self.stdout.write("""
   from ninja import Router

   router = Router(tags=["My App"])

   @router.get("/items/")
   def list_items(request):
       return {"items": []}
""")
        self.stdout.write("3. Restart your Django server")
        self.stdout.write("4. Check /api/docs for your endpoints\n")

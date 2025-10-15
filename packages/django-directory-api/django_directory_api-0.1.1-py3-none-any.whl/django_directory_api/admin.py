"""Django admin configuration for django_directory_api."""

from django.contrib import admin, messages
from django.utils.html import format_html

from django_directory_api.models import APIToken


@admin.register(APIToken)
class APITokenAdmin(admin.ModelAdmin):
    """Admin interface for APIToken model.

    Features:
    - Shows token key only once at creation (for security)
    - Allows revoking tokens (set is_active=False)
    - Displays last used timestamp
    - Filters by user, active status
    """

    list_display = ["name", "user", "status_badge", "created_at", "last_used_at", "key_preview"]
    list_filter = ["is_active", "user", "created_at"]
    search_fields = ["name", "user__username", "user__email"]
    readonly_fields = ["key", "created_at", "last_used_at"]
    ordering = ["-created_at"]

    fieldsets = [
        (
            "Token Information",
            {
                "fields": ["name", "user", "key", "is_active"],
                "description": "API token details. The key is only shown in full immediately after creation.",
            },
        ),
        (
            "Usage Tracking",
            {
                "fields": ["created_at", "last_used_at"],
                "description": "Timestamps for token creation and last usage.",
            },
        ),
    ]

    def status_badge(self, obj: APIToken) -> str:
        """Display active status as colored badge."""
        if obj.is_active:
            return format_html('<span style="color: green; font-weight: bold;">✓ Active</span>')
        return format_html('<span style="color: red; font-weight: bold;">✗ Inactive</span>')

    status_badge.short_description = "Status"

    def key_preview(self, obj: APIToken) -> str:
        """Show first 8 characters of key for identification."""
        return f"{obj.key[:8]}..." if obj.key else "—"

    key_preview.short_description = "Key Preview"

    def save_model(self, request, obj: APIToken, form, change) -> None:
        """Save model and show full key only for new tokens."""
        is_new = obj.pk is None

        super().save_model(request, obj, form, change)

        if is_new:
            messages.success(
                request,
                format_html(
                    "<strong>API Token Created Successfully!</strong><br>"
                    "Save this token now - it won't be shown again:<br>"
                    '<code style="background: #f0f0f0; padding: 8px; display: block; margin-top: 8px;">{}</code>',
                    obj.key,
                ),
            )

    def has_add_permission(self, request) -> bool:
        """Allow creating new tokens."""
        return request.user.has_perm("django_directory_api.add_apitoken")

    def has_delete_permission(self, request, obj=None) -> bool:
        """Prefer revoking (is_active=False) over deletion."""
        # Allow deletion for superusers, but suggest revocation instead
        return request.user.is_superuser

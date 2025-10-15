"""Models for directory_api - API token authentication."""

import secrets

from django.conf import settings
from django.db import models


def generate_api_key() -> str:
    """Generate a secure random API key."""
    return secrets.token_urlsafe(48)  # 64 characters after base64 encoding


class APIToken(models.Model):
    """API authentication tokens for LLM agents and programmatic access.

    Each token is associated with a Django user and can be revoked independently.
    Tokens are generated securely and only shown once at creation.
    """

    key = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        default=generate_api_key,
        help_text="API authentication token (generated automatically)",
    )
    name = models.CharField(
        max_length=100, help_text="Human-readable identifier (e.g., 'GPT-4 Agent', 'Claude API', 'Production Bot')"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="api_tokens",
        help_text="User who owns this API token",
    )
    is_active = models.BooleanField(
        default=True, db_index=True, help_text="Whether this token is currently active (can be revoked)"
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text="When this token was created")
    last_used_at = models.DateTimeField(
        null=True, blank=True, help_text="Last time this token was used for API authentication"
    )

    class Meta:
        """Metaclass for APIToken."""

        ordering = ["-created_at"]
        verbose_name = "API Token"
        verbose_name_plural = "API Tokens"
        indexes = [
            models.Index(fields=["key", "is_active"]),  # Fast auth lookups
        ]

    def __str__(self) -> str:
        """Return string representation."""
        status = "active" if self.is_active else "inactive"
        return f"{self.name} ({self.user.username}) - {status}"

    def save(self, *args, **kwargs) -> None:
        """Override save to ensure key is generated."""
        if not self.key:
            self.key = generate_api_key()
        super().save(*args, **kwargs)

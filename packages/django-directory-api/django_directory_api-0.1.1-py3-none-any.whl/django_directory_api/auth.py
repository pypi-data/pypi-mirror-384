"""Authentication for directory_api - Bearer token authentication."""

from django.utils import timezone
from ninja.security import HttpBearer

from django_directory_api.models import APIToken


class APIKeyAuth(HttpBearer):
    """Bearer token authentication using APIToken model.

    Usage in API headers:
        Authorization: Bearer <your-api-token>

    This authentication class:
    - Validates the token exists and is active
    - Updates last_used_at timestamp on successful auth
    - Returns None if authentication fails (401 response)
    """

    def authenticate(self, request, token: str):
        """Authenticate request using API token.

        Args:
            request: Django HttpRequest object
            token: Bearer token from Authorization header

        Returns:
            User object if authentication succeeds, None otherwise

        """
        try:
            # Look up token (active tokens only)
            api_token = APIToken.objects.select_related("user").get(key=token, is_active=True)

            # Update last used timestamp (async to avoid blocking)
            APIToken.objects.filter(pk=api_token.pk).update(last_used_at=timezone.now())

            # Return the associated user
            return api_token.user

        except APIToken.DoesNotExist:
            # Invalid or inactive token
            return None


# Create singleton instance for use in routers
api_key_auth = APIKeyAuth()

"""Client for authentication operations."""

from typing import TYPE_CHECKING

from ..models import APIAccess, APIKey

if TYPE_CHECKING:
    from ..http_client import HTTPClient


class AuthClient:
    """Client for managing API keys."""

    def __init__(self, http_client: "HTTPClient"):
        """
        Initialize the auth client.

        Args:
            http_client: HTTP client for making requests
        """
        self._http = http_client

    def create_api_key(self, key_name: str, access: APIAccess = APIAccess.READ) -> APIKey:
        """
        Create a new API key.

        Args:
            key_name: Name for the API key
            access: Access level (ADMIN, READ_WRITE, or READ)

        Returns:
            Created APIKey object

        Raises:
            AuthenticationError: If authentication fails
            ForbiddenError: If user doesn't have ADMIN permission
        """
        data = {"keyName": key_name, "access": access.value}
        response = self._http.post("/api/v1/auth/api-keys", data)
        return APIKey(
            key_name=key_name,
            api_key=response.get("apiKey", ""),
            access=access,
        )

    def list_api_keys(self) -> list[APIKey]:
        """
        List all API keys.

        Returns:
            List of APIKey objects

        Raises:
            AuthenticationError: If authentication fails
            ForbiddenError: If user doesn't have ADMIN permission
        """
        response = self._http.get("/api/v1/auth/api-keys")
        if isinstance(response, list):
            return [APIKey.from_dict(key) for key in response]
        return []

    def delete_api_key(self, api_key_id: str) -> dict:
        """
        Delete an API key.

        Args:
            api_key_id: ID of the API key to delete

        Returns:
            Response message

        Raises:
            NotFoundError: If API key not found
            AuthenticationError: If authentication fails
            ForbiddenError: If user doesn't have ADMIN permission
        """
        return self._http.delete(f"/api/v1/auth/api-keys/{api_key_id}")


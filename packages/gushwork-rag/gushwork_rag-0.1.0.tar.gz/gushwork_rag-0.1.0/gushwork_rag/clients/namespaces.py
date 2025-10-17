"""Client for namespace operations."""

from typing import TYPE_CHECKING

from ..models import Namespace

if TYPE_CHECKING:
    from ..http_client import HTTPClient


class NamespacesClient:
    """Client for managing namespaces."""

    def __init__(self, http_client: "HTTPClient"):
        """
        Initialize the namespaces client.

        Args:
            http_client: HTTP client for making requests
        """
        self._http = http_client

    def create(self, name: str, instructions: str = "") -> Namespace:
        """
        Create a new namespace.

        Args:
            name: Name of the namespace
            instructions: Instructions for the namespace (used in chat completions)

        Returns:
            Created Namespace object

        Raises:
            BadRequestError: If namespace already exists
            AuthenticationError: If authentication fails
            ForbiddenError: If user doesn't have permission
        """
        data = {"name": name, "instructions": instructions}
        response = self._http.post("/api/v1/namespaces", data)
        return Namespace.from_dict(response.get("namespace", {}))

    def list(self) -> list[Namespace]:
        """
        List all namespaces.

        Returns:
            List of Namespace objects

        Raises:
            AuthenticationError: If authentication fails
        """
        response = self._http.get("/api/v1/namespaces")
        if isinstance(response, list):
            return [Namespace.from_dict(ns) for ns in response]
        return []

    def get(self, namespace_id: str) -> Namespace:
        """
        Get a namespace by ID.

        Args:
            namespace_id: ID of the namespace

        Returns:
            Namespace object

        Raises:
            NotFoundError: If namespace not found
            AuthenticationError: If authentication fails
        """
        response = self._http.get(f"/api/v1/namespaces/{namespace_id}")
        return Namespace.from_dict(response)

    def update(self, namespace_id: str, instructions: str) -> Namespace:
        """
        Update a namespace.

        Args:
            namespace_id: ID of the namespace
            instructions: New instructions

        Returns:
            Updated Namespace object

        Raises:
            NotFoundError: If namespace not found
            AuthenticationError: If authentication fails
            ForbiddenError: If user doesn't have permission
        """
        data = {"instructions": instructions}
        response = self._http.patch(f"/api/v1/namespaces/{namespace_id}", data)
        return Namespace.from_dict(response)

    def delete(self, namespace_id: str) -> dict:
        """
        Delete a namespace.

        Args:
            namespace_id: ID of the namespace

        Returns:
            Response message

        Raises:
            NotFoundError: If namespace not found
            AuthenticationError: If authentication fails
            ForbiddenError: If user doesn't have permission
        """
        return self._http.delete(f"/api/v1/namespaces/{namespace_id}")


"""Main client for the Gushwork RAG SDK."""

from typing import Optional

from .clients import AuthClient, ChatClient, FilesClient, NamespacesClient
from .http_client import HTTPClient


class GushworkRAG:
    """
    Main client for the Gushwork RAG API.

    This client provides access to all API functionality through sub-clients:
    - namespaces: Manage document namespaces
    - files: Upload and manage files
    - chat: Chat completions with RAG
    - auth: Manage API keys

    Example:
        >>> from gushwork_rag import GushworkRAG
        >>> client = GushworkRAG(api_key="your-api-key")
        >>> 
        >>> # Create a namespace
        >>> namespace = client.namespaces.create(
        ...     name="my-docs",
        ...     instructions="Answer questions about the documents."
        ... )
        >>> 
        >>> # Upload a file
        >>> file = client.files.upload("document.pdf", namespace="my-docs")
        >>> 
        >>> # Chat with your documents
        >>> response = client.chat.create(
        ...     namespace="my-docs",
        ...     messages=[{"role": "user", "content": "What is this about?"}],
        ...     model="gpt-3.5-turbo"
        ... )
        >>> print(response.content)
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "http://localhost:8080",
    ):
        """
        Initialize the Gushwork RAG client.

        Args:
            api_key: API key for authentication. Get this by creating an API key
                    with ADMIN access using the auth endpoints.
            base_url: Base URL of the API (default: http://localhost:8080).
                     For production, use your deployed API URL.

        Example:
            >>> client = GushworkRAG(
            ...     api_key="rag_sk_1234567890abcdef",
            ...     base_url="https://api.example.com"
            ... )
        """
        self._http = HTTPClient(api_key=api_key, base_url=base_url)
        
        # Initialize sub-clients
        self._namespaces = NamespacesClient(self._http)
        self._files = FilesClient(self._http)
        self._chat = ChatClient(self._http)
        self._auth = AuthClient(self._http)

    @property
    def namespaces(self) -> NamespacesClient:
        """
        Access the namespaces client.

        Returns:
            NamespacesClient for managing namespaces

        Example:
            >>> # Create a namespace
            >>> namespace = client.namespaces.create(
            ...     name="my-docs",
            ...     instructions="Answer based on these documents."
            ... )
            >>> 
            >>> # List all namespaces
            >>> namespaces = client.namespaces.list()
            >>> 
            >>> # Get a specific namespace
            >>> namespace = client.namespaces.get(namespace_id)
        """
        return self._namespaces

    @property
    def files(self) -> FilesClient:
        """
        Access the files client.

        Returns:
            FilesClient for managing files

        Example:
            >>> # Upload a file
            >>> file = client.files.upload("document.pdf", namespace="my-docs")
            >>> 
            >>> # List files in a namespace
            >>> files = client.files.list_by_namespace("my-docs", limit=10)
            >>> 
            >>> # Get file details
            >>> file = client.files.get(file_id)
        """
        return self._files

    @property
    def chat(self) -> ChatClient:
        """
        Access the chat client.

        Returns:
            ChatClient for chat completions

        Example:
            >>> # Simple chat
            >>> response = client.chat.create(
            ...     namespace="my-docs",
            ...     messages=[{"role": "user", "content": "What is this about?"}],
            ...     model="gpt-3.5-turbo"
            ... )
            >>> print(response.content)
            >>> 
            >>> # Streaming chat
            >>> for chunk in client.chat.stream(
            ...     namespace="my-docs",
            ...     messages=[{"role": "user", "content": "Summarize this."}],
            ...     model="gpt-3.5-turbo"
            ... ):
            ...     print(chunk.get("content", ""), end="")
        """
        return self._chat

    @property
    def auth(self) -> AuthClient:
        """
        Access the auth client.

        Returns:
            AuthClient for managing API keys

        Example:
            >>> # Create a new API key (requires ADMIN access)
            >>> api_key = client.auth.create_api_key(
            ...     key_name="new-key",
            ...     access=APIAccess.READ_WRITE
            ... )
            >>> print(api_key.api_key)
            >>> 
            >>> # List all API keys
            >>> keys = client.auth.list_api_keys()
            >>> 
            >>> # Delete an API key
            >>> client.auth.delete_api_key(api_key_id)
        """
        return self._auth

    def health_check(self) -> dict:
        """
        Check if the API is healthy.

        Returns:
            Health status information

        Example:
            >>> health = client.health_check()
            >>> print(health["status"])  # 'healthy'
        """
        return self._http.get("/health")

    def close(self) -> None:
        """
        Close the HTTP session.

        It's recommended to use the client as a context manager instead:

        Example:
            >>> with GushworkRAG(api_key="key") as client:
            ...     # Use the client
            ...     pass
            >>> # Client is automatically closed
        """
        self._http.close()

    def __enter__(self) -> "GushworkRAG":
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager and close session."""
        self.close()

    def __repr__(self) -> str:
        """String representation of the client."""
        return f"GushworkRAG(base_url='{self._http.base_url}')"


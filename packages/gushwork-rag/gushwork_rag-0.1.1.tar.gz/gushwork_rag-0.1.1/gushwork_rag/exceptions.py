"""Exception classes for the Gushwork RAG SDK."""

from typing import Optional


class GushworkError(Exception):
    """Base exception for all Gushwork SDK errors."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(GushworkError):
    """Raised when authentication fails (401)."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class ForbiddenError(GushworkError):
    """Raised when the request is forbidden (403)."""

    def __init__(self, message: str = "Access forbidden"):
        super().__init__(message, status_code=403)


class NotFoundError(GushworkError):
    """Raised when a resource is not found (404)."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class BadRequestError(GushworkError):
    """Raised when the request is invalid (400)."""

    def __init__(self, message: str = "Bad request"):
        super().__init__(message, status_code=400)


class ServerError(GushworkError):
    """Raised when the server encounters an error (500)."""

    def __init__(self, message: str = "Internal server error"):
        super().__init__(message, status_code=500)


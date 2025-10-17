"""Gushwork RAG SDK - A Python client for the Gushwork RAG API."""

from .client import GushworkRAG
from .exceptions import (
    GushworkError,
    AuthenticationError,
    NotFoundError,
    BadRequestError,
    ForbiddenError,
    ServerError,
)
from .models import (
    Namespace,
    File,
    FileStatus,
    Message,
    ChatCompletionRequest,
    ChatCompletionResponse,
    APIKey,
)

__version__ = "0.1.0"
__all__ = [
    "GushworkRAG",
    "GushworkError",
    "AuthenticationError",
    "NotFoundError",
    "BadRequestError",
    "ForbiddenError",
    "ServerError",
    "Namespace",
    "File",
    "FileStatus",
    "Message",
    "ChatCompletionRequest",
    "ChatCompletionResponse",
    "APIKey",
]


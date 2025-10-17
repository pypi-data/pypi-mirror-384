"""Data models for the Gushwork RAG SDK."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class FileStatus(str, Enum):
    """Status of a file in the RAG pipeline."""

    UPLOAD_URL_CREATED = "UPLOAD_URL_CREATED"
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    FILE_PARSED = "FILE_PARSED"
    FILE_CHUNKED = "FILE_CHUNKED"
    FILE_INDEXED = "FILE_INDEXED"
    FAILED = "FAILED"


class APIAccess(str, Enum):
    """API access levels."""

    ADMIN = "ADMIN"
    READ_WRITE = "READ_WRITE"
    READ = "READ"


class RetrievalType(str, Enum):
    """Type of retrieval for chat completions."""

    SIMPLE = "simple"
    GEMINI = "gemini"


@dataclass
class Namespace:
    """Represents a namespace for organizing documents."""

    name: str
    instructions: str
    id: Optional[str] = None
    created_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Namespace":
        """Create a Namespace from a dictionary."""
        return cls(
            name=data.get("name", ""),
            instructions=data.get("instructions", ""),
            id=data.get("_id"),
            created_at=datetime.fromisoformat(data["createdAt"].replace("Z", "+00:00"))
            if data.get("createdAt")
            else None,
        )


@dataclass
class File:
    """Represents a file in the RAG system."""

    file_name: str
    namespace: str
    status: FileStatus
    mime_type: str
    max_size: int
    id: Optional[str] = None
    location: Optional[str] = None
    created_at: Optional[datetime] = None
    uploaded_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "File":
        """Create a File from a dictionary."""
        return cls(
            file_name=data.get("fileName", ""),
            namespace=data.get("namespace", ""),
            status=FileStatus(data.get("status", FileStatus.UPLOAD_URL_CREATED)),
            mime_type=data.get("mimeType", ""),
            max_size=data.get("maxSize", 0),
            id=data.get("_id"),
            location=data.get("location"),
            created_at=datetime.fromisoformat(data["createdAt"].replace("Z", "+00:00"))
            if data.get("createdAt")
            else None,
            uploaded_at=datetime.fromisoformat(data["uploadedAt"].replace("Z", "+00:00"))
            if data.get("uploadedAt")
            else None,
            processed_at=datetime.fromisoformat(data["processedAt"].replace("Z", "+00:00"))
            if data.get("processedAt")
            else None,
            error_message=data.get("errorMessage"),
            metadata=data.get("metadata"),
        )


@dataclass
class APIKey:
    """Represents an API key."""

    key_name: str
    api_key: str
    access: APIAccess
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    last_used: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "APIKey":
        """Create an APIKey from a dictionary."""
        return cls(
            key_name=data.get("keyName", ""),
            api_key=data.get("apiKey", ""),
            access=APIAccess(data.get("access", APIAccess.READ)),
            id=data.get("_id"),
            created_at=datetime.fromisoformat(data["createdAt"].replace("Z", "+00:00"))
            if data.get("createdAt")
            else None,
            last_used=datetime.fromisoformat(data["lastUsed"].replace("Z", "+00:00"))
            if data.get("lastUsed")
            else None,
        )


@dataclass
class Message:
    """Represents a chat message."""

    role: str
    content: str


@dataclass
class ChatCompletionRequest:
    """Request for chat completion."""

    namespace: str
    messages: List[Message]
    model: str
    retrieval_type: RetrievalType = RetrievalType.GEMINI
    stream: bool = False
    top_k: Optional[int] = None
    top_n: Optional[int] = None
    top_p: Optional[float] = None
    response_format: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request."""
        data = {
            "namespace": self.namespace,
            "messages": [{"role": msg.role, "content": msg.content} for msg in self.messages],
            "model": self.model,
            "retrievalType": self.retrieval_type.value,
            "stream": self.stream,
        }
        if self.top_k is not None:
            data["topK"] = self.top_k
        if self.top_n is not None:
            data["topN"] = self.top_n
        if self.top_p is not None:
            data["topP"] = self.top_p
        if self.response_format is not None:
            data["response_format"] = self.response_format
        return data


@dataclass
class ChatCompletionResponse:
    """Response from chat completion."""

    content: Union[str, Dict[str, Any]]
    raw_response: Dict[str, Any]

    @classmethod
    def from_dict(cls, data: Union[str, Dict[str, Any]]) -> "ChatCompletionResponse":
        """Create a ChatCompletionResponse from API response."""
        if isinstance(data, str):
            return cls(content=data, raw_response={"content": data})
        return cls(content=data, raw_response=data)


@dataclass
class FileListResponse:
    """Response from listing files."""

    files: List[File]
    total: int
    limit: int
    skip: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileListResponse":
        """Create a FileListResponse from a dictionary."""
        return cls(
            files=[File.from_dict(f) for f in data.get("files", [])],
            total=data.get("total", 0),
            limit=data.get("limit", 50),
            skip=data.get("skip", 0),
        )


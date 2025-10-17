"""Client for chat completion operations."""

from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional, Union

from ..models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    Message,
    RetrievalType,
)

if TYPE_CHECKING:
    from ..http_client import HTTPClient


class ChatClient:
    """Client for chat completions with RAG."""

    def __init__(self, http_client: "HTTPClient"):
        """
        Initialize the chat client.

        Args:
            http_client: HTTP client for making requests
        """
        self._http = http_client

    def completions(
        self,
        namespace: str,
        messages: List[Union[Message, Dict[str, str]]],
        model: str = "gpt-3.5-turbo",
        retrieval_type: RetrievalType = RetrievalType.GEMINI,
        stream: bool = False,
        top_k: Optional[int] = None,
        top_n: Optional[int] = None,
        top_p: Optional[float] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Union[ChatCompletionResponse, Iterator[Dict[str, Any]]]:
        """
        Get a chat completion with RAG retrieval.

        Args:
            namespace: Namespace containing the documents
            messages: List of messages (user/assistant conversation)
            model: Model to use (e.g., 'gpt-3.5-turbo', 'gpt-4')
            retrieval_type: Type of retrieval ('simple' or 'gemini')
            stream: Whether to stream the response
            top_k: Number of top results to retrieve
            top_n: Number of top chunks to return
            top_p: Top-p sampling parameter
            response_format: Format for structured output (JSON schema)

        Returns:
            ChatCompletionResponse for normal requests
            Iterator of response chunks for streaming requests

        Raises:
            NotFoundError: If namespace not found
            AuthenticationError: If authentication fails
            BadRequestError: If request parameters are invalid
        """
        # Convert dict messages to Message objects
        parsed_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                parsed_messages.append(Message(role=msg["role"], content=msg["content"]))
            else:
                parsed_messages.append(msg)

        request = ChatCompletionRequest(
            namespace=namespace,
            messages=parsed_messages,
            model=model,
            retrieval_type=retrieval_type,
            stream=stream,
            top_k=top_k,
            top_n=top_n,
            top_p=top_p,
            response_format=response_format,
        )

        if stream:
            return self._http.request_stream(
                "POST",
                "/api/v1/chat/completions",
                request.to_dict(),
            )
        else:
            response = self._http.post("/api/v1/chat/completions", request.to_dict())
            return ChatCompletionResponse.from_dict(response)

    def create(
        self,
        namespace: str,
        messages: List[Union[Message, Dict[str, str]]],
        model: str = "gpt-3.5-turbo",
        **kwargs: Any,
    ) -> ChatCompletionResponse:
        """
        Create a chat completion (alias for completions without streaming).

        Args:
            namespace: Namespace containing the documents
            messages: List of messages
            model: Model to use
            **kwargs: Additional arguments passed to completions()

        Returns:
            ChatCompletionResponse

        Raises:
            NotFoundError: If namespace not found
            AuthenticationError: If authentication fails
            BadRequestError: If request parameters are invalid
        """
        kwargs["stream"] = False
        result = self.completions(namespace, messages, model, **kwargs)
        if not isinstance(result, ChatCompletionResponse):
            raise TypeError("Expected ChatCompletionResponse but got streaming iterator")
        return result

    def stream(
        self,
        namespace: str,
        messages: List[Union[Message, Dict[str, str]]],
        model: str = "gpt-3.5-turbo",
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """
        Stream a chat completion (alias for completions with streaming).

        Args:
            namespace: Namespace containing the documents
            messages: List of messages
            model: Model to use
            **kwargs: Additional arguments passed to completions()

        Yields:
            Response chunks

        Raises:
            NotFoundError: If namespace not found
            AuthenticationError: If authentication fails
            BadRequestError: If request parameters are invalid
        """
        kwargs["stream"] = True
        result = self.completions(namespace, messages, model, **kwargs)
        if isinstance(result, ChatCompletionResponse):
            raise TypeError("Expected streaming iterator but got ChatCompletionResponse")
        return result


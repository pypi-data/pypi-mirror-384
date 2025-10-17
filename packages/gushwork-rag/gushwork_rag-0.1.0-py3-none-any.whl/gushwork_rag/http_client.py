"""HTTP client for making requests to the Gushwork RAG API."""

import json
from typing import Any, Dict, Iterator, Optional
from urllib.parse import urljoin

import requests

from .exceptions import (
    AuthenticationError,
    BadRequestError,
    ForbiddenError,
    GushworkError,
    NotFoundError,
    ServerError,
)


class HTTPClient:
    """HTTP client for making requests to the API."""

    def __init__(self, api_key: str, base_url: str = "http://localhost:8080"):
        """
        Initialize the HTTP client.

        Args:
            api_key: API key for authentication
            base_url: Base URL of the API
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"{api_key}",
                "Content-Type": "application/json",
            }
        )

    def _handle_error(self, response: requests.Response) -> None:
        """Handle error responses from the API."""
        try:
            error_data = response.json()
            message = error_data.get("error", response.text)
        except (json.JSONDecodeError, ValueError):
            message = response.text or response.reason

        if response.status_code == 400:
            raise BadRequestError(message)
        elif response.status_code == 401:
            raise AuthenticationError(message)
        elif response.status_code == 403:
            raise ForbiddenError(message)
        elif response.status_code == 404:
            raise NotFoundError(message)
        elif response.status_code >= 500:
            raise ServerError(message)
        else:
            raise GushworkError(message, status_code=response.status_code)

    def request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make a request to the API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., '/api/v1/files')
            data: Request body data
            params: Query parameters

        Returns:
            Response data as a dictionary

        Raises:
            GushworkError: If the request fails
        """
        url = urljoin(self.base_url, endpoint)
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
            )
            
            if not response.ok:
                self._handle_error(response)
            
            # Handle empty responses
            if not response.content:
                return {}
            
            return response.json()
        except requests.RequestException as e:
            raise GushworkError(f"Request failed: {str(e)}")

    def request_stream(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Iterator[Dict[str, Any]]:
        """
        Make a streaming request to the API.

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request body data

        Yields:
            Response chunks as dictionaries

        Raises:
            GushworkError: If the request fails
        """
        url = urljoin(self.base_url, endpoint)
        
        try:
            with self.session.request(
                method=method,
                url=url,
                json=data,
                stream=True,
            ) as response:
                if not response.ok:
                    self._handle_error(response)
                
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode("utf-8")
                        if line_str.startswith("data: "):
                            try:
                                yield json.loads(line_str[6:])
                            except json.JSONDecodeError:
                                continue
        except requests.RequestException as e:
            raise GushworkError(f"Streaming request failed: {str(e)}")

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a GET request."""
        return self.request("GET", endpoint, params=params)

    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a POST request."""
        return self.request("POST", endpoint, data=data)

    def patch(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a PATCH request."""
        return self.request("PATCH", endpoint, data=data)

    def delete(self, endpoint: str) -> Dict[str, Any]:
        """Make a DELETE request."""
        return self.request("DELETE", endpoint)

    def close(self) -> None:
        """Close the HTTP session."""
        self.session.close()


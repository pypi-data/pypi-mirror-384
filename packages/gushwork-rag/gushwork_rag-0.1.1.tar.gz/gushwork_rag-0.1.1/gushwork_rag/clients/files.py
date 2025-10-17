"""Client for file operations."""

from typing import TYPE_CHECKING, Optional

import requests

from ..models import File, FileListResponse, FileStatus

if TYPE_CHECKING:
    from ..http_client import HTTPClient


class FilesClient:
    """Client for managing files."""

    def __init__(self, http_client: "HTTPClient"):
        """
        Initialize the files client.

        Args:
            http_client: HTTP client for making requests
        """
        self._http = http_client

    def upload(
        self,
        file_path: str,
        namespace: str,
        mime_type: Optional[str] = None,
    ) -> File:
        """
        Upload a file to a namespace.

        This method:
        1. Gets a presigned URL from the API
        2. Uploads the file to S3 using the presigned URL
        3. Returns the file metadata

        Args:
            file_path: Path to the file to upload
            namespace: Namespace to upload to
            mime_type: MIME type of the file (auto-detected if not provided)

        Returns:
            File object with upload information

        Raises:
            NotFoundError: If namespace not found
            AuthenticationError: If authentication fails
            ForbiddenError: If user doesn't have READ_WRITE permission
            GushworkError: If upload fails
        """
        import os
        import mimetypes

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)

        if mime_type is None:
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type is None:
                mime_type = "application/octet-stream"

        # Step 1: Get presigned URL
        data = {
            "fileName": file_name,
            "maxSize": file_size,
            "mimeType": mime_type,
            "namespace": namespace,
        }
        print("data", data)
        response = self._http.post("/api/v1/files/upload", data)
        presigned_url = response.get("url")

        if not presigned_url:
            raise ValueError("No presigned URL returned from API")

        # Step 2: Upload to S3
        with open(file_path, "rb") as f:
            upload_response = requests.put(
                presigned_url,
                data=f,
                headers={"Content-Type": mime_type},
            )
            upload_response.raise_for_status()

        return File(
            file_name=file_name,
            namespace=namespace,
            status=FileStatus.UPLOAD_URL_CREATED,
            mime_type=mime_type,
            max_size=file_size,
        )

    def get(self, file_id: str) -> File:
        """
        Get a file by ID.

        Args:
            file_id: ID of the file

        Returns:
            File object

        Raises:
            NotFoundError: If file not found
            AuthenticationError: If authentication fails
        """
        response = self._http.get(f"/api/v1/files/{file_id}")
        return File.from_dict(response)

    def list_by_namespace(
        self,
        namespace: str,
        limit: int = 50,
        skip: int = 0,
    ) -> FileListResponse:
        """
        List files in a namespace.

        Args:
            namespace: Namespace to list files from
            limit: Maximum number of files to return
            skip: Number of files to skip (for pagination)

        Returns:
            FileListResponse with files and pagination info

        Raises:
            NotFoundError: If namespace not found
            AuthenticationError: If authentication fails
        """
        params = {"limit": limit, "skip": skip}
        response = self._http.get(f"/api/v1/files/namespace/{namespace}", params=params)
        return FileListResponse.from_dict(response)

    def update_status(
        self,
        file_id: str,
        status: FileStatus,
        uploaded_at: Optional[str] = None,
        processed_at: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> File:
        """
        Update file status.

        Args:
            file_id: ID of the file
            status: New status
            uploaded_at: Upload timestamp (ISO format)
            processed_at: Processing timestamp (ISO format)
            error_message: Error message if status is FAILED

        Returns:
            Updated File object

        Raises:
            NotFoundError: If file not found
            AuthenticationError: If authentication fails
            ForbiddenError: If user doesn't have READ_WRITE permission
        """
        data = {"status": status.value}
        if uploaded_at:
            data["uploadedAt"] = uploaded_at
        if processed_at:
            data["processedAt"] = processed_at
        if error_message:
            data["errorMessage"] = error_message

        response = self._http.patch(f"/api/v1/files/{file_id}/status", data)
        return File.from_dict(response)

    def delete(self, file_id: str) -> dict:
        """
        Delete a file.

        Args:
            file_id: ID of the file

        Returns:
            Response message

        Raises:
            NotFoundError: If file not found
            AuthenticationError: If authentication fails
            ForbiddenError: If user doesn't have READ_WRITE permission
        """
        return self._http.delete(f"/api/v1/files/{file_id}")


"""Documents API client."""

from typing import BinaryIO, Optional, Union
from pathlib import Path
import mimetypes
from .base import BaseAPI
from ..models import (
    DocumentResponse,
    DocumentExistsResponse,
    ListDocumentsResponse,
    DownloadDocumentResponse,
    DocumentFromUrlRequest,
)


class DocumentsAPI(BaseAPI):
    """Client for document operations."""
    
    def create(
        self,
        file: Union[str, Path, BinaryIO],
        ttl_seconds: Optional[int] = None,
        return_markdown: bool = False,
    ) -> DocumentResponse:
        """Upload a document.
        
        Args:
            file: File path or file-like object
            ttl_seconds: Time to live in seconds (300-21600)
            return_markdown: Whether to return markdown representation
            
        Returns:
            DocumentResponse with document metadata
        """
        # Handle file input
        if isinstance(file, (str, Path)):
            file_path = Path(file)
            with open(file_path, "rb") as f:
                file_content = f.read()
            filename = file_path.name
            # Guess content type from filename
            content_type, _ = mimetypes.guess_type(filename)
            if content_type is None:
                content_type = "application/octet-stream"
        else:
            file_content = file.read()
            filename = getattr(file, "name", "document")
            # Try to guess content type from filename if available
            content_type, _ = mimetypes.guess_type(filename)
            if content_type is None:
                content_type = "application/octet-stream"
        
        # Prepare form data with content type
        files = {"file": (filename, file_content, content_type)}
        data = {}
        if ttl_seconds is not None:
            data["ttl_seconds"] = ttl_seconds
        if return_markdown:
            data["return_markdown"] = return_markdown
        
        response = self._post("/v1/documents/", files=files, data=data)
        return DocumentResponse.from_dict(response)
    
    def create_from_url(self, request: DocumentFromUrlRequest) -> DocumentResponse:
        """Create a document from a URL.
        
        Args:
            request: DocumentFromUrlRequest with file URL and options
            
        Returns:
            DocumentResponse with document metadata
        """
        response = self._post("/v1/documents/url", json_data=request.to_dict())
        return DocumentResponse.from_dict(response)
    
    def list(self) -> ListDocumentsResponse:
        """List all documents.
        
        Returns:
            ListDocumentsResponse with list of documents
        """
        response = self._get("/v1/documents/")
        return ListDocumentsResponse.from_dict(response)
    
    def download(self, doc_id: str, expires_in: int = 3600) -> DownloadDocumentResponse:
        """Get presigned URL to download a document.
        
        Args:
            doc_id: Document ID
            expires_in: URL expiration time in seconds (1-86400)
            
        Returns:
            DownloadDocumentResponse with download URL
        """
        params = {"expiresIn": expires_in}
        response = self._get(f"/v1/documents/{doc_id}", params=params)
        return DownloadDocumentResponse.from_dict(response)
    
    def exists(self, doc_id: str) -> DocumentExistsResponse:
        """Check if a document exists.
        
        Args:
            doc_id: Document ID
            
        Returns:
            DocumentExistsResponse with existence check result
        """
        response = self._get(f"/v1/documents/{doc_id}/exists")
        return DocumentExistsResponse.from_dict(response)


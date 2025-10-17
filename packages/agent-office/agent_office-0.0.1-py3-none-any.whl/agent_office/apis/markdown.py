"""Markdown API client."""

from .base import BaseAPI
from ..models import MarkdownReadRequest, MarkdownReadResponse


class MarkdownAPI(BaseAPI):
    """Client for markdown operations."""
    
    def read(self, doc_id: str, request: MarkdownReadRequest) -> MarkdownReadResponse:
        """Read document as markdown.
        
        Args:
            doc_id: Document ID
            request: MarkdownReadRequest with read UID
            
        Returns:
            MarkdownReadResponse with markdown content
        """
        response = self._post(
            f"/v1/documents/{doc_id}/markdown",
            json_data=request.to_dict()
        )
        return MarkdownReadResponse.from_dict(response)


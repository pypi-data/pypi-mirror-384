"""Edits API client."""

from .base import BaseAPI
from ..models import EditRequest, EditResponse


class EditsAPI(BaseAPI):
    """Client for document edit operations."""
    
    def edit(self, doc_id: str, request: EditRequest) -> EditResponse:
        """Edit a document.
        
        Args:
            doc_id: Document ID
            request: EditRequest with edit instructions
            
        Returns:
            EditResponse with edit result
        """
        response = self._post(
            f"/v1/documents/{doc_id}/edits",
            json_data=request.to_dict()
        )
        return EditResponse.from_dict(response)


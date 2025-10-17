"""Edit-related data models."""

from typing import Optional
from dataclasses import dataclass


@dataclass
class EditRequest:
    """Request to edit a document."""
    
    edit_uid: str
    edit_instructions: str
    lookup_text: Optional[str] = None
    tracked_changes: bool = False
    use_large_model: bool = False
    
    def to_dict(self) -> dict:
        """Convert to API request dict."""
        return {
            "editUid": self.edit_uid,
            "editInstructions": self.edit_instructions,
            "lookupText": self.lookup_text,
            "trackedChanges": self.tracked_changes,
            "useLargeModel": self.use_large_model,
        }


@dataclass
class EditResponse:
    """Response from document edit."""
    
    edit_uid: str
    edit_applied: bool
    time_to_edit: float
    document_name: str
    document_id: str
    
    @classmethod
    def from_dict(cls, data: dict) -> "EditResponse":
        """Create instance from API response dict."""
        return cls(
            edit_uid=data["editUid"],
            edit_applied=data["editApplied"],
            time_to_edit=data["timeToEdit"],
            document_name=data["documentName"],
            document_id=data["documentId"],
        )


"""Markdown-related data models."""

from dataclasses import dataclass


@dataclass
class MarkdownReadRequest:
    """Request to read document as markdown."""
    
    read_uid: str
    
    def to_dict(self) -> dict:
        """Convert to API request dict."""
        return {"readUid": self.read_uid}


@dataclass
class MarkdownReadResponse:
    """Response from markdown read."""
    
    read_uid: str
    markdown: str
    time_to_generate: float
    document_name: str
    document_id: str
    
    @classmethod
    def from_dict(cls, data: dict) -> "MarkdownReadResponse":
        """Create instance from API response dict."""
        return cls(
            read_uid=data["readUid"],
            markdown=data["markdown"],
            time_to_generate=data["timeToGenerate"],
            document_name=data["documentName"],
            document_id=data["documentId"],
        )


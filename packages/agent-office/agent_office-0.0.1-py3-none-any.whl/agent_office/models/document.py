"""Document-related data models."""

from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class ImageAnnotation:
    """Image annotation with caption."""
    
    image_id: str
    caption: str
    source: str  # 'generated' or 'existing'


@dataclass
class DocumentResponse:
    """Response from document creation."""
    
    doc_id: str
    name: str
    created_at: datetime
    file_type: Optional[str] = None
    image_annotations: Optional[List[ImageAnnotation]] = None
    markdown: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> "DocumentResponse":
        """Create instance from API response dict."""
        image_annotations = None
        if data.get("imageAnnotations"):
            image_annotations = [
                ImageAnnotation(**ann) for ann in data["imageAnnotations"]
            ]
        
        return cls(
            doc_id=data["docId"],
            name=data["name"],
            created_at=datetime.fromisoformat(data["createdAt"].replace("Z", "+00:00")),
            file_type=data.get("fileType"),
            image_annotations=image_annotations,
            markdown=data.get("markdown"),
        )


@dataclass
class DocumentInfo:
    """Document metadata."""
    
    doc_id: str
    name: str
    size: int
    created_at: datetime
    updated_at: datetime
    content_type: str
    image_annotations: Optional[List[ImageAnnotation]] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> "DocumentInfo":
        """Create instance from API response dict."""
        image_annotations = None
        if data.get("imageAnnotations"):
            image_annotations = [
                ImageAnnotation(**ann) for ann in data["imageAnnotations"]
            ]
        
        return cls(
            doc_id=data["docId"],
            name=data["name"],
            size=data["size"],
            created_at=datetime.fromisoformat(data["createdAt"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(data["updatedAt"].replace("Z", "+00:00")),
            content_type=data["contentType"],
            image_annotations=image_annotations,
        )


@dataclass
class DocumentExistsResponse:
    """Response for document exists check."""
    
    exists: bool
    document: Optional[DocumentInfo] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> "DocumentExistsResponse":
        """Create instance from API response dict."""
        document = None
        if data.get("document"):
            document = DocumentInfo.from_dict(data["document"])
        
        return cls(
            exists=data["exists"],
            document=document,
        )


@dataclass
class ListDocumentsResponse:
    """Response for list documents."""
    
    documents: List[DocumentInfo]
    total_count: int
    
    @classmethod
    def from_dict(cls, data: dict) -> "ListDocumentsResponse":
        """Create instance from API response dict."""
        documents = [DocumentInfo.from_dict(doc) for doc in data["documents"]]
        return cls(
            documents=documents,
            total_count=data["totalCount"],
        )


@dataclass
class DownloadDocumentResponse:
    """Response for document download request."""
    
    doc_id: str
    download_url: str
    expires_in: int
    filename: str
    
    @classmethod
    def from_dict(cls, data: dict) -> "DownloadDocumentResponse":
        """Create instance from API response dict."""
        return cls(
            doc_id=data["docId"],
            download_url=data["downloadUrl"],
            expires_in=data["expiresIn"],
            filename=data["filename"],
        )


@dataclass
class DocumentFromUrlRequest:
    """Request to create document from URL."""
    
    file_url: str
    ttl_seconds: Optional[int] = None
    
    def to_dict(self) -> dict:
        """Convert to API request dict."""
        result = {"fileUrl": self.file_url}
        if self.ttl_seconds is not None:
            result["ttlSeconds"] = self.ttl_seconds
        return result


"""Main Agent Office client."""

from typing import BinaryIO, Optional, Union
from pathlib import Path
from uuid import uuid4

from .apis import DocumentsAPI, EditsAPI, MarkdownAPI
from .models import (
    DocumentResponse,
    DocumentExistsResponse,
    ListDocumentsResponse,
    DownloadDocumentResponse,
    DocumentFromUrlRequest,
    EditRequest,
    EditResponse,
    MarkdownReadRequest,
    MarkdownReadResponse,
)


class AgentOffice:
    """Main client for Agent Office API.
    
    Example:
        >>> from agent_office import AgentOffice
        >>> client = AgentOffice(api_key="sk_ao_your_api_key")
        >>> 
        >>> # Upload a document
        >>> doc = client.documents.create("document.docx", return_markdown=True)
        >>> print(f"Uploaded: {doc.doc_id}")
        >>> 
        >>> # Edit the document
        >>> edit = client.edit(
        ...     doc_id=doc.doc_id,
        ...     edit_uid=str(uuid4()),
        ...     edit_instructions="Change the title to 'My New Title'"
        ... )
        >>> print(f"Edit applied: {edit.edit_applied}")
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.agentoffice.dev",
        timeout: int = 60,
    ):
        """Initialize Agent Office client.
        
        Args:
            api_key: Your API key (get one at https://agentoffice.dev)
            base_url: Base URL for the API (default: https://api.agentoffice.dev)
            timeout: Request timeout in seconds (default: 60)
        """
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        
        # Initialize API clients
        self._documents_api = DocumentsAPI(base_url, api_key, timeout)
        self._edits_api = EditsAPI(base_url, api_key, timeout)
        self._markdown_api = MarkdownAPI(base_url, api_key, timeout)
    
    @property
    def documents(self) -> "DocumentsNamespace":
        """Access document operations."""
        return DocumentsNamespace(self._documents_api)
    
    def edit(
        self,
        doc_id: str,
        edit_uid: str,
        edit_instructions: str,
        lookup_text: Optional[str] = None,
        tracked_changes: bool = False,
        use_large_model: bool = False,
    ) -> EditResponse:
        """Edit a document.
        
        Args:
            doc_id: Document ID
            edit_uid: Unique identifier for this edit (for idempotency)
            edit_instructions: Natural language edit instructions
            lookup_text: Text to locate the edit position (for longer documents)
            tracked_changes: Enable track changes
            use_large_model: Use larger AI model for more complex edits
            
        Returns:
            EditResponse with edit result
            
        Example:
            >>> edit = client.edit(
            ...     doc_id="doc123",
            ...     edit_uid=str(uuid4()),
            ...     edit_instructions="Change the title to 'My New Title'"
            ... )
        """
        request = EditRequest(
            edit_uid=edit_uid,
            edit_instructions=edit_instructions,
            lookup_text=lookup_text,
            tracked_changes=tracked_changes,
            use_large_model=use_large_model,
        )
        return self._edits_api.edit(doc_id, request)
    
    def read(self, doc_id: str, read_uid: Optional[str] = None) -> MarkdownReadResponse:
        """Read document as markdown.
        
        Args:
            doc_id: Document ID
            read_uid: Unique identifier for this read (auto-generated if not provided)
            
        Returns:
            MarkdownReadResponse with markdown content
            
        Example:
            >>> result = client.read(doc_id="doc123")
            >>> print(result.markdown)
        """
        if read_uid is None:
            read_uid = str(uuid4())
        
        request = MarkdownReadRequest(read_uid=read_uid)
        return self._markdown_api.read(doc_id, request)


class DocumentsNamespace:
    """Namespace for document operations."""
    
    def __init__(self, api: DocumentsAPI):
        """Initialize documents namespace.
        
        Args:
            api: DocumentsAPI instance
        """
        self._api = api
    
    def create(
        self,
        file: Union[str, Path, BinaryIO],
        ttl_seconds: Optional[int] = None,
        return_markdown: bool = False,
    ) -> DocumentResponse:
        """Upload a document.
        
        Args:
            file: File path or file-like object
            ttl_seconds: Time to live in seconds (300-21600, i.e., 5 minutes to 6 hours)
            return_markdown: Whether to return markdown representation
            
        Returns:
            DocumentResponse with document metadata
            
        Example:
            >>> doc = client.documents.create("document.docx", return_markdown=True)
            >>> print(f"Document ID: {doc.doc_id}")
        """
        return self._api.create(file, ttl_seconds, return_markdown)
    
    def create_from_url(
        self,
        file_url: str,
        ttl_seconds: Optional[int] = None,
    ) -> DocumentResponse:
        """Create a document from a URL.
        
        Args:
            file_url: URL of the file to download and process
            ttl_seconds: Time to live in seconds (300-21600)
            
        Returns:
            DocumentResponse with document metadata
            
        Example:
            >>> doc = client.documents.create_from_url(
            ...     "https://example.com/document.docx"
            ... )
        """
        request = DocumentFromUrlRequest(file_url=file_url, ttl_seconds=ttl_seconds)
        return self._api.create_from_url(request)
    
    # DISABLED: Endpoint removed due to security issues
    # def list(self) -> ListDocumentsResponse:
    #     """List all documents.
    #     
    #     Returns:
    #         ListDocumentsResponse with list of documents
    #         
    #     Example:
    #         >>> docs = client.documents.list()
    #         >>> for doc in docs.documents:
    #         ...     print(f"{doc.name}: {doc.doc_id}")
    #     """
    #     return self._api.list()
    
    def download(self, doc_id: str, expires_in: int = 3600) -> DownloadDocumentResponse:
        """Get presigned URL to download a document.
        
        Args:
            doc_id: Document ID
            expires_in: URL expiration time in seconds (1-86400)
            
        Returns:
            DownloadDocumentResponse with download URL
            
        Example:
            >>> result = client.documents.download(doc_id="doc123")
            >>> print(f"Download URL: {result.download_url}")
        """
        return self._api.download(doc_id, expires_in)
    
    def exists(self, doc_id: str) -> DocumentExistsResponse:
        """Check if a document exists.
        
        Args:
            doc_id: Document ID
            
        Returns:
            DocumentExistsResponse with existence check result
            
        Example:
            >>> result = client.documents.exists(doc_id="doc123")
            >>> if result.exists:
            ...     print(f"Document exists: {result.document.name}")
        """
        return self._api.exists(doc_id)


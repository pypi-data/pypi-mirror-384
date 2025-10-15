"""documents resource module."""

from .client import DocumentsClient
from .models import Document, CreateDocumentRequest, UpdateDocumentRequest

__all__ = ["DocumentsClient", "Document", "CreateDocumentRequest", "UpdateDocumentRequest"]

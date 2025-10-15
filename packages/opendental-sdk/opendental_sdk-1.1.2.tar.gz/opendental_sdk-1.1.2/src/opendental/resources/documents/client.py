"""documents client for Open Dental SDK."""

from typing import List, Optional, Union
from ...base.resource import BaseResource
from .models import (
    Document,
    CreateDocumentRequest,
    UpdateDocumentRequest,
    DocumentListResponse,
    DocumentSearchRequest
)


class DocumentsClient(BaseResource):
    """Client for managing documents in Open Dental."""
    
    def __init__(self, client):
        """Initialize the documents client."""
        super().__init__(client, "documents")
    
    def get(self, item_id: Union[int, str]) -> Document:
        """Get a document by ID."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._get(endpoint)
        return self._handle_response(response, Document)
    
    def list(self, page: int = 1, per_page: int = 50) -> DocumentListResponse:
        """List all documents."""
        params = {"page": page, "per_page": per_page}
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return DocumentListResponse(**response)
        elif isinstance(response, list):
            return DocumentListResponse(
                documents=[Document(**item) for item in response],
                total=len(response), page=page, per_page=per_page
            )
        return DocumentListResponse(documents=[], total=0, page=page, per_page=per_page)
    
    def create(self, item_data: CreateDocumentRequest) -> Document:
        """Create a new document."""
        endpoint = self._build_endpoint()
        data = item_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, Document)
    
    def update(self, item_id: Union[int, str], item_data: UpdateDocumentRequest) -> Document:
        """Update an existing document."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        data = item_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, Document)
    
    def delete(self, item_id: Union[int, str]) -> bool:
        """Delete a document."""
        item_id = self._validate_id(item_id)
        endpoint = self._build_endpoint(item_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: DocumentSearchRequest) -> DocumentListResponse:
        """Search for documents."""
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return DocumentListResponse(**response)
        elif isinstance(response, list):
            return DocumentListResponse(
                documents=[Document(**item) for item in response],
                total=len(response), page=search_params.page, per_page=search_params.per_page
            )
        return DocumentListResponse(
            documents=[], total=0, page=search_params.page, per_page=search_params.per_page
        )

"""Auto notes client for Open Dental SDK."""

from typing import List, Optional, Union
from ...base.resource import BaseResource
from .models import (
    AutoNote,
    CreateAutoNoteRequest,
    UpdateAutoNoteRequest,
    AutoNoteListResponse,
    AutoNoteSearchRequest
)


class AutoNotesClient(BaseResource):
    """Client for managing auto notes in Open Dental."""
    
    def __init__(self, client):
        """Initialize the auto notes client."""
        super().__init__(client, "auto_notes")
    
    def get(self, note_id: Union[int, str]) -> AutoNote:
        """
        Get an auto note by ID.
        
        Args:
            note_id: The auto note ID
            
        Returns:
            AutoNote: The auto note object
        """
        note_id = self._validate_id(note_id)
        endpoint = self._build_endpoint(note_id)
        response = self._get(endpoint)
        return self._handle_response(response, AutoNote)
    
    def list(self, page: int = 1, per_page: int = 50) -> AutoNoteListResponse:
        """
        List all auto notes.
        
        Args:
            page: Page number (default: 1)
            per_page: Items per page (default: 50)
            
        Returns:
            AutoNoteListResponse: List of auto notes with pagination info
        """
        params = {
            "page": page,
            "per_page": per_page
        }
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return AutoNoteListResponse(**response)
        elif isinstance(response, list):
            return AutoNoteListResponse(
                auto_notes=[AutoNote(**item) for item in response],
                total=len(response),
                page=page,
                per_page=per_page
            )
        else:
            return AutoNoteListResponse(auto_notes=[], total=0, page=page, per_page=per_page)
    
    def create(self, note_data: CreateAutoNoteRequest) -> AutoNote:
        """
        Create a new auto note.
        
        Args:
            note_data: The auto note data to create
            
        Returns:
            AutoNote: The created auto note object
        """
        endpoint = self._build_endpoint()
        data = note_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, AutoNote)
    
    def update(self, note_id: Union[int, str], note_data: UpdateAutoNoteRequest) -> AutoNote:
        """
        Update an existing auto note.
        
        Args:
            note_id: The auto note ID
            note_data: The auto note data to update
            
        Returns:
            AutoNote: The updated auto note object
        """
        note_id = self._validate_id(note_id)
        endpoint = self._build_endpoint(note_id)
        data = note_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, AutoNote)
    
    def delete(self, note_id: Union[int, str]) -> bool:
        """
        Delete an auto note.
        
        Args:
            note_id: The auto note ID
            
        Returns:
            bool: True if deletion was successful
        """
        note_id = self._validate_id(note_id)
        endpoint = self._build_endpoint(note_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: AutoNoteSearchRequest) -> AutoNoteListResponse:
        """
        Search for auto notes.
        
        Args:
            search_params: Search parameters
            
        Returns:
            AutoNoteListResponse: List of matching auto notes
        """
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return AutoNoteListResponse(**response)
        elif isinstance(response, list):
            return AutoNoteListResponse(
                auto_notes=[AutoNote(**item) for item in response],
                total=len(response),
                page=search_params.page,
                per_page=search_params.per_page
            )
        else:
            return AutoNoteListResponse(
                auto_notes=[], 
                total=0, 
                page=search_params.page, 
                per_page=search_params.per_page
            )
    
    def get_by_category(self, category: str) -> List[AutoNote]:
        """
        Get auto notes by category.
        
        Args:
            category: Category to search for
            
        Returns:
            List[AutoNote]: List of matching auto notes
        """
        search_params = AutoNoteSearchRequest(category=category)
        result = self.search(search_params)
        return result.auto_notes
    
    def search_text(self, text: str) -> List[AutoNote]:
        """
        Search auto notes by text content.
        
        Args:
            text: Text to search for
            
        Returns:
            List[AutoNote]: List of matching auto notes
        """
        search_params = AutoNoteSearchRequest(text_search=text)
        result = self.search(search_params)
        return result.auto_notes
    
    def get_active_notes(self) -> List[AutoNote]:
        """
        Get all active auto notes.
        
        Returns:
            List[AutoNote]: List of active auto notes
        """
        search_params = AutoNoteSearchRequest(is_active=True)
        result = self.search(search_params)
        return result.auto_notes
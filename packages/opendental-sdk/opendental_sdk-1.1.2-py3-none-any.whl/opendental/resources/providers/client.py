"""Providers client for Open Dental SDK."""

from typing import List, Optional, Union
from ...base.resource import BaseResource
from .models import (
    Provider,
    CreateProviderRequest,
    UpdateProviderRequest,
    ProviderListResponse,
    ProviderSearchRequest
)


class ProvidersClient(BaseResource):
    """Client for managing providers in Open Dental."""
    
    def __init__(self, client):
        """Initialize the providers client."""
        super().__init__(client, "providers")
    
    def get(self, provider_id: Union[int, str]) -> Provider:
        """
        Get a provider by ID.
        
        Args:
            provider_id: The provider ID
            
        Returns:
            Provider: The provider object
        """
        provider_id = self._validate_id(provider_id)
        endpoint = self._build_endpoint(provider_id)
        response = self._get(endpoint)
        return self._handle_response(response, Provider)
    
    def list(self, page: int = 1, per_page: int = 50) -> ProviderListResponse:
        """
        List all providers.
        
        Args:
            page: Page number (default: 1)
            per_page: Items per page (default: 50)
            
        Returns:
            ProviderListResponse: List of providers with pagination info
        """
        params = {
            "page": page,
            "per_page": per_page
        }
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return ProviderListResponse(**response)
        elif isinstance(response, list):
            return ProviderListResponse(
                providers=[Provider(**item) for item in response],
                total=len(response),
                page=page,
                per_page=per_page
            )
        else:
            return ProviderListResponse(providers=[], total=0, page=page, per_page=per_page)
    
    def create(self, provider_data: CreateProviderRequest) -> Provider:
        """
        Create a new provider.
        
        Args:
            provider_data: The provider data to create
            
        Returns:
            Provider: The created provider object
        """
        endpoint = self._build_endpoint()
        data = provider_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, Provider)
    
    def update(self, provider_id: Union[int, str], provider_data: UpdateProviderRequest) -> Provider:
        """
        Update an existing provider.
        
        Args:
            provider_id: The provider ID
            provider_data: The provider data to update
            
        Returns:
            Provider: The updated provider object
        """
        provider_id = self._validate_id(provider_id)
        endpoint = self._build_endpoint(provider_id)
        data = provider_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, Provider)
    
    def delete(self, provider_id: Union[int, str]) -> bool:
        """
        Delete a provider.
        
        Args:
            provider_id: The provider ID
            
        Returns:
            bool: True if deletion was successful
        """
        provider_id = self._validate_id(provider_id)
        endpoint = self._build_endpoint(provider_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: ProviderSearchRequest) -> ProviderListResponse:
        """
        Search for providers.
        
        Args:
            search_params: Search parameters
            
        Returns:
            ProviderListResponse: List of matching providers
        """
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return ProviderListResponse(**response)
        elif isinstance(response, list):
            return ProviderListResponse(
                providers=[Provider(**item) for item in response],
                total=len(response),
                page=search_params.page,
                per_page=search_params.per_page
            )
        else:
            return ProviderListResponse(
                providers=[], 
                total=0, 
                page=search_params.page, 
                per_page=search_params.per_page
            )
    
    def get_active(self) -> List[Provider]:
        """
        Get all active providers.
        
        Returns:
            List[Provider]: List of active providers
        """
        search_params = ProviderSearchRequest(is_active=True)
        result = self.search(search_params)
        return result.providers
    
    def get_dentists(self) -> List[Provider]:
        """
        Get all dentist providers.
        
        Returns:
            List[Provider]: List of dentist providers
        """
        search_params = ProviderSearchRequest(is_dentist=True)
        result = self.search(search_params)
        return result.providers
    
    def get_hygienists(self) -> List[Provider]:
        """
        Get all hygienist providers.
        
        Returns:
            List[Provider]: List of hygienist providers
        """
        search_params = ProviderSearchRequest(is_hygienist=True)
        result = self.search(search_params)
        return result.providers
    
    def get_by_specialty(self, specialty: str) -> List[Provider]:
        """
        Get providers by specialty.
        
        Args:
            specialty: Provider specialty
            
        Returns:
            List[Provider]: List of providers with the specified specialty
        """
        search_params = ProviderSearchRequest(specialty=specialty)
        result = self.search(search_params)
        return result.providers
    
    def get_by_abbreviation(self, abbreviation: str) -> Optional[Provider]:
        """
        Get a provider by abbreviation.
        
        Args:
            abbreviation: Provider abbreviation
            
        Returns:
            Optional[Provider]: Provider with the specified abbreviation
        """
        search_params = ProviderSearchRequest(abbreviation=abbreviation)
        result = self.search(search_params)
        return result.providers[0] if result.providers else None
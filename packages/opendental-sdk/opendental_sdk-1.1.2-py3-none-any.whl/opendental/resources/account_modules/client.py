"""Account modules client for Open Dental SDK."""

from typing import List, Optional, Union
from ...base.resource import BaseResource
from .models import (
    AccountModule,
    CreateAccountModuleRequest,
    UpdateAccountModuleRequest,
    AccountModuleListResponse,
    AccountModuleSearchRequest
)


class AccountModulesClient(BaseResource):
    """Client for managing account modules in Open Dental."""
    
    def __init__(self, client):
        """Initialize the account modules client."""
        super().__init__(client, "account_modules")
    
    def get(self, module_id: Union[int, str]) -> AccountModule:
        """
        Get an account module by ID.
        
        Args:
            module_id: The account module ID
            
        Returns:
            AccountModule: The account module object
        """
        module_id = self._validate_id(module_id)
        endpoint = self._build_endpoint(module_id)
        response = self._get(endpoint)
        return self._handle_response(response, AccountModule)
    
    def list(self, page: int = 1, per_page: int = 50) -> AccountModuleListResponse:
        """
        List all account modules.
        
        Args:
            page: Page number (default: 1)
            per_page: Items per page (default: 50)
            
        Returns:
            AccountModuleListResponse: List of account modules with pagination info
        """
        params = {
            "page": page,
            "per_page": per_page
        }
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return AccountModuleListResponse(**response)
        elif isinstance(response, list):
            return AccountModuleListResponse(
                account_modules=[AccountModule(**item) for item in response],
                total=len(response),
                page=page,
                per_page=per_page
            )
        else:
            return AccountModuleListResponse(account_modules=[], total=0, page=page, per_page=per_page)
    
    def create(self, module_data: CreateAccountModuleRequest) -> AccountModule:
        """
        Create a new account module.
        
        Args:
            module_data: The account module data to create
            
        Returns:
            AccountModule: The created account module object
        """
        endpoint = self._build_endpoint()
        data = module_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, AccountModule)
    
    def update(self, module_id: Union[int, str], module_data: UpdateAccountModuleRequest) -> AccountModule:
        """
        Update an existing account module.
        
        Args:
            module_id: The account module ID
            module_data: The account module data to update
            
        Returns:
            AccountModule: The updated account module object
        """
        module_id = self._validate_id(module_id)
        endpoint = self._build_endpoint(module_id)
        data = module_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, AccountModule)
    
    def delete(self, module_id: Union[int, str]) -> bool:
        """
        Delete an account module.
        
        Args:
            module_id: The account module ID
            
        Returns:
            bool: True if deletion was successful
        """
        module_id = self._validate_id(module_id)
        endpoint = self._build_endpoint(module_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: AccountModuleSearchRequest) -> AccountModuleListResponse:
        """
        Search for account modules.
        
        Args:
            search_params: Search parameters
            
        Returns:
            AccountModuleListResponse: List of matching account modules
        """
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return AccountModuleListResponse(**response)
        elif isinstance(response, list):
            return AccountModuleListResponse(
                account_modules=[AccountModule(**item) for item in response],
                total=len(response),
                page=search_params.page,
                per_page=search_params.per_page
            )
        else:
            return AccountModuleListResponse(
                account_modules=[], 
                total=0, 
                page=search_params.page, 
                per_page=search_params.per_page
            )
    
    def get_enabled_modules(self) -> List[AccountModule]:
        """
        Get all enabled account modules.
        
        Returns:
            List[AccountModule]: List of enabled modules
        """
        search_params = AccountModuleSearchRequest(is_enabled=True)
        result = self.search(search_params)
        return result.account_modules
    
    def get_required_modules(self) -> List[AccountModule]:
        """
        Get all required account modules.
        
        Returns:
            List[AccountModule]: List of required modules
        """
        search_params = AccountModuleSearchRequest(is_required=True)
        result = self.search(search_params)
        return result.account_modules
    
    def get_by_name(self, module_name: str) -> List[AccountModule]:
        """
        Get account modules by name.
        
        Args:
            module_name: Module name to search for
            
        Returns:
            List[AccountModule]: List of matching modules
        """
        search_params = AccountModuleSearchRequest(module_name=module_name)
        result = self.search(search_params)
        return result.account_modules
"""Users client for Open Dental SDK."""

from typing import List, Optional, Union
from ...base.resource import BaseResource
from .models import (
    User,
    CreateUserRequest,
    UpdateUserRequest,
    UserListResponse,
    UserSearchRequest
)


class UsersClient(BaseResource):
    """Client for managing users in Open Dental."""
    
    def __init__(self, client):
        """Initialize the users client."""
        super().__init__(client, "users")
    
    def get(self, user_id: Union[int, str]) -> User:
        """
        Get a user by ID.
        
        Args:
            user_id: The user ID
            
        Returns:
            User: The user object
        """
        user_id = self._validate_id(user_id)
        endpoint = self._build_endpoint(user_id)
        response = self._get(endpoint)
        return self._handle_response(response, User)
    
    def list(self, page: int = 1, per_page: int = 50) -> UserListResponse:
        """
        List all users.
        
        Args:
            page: Page number (default: 1)
            per_page: Items per page (default: 50)
            
        Returns:
            UserListResponse: List of users with pagination info
        """
        params = {
            "page": page,
            "per_page": per_page
        }
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return UserListResponse(**response)
        elif isinstance(response, list):
            return UserListResponse(
                users=[User(**item) for item in response],
                total=len(response),
                page=page,
                per_page=per_page
            )
        else:
            return UserListResponse(users=[], total=0, page=page, per_page=per_page)
    
    def create(self, user_data: CreateUserRequest) -> User:
        """
        Create a new user.
        
        Args:
            user_data: The user data to create
            
        Returns:
            User: The created user object
        """
        endpoint = self._build_endpoint()
        data = user_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, User)
    
    def update(self, user_id: Union[int, str], user_data: UpdateUserRequest) -> User:
        """
        Update an existing user.
        
        Args:
            user_id: The user ID
            user_data: The user data to update
            
        Returns:
            User: The updated user object
        """
        user_id = self._validate_id(user_id)
        endpoint = self._build_endpoint(user_id)
        data = user_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, User)
    
    def delete(self, user_id: Union[int, str]) -> bool:
        """
        Delete a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            bool: True if deletion was successful
        """
        user_id = self._validate_id(user_id)
        endpoint = self._build_endpoint(user_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: UserSearchRequest) -> UserListResponse:
        """
        Search for users.
        
        Args:
            search_params: Search parameters
            
        Returns:
            UserListResponse: List of matching users
        """
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return UserListResponse(**response)
        elif isinstance(response, list):
            return UserListResponse(
                users=[User(**item) for item in response],
                total=len(response),
                page=search_params.page,
                per_page=search_params.per_page
            )
        else:
            return UserListResponse(
                users=[], 
                total=0, 
                page=search_params.page, 
                per_page=search_params.per_page
            )
    
    def get_by_username(self, user_name: str) -> Optional[User]:
        """
        Get a user by username.
        
        Args:
            user_name: Username to search for
            
        Returns:
            Optional[User]: The user object if found, None otherwise
        """
        search_params = UserSearchRequest(user_name=user_name)
        result = self.search(search_params)
        return result.users[0] if result.users else None
    
    def get_by_employee(self, employee_num: int) -> Optional[User]:
        """
        Get a user by employee number.
        
        Args:
            employee_num: Employee number
            
        Returns:
            Optional[User]: The user object if found, None otherwise
        """
        search_params = UserSearchRequest(employee_num=employee_num)
        result = self.search(search_params)
        return result.users[0] if result.users else None
    
    def get_by_provider(self, prov_num: int) -> Optional[User]:
        """
        Get a user by provider number.
        
        Args:
            prov_num: Provider number
            
        Returns:
            Optional[User]: The user object if found, None otherwise
        """
        search_params = UserSearchRequest(prov_num=prov_num)
        result = self.search(search_params)
        return result.users[0] if result.users else None
    
    def get_by_clinic(self, clinic_num: int) -> List[User]:
        """
        Get users by clinic.
        
        Args:
            clinic_num: Clinic number
            
        Returns:
            List[User]: List of users in the clinic
        """
        search_params = UserSearchRequest(clinic_num=clinic_num)
        result = self.search(search_params)
        return result.users
    
    def get_active(self) -> List[User]:
        """
        Get all active (non-hidden) users.
        
        Returns:
            List[User]: List of active users
        """
        search_params = UserSearchRequest(is_hidden=False)
        result = self.search(search_params)
        return result.users
    
    def get_locked(self) -> List[User]:
        """
        Get all locked users.
        
        Returns:
            List[User]: List of locked users
        """
        search_params = UserSearchRequest(is_locked=True)
        result = self.search(search_params)
        return result.users
    
    def lock_user(self, user_id: Union[int, str]) -> User:
        """
        Lock a user account.
        
        Args:
            user_id: The user ID
            
        Returns:
            User: The updated user object
        """
        update_data = UpdateUserRequest(is_locked=True)
        return self.update(user_id, update_data)
    
    def unlock_user(self, user_id: Union[int, str]) -> User:
        """
        Unlock a user account.
        
        Args:
            user_id: The user ID
            
        Returns:
            User: The updated user object
        """
        update_data = UpdateUserRequest(is_locked=False, failed_attempts=0)
        return self.update(user_id, update_data)
    
    def hide_user(self, user_id: Union[int, str]) -> User:
        """
        Hide a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            User: The updated user object
        """
        update_data = UpdateUserRequest(is_hidden=True)
        return self.update(user_id, update_data)
    
    def unhide_user(self, user_id: Union[int, str]) -> User:
        """
        Unhide a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            User: The updated user object
        """
        update_data = UpdateUserRequest(is_hidden=False)
        return self.update(user_id, update_data)
    
    def reset_password(self, user_id: Union[int, str], new_password_hash: str) -> User:
        """
        Reset a user's password.
        
        Args:
            user_id: The user ID
            new_password_hash: New password hash
            
        Returns:
            User: The updated user object
        """
        update_data = UpdateUserRequest(
            password_hash=new_password_hash,
            failed_attempts=0,
            is_locked=False
        )
        return self.update(user_id, update_data)
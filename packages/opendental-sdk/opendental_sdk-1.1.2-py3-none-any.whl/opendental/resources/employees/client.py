"""Employees client for Open Dental SDK."""

from typing import List, Optional, Union
from ...base.resource import BaseResource
from .models import (
    Employee,
    CreateEmployeeRequest,
    UpdateEmployeeRequest,
    EmployeeListResponse,
    EmployeeSearchRequest
)


class EmployeesClient(BaseResource):
    """Client for managing employees in Open Dental."""
    
    def __init__(self, client):
        """Initialize the employees client."""
        super().__init__(client, "employees")
    
    def get(self, employee_id: Union[int, str]) -> Employee:
        """
        Get an employee by ID.
        
        Args:
            employee_id: The employee ID
            
        Returns:
            Employee: The employee object
        """
        employee_id = self._validate_id(employee_id)
        endpoint = self._build_endpoint(employee_id)
        response = self._get(endpoint)
        return self._handle_response(response, Employee)
    
    def list(self, page: int = 1, per_page: int = 50) -> EmployeeListResponse:
        """
        List all employees.
        
        Args:
            page: Page number (default: 1)
            per_page: Items per page (default: 50)
            
        Returns:
            EmployeeListResponse: List of employees with pagination info
        """
        params = {
            "page": page,
            "per_page": per_page
        }
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return EmployeeListResponse(**response)
        elif isinstance(response, list):
            return EmployeeListResponse(
                employees=[Employee(**item) for item in response],
                total=len(response),
                page=page,
                per_page=per_page
            )
        else:
            return EmployeeListResponse(employees=[], total=0, page=page, per_page=per_page)
    
    def create(self, employee_data: CreateEmployeeRequest) -> Employee:
        """
        Create a new employee.
        
        Args:
            employee_data: The employee data to create
            
        Returns:
            Employee: The created employee object
        """
        endpoint = self._build_endpoint()
        data = employee_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, Employee)
    
    def update(self, employee_id: Union[int, str], employee_data: UpdateEmployeeRequest) -> Employee:
        """
        Update an existing employee.
        
        Args:
            employee_id: The employee ID
            employee_data: The employee data to update
            
        Returns:
            Employee: The updated employee object
        """
        employee_id = self._validate_id(employee_id)
        endpoint = self._build_endpoint(employee_id)
        data = employee_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, Employee)
    
    def delete(self, employee_id: Union[int, str]) -> bool:
        """
        Delete an employee.
        
        Args:
            employee_id: The employee ID
            
        Returns:
            bool: True if deletion was successful
        """
        employee_id = self._validate_id(employee_id)
        endpoint = self._build_endpoint(employee_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: EmployeeSearchRequest) -> EmployeeListResponse:
        """
        Search for employees.
        
        Args:
            search_params: Search parameters
            
        Returns:
            EmployeeListResponse: List of matching employees
        """
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return EmployeeListResponse(**response)
        elif isinstance(response, list):
            return EmployeeListResponse(
                employees=[Employee(**item) for item in response],
                total=len(response),
                page=search_params.page,
                per_page=search_params.per_page
            )
        else:
            return EmployeeListResponse(
                employees=[], 
                total=0, 
                page=search_params.page, 
                per_page=search_params.per_page
            )
    
    def get_active(self) -> List[Employee]:
        """
        Get all active employees.
        
        Returns:
            List[Employee]: List of active employees
        """
        search_params = EmployeeSearchRequest(is_working=True, is_hidden=False)
        result = self.search(search_params)
        return result.employees
    
    def get_by_clinic(self, clinic_num: int) -> List[Employee]:
        """
        Get employees by clinic.
        
        Args:
            clinic_num: Clinic number
            
        Returns:
            List[Employee]: List of employees in the clinic
        """
        search_params = EmployeeSearchRequest(clinic_num=clinic_num)
        result = self.search(search_params)
        return result.employees
    
    def get_dentists(self) -> List[Employee]:
        """
        Get all dentist employees.
        
        Returns:
            List[Employee]: List of dentist employees
        """
        # This would need to be implemented with proper filtering
        # For now, get all active employees
        return self.get_active()
    
    def get_hygienists(self) -> List[Employee]:
        """
        Get all hygienist employees.
        
        Returns:
            List[Employee]: List of hygienist employees
        """
        # This would need to be implemented with proper filtering
        # For now, get all active employees
        return self.get_active()
    
    def terminate_employee(self, employee_id: Union[int, str]) -> Employee:
        """
        Terminate an employee.
        
        Args:
            employee_id: The employee ID
            
        Returns:
            Employee: The updated employee object
        """
        from datetime import date
        update_data = UpdateEmployeeRequest(
            is_working=False,
            date_terminated=date.today()
        )
        return self.update(employee_id, update_data)
"""Treatment Plans client for Open Dental SDK."""

from typing import List, Optional, Union
from ...base.resource import BaseResource
from .models import (
    TreatmentPlan,
    TreatmentPlanAttach,
    CreateTreatmentPlanRequest,
    UpdateTreatmentPlanRequest,
    TreatmentPlanListResponse,
    TreatmentPlanSearchRequest,
    AttachProcedureRequest
)


class TreatmentPlansClient(BaseResource):
    """Client for managing treatment plans in Open Dental."""
    
    def __init__(self, client):
        """Initialize the treatment plans client."""
        super().__init__(client, "treatment-plans")
    
    def get(self, tp_id: Union[int, str]) -> TreatmentPlan:
        """
        Get a treatment plan by ID.
        
        Args:
            tp_id: The treatment plan ID
            
        Returns:
            TreatmentPlan: The treatment plan object
        """
        tp_id = self._validate_id(tp_id)
        endpoint = self._build_endpoint(tp_id)
        response = self._get(endpoint)
        return self._handle_response(response, TreatmentPlan)
    
    def list(self, page: int = 1, per_page: int = 50) -> TreatmentPlanListResponse:
        """
        List all treatment plans.
        
        Args:
            page: Page number (default: 1)
            per_page: Items per page (default: 50)
            
        Returns:
            TreatmentPlanListResponse: List of treatment plans with pagination info
        """
        params = {
            "page": page,
            "per_page": per_page
        }
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return TreatmentPlanListResponse(**response)
        elif isinstance(response, list):
            return TreatmentPlanListResponse(
                treatment_plans=[TreatmentPlan(**item) for item in response],
                total=len(response),
                page=page,
                per_page=per_page
            )
        else:
            return TreatmentPlanListResponse(treatment_plans=[], total=0, page=page, per_page=per_page)
    
    def create(self, tp_data: CreateTreatmentPlanRequest) -> TreatmentPlan:
        """
        Create a new treatment plan.
        
        Args:
            tp_data: The treatment plan data to create
            
        Returns:
            TreatmentPlan: The created treatment plan object
        """
        endpoint = self._build_endpoint()
        data = tp_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, TreatmentPlan)
    
    def update(self, tp_id: Union[int, str], tp_data: UpdateTreatmentPlanRequest) -> TreatmentPlan:
        """
        Update an existing treatment plan.
        
        Args:
            tp_id: The treatment plan ID
            tp_data: The treatment plan data to update
            
        Returns:
            TreatmentPlan: The updated treatment plan object
        """
        tp_id = self._validate_id(tp_id)
        endpoint = self._build_endpoint(tp_id)
        data = tp_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, TreatmentPlan)
    
    def delete(self, tp_id: Union[int, str]) -> bool:
        """
        Delete a treatment plan.
        
        Args:
            tp_id: The treatment plan ID
            
        Returns:
            bool: True if deletion was successful
        """
        tp_id = self._validate_id(tp_id)
        endpoint = self._build_endpoint(tp_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: TreatmentPlanSearchRequest) -> TreatmentPlanListResponse:
        """
        Search for treatment plans.
        
        Args:
            search_params: Search parameters
            
        Returns:
            TreatmentPlanListResponse: List of matching treatment plans
        """
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return TreatmentPlanListResponse(**response)
        elif isinstance(response, list):
            return TreatmentPlanListResponse(
                treatment_plans=[TreatmentPlan(**item) for item in response],
                total=len(response),
                page=search_params.page,
                per_page=search_params.per_page
            )
        else:
            return TreatmentPlanListResponse(
                treatment_plans=[], 
                total=0, 
                page=search_params.page, 
                per_page=search_params.per_page
            )
    
    def get_by_patient(self, patient_id: Union[int, str]) -> List[TreatmentPlan]:
        """
        Get treatment plans for a specific patient.
        
        Args:
            patient_id: Patient ID
            
        Returns:
            List[TreatmentPlan]: List of treatment plans for the patient
        """
        patient_id = int(self._validate_id(patient_id))
        search_params = TreatmentPlanSearchRequest(patient_id=patient_id)
        result = self.search(search_params)
        return result.treatment_plans
    
    def get_by_provider(self, provider_id: Union[int, str]) -> List[TreatmentPlan]:
        """
        Get treatment plans for a specific provider.
        
        Args:
            provider_id: Provider ID
            
        Returns:
            List[TreatmentPlan]: List of treatment plans for the provider
        """
        provider_id = int(self._validate_id(provider_id))
        search_params = TreatmentPlanSearchRequest(provider_id=provider_id)
        result = self.search(search_params)
        return result.treatment_plans
    
    def get_by_status(self, status: str) -> List[TreatmentPlan]:
        """
        Get treatment plans by status.
        
        Args:
            status: Treatment plan status
            
        Returns:
            List[TreatmentPlan]: List of treatment plans with the specified status
        """
        search_params = TreatmentPlanSearchRequest(tp_status=status)
        result = self.search(search_params)
        return result.treatment_plans
    
    def get_active(self) -> List[TreatmentPlan]:
        """
        Get all active treatment plans.
        
        Returns:
            List[TreatmentPlan]: List of active treatment plans
        """
        return self.get_by_status("active")
    
    def attach_procedure(self, tp_id: Union[int, str], attach_data: AttachProcedureRequest) -> TreatmentPlanAttach:
        """
        Attach a procedure to a treatment plan.
        
        Args:
            tp_id: Treatment plan ID
            attach_data: Procedure attachment data
            
        Returns:
            TreatmentPlanAttach: The attachment object
        """
        tp_id = self._validate_id(tp_id)
        endpoint = self._build_endpoint(f"{tp_id}/attach")
        data = attach_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, TreatmentPlanAttach)
    
    def get_attachments(self, tp_id: Union[int, str]) -> List[TreatmentPlanAttach]:
        """
        Get procedure attachments for a treatment plan.
        
        Args:
            tp_id: Treatment plan ID
            
        Returns:
            List[TreatmentPlanAttach]: List of procedure attachments
        """
        tp_id = self._validate_id(tp_id)
        endpoint = self._build_endpoint(f"{tp_id}/attachments")
        response = self._get(endpoint)
        return self._handle_list_response(response, TreatmentPlanAttach)
    
    def sign(self, tp_id: Union[int, str], signature: str) -> TreatmentPlan:
        """
        Sign a treatment plan.
        
        Args:
            tp_id: Treatment plan ID
            signature: Digital signature
            
        Returns:
            TreatmentPlan: The signed treatment plan
        """
        from datetime import date
        update_data = UpdateTreatmentPlanRequest(
            signature=signature,
            sig_date=date.today()
        )
        return self.update(tp_id, update_data)
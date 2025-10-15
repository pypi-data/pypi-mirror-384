"""Claims client for Open Dental SDK."""

from datetime import date
from typing import List, Optional, Union
from decimal import Decimal
from ...base.resource import BaseResource
from .models import (
    Claim,
    CreateClaimRequest,
    UpdateClaimRequest,
    ClaimListResponse,
    ClaimSearchRequest,
    ClaimPayment,
    ClaimEOB
)


class ClaimsClient(BaseResource):
    """Client for managing claims in Open Dental."""
    
    def __init__(self, client):
        """Initialize the claims client."""
        super().__init__(client, "claims")
    
    def get(self, claim_id: Union[int, str]) -> Claim:
        """
        Get a claim by ID.
        
        Args:
            claim_id: The claim ID
            
        Returns:
            Claim: The claim object
        """
        claim_id = self._validate_id(claim_id)
        endpoint = self._build_endpoint(claim_id)
        response = self._get(endpoint)
        return self._handle_response(response, Claim)
    
    def list(self, page: int = 1, per_page: int = 50) -> ClaimListResponse:
        """
        List all claims.
        
        Args:
            page: Page number (default: 1)
            per_page: Items per page (default: 50)
            
        Returns:
            ClaimListResponse: List of claims with pagination info
        """
        params = {
            "page": page,
            "per_page": per_page
        }
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return ClaimListResponse(**response)
        elif isinstance(response, list):
            return ClaimListResponse(
                claims=[Claim(**item) for item in response],
                total=len(response),
                page=page,
                per_page=per_page
            )
        else:
            return ClaimListResponse(claims=[], total=0, page=page, per_page=per_page)
    
    def create(self, claim_data: CreateClaimRequest) -> Claim:
        """
        Create a new claim.
        
        Args:
            claim_data: The claim data to create
            
        Returns:
            Claim: The created claim object
        """
        endpoint = self._build_endpoint()
        data = claim_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, Claim)
    
    def update(self, claim_id: Union[int, str], claim_data: UpdateClaimRequest) -> Claim:
        """
        Update an existing claim.
        
        Args:
            claim_id: The claim ID
            claim_data: The claim data to update
            
        Returns:
            Claim: The updated claim object
        """
        claim_id = self._validate_id(claim_id)
        endpoint = self._build_endpoint(claim_id)
        data = claim_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, Claim)
    
    def delete(self, claim_id: Union[int, str]) -> bool:
        """
        Delete a claim.
        
        Args:
            claim_id: The claim ID
            
        Returns:
            bool: True if deletion was successful
        """
        claim_id = self._validate_id(claim_id)
        endpoint = self._build_endpoint(claim_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: ClaimSearchRequest) -> ClaimListResponse:
        """
        Search for claims.
        
        Args:
            search_params: Search parameters
            
        Returns:
            ClaimListResponse: List of matching claims
        """
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return ClaimListResponse(**response)
        elif isinstance(response, list):
            return ClaimListResponse(
                claims=[Claim(**item) for item in response],
                total=len(response),
                page=search_params.page,
                per_page=search_params.per_page
            )
        else:
            return ClaimListResponse(
                claims=[], 
                total=0, 
                page=search_params.page, 
                per_page=search_params.per_page
            )
    
    def get_by_patient(self, patient_id: Union[int, str]) -> List[Claim]:
        """
        Get claims for a specific patient.
        
        Args:
            patient_id: Patient ID
            
        Returns:
            List[Claim]: List of claims for the patient
        """
        patient_id = int(self._validate_id(patient_id))
        search_params = ClaimSearchRequest(patient_id=patient_id)
        result = self.search(search_params)
        return result.claims
    
    def get_by_provider(self, provider_id: Union[int, str]) -> List[Claim]:
        """
        Get claims for a specific provider.
        
        Args:
            provider_id: Provider ID
            
        Returns:
            List[Claim]: List of claims for the provider
        """
        provider_id = int(self._validate_id(provider_id))
        search_params = ClaimSearchRequest(provider_id=provider_id)
        result = self.search(search_params)
        return result.claims
    
    def get_by_status(self, status: str) -> List[Claim]:
        """
        Get claims by status.
        
        Args:
            status: Claim status
            
        Returns:
            List[Claim]: List of claims with the specified status
        """
        search_params = ClaimSearchRequest(claim_status=status)
        result = self.search(search_params)
        return result.claims
    
    def get_unsent(self) -> List[Claim]:
        """
        Get unsent claims.
        
        Returns:
            List[Claim]: List of unsent claims
        """
        return self.get_by_status("unsent")
    
    def get_sent(self) -> List[Claim]:
        """
        Get sent claims.
        
        Returns:
            List[Claim]: List of sent claims
        """
        return self.get_by_status("sent")
    
    def get_received(self) -> List[Claim]:
        """
        Get received claims.
        
        Returns:
            List[Claim]: List of received claims
        """
        return self.get_by_status("received")
    
    def send(self, claim_id: Union[int, str]) -> Claim:
        """
        Send a claim to insurance.
        
        Args:
            claim_id: The claim ID
            
        Returns:
            Claim: The sent claim
        """
        claim_id = self._validate_id(claim_id)
        endpoint = self._build_endpoint(f"{claim_id}/send")
        response = self._post(endpoint)
        return self._handle_response(response, Claim)
    
    def create_from_procedures(self, patient_id: int, procedure_ids: List[int], 
                              insurance_plan_id: int, provider_id: int) -> Claim:
        """
        Create a claim from procedures.
        
        Args:
            patient_id: Patient ID
            procedure_ids: List of procedure IDs
            insurance_plan_id: Insurance plan ID
            provider_id: Provider ID
            
        Returns:
            Claim: The created claim
        """
        claim_data = CreateClaimRequest(
            patient_id=patient_id,
            procedure_ids=procedure_ids,
            insurance_plan_id=insurance_plan_id,
            provider_id=provider_id,
            claim_type="primary",
            date_service=date.today()
        )
        return self.create(claim_data)
    
    def record_payment(self, claim_id: Union[int, str], amount: Decimal, 
                      date_paid: date, check_number: Optional[str] = None,
                      note: Optional[str] = None) -> ClaimPayment:
        """
        Record a payment for a claim.
        
        Args:
            claim_id: The claim ID
            amount: Payment amount
            date_paid: Date payment was received
            check_number: Check number (optional)
            note: Payment note (optional)
            
        Returns:
            ClaimPayment: The recorded payment
        """
        claim_id = self._validate_id(claim_id)
        endpoint = self._build_endpoint(f"{claim_id}/payments")
        data = {
            "amount_paid": str(amount),
            "date_paid": date_paid.isoformat(),
            "check_number": check_number,
            "note": note
        }
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, ClaimPayment)
    
    def get_payments(self, claim_id: Union[int, str]) -> List[ClaimPayment]:
        """
        Get payments for a claim.
        
        Args:
            claim_id: The claim ID
            
        Returns:
            List[ClaimPayment]: List of payments for the claim
        """
        claim_id = self._validate_id(claim_id)
        endpoint = self._build_endpoint(f"{claim_id}/payments")
        response = self._get(endpoint)
        return self._handle_list_response(response, ClaimPayment)
    
    def attach_eob(self, claim_id: Union[int, str], eob_data: dict) -> ClaimEOB:
        """
        Attach an EOB to a claim.
        
        Args:
            claim_id: The claim ID
            eob_data: EOB data
            
        Returns:
            ClaimEOB: The attached EOB
        """
        claim_id = self._validate_id(claim_id)
        endpoint = self._build_endpoint(f"{claim_id}/eob")
        response = self._post(endpoint, json_data=eob_data)
        return self._handle_response(response, ClaimEOB)
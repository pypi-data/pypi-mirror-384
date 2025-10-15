"""Payments client for Open Dental SDK."""

from typing import List, Optional, Union
from datetime import date
from decimal import Decimal
from ...base.resource import BaseResource
from .models import (
    Payment,
    CreatePaymentRequest,
    UpdatePaymentRequest,
    PaymentListResponse,
    PaymentSearchRequest
)


class PaymentsClient(BaseResource):
    """Client for managing payments in Open Dental."""
    
    def __init__(self, client):
        """Initialize the payments client."""
        super().__init__(client, "payments")
    
    def get(self, payment_id: Union[int, str]) -> Payment:
        """
        Get a payment by ID.
        
        Args:
            payment_id: The payment ID
            
        Returns:
            Payment: The payment object
        """
        payment_id = self._validate_id(payment_id)
        endpoint = self._build_endpoint(payment_id)
        response = self._get(endpoint)
        return self._handle_response(response, Payment)
    
    def list(self, page: int = 1, per_page: int = 50) -> PaymentListResponse:
        """
        List all payments.
        
        Args:
            page: Page number (default: 1)
            per_page: Items per page (default: 50)
            
        Returns:
            PaymentListResponse: List of payments with pagination info
        """
        params = {
            "page": page,
            "per_page": per_page
        }
        endpoint = self._build_endpoint()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return PaymentListResponse(**response)
        elif isinstance(response, list):
            return PaymentListResponse(
                payments=[Payment(**item) for item in response],
                total=len(response),
                page=page,
                per_page=per_page
            )
        else:
            return PaymentListResponse(payments=[], total=0, page=page, per_page=per_page)
    
    def create(self, payment_data: CreatePaymentRequest) -> Payment:
        """
        Create a new payment.
        
        Args:
            payment_data: The payment data to create
            
        Returns:
            Payment: The created payment object
        """
        endpoint = self._build_endpoint()
        data = payment_data.model_dump()
        response = self._post(endpoint, json_data=data)
        return self._handle_response(response, Payment)
    
    def update(self, payment_id: Union[int, str], payment_data: UpdatePaymentRequest) -> Payment:
        """
        Update an existing payment.
        
        Args:
            payment_id: The payment ID
            payment_data: The payment data to update
            
        Returns:
            Payment: The updated payment object
        """
        payment_id = self._validate_id(payment_id)
        endpoint = self._build_endpoint(payment_id)
        data = payment_data.model_dump()
        response = self._put(endpoint, json_data=data)
        return self._handle_response(response, Payment)
    
    def delete(self, payment_id: Union[int, str]) -> bool:
        """
        Delete a payment.
        
        Args:
            payment_id: The payment ID
            
        Returns:
            bool: True if deletion was successful
        """
        payment_id = self._validate_id(payment_id)
        endpoint = self._build_endpoint(payment_id)
        response = self._delete(endpoint)
        return response is None or response.get("success", True)
    
    def search(self, search_params: PaymentSearchRequest) -> PaymentListResponse:
        """
        Search for payments.
        
        Args:
            search_params: Search parameters
            
        Returns:
            PaymentListResponse: List of matching payments
        """
        endpoint = self._build_endpoint("search")
        params = search_params.model_dump()
        response = self._get(endpoint, params=params)
        
        if isinstance(response, dict):
            return PaymentListResponse(**response)
        elif isinstance(response, list):
            return PaymentListResponse(
                payments=[Payment(**item) for item in response],
                total=len(response),
                page=search_params.page,
                per_page=search_params.per_page
            )
        else:
            return PaymentListResponse(
                payments=[], 
                total=0, 
                page=search_params.page, 
                per_page=search_params.per_page
            )
    
    def get_by_patient(self, pat_num: int) -> List[Payment]:
        """
        Get payments for a specific patient.
        
        Args:
            pat_num: Patient number
            
        Returns:
            List[Payment]: List of payments for the patient
        """
        search_params = PaymentSearchRequest(pat_num=pat_num)
        result = self.search(search_params)
        return result.payments
    
    def get_by_provider(self, prov_num: int) -> List[Payment]:
        """
        Get payments for a specific provider.
        
        Args:
            prov_num: Provider number
            
        Returns:
            List[Payment]: List of payments for the provider
        """
        search_params = PaymentSearchRequest(prov_num=prov_num)
        result = self.search(search_params)
        return result.payments
    
    def get_by_clinic(self, clinic_num: int) -> List[Payment]:
        """
        Get payments for a specific clinic.
        
        Args:
            clinic_num: Clinic number
            
        Returns:
            List[Payment]: List of payments for the clinic
        """
        search_params = PaymentSearchRequest(clinic_num=clinic_num)
        result = self.search(search_params)
        return result.payments
    
    def get_by_payment_type(self, payment_type: str) -> List[Payment]:
        """
        Get payments by payment type.
        
        Args:
            payment_type: Payment type to search for
            
        Returns:
            List[Payment]: List of payments with matching type
        """
        search_params = PaymentSearchRequest(payment_type=payment_type)
        result = self.search(search_params)
        return result.payments
    
    def get_by_date_range(self, start_date: date, end_date: date) -> List[Payment]:
        """
        Get payments within a date range.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            List[Payment]: List of payments within the date range
        """
        search_params = PaymentSearchRequest(
            payment_date_start=start_date,
            payment_date_end=end_date
        )
        result = self.search(search_params)
        return result.payments
    
    def get_unallocated(self) -> List[Payment]:
        """
        Get all unallocated payments.
        
        Returns:
            List[Payment]: List of unallocated payments
        """
        search_params = PaymentSearchRequest(is_unallocated=True)
        result = self.search(search_params)
        return result.payments
    
    def create_cash_payment(self, pat_num: int, amount: Decimal, 
                           payment_date: Optional[date] = None,
                           note: Optional[str] = None) -> Payment:
        """
        Create a cash payment.
        
        Args:
            pat_num: Patient number
            amount: Payment amount
            payment_date: Payment date (defaults to today)
            note: Optional payment note
            
        Returns:
            Payment: The created payment object
        """
        if payment_date is None:
            payment_date = date.today()
            
        payment_data = CreatePaymentRequest(
            pat_num=pat_num,
            payment_date=payment_date,
            payment_amt=amount,
            payment_type="cash",
            payment_note=note
        )
        return self.create(payment_data)
    
    def create_check_payment(self, pat_num: int, amount: Decimal, check_num: str,
                            payment_date: Optional[date] = None,
                            note: Optional[str] = None) -> Payment:
        """
        Create a check payment.
        
        Args:
            pat_num: Patient number
            amount: Payment amount
            check_num: Check number
            payment_date: Payment date (defaults to today)
            note: Optional payment note
            
        Returns:
            Payment: The created payment object
        """
        if payment_date is None:
            payment_date = date.today()
            
        payment_data = CreatePaymentRequest(
            pat_num=pat_num,
            payment_date=payment_date,
            payment_amt=amount,
            payment_type="check",
            check_num=check_num,
            payment_note=note
        )
        return self.create(payment_data)
    
    def create_credit_card_payment(self, pat_num: int, amount: Decimal,
                                  payment_date: Optional[date] = None,
                                  note: Optional[str] = None) -> Payment:
        """
        Create a credit card payment.
        
        Args:
            pat_num: Patient number
            amount: Payment amount
            payment_date: Payment date (defaults to today)
            note: Optional payment note
            
        Returns:
            Payment: The created payment object
        """
        if payment_date is None:
            payment_date = date.today()
            
        payment_data = CreatePaymentRequest(
            pat_num=pat_num,
            payment_date=payment_date,
            payment_amt=amount,
            payment_type="credit_card",
            payment_note=note
        )
        return self.create(payment_data)
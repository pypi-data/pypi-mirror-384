"""Payment models for Open Dental SDK."""

from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
from pydantic import Field

from ...base.models import BaseModel


class Payment(BaseModel):
    """Payment model."""
    
    # Primary identifiers
    id: int = Field(..., alias="PayNum", description="Payment number (primary key)")
    payment_num: int = Field(..., alias="PayNum", description="Payment number")
    
    # Patient information
    pat_num: int = Field(..., alias="PatNum", description="Patient number")
    
    # Payment details
    payment_date: date = Field(..., alias="PayDate", description="Payment date")
    payment_amt: Decimal = Field(..., alias="PayAmt", description="Payment amount")
    payment_type: str = Field(..., alias="PayType", description="Payment type")
    
    # Reference information
    check_num: Optional[str] = Field(None, alias="CheckNum", description="Check number")
    receipt_num: Optional[str] = Field(None, alias="ReceiptNum", description="Receipt number")
    
    # Provider and clinic
    prov_num: Optional[int] = Field(None, alias="ProvNum", description="Provider number")
    clinic_num: Optional[int] = Field(None, alias="ClinicNum", description="Clinic number")
    
    # Notes
    payment_note: Optional[str] = Field(None, alias="PayNote", description="Payment note")
    
    # Status
    is_from_deposit: bool = Field(False, alias="IsFromDeposit", description="Whether payment is from deposit")
    is_unallocated: bool = Field(False, alias="IsUnallocated", description="Whether payment is unallocated")
    
    # Timestamps
    date_entry: Optional[datetime] = Field(None, alias="DateEntry", description="Date entry was created")
    date_created: Optional[datetime] = Field(None, alias="DateCreated", description="Date record was created")
    date_modified: Optional[datetime] = Field(None, alias="DateModified", description="Date record was last modified")


class CreatePaymentRequest(BaseModel):
    """Request model for creating a new payment."""
    
    # Required fields
    pat_num: int = Field(..., alias="PatNum", description="Patient number")
    payment_date: date = Field(..., alias="PayDate", description="Payment date")
    payment_amt: Decimal = Field(..., alias="PayAmt", description="Payment amount")
    payment_type: str = Field(..., alias="PayType", description="Payment type")
    
    # Optional fields
    check_num: Optional[str] = Field(None, alias="CheckNum", description="Check number")
    receipt_num: Optional[str] = Field(None, alias="ReceiptNum", description="Receipt number")
    prov_num: Optional[int] = Field(None, alias="ProvNum", description="Provider number")
    clinic_num: Optional[int] = Field(None, alias="ClinicNum", description="Clinic number")
    payment_note: Optional[str] = Field(None, alias="PayNote", description="Payment note")
    is_from_deposit: bool = Field(False, alias="IsFromDeposit", description="Whether payment is from deposit")
    is_unallocated: bool = Field(False, alias="IsUnallocated", description="Whether payment is unallocated")


class UpdatePaymentRequest(BaseModel):
    """Request model for updating an existing payment."""
    
    # All fields are optional for updates
    payment_date: Optional[date] = Field(None, alias="PayDate", description="Payment date")
    payment_amt: Optional[Decimal] = Field(None, alias="PayAmt", description="Payment amount")
    payment_type: Optional[str] = Field(None, alias="PayType", description="Payment type")
    check_num: Optional[str] = Field(None, alias="CheckNum", description="Check number")
    receipt_num: Optional[str] = Field(None, alias="ReceiptNum", description="Receipt number")
    prov_num: Optional[int] = Field(None, alias="ProvNum", description="Provider number")
    clinic_num: Optional[int] = Field(None, alias="ClinicNum", description="Clinic number")
    payment_note: Optional[str] = Field(None, alias="PayNote", description="Payment note")
    is_from_deposit: Optional[bool] = Field(None, alias="IsFromDeposit", description="Whether payment is from deposit")
    is_unallocated: Optional[bool] = Field(None, alias="IsUnallocated", description="Whether payment is unallocated")


class PaymentListResponse(BaseModel):
    """Response model for payment list operations."""
    
    payments: List[Payment]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class PaymentSearchRequest(BaseModel):
    """Request model for searching payments."""
    
    pat_num: Optional[int] = Field(None, alias="PatNum", description="Patient number")
    prov_num: Optional[int] = Field(None, alias="ProvNum", description="Provider number")
    clinic_num: Optional[int] = Field(None, alias="ClinicNum", description="Clinic number")
    payment_type: Optional[str] = Field(None, alias="PayType", description="Payment type")
    payment_date_start: Optional[date] = Field(None, alias="PayDateStart", description="Payment date start range")
    payment_date_end: Optional[date] = Field(None, alias="PayDateEnd", description="Payment date end range")
    is_unallocated: Optional[bool] = Field(None, alias="IsUnallocated", description="Whether payment is unallocated")
    
    # Pagination
    page: Optional[int] = Field(1, description="Page number for pagination")
    per_page: Optional[int] = Field(50, description="Number of records per page")
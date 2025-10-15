"""statements models for Open Dental SDK."""

from datetime import datetime, date
from typing import Optional, List

from pydantic import Field
from ...base.models import BaseModel


class Statement(BaseModel):
    """Statement model."""
    
    # Primary identifiers
    id: int = Field(..., alias="StatementNum", description="Statement number (primary key)")
    patient_num: int = Field(..., alias="PatNum", description="Patient number")
    
    # Statement details
    date_sent: Optional[date] = Field(None, alias="DateSent", description="Date statement was sent")
    statement_mode: int = Field(..., alias="Mode_", description="Statement mode (0=Mail, 1=Email, etc.)")
    note: Optional[str] = Field(None, alias="Note", description="Statement note")
    not_bold: bool = Field(False, alias="NotBold", description="Whether statement text should not be bold")
    
    # Financial information
    bal_total: Optional[float] = Field(None, alias="BalTotal", description="Total balance on statement")
    ins_est: Optional[float] = Field(None, alias="InsEst", description="Insurance estimate")
    
    # Date information
    date_range_from: Optional[date] = Field(None, alias="DateRangeFrom", description="Statement date range start")
    date_range_to: Optional[date] = Field(None, alias="DateRangeTo", description="Statement date range end")
    
    # Statement type and processing
    statement_type: int = Field(0, alias="StatementType", description="Statement type (0=Regular, 1=LimitedStatement)")
    is_invoice: bool = Field(False, alias="IsInvoice", description="Whether this is an invoice")
    hide_payment: bool = Field(False, alias="HidePayment", description="Whether to hide payment information")
    single_patient: bool = Field(False, alias="SinglePatient", description="Whether statement is for single patient only")
    
    # Intermingling and family handling
    intermingled_family: bool = Field(False, alias="IntermingledFamily", description="Whether family accounts are intermingled")
    super_family: int = Field(0, alias="SuperFamily", description="Super family number for combined statements")
    
    # Timestamps
    date_time_sent: Optional[datetime] = Field(None, alias="DateTimeSent", description="Date and time statement was sent")
    date_created: Optional[datetime] = Field(None, alias="SecDateTEdit", description="Date statement was created/edited")
    
    # Security and user tracking
    user_num: int = Field(0, alias="UserNum", description="User who created the statement")
    
    # Document handling
    doc_num: int = Field(0, alias="DocNum", description="Document number if statement saved as document")
    
    # Email specific fields
    email_subject: Optional[str] = Field(None, alias="EmailSubject", description="Email subject line")
    email_body: Optional[str] = Field(None, alias="EmailBody", description="Email body text")
    
    # Mailing information
    short_guid: Optional[str] = Field(None, alias="ShortGUID", description="Short GUID for statement identification")
    statement_url: Optional[str] = Field(None, alias="StatementURL", description="URL for online statement viewing")
    statement_short_url: Optional[str] = Field(None, alias="StatementShortURL", description="Shortened URL for statement")
    
    # Status flags
    is_sent: bool = Field(False, alias="IsSent", description="Whether statement has been sent")
    is_electronic: bool = Field(False, alias="IsElectronic", description="Whether statement was sent electronically")
    
    # Clinic information
    clinic_num: int = Field(0, alias="ClinicNum", description="Clinic number for multi-clinic practices")


class CreateStatementRequest(BaseModel):
    """Request model for creating a new statement."""
    
    # Required fields
    patient_num: int = Field(..., alias="PatNum", description="Patient number")
    statement_mode: int = Field(..., alias="Mode_", description="Statement mode (0=Mail, 1=Email, etc.)")
    
    # Optional fields
    date_sent: Optional[date] = Field(None, alias="DateSent", description="Date statement was sent")
    note: Optional[str] = Field(None, alias="Note", description="Statement note")
    not_bold: bool = Field(False, alias="NotBold", description="Whether statement text should not be bold")
    bal_total: Optional[float] = Field(None, alias="BalTotal", description="Total balance on statement")
    ins_est: Optional[float] = Field(None, alias="InsEst", description="Insurance estimate")
    date_range_from: Optional[date] = Field(None, alias="DateRangeFrom", description="Statement date range start")
    date_range_to: Optional[date] = Field(None, alias="DateRangeTo", description="Statement date range end")
    statement_type: int = Field(0, alias="StatementType", description="Statement type (0=Regular, 1=LimitedStatement)")
    is_invoice: bool = Field(False, alias="IsInvoice", description="Whether this is an invoice")
    hide_payment: bool = Field(False, alias="HidePayment", description="Whether to hide payment information")
    single_patient: bool = Field(False, alias="SinglePatient", description="Whether statement is for single patient only")
    intermingled_family: bool = Field(False, alias="IntermingledFamily", description="Whether family accounts are intermingled")
    super_family: int = Field(0, alias="SuperFamily", description="Super family number for combined statements")
    clinic_num: int = Field(0, alias="ClinicNum", description="Clinic number for multi-clinic practices")
    email_subject: Optional[str] = Field(None, alias="EmailSubject", description="Email subject line")
    email_body: Optional[str] = Field(None, alias="EmailBody", description="Email body text")


class UpdateStatementRequest(BaseModel):
    """Request model for updating an existing statement."""
    
    # All fields are optional for updates
    patient_num: Optional[int] = Field(None, alias="PatNum", description="Patient number")
    statement_mode: Optional[int] = Field(None, alias="Mode_", description="Statement mode (0=Mail, 1=Email, etc.)")
    date_sent: Optional[date] = Field(None, alias="DateSent", description="Date statement was sent")
    note: Optional[str] = Field(None, alias="Note", description="Statement note")
    not_bold: Optional[bool] = Field(None, alias="NotBold", description="Whether statement text should not be bold")
    bal_total: Optional[float] = Field(None, alias="BalTotal", description="Total balance on statement")
    ins_est: Optional[float] = Field(None, alias="InsEst", description="Insurance estimate")
    date_range_from: Optional[date] = Field(None, alias="DateRangeFrom", description="Statement date range start")
    date_range_to: Optional[date] = Field(None, alias="DateRangeTo", description="Statement date range end")
    statement_type: Optional[int] = Field(None, alias="StatementType", description="Statement type (0=Regular, 1=LimitedStatement)")
    is_invoice: Optional[bool] = Field(None, alias="IsInvoice", description="Whether this is an invoice")
    hide_payment: Optional[bool] = Field(None, alias="HidePayment", description="Whether to hide payment information")
    single_patient: Optional[bool] = Field(None, alias="SinglePatient", description="Whether statement is for single patient only")
    intermingled_family: Optional[bool] = Field(None, alias="IntermingledFamily", description="Whether family accounts are intermingled")
    super_family: Optional[int] = Field(None, alias="SuperFamily", description="Super family number for combined statements")
    clinic_num: Optional[int] = Field(None, alias="ClinicNum", description="Clinic number for multi-clinic practices")
    email_subject: Optional[str] = Field(None, alias="EmailSubject", description="Email subject line")
    email_body: Optional[str] = Field(None, alias="EmailBody", description="Email body text")


class StatementListResponse(BaseModel):
    """Response model for statement list operations."""
    
    statements: List[Statement]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class StatementSearchRequest(BaseModel):
    """Request model for searching statements."""
    
    patient_num: Optional[int] = Field(None, alias="PatNum", description="Patient number")
    statement_mode: Optional[int] = Field(None, alias="Mode_", description="Statement mode (0=Mail, 1=Email, etc.)")
    date_sent_from: Optional[date] = Field(None, alias="DateSentFrom", description="Search statements sent from this date")
    date_sent_to: Optional[date] = Field(None, alias="DateSentTo", description="Search statements sent to this date")
    is_sent: Optional[bool] = Field(None, alias="IsSent", description="Whether statement has been sent")
    is_electronic: Optional[bool] = Field(None, alias="IsElectronic", description="Whether statement was sent electronically")
    clinic_num: Optional[int] = Field(None, alias="ClinicNum", description="Clinic number for multi-clinic practices")
    
    # Pagination
    page: Optional[int] = 1
    per_page: Optional[int] = 50

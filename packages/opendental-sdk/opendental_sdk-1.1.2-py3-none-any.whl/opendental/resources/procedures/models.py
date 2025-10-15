"""Procedure models for Open Dental SDK."""

from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
from pydantic import Field

from ...base.models import BaseModel


class Procedure(BaseModel):
    """Procedure model with exact Open Dental database field mapping."""
    
    # Primary identifiers (exact database field mapping)
    id: int = Field(..., alias="ProcNum", description="Procedure number (primary key)")
    proc_num: int = Field(..., alias="ProcNum", description="Procedure number")
    
    # Patient and provider information
    pat_num: int = Field(..., alias="PatNum", description="Patient number")
    prov_num: int = Field(..., alias="ProvNum", description="Provider number")
    
    # Procedure details
    code_num: int = Field(..., alias="CodeNum", description="Procedure code number")
    proc_code: str = Field(..., alias="ProcCode", description="Procedure code")
    descript: str = Field(..., alias="Descript", description="Procedure description")
    proc_fee: Decimal = Field(..., alias="ProcFee", description="Procedure fee")
    
    # Dates
    proc_date: date = Field(..., alias="ProcDate", description="Procedure date")
    date_entry_c: Optional[datetime] = Field(None, alias="DateEntryC", description="Date entry created")
    date_original: Optional[date] = Field(None, alias="DateOriginal", description="Original procedure date")
    date_complete: Optional[date] = Field(None, alias="DateComplete", description="Date completed")
    
    # Status
    proc_status: str = Field("TP", alias="ProcStatus", description="Procedure status (TP=Treatment Planned, C=Complete, etc.)")
    is_locked: bool = Field(False, alias="IsLocked", description="Procedure is locked")
    
    # Billing and insurance
    bill_type: Optional[str] = Field(None, alias="BillType", description="Billing type")
    billed_to_ins: bool = Field(False, alias="BilledToIns", description="Billed to insurance")
    proc_num_lab: Optional[int] = Field(None, alias="ProcNumLab", description="Lab procedure number")
    
    # Clinical information
    surf: Optional[str] = Field(None, alias="Surf", description="Tooth surface")
    tooth_num: Optional[str] = Field(None, alias="ToothNum", description="Tooth number")
    tooth_range: Optional[str] = Field(None, alias="ToothRange", description="Tooth range")
    priority: Optional[int] = Field(None, alias="Priority", description="Priority level")
    
    # Financial
    estimate: Optional[Decimal] = Field(None, alias="Estimate", description="Estimated cost")
    base_units: Optional[int] = Field(None, alias="BaseUnits", description="Base units")
    unit_qty: Optional[int] = Field(None, alias="UnitQty", description="Unit quantity")
    
    # Notes and diagnosis
    note: Optional[str] = Field(None, alias="Note", description="Procedure note")
    diagnosis: Optional[str] = Field(None, alias="Diagnosis", description="Diagnosis")
    
    # References
    apt_num: Optional[int] = Field(None, alias="AptNum", description="Appointment number")
    claim_num: Optional[int] = Field(None, alias="ClaimNum", description="Claim number")
    
    # Timestamps
    date_created: Optional[datetime] = Field(None, alias="DateTStamp", description="Creation timestamp")
    date_modified: Optional[datetime] = Field(None, alias="DateTStamp", description="Last modified timestamp")
    
    # Clinic information
    clinic_num: Optional[int] = Field(None, alias="ClinicNum", description="Clinic number")
    
    # Additional Open Dental fields
    is_canadian: bool = Field(False, alias="IsCanadian", description="Canadian procedure flag")
    hidden: bool = Field(False, alias="Hidden", description="Hidden from view")
    
    # Lab information
    lab_case_num: Optional[int] = Field(None, alias="LabCaseNum", description="Lab case number")
    
    # Medical information
    medical_code: Optional[str] = Field(None, alias="MedicalCode", description="Medical code")
    diag_code: Optional[str] = Field(None, alias="DiagnosticCode", description="Diagnostic code")
    
    # Procedure modifications
    proc_time: Optional[str] = Field(None, alias="ProcTime", description="Procedure time")
    proc_time_end: Optional[str] = Field(None, alias="ProcTimeEnd", description="Procedure end time")
    
    # Provider assignments
    prov_num_assistant: Optional[int] = Field(None, alias="ProvNumAssistant", description="Assistant provider number")
    prov_num_hygienist: Optional[int] = Field(None, alias="ProvNumHygienist", description="Hygienist provider number")
    
    # Billing details
    ins_pay_est: Optional[Decimal] = Field(None, alias="InsPayEst", description="Insurance payment estimate")
    ins_pay_amt: Optional[Decimal] = Field(None, alias="InsPayAmt", description="Insurance payment amount")
    
    # Security
    user_num: Optional[int] = Field(None, alias="UserNum", description="User number")
    
    # Procedure flags
    is_repeat: bool = Field(False, alias="IsRepeat", description="Repeat procedure flag")
    is_prosth: bool = Field(False, alias="IsProsth", description="Prosthetic procedure flag")
    
    # Revenue code
    revenue_code: Optional[str] = Field(None, alias="RevenueCode", description="Revenue code")
    
    # Repeat charge
    repeat_charge: Optional[Decimal] = Field(None, alias="RepeatCharge", description="Repeat charge amount")
    
    # Procedure modifier
    proc_modifier: Optional[str] = Field(None, alias="ProcModifier", description="Procedure modifier")
    
    # Override fees
    override_fee: Optional[Decimal] = Field(None, alias="OverrideFee", description="Override fee amount")
    
    # Claim procedure
    claim_proc_num: Optional[int] = Field(None, alias="ClaimProcNum", description="Claim procedure number")


class CreateProcedureRequest(BaseModel):
    """Request model for creating a new procedure."""
    
    # Required fields
    pat_num: int
    prov_num: int
    proc_code: str
    proc_date: date
    proc_fee: Decimal
    
    # Optional procedure details
    descript: Optional[str] = None
    
    # Status
    proc_status: str = "TP"  # Treatment Planned by default
    
    # Clinical information
    surf: Optional[str] = None
    tooth_num: Optional[str] = None
    tooth_range: Optional[str] = None
    priority: Optional[int] = None
    
    # Financial
    estimate: Optional[Decimal] = None
    base_units: Optional[int] = None
    unit_qty: Optional[int] = None
    
    # Notes and diagnosis
    note: Optional[str] = None
    diagnosis: Optional[str] = None
    
    # References
    apt_num: Optional[int] = None
    
    # Clinic information
    clinic_num: Optional[int] = None


class UpdateProcedureRequest(BaseModel):
    """Request model for updating an existing procedure."""
    
    # All fields are optional for updates
    prov_num: Optional[int] = None
    proc_code: Optional[str] = None
    proc_date: Optional[date] = None
    proc_fee: Optional[Decimal] = None
    descript: Optional[str] = None
    
    # Status
    proc_status: Optional[str] = None
    
    # Clinical information
    surf: Optional[str] = None
    tooth_num: Optional[str] = None
    tooth_range: Optional[str] = None
    priority: Optional[int] = None
    
    # Financial
    estimate: Optional[Decimal] = None
    base_units: Optional[int] = None
    unit_qty: Optional[int] = None
    
    # Notes and diagnosis
    note: Optional[str] = None
    diagnosis: Optional[str] = None
    
    # References
    apt_num: Optional[int] = None
    claim_num: Optional[int] = None
    
    # Clinic information
    clinic_num: Optional[int] = None


class ProcedureListResponse(BaseModel):
    """Response model for procedure list operations."""
    
    procedures: List[Procedure]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class ProcedureSearchRequest(BaseModel):
    """Request model for searching procedures."""
    
    pat_num: Optional[int] = None
    prov_num: Optional[int] = None
    proc_code: Optional[str] = None
    proc_status: Optional[str] = None
    proc_date_start: Optional[date] = None
    proc_date_end: Optional[date] = None
    tooth_num: Optional[str] = None
    clinic_num: Optional[int] = None
    
    # Pagination
    page: Optional[int] = 1
    per_page: Optional[int] = 50
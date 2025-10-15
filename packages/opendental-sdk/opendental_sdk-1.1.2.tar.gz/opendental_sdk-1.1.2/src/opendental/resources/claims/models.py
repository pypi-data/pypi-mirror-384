"""Claims models for Open Dental SDK."""

from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
from pydantic import Field

from ...base.models import BaseModel
from ..patients.models import Patient  # Import Patient from patients domain


class InsurancePlan(BaseModel):
    """Insurance plan model - will be moved to insurance_plans resource later."""
    id: int
    plan_num: int
    employer: str
    group_name: Optional[str] = None
    group_num: Optional[str] = None
    carrier: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None


class Procedure(BaseModel):
    """Procedure model - will be moved to procedures resource later."""
    id: int
    proc_num: int
    proc_code: str
    description: str
    fee: Decimal
    date_performed: date
    provider_id: int
    patient_id: int


class Claim(BaseModel):
    """Claim model with exact Open Dental database field mapping."""
    
    # Primary identifiers (exact database field mapping)
    id: int = Field(..., alias="ClaimNum", description="Claim number (primary key)")
    claim_num: int = Field(..., alias="ClaimNum", description="Claim number")
    
    # Patient and insurance references
    patient_num: int = Field(..., alias="PatNum", description="Patient number")
    plan_num: int = Field(..., alias="PlanNum", description="Insurance plan number")
    ins_sub_num: int = Field(..., alias="InsSubNum", description="Insurance subscriber number")
    
    # Claim details
    claim_type: str = Field(..., alias="ClaimType", description="Claim type (P=Primary, S=Secondary, PreAuth=Preauth, etc.)")
    claim_status: str = Field("U", alias="ClaimStatus", description="Claim status (U=Unsent, S=Sent, R=Received, etc.)")
    date_service: date = Field(..., alias="DateService", description="Date of service")
    date_sent: Optional[date] = Field(None, alias="DateSent", description="Date claim was sent")
    date_received: Optional[date] = Field(None, alias="DateReceived", description="Date claim was received")
    
    # Financial information
    claim_fee: Decimal = Field(..., alias="ClaimFee", description="Total claim fee")
    insurance_paid: Optional[Decimal] = Field(None, alias="InsPayAmt", description="Insurance paid amount")
    patient_portion: Optional[Decimal] = Field(None, alias="PatPortion", description="Patient portion amount")
    writeoff: Optional[Decimal] = Field(None, alias="WriteOff", description="Write-off amount")
    
    # Provider information
    provider_treat: int = Field(..., alias="ProvTreat", description="Treating provider number")
    provider_bill: Optional[int] = Field(None, alias="ProvBill", description="Billing provider number")
    clinic_num: Optional[int] = Field(None, alias="ClinicNum", description="Clinic number")
    
    # Insurance information
    subscriber_id: Optional[str] = Field(None, alias="SubscriberID", description="Subscriber ID")
    relationship: Optional[str] = Field(None, alias="PatRelat", description="Patient relationship")
    
    # Medical information
    diagnosis_codes: Optional[str] = Field(None, alias="ICD9", description="ICD-9 diagnosis codes")
    medical_code: Optional[str] = Field(None, alias="MedCode", description="Medical code")
    
    # Claim processing
    batch_number: Optional[str] = Field(None, alias="BatchNum", description="Batch number")
    claim_identifier: Optional[str] = Field(None, alias="ClaimIdentifier", description="Claim identifier")
    
    # Timestamps
    date_created: Optional[datetime] = Field(None, alias="DateTStamp", description="Creation timestamp")
    date_modified: Optional[datetime] = Field(None, alias="DateTStamp", description="Last modified timestamp")
    
    # Additional information
    note: Optional[str] = Field(None, alias="Note", description="Claim note")
    custom_tracking: Optional[str] = Field(None, alias="CustomTracking", description="Custom tracking")
    
    # Electronic claim information
    electronic_claim_id: Optional[str] = Field(None, alias="ElectronicClaimID", description="Electronic claim ID")
    clearinghouse: Optional[str] = Field(None, alias="Clearinghouse", description="Clearinghouse")
    
    # Claim corrections
    corrected_claim_num: Optional[int] = Field(None, alias="CorrectedClaimNum", description="Corrected claim number")
    original_claim_num: Optional[int] = Field(None, alias="OriginalClaimNum", description="Original claim number")
    
    # Preauthorization
    preauth_number: Optional[str] = Field(None, alias="PreAuthNum", description="Preauthorization number")
    
    # Referral
    referral_number: Optional[str] = Field(None, alias="ReferralNum", description="Referral number")
    
    # Accident information
    accident_related: bool = Field(False, alias="AccidentRelated", description="Accident related flag")
    accident_date: Optional[date] = Field(None, alias="AccidentDate", description="Accident date")
    accident_type: Optional[str] = Field(None, alias="AccidentType", description="Accident type")
    
    # Additional Open Dental fields
    employment_related: bool = Field(False, alias="EmploymentRelated", description="Employment related flag")
    is_orthodontic: bool = Field(False, alias="IsOrthodontic", description="Orthodontic claim flag")
    ortho_date: Optional[date] = Field(None, alias="OrthoDate", description="Orthodontic date")
    ortho_months_total: Optional[int] = Field(None, alias="OrthoMonthsTotal", description="Total orthodontic months")
    ortho_months_remain: Optional[int] = Field(None, alias="OrthoMonthsRemain", description="Remaining orthodontic months")
    
    # Claim form
    claim_form: Optional[int] = Field(None, alias="ClaimForm", description="Claim form number")
    
    # Attachment information
    attachments: Optional[str] = Field(None, alias="Attachments", description="Attachment information")
    
    # Security
    user_num: Optional[int] = Field(None, alias="UserNum", description="User number")
    
    # Claim filing
    claim_filing_code: Optional[str] = Field(None, alias="ClaimFilingCode", description="Claim filing code")
    
    # Place of service
    place_service: Optional[str] = Field(None, alias="PlaceService", description="Place of service")
    
    # Claim frequency
    claim_frequency: Optional[str] = Field(None, alias="ClaimFrequency", description="Claim frequency")
    
    # Special program
    special_program: Optional[str] = Field(None, alias="SpecialProgram", description="Special program")
    
    # Ordering provider
    ordering_provider: Optional[int] = Field(None, alias="OrderingProvider", description="Ordering provider number")
    
    # Referring provider
    referring_provider: Optional[int] = Field(None, alias="ReferringProvider", description="Referring provider number")
    
    # Supervising provider
    supervising_provider: Optional[int] = Field(None, alias="SupervisingProvider", description="Supervising provider number")
    
    # Claim note
    claim_note: Optional[str] = Field(None, alias="ClaimNote", description="Additional claim note")
    
    # Replacement of prior authorization
    replacement_of_prior_auth: Optional[str] = Field(None, alias="ReplacementOfPriorAuth", description="Replacement of prior authorization")
    
    # Billing note
    billing_note: Optional[str] = Field(None, alias="BillingNote", description="Billing note")
    
    # Claim correction type
    correction_type: Optional[str] = Field(None, alias="CorrectionType", description="Correction type")
    
    # Claim custom fields
    custom_claim_id: Optional[str] = Field(None, alias="CustomClaimID", description="Custom claim ID")
    
    # Claim identifier from clearinghouse
    claim_id_from_clearinghouse: Optional[str] = Field(None, alias="ClaimIDFromClearinghouse", description="Claim ID from clearinghouse")


class CreateClaimRequest(BaseModel):
    """Request model for creating a new claim."""
    
    # Required fields
    patient_id: int
    insurance_plan_id: int
    procedure_ids: List[int]
    claim_type: str
    date_service: date
    provider_id: int
    
    # Optional fields
    claim_status: str = "unsent"
    subscriber_id: Optional[str] = None
    relationship: Optional[str] = None
    diagnosis_codes: Optional[List[str]] = None
    medical_code: Optional[str] = None
    clinic_num: Optional[int] = None
    note: Optional[str] = None
    custom_tracking: Optional[str] = None
    preauth_number: Optional[str] = None
    referral_number: Optional[str] = None
    accident_related: bool = False
    accident_date: Optional[date] = None
    accident_type: Optional[str] = None


class UpdateClaimRequest(BaseModel):
    """Request model for updating an existing claim."""
    
    # All fields are optional for updates
    patient_id: Optional[int] = None
    insurance_plan_id: Optional[int] = None
    procedure_ids: Optional[List[int]] = None
    claim_type: Optional[str] = None
    claim_status: Optional[str] = None
    date_service: Optional[date] = None
    date_sent: Optional[date] = None
    date_received: Optional[date] = None
    provider_id: Optional[int] = None
    clinic_num: Optional[int] = None
    subscriber_id: Optional[str] = None
    relationship: Optional[str] = None
    diagnosis_codes: Optional[List[str]] = None
    medical_code: Optional[str] = None
    insurance_paid: Optional[Decimal] = None
    patient_portion: Optional[Decimal] = None
    writeoff: Optional[Decimal] = None
    note: Optional[str] = None
    custom_tracking: Optional[str] = None
    batch_number: Optional[str] = None
    claim_identifier: Optional[str] = None
    electronic_claim_id: Optional[str] = None
    clearinghouse: Optional[str] = None
    preauth_number: Optional[str] = None
    referral_number: Optional[str] = None
    accident_related: Optional[bool] = None
    accident_date: Optional[date] = None
    accident_type: Optional[str] = None


class ClaimListResponse(BaseModel):
    """Response model for claim list operations."""
    
    claims: List[Claim]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class ClaimSearchRequest(BaseModel):
    """Request model for searching claims."""
    
    patient_id: Optional[int] = None
    insurance_plan_id: Optional[int] = None
    provider_id: Optional[int] = None
    claim_type: Optional[str] = None
    claim_status: Optional[str] = None
    date_service_start: Optional[date] = None
    date_service_end: Optional[date] = None
    date_sent_start: Optional[date] = None
    date_sent_end: Optional[date] = None
    
    # Pagination
    page: Optional[int] = 1
    per_page: Optional[int] = 50


class ClaimPayment(BaseModel):
    """Model for recording claim payments."""
    
    id: int
    claim_id: int
    amount_paid: Decimal
    date_paid: date
    check_number: Optional[str] = None
    note: Optional[str] = None
    
    # Payment breakdown
    procedure_payments: Optional[List[dict]] = None  # Will be typed later
    
    # Timestamps
    date_created: Optional[datetime] = None


class ClaimEOB(BaseModel):
    """Model for Explanation of Benefits (EOB)."""
    
    id: int
    claim_id: int
    date_received: date
    total_paid: Decimal
    patient_responsibility: Decimal
    
    # EOB details
    procedure_details: Optional[List[dict]] = None  # Will be typed later
    denial_codes: Optional[List[str]] = None
    
    # File attachment
    file_path: Optional[str] = None
    
    # Timestamps
    date_created: Optional[datetime] = None
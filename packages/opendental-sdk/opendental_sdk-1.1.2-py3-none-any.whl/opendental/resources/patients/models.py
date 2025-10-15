"""Patient models for Open Dental SDK with database field mapping."""

from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
from pydantic import Field

from ...base.models import BaseModel


class Patient(BaseModel):
    """Patient model with exact Open Dental database field mapping."""
    
    # Primary identifiers (exact database field mapping)
    id: int = Field(..., alias="PatNum", description="Patient number (primary key)")
    
    # Required personal information
    first_name: str = Field(..., alias="FName", description="Patient first name")
    last_name: str = Field(..., alias="LName", description="Patient last name")
    
    # Optional personal information
    middle_initial: Optional[str] = Field(None, alias="MiddleI", description="Middle initial")
    preferred_name: Optional[str] = Field(None, alias="Preferred", description="Preferred name")
    title: Optional[str] = Field(None, alias="Title", description="Title (Mr., Mrs., etc.)")
    salutation: Optional[str] = Field(None, alias="Salutation", description="Greeting salutation")
    
    # Contact information
    email: Optional[str] = Field(None, alias="Email", description="Email address")
    home_phone: Optional[str] = Field(None, alias="HmPhone", description="Home phone number")
    work_phone: Optional[str] = Field(None, alias="WkPhone", description="Work phone number")
    cell_phone: Optional[str] = Field(None, alias="WirelessPhone", description="Cell phone number")
    address: Optional[str] = Field(None, alias="Address", description="Street address")
    address2: Optional[str] = Field(None, alias="Address2", description="Address line 2")
    city: Optional[str] = Field(None, alias="City", description="City")
    state: Optional[str] = Field(None, alias="State", description="State")
    zip_code: Optional[str] = Field(None, alias="Zip", description="ZIP/postal code")
    
    # Demographics
    birth_date: Optional[date] = Field(None, alias="Birthdate", description="Date of birth")
    gender: Optional[int] = Field(None, alias="Gender", description="Gender (0=Unknown, 1=Male, 2=Female)")
    ssn: Optional[str] = Field(None, alias="SSN", description="Social Security Number")
    
    # Medical information
    medical_alert: Optional[str] = Field(None, alias="MedAlert", description="Medical alert information")
    premedication_required: Optional[bool] = Field(None, alias="Premed", description="Premedication required")
    medical_urgent_note: Optional[str] = Field(None, alias="MedUrgNote", description="Medical urgent note")
    
    # Financial information
    total_balance: Optional[Decimal] = Field(None, alias="BalTotal", description="Total account balance")
    balance_0_30: Optional[Decimal] = Field(None, alias="Bal_0_30", description="0-30 day balance")
    balance_31_60: Optional[Decimal] = Field(None, alias="Bal_31_60", description="31-60 day balance")
    balance_61_90: Optional[Decimal] = Field(None, alias="Bal_61_90", description="61-90 day balance")
    balance_over_90: Optional[Decimal] = Field(None, alias="BalOver90", description="Over 90 day balance")
    insurance_estimate: Optional[Decimal] = Field(None, alias="InsEst", description="Insurance estimate")
    
    # Family and guarantor information
    guarantor_num: Optional[int] = Field(None, alias="Guarantor", description="Guarantor patient number")
    responsible_party: Optional[int] = Field(None, alias="ResponsParty", description="Responsible party patient number")
    position: Optional[int] = Field(None, alias="Position", description="Position in family (1=Guarantor, 2=Spouse, etc.)")
    
    # Provider information
    primary_provider: Optional[int] = Field(None, alias="PriProv", description="Primary provider number")
    secondary_provider: Optional[int] = Field(None, alias="SecProv", description="Secondary provider number")
    
    # Practice information
    clinic_num: Optional[int] = Field(None, alias="ClinicNum", description="Clinic number")
    chart_number: Optional[str] = Field(None, alias="ChartNumber", description="Chart number")
    
    # Status
    patient_status: Optional[int] = Field(None, alias="PatStatus", description="Patient status (0=Patient, 1=NonPatient, 2=Inactive, 3=Archived, 4=Deceased)")
    billing_type: Optional[int] = Field(None, alias="BillingType", description="Billing type definition number")
    
    # Contact preferences
    contact_method: Optional[int] = Field(None, alias="ContactMethod", description="Preferred contact method")
    text_message_ok: Optional[int] = Field(None, alias="TxtMsgOk", description="Text message permission")
    
    # Employment information
    employer: Optional[str] = Field(None, alias="Employer", description="Employer name")
    
    # Emergency contact
    emergency_contact_name: Optional[str] = Field(None, alias="ICEName", description="In Case of Emergency contact name")
    emergency_contact_phone: Optional[str] = Field(None, alias="ICEPhone", description="In Case of Emergency contact phone")
    
    # Timestamps
    date_first_visit: Optional[date] = Field(None, alias="DateFirstVisit", description="Date of first visit")
    date_timestamp: Optional[datetime] = Field(None, alias="DateTStamp", description="Last modified timestamp")
    
    # User tracking
    user_entry: Optional[int] = Field(None, alias="SecUserNumEntry", description="User who created record")
    date_entry: Optional[date] = Field(None, alias="SecDateEntry", description="Date record was created")
    
    # Additional fields
    student_status: Optional[str] = Field(None, alias="StudentStatus", description="Student status")
    school_name: Optional[str] = Field(None, alias="SchoolName", description="School name")
    credit_type: Optional[str] = Field(None, alias="CreditType", description="Credit type")
    language: Optional[str] = Field(None, alias="Language", description="Preferred language")
    address_note: Optional[str] = Field(None, alias="AddrNote", description="Address note")
    
    # Scheduling preferences
    ask_to_arrive_early: Optional[int] = Field(None, alias="AskToArriveEarly", description="Minutes to ask to arrive early")
    
    # Race and ethnicity (for reporting)
    race: Optional[int] = Field(None, alias="Race", description="Race category")
    county: Optional[str] = Field(None, alias="County", description="County")
    country: Optional[str] = Field(None, alias="Country", description="Country")


class CreatePatientRequest(BaseModel):
    """Request model for creating a new patient."""
    
    # Required fields
    first_name: str
    last_name: str
    
    # Optional personal information
    middle_name: Optional[str] = None
    preferred_name: Optional[str] = None
    salutation: Optional[str] = None
    
    # Contact information
    email: Optional[str] = None
    home_phone: Optional[str] = None
    work_phone: Optional[str] = None
    cell_phone: Optional[str] = None
    address: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    
    # Demographics
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    ssn: Optional[str] = None
    
    # Medical information
    medical_alert: Optional[str] = None
    allergies: Optional[str] = None
    medications: Optional[str] = None
    medical_history: Optional[str] = None
    
    # Financial information
    credit_type: Optional[str] = None
    
    # Practice information
    guarantor_num: Optional[int] = None
    responsible_party: Optional[int] = None
    primary_provider_num: Optional[int] = None
    chart_number: Optional[str] = None
    
    # Status
    is_active: bool = True
    patient_status: Optional[str] = None
    
    # Emergency contact
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    
    # Practice management
    family_num: Optional[int] = None
    position: Optional[int] = None
    clinic_num: Optional[int] = None


class UpdatePatientRequest(BaseModel):
    """Request model for updating an existing patient."""
    
    # All fields are optional for updates
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    preferred_name: Optional[str] = None
    salutation: Optional[str] = None
    
    # Contact information
    email: Optional[str] = None
    home_phone: Optional[str] = None
    work_phone: Optional[str] = None
    cell_phone: Optional[str] = None
    address: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    
    # Demographics
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    ssn: Optional[str] = None
    
    # Medical information
    medical_alert: Optional[str] = None
    allergies: Optional[str] = None
    medications: Optional[str] = None
    medical_history: Optional[str] = None
    
    # Financial information
    credit_type: Optional[str] = None
    
    # Practice information
    guarantor_num: Optional[int] = None
    responsible_party: Optional[int] = None
    primary_provider_num: Optional[int] = None
    chart_number: Optional[str] = None
    
    # Status
    is_active: Optional[bool] = None
    patient_status: Optional[str] = None
    
    # Emergency contact
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    
    # Practice management
    family_num: Optional[int] = None
    position: Optional[int] = None
    clinic_num: Optional[int] = None


class PatientListResponse(BaseModel):
    """Response model for patient list operations."""
    
    patients: List[Patient]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class PatientSearchRequest(BaseModel):
    """Request model for searching patients."""
    
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    birth_date: Optional[date] = None
    chart_number: Optional[str] = None
    
    # Pagination
    page: Optional[int] = 1
    per_page: Optional[int] = 50
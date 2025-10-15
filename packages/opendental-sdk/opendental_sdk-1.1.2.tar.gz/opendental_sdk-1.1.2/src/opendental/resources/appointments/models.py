"""Appointment models for Open Dental SDK."""

from datetime import datetime, date, time
from typing import Optional, List
from decimal import Decimal
from pydantic import Field

from ...base.models import BaseModel
from ..patients.models import Patient  # Import Patient from patients domain


class Provider(BaseModel):
    """Provider model - will be moved to providers resource later."""
    id: int
    provider_num: int
    first_name: str
    last_name: str
    abbreviation: Optional[str] = None
    specialty: Optional[str] = None
    is_active: bool = True


class Operatory(BaseModel):
    """Operatory model - will be moved to operatories resource later."""
    id: int
    operatory_num: int
    name: str
    abbreviation: Optional[str] = None
    is_active: bool = True


class AppointmentType(BaseModel):
    """Appointment type model."""
    id: int
    name: str
    duration: int  # in minutes
    color: Optional[str] = None
    procedure_codes: Optional[List[str]] = None


class Appointment(BaseModel):
    """Appointment model with exact Open Dental database field mapping."""
    
    # Primary identifiers (exact database field mapping)
    id: int = Field(..., alias="AptNum", description="Appointment number (primary key)")
    apt_num: int = Field(..., alias="AptNum", description="Appointment number")
    
    # Patient and provider references
    patient_num: int = Field(..., alias="PatNum", description="Patient number")
    provider_num: int = Field(..., alias="ProvNum", description="Provider number")
    provider_hygienist: Optional[int] = Field(None, alias="ProvHyg", description="Hygienist provider number")
    
    # Appointment timing
    apt_date_time: datetime = Field(..., alias="AptDateTime", description="Appointment date and time")
    duration: int = Field(..., alias="Length", description="Duration in minutes")
    
    # Operatory assignment
    operatory_num: Optional[int] = Field(None, alias="Op", description="Operatory number")
    
    # Status and confirmation
    apt_status: int = Field(1, alias="AptStatus", description="Appointment status (1=Scheduled, 2=Complete, etc.)")
    confirmed: Optional[int] = Field(None, alias="Confirmed", description="Confirmation status")
    is_complete: bool = Field(False, alias="IsComplete", description="Whether appointment is complete")
    
    # Clinical information
    note: Optional[str] = Field(None, alias="Note", description="Appointment note")
    procedures: Optional[str] = Field(None, alias="ProcsColored", description="Procedures with color coding")
    
    # Appointment type
    appointment_type_num: Optional[int] = Field(None, alias="AppointmentTypeNum", description="Appointment type number")
    
    # Financial information
    estimated_cost: Optional[Decimal] = Field(None, alias="EstimatedCost", description="Estimated cost")
    
    # Practice management
    clinic_num: Optional[int] = Field(None, alias="ClinicNum", description="Clinic number")
    time_locked: bool = Field(False, alias="TimeLocked", description="Time slot locked")
    
    # Timestamps
    date_created: Optional[datetime] = Field(None, alias="DateTStamp", description="Creation timestamp")
    date_modified: Optional[datetime] = Field(None, alias="DateTStamp", description="Last modified timestamp")
    
    # Reminder information
    reminder_sent: bool = Field(False, alias="ReminderSent", description="Reminder sent flag")
    
    # Pattern for recurring appointments
    pattern: Optional[str] = Field(None, alias="Pattern", description="Recurring appointment pattern")
    
    # Priority
    priority: Optional[int] = Field(None, alias="Priority", description="Priority level")
    
    # Insurance information
    insurance_estimate: Optional[Decimal] = Field(None, alias="InsEst", description="Insurance estimate")
    
    # Lab case information
    lab_case_num: Optional[int] = Field(None, alias="LabCaseNum", description="Lab case number")
    
    # Additional Open Dental fields
    is_new_patient: bool = Field(False, alias="IsNewPatient", description="New patient flag")
    is_web_sched: bool = Field(False, alias="IsWebSched", description="Web scheduled flag")
    date_stamp: Optional[datetime] = Field(None, alias="DateStamp", description="Date stamp")
    
    # Security
    user_num: Optional[int] = Field(None, alias="SecUserNumEntry", description="User who created appointment")
    date_entry: Optional[datetime] = Field(None, alias="SecDateEntry", description="Date entry was created")
    
    # Appointment colors
    color_override: Optional[str] = Field(None, alias="ColorOverride", description="Override color")
    
    # Web scheduling
    web_sched_date_time: Optional[datetime] = Field(None, alias="WebSchedDateTime", description="Web schedule date/time")
    
    # Confirmation
    confirm_code: Optional[str] = Field(None, alias="ConfirmCode", description="Confirmation code")
    
    # Additional flags
    is_hygiene: bool = Field(False, alias="IsHygiene", description="Hygiene appointment flag")
    time_arrived: Optional[datetime] = Field(None, alias="TimeArrived", description="Time patient arrived")
    time_seated: Optional[datetime] = Field(None, alias="TimeSeated", description="Time patient was seated")
    time_dismissed: Optional[datetime] = Field(None, alias="TimeDismissed", description="Time patient was dismissed")


class CreateAppointmentRequest(BaseModel):
    """Request model for creating a new appointment."""
    
    # Required fields
    patient_id: int  # ID reference for creation
    provider_id: int
    apt_date_time: datetime
    duration: int  # in minutes
    
    # Optional fields
    operatory_id: Optional[int] = None
    appointment_type_id: Optional[int] = None
    apt_status: str = "scheduled"
    confirmed: bool = False
    note: Optional[str] = None
    procedures: Optional[List[str]] = None
    estimated_cost: Optional[Decimal] = None
    clinic_num: Optional[int] = None
    priority: Optional[str] = None
    pattern: Optional[str] = None


class UpdateAppointmentRequest(BaseModel):
    """Request model for updating an existing appointment."""
    
    # All fields are optional for updates
    patient_id: Optional[int] = None
    provider_id: Optional[int] = None
    apt_date_time: Optional[datetime] = None
    duration: Optional[int] = None
    operatory_id: Optional[int] = None
    appointment_type_id: Optional[int] = None
    apt_status: Optional[str] = None
    confirmed: Optional[bool] = None
    is_complete: Optional[bool] = None
    note: Optional[str] = None
    procedures: Optional[List[str]] = None
    estimated_cost: Optional[Decimal] = None
    clinic_num: Optional[int] = None
    time_locked: Optional[bool] = None
    priority: Optional[str] = None
    pattern: Optional[str] = None


class AppointmentListResponse(BaseModel):
    """Response model for appointment list operations."""
    
    appointments: List[Appointment]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class AppointmentSearchRequest(BaseModel):
    """Request model for searching appointments."""
    
    patient_id: Optional[int] = None
    provider_id: Optional[int] = None
    operatory_id: Optional[int] = None
    date_start: Optional[date] = None
    date_end: Optional[date] = None
    apt_status: Optional[str] = None
    confirmed: Optional[bool] = None
    is_complete: Optional[bool] = None
    
    # Pagination
    page: Optional[int] = 1
    per_page: Optional[int] = 50


class AppointmentBlock(BaseModel):
    """Model for appointment scheduling blocks."""
    
    id: int
    operatory_id: int
    start_time: datetime
    end_time: datetime
    block_type: str  # "schedule", "lunch", "meeting", etc.
    description: Optional[str] = None
    provider_id: Optional[int] = None
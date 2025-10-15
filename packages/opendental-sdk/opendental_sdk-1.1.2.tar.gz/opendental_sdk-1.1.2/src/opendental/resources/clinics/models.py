"""Clinic models for Open Dental SDK."""

from datetime import datetime, date
from typing import Optional, List
from pydantic import Field

from ...base.models import BaseModel


class Clinic(BaseModel):
    """Clinic model with exact Open Dental database field mapping."""
    
    # Primary identifiers (exact database field mapping)
    id: int = Field(..., alias="ClinicNum", description="Clinic number (primary key)")
    clinic_num: int = Field(..., alias="ClinicNum", description="Clinic number")
    
    # Clinic information
    description: str = Field(..., alias="Description", description="Clinic description")
    abbreviation: Optional[str] = Field(None, alias="Abbr", description="Clinic abbreviation")
    
    # Contact information
    address: Optional[str] = Field(None, alias="Address", description="Street address")
    address2: Optional[str] = Field(None, alias="Address2", description="Address line 2")
    city: Optional[str] = Field(None, alias="City", description="City")
    state: Optional[str] = Field(None, alias="State", description="State")
    zip: Optional[str] = Field(None, alias="Zip", description="ZIP code")
    phone: Optional[str] = Field(None, alias="Phone", description="Phone number")
    fax: Optional[str] = Field(None, alias="Fax", description="Fax number")
    email: Optional[str] = Field(None, alias="EmailAddress", description="Email address")
    
    # Status
    is_hidden: bool = Field(False, alias="IsHidden", description="Hidden from lists")
    is_medical: bool = Field(False, alias="IsMedical", description="Medical clinic flag")
    
    # Timestamps
    date_created: Optional[datetime] = Field(None, alias="DateTStamp", description="Creation timestamp")
    date_modified: Optional[datetime] = Field(None, alias="DateTStamp", description="Last modified timestamp")
    
    # Additional Open Dental fields
    billing_address: Optional[str] = Field(None, alias="BillingAddress", description="Billing address")
    billing_address2: Optional[str] = Field(None, alias="BillingAddress2", description="Billing address line 2")
    billing_city: Optional[str] = Field(None, alias="BillingCity", description="Billing city")
    billing_state: Optional[str] = Field(None, alias="BillingState", description="Billing state")
    billing_zip: Optional[str] = Field(None, alias="BillingZip", description="Billing ZIP code")
    
    # Provider defaults
    default_provider: Optional[int] = Field(None, alias="DefaultProv", description="Default provider number")
    
    # Scheduling colors
    clinic_color: Optional[str] = Field(None, alias="ClinicColor", description="Clinic color")
    
    # Medical fields
    medical_program: Optional[str] = Field(None, alias="MedicalProgram", description="Medical program")
    
    # Custom fields
    custom1: Optional[str] = Field(None, alias="Custom1", description="Custom field 1")
    custom2: Optional[str] = Field(None, alias="Custom2", description="Custom field 2")
    custom3: Optional[str] = Field(None, alias="Custom3", description="Custom field 3")
    
    # Order display
    item_order: Optional[int] = Field(None, alias="ItemOrder", description="Display order")
    
    # Additional clinic settings
    is_default: bool = Field(False, alias="IsDefault", description="Default clinic flag")
    
    # Web settings
    web_sched_url: Optional[str] = Field(None, alias="WebSchedUrl", description="Web schedule URL")
    
    # Region information
    region: Optional[str] = Field(None, alias="Region", description="Clinic region")
    
    # Additional contact
    contact_person: Optional[str] = Field(None, alias="ContactPerson", description="Contact person")
    
    # Practice information
    practice_title: Optional[str] = Field(None, alias="PracticeTitle", description="Practice title")
    practice_phone: Optional[str] = Field(None, alias="PracticePhone", description="Practice phone")


class CreateClinicRequest(BaseModel):
    """Request model for creating a new clinic."""
    
    # Required fields
    description: str
    
    # Optional fields
    abbreviation: Optional[str] = None
    address: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[str] = None
    is_hidden: bool = False
    is_medical: bool = False


class UpdateClinicRequest(BaseModel):
    """Request model for updating an existing clinic."""
    
    # All fields are optional for updates
    description: Optional[str] = None
    abbreviation: Optional[str] = None
    address: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[str] = None
    is_hidden: Optional[bool] = None
    is_medical: Optional[bool] = None


class ClinicListResponse(BaseModel):
    """Response model for clinic list operations."""
    
    clinics: List[Clinic]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class ClinicSearchRequest(BaseModel):
    """Request model for searching clinics."""
    
    description: Optional[str] = None
    abbreviation: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    is_hidden: Optional[bool] = None
    is_medical: Optional[bool] = None
    
    # Pagination
    page: Optional[int] = 1
    per_page: Optional[int] = 50
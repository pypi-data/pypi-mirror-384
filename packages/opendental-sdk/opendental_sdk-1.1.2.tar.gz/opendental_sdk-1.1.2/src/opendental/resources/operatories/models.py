"""Operatories models for Open Dental SDK."""

from datetime import datetime
from typing import Optional, List
from pydantic import Field

from ...base.models import BaseModel


class Operatory(BaseModel):
    """Operatory model with exact Open Dental database field mapping."""
    
    # Primary identifiers (exact database field mapping)
    id: int = Field(..., alias="OperatoryNum", description="Operatory number (primary key)")
    operatory_num: int = Field(..., alias="OperatoryNum", description="Operatory number")
    
    # Basic information
    name: str = Field(..., alias="OpName", description="Operatory name")
    abbreviation: Optional[str] = Field(None, alias="Abbrev", description="Operatory abbreviation")
    description: Optional[str] = Field(None, alias="Description", description="Operatory description")
    
    # Status
    is_active: bool = Field(True, alias="IsActive", description="Active operatory flag")
    is_hygiene: bool = Field(False, alias="IsHygiene", description="Hygiene operatory flag")
    
    # Clinic assignment
    clinic_num: Optional[int] = Field(None, alias="ClinicNum", description="Clinic number")
    
    # Provider assignment
    provider_dentist: Optional[int] = Field(None, alias="ProvDentist", description="Dentist provider number")
    provider_hygienist: Optional[int] = Field(None, alias="ProvHygienist", description="Hygienist provider number")
    
    # Display settings
    item_order: Optional[int] = Field(None, alias="ItemOrder", description="Display order")
    
    # Operatory colors
    operatory_color: Optional[str] = Field(None, alias="OperatoryColor", description="Operatory color")
    
    # Additional settings
    is_web_sched: bool = Field(False, alias="IsWebSched", description="Web schedule enabled")
    
    # Timestamps
    date_created: Optional[datetime] = Field(None, alias="DateTStamp", description="Creation timestamp")
    date_modified: Optional[datetime] = Field(None, alias="DateTStamp", description="Last modified timestamp")
    
    # Additional Open Dental fields
    is_hidden: bool = Field(False, alias="IsHidden", description="Hidden from schedule")
    
    # Custom operatory settings
    set_prospective: bool = Field(False, alias="SetProspective", description="Set prospective flag")
    
    # Operatory type
    operatory_type: Optional[int] = Field(None, alias="OperatoryType", description="Operatory type")
    
    # Web schedule settings
    web_sched_new_pat: bool = Field(False, alias="WebSchedNewPat", description="Web schedule new patients")
    
    # Custom fields
    custom1: Optional[str] = Field(None, alias="Custom1", description="Custom field 1")
    custom2: Optional[str] = Field(None, alias="Custom2", description="Custom field 2")
    
    # Additional provider assignments
    assistant_provider: Optional[int] = Field(None, alias="ProvAssistant", description="Assistant provider number")
    
    # Operatory capacity
    capacity: Optional[int] = Field(None, alias="Capacity", description="Operatory capacity")
    
    # Equipment information
    equipment_list: Optional[str] = Field(None, alias="EquipmentList", description="Equipment list")
    
    # Special settings
    is_new_patient: bool = Field(False, alias="IsNewPatient", description="New patient operatory")
    
    # User permissions
    user_num: Optional[int] = Field(None, alias="UserNum", description="User number")


class CreateOperatoryRequest(BaseModel):
    """Request model for creating a new operatory/room."""
    
    # Required fields
    name: str
    
    # Optional fields
    description: Optional[str] = None
    is_active: bool = True


class UpdateOperatoryRequest(BaseModel):
    """Request model for updating an existing operatory/room."""
    
    # All fields are optional for updates
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class OperatoryListResponse(BaseModel):
    """Response model for operatory/room list operations."""
    
    operatories: List[Operatory]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class OperatorySearchRequest(BaseModel):
    """Request model for searching operatory/rooms."""
    
    name: Optional[str] = None
    is_active: Optional[bool] = None
    
    # Pagination
    page: Optional[int] = 1
    per_page: Optional[int] = 50

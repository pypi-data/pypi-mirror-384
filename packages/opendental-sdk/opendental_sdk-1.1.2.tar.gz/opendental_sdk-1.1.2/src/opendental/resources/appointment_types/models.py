"""Appointment types models for Open Dental SDK."""

from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import Field

from ...base.models import BaseModel


class AppointmentType(BaseModel):
    """Appointment type model."""
    
    # Primary identifiers
    id: int = Field(..., alias="AppointmentTypeNum", description="Appointment type number (primary key)")
    appointment_type_num: int = Field(..., alias="AppointmentTypeNum", description="Appointment type number")
    
    # Basic information
    name: str = Field(..., alias="AppointmentTypeName", description="Appointment type name")
    description: Optional[str] = Field(None, alias="Description", description="Appointment type description")
    code: Optional[str] = Field(None, alias="AppointmentTypeCode", description="Appointment type code")
    
    # Timing
    duration: int = Field(..., alias="Duration", description="Duration in minutes")
    default_time: Optional[str] = Field(None, alias="DefaultTime", description="Default appointment time")
    pattern: Optional[str] = Field(None, alias="Pattern", description="Time pattern")
    
    # Configuration
    is_active: bool = Field(True, alias="IsActive", description="Whether appointment type is active")
    is_hidden: bool = Field(False, alias="IsHidden", description="Hidden from lists")
    color: Optional[str] = Field(None, alias="AppointmentTypeColor", description="Appointment type color (hex code)")
    
    # Scheduling constraints
    max_per_day: Optional[int] = Field(None, alias="MaxPerDay", description="Maximum appointments per day")
    buffer_time_before: Optional[int] = Field(None, alias="BufferTimeBefore", description="Buffer time before appointment (minutes)")
    buffer_time_after: Optional[int] = Field(None, alias="BufferTimeAfter", description="Buffer time after appointment (minutes)")
    
    # Provider restrictions
    allowed_providers: Optional[List[int]] = Field(None, alias="AllowedProviders", description="List of allowed provider IDs")
    required_provider_type: Optional[str] = Field(None, alias="RequiredProviderType", description="Required provider type")
    
    # Operatory requirements
    operatory_requirements: Optional[str] = Field(None, alias="OperatoryRequirements", description="Operatory requirements")
    preferred_operatories: Optional[List[int]] = Field(None, alias="PreferredOperatories", description="List of preferred operatory IDs")
    
    # Billing
    default_procedure_codes: Optional[List[str]] = Field(None, alias="DefaultProcedureCodes", description="Default procedure codes")
    estimated_cost: Optional[Decimal] = Field(None, alias="EstimatedCost", description="Estimated cost")
    
    # Timestamps
    date_created: Optional[datetime] = Field(None, alias="DateCreated", description="Date created")
    date_modified: Optional[datetime] = Field(None, alias="DateModified", description="Date last modified")


class CreateAppointmentTypeRequest(BaseModel):
    """Request model for creating a new appointment type."""
    
    # Required fields
    name: str = Field(..., alias="AppointmentTypeName", description="Appointment type name")
    duration: int = Field(..., alias="Duration", description="Duration in minutes")
    
    # Optional fields
    description: Optional[str] = Field(None, alias="Description", description="Appointment type description")
    code: Optional[str] = Field(None, alias="AppointmentTypeCode", description="Appointment type code")
    default_time: Optional[str] = Field(None, alias="DefaultTime", description="Default appointment time")
    pattern: Optional[str] = Field(None, alias="Pattern", description="Time pattern")
    
    # Configuration
    is_active: bool = Field(True, alias="IsActive", description="Whether appointment type is active")
    is_hidden: bool = Field(False, alias="IsHidden", description="Hidden from lists")
    color: Optional[str] = Field(None, alias="AppointmentTypeColor", description="Appointment type color (hex code)")
    
    # Scheduling constraints
    max_per_day: Optional[int] = Field(None, alias="MaxPerDay", description="Maximum appointments per day")
    buffer_time_before: Optional[int] = Field(None, alias="BufferTimeBefore", description="Buffer time before appointment (minutes)")
    buffer_time_after: Optional[int] = Field(None, alias="BufferTimeAfter", description="Buffer time after appointment (minutes)")
    
    # Provider restrictions
    allowed_providers: Optional[List[int]] = Field(None, alias="AllowedProviders", description="List of allowed provider IDs")
    required_provider_type: Optional[str] = Field(None, alias="RequiredProviderType", description="Required provider type")
    
    # Operatory requirements
    operatory_requirements: Optional[str] = Field(None, alias="OperatoryRequirements", description="Operatory requirements")
    preferred_operatories: Optional[List[int]] = Field(None, alias="PreferredOperatories", description="List of preferred operatory IDs")
    
    # Billing
    default_procedure_codes: Optional[List[str]] = Field(None, alias="DefaultProcedureCodes", description="Default procedure codes")
    estimated_cost: Optional[Decimal] = Field(None, alias="EstimatedCost", description="Estimated cost")


class UpdateAppointmentTypeRequest(BaseModel):
    """Request model for updating an existing appointment type."""
    
    # All fields are optional for updates
    name: Optional[str] = Field(None, alias="AppointmentTypeName", description="Appointment type name")
    duration: Optional[int] = Field(None, alias="Duration", description="Duration in minutes")
    description: Optional[str] = Field(None, alias="Description", description="Appointment type description")
    code: Optional[str] = Field(None, alias="AppointmentTypeCode", description="Appointment type code")
    default_time: Optional[str] = Field(None, alias="DefaultTime", description="Default appointment time")
    pattern: Optional[str] = Field(None, alias="Pattern", description="Time pattern")
    
    # Configuration
    is_active: Optional[bool] = Field(None, alias="IsActive", description="Whether appointment type is active")
    is_hidden: Optional[bool] = Field(None, alias="IsHidden", description="Hidden from lists")
    color: Optional[str] = Field(None, alias="AppointmentTypeColor", description="Appointment type color (hex code)")
    
    # Scheduling constraints
    max_per_day: Optional[int] = Field(None, alias="MaxPerDay", description="Maximum appointments per day")
    buffer_time_before: Optional[int] = Field(None, alias="BufferTimeBefore", description="Buffer time before appointment (minutes)")
    buffer_time_after: Optional[int] = Field(None, alias="BufferTimeAfter", description="Buffer time after appointment (minutes)")
    
    # Provider restrictions
    allowed_providers: Optional[List[int]] = Field(None, alias="AllowedProviders", description="List of allowed provider IDs")
    required_provider_type: Optional[str] = Field(None, alias="RequiredProviderType", description="Required provider type")
    
    # Operatory requirements
    operatory_requirements: Optional[str] = Field(None, alias="OperatoryRequirements", description="Operatory requirements")
    preferred_operatories: Optional[List[int]] = Field(None, alias="PreferredOperatories", description="List of preferred operatory IDs")
    
    # Billing
    default_procedure_codes: Optional[List[str]] = Field(None, alias="DefaultProcedureCodes", description="Default procedure codes")
    estimated_cost: Optional[Decimal] = Field(None, alias="EstimatedCost", description="Estimated cost")


class AppointmentTypeListResponse(BaseModel):
    """Response model for appointment type list operations."""
    
    appointment_types: List[AppointmentType]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class AppointmentTypeSearchRequest(BaseModel):
    """Request model for searching appointment types."""
    
    name: Optional[str] = Field(None, alias="AppointmentTypeName", description="Appointment type name to search for")
    code: Optional[str] = Field(None, alias="AppointmentTypeCode", description="Appointment type code to search for")
    is_active: Optional[bool] = Field(None, alias="IsActive", description="Filter by active status")
    is_hidden: Optional[bool] = Field(None, alias="IsHidden", description="Filter by hidden status")
    duration_min: Optional[int] = Field(None, alias="DurationMin", description="Minimum duration in minutes")
    duration_max: Optional[int] = Field(None, alias="DurationMax", description="Maximum duration in minutes")
    
    # Pagination
    page: Optional[int] = Field(1, alias="Page", description="Page number for pagination")
    per_page: Optional[int] = Field(50, alias="PerPage", description="Number of items per page")
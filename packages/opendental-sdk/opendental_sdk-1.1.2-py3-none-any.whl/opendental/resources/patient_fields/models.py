"""patientfields models for Open Dental SDK."""

from datetime import datetime
from typing import Optional, List

from ...base.models import BaseModel


class PatientField(BaseModel):
    """PatientField model."""
    
    # Primary identifiers
    id: int
    patient_fields_num: int
    
    # Basic information
    name: str
    description: Optional[str] = None
    
    # Status
    is_active: bool = True
    
    # Timestamps
    date_created: Optional[datetime] = None
    date_modified: Optional[datetime] = None


class CreatePatientFieldRequest(BaseModel):
    """Request model for creating a new patient field."""
    
    # Required fields
    name: str
    
    # Optional fields
    description: Optional[str] = None
    is_active: bool = True


class UpdatePatientFieldRequest(BaseModel):
    """Request model for updating an existing patient field."""
    
    # All fields are optional for updates
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class PatientFieldListResponse(BaseModel):
    """Response model for patient field list operations."""
    
    patient_fields: List[PatientField]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class PatientFieldSearchRequest(BaseModel):
    """Request model for searching patient fields."""
    
    name: Optional[str] = None
    is_active: Optional[bool] = None
    
    # Pagination
    page: Optional[int] = 1
    per_page: Optional[int] = 50

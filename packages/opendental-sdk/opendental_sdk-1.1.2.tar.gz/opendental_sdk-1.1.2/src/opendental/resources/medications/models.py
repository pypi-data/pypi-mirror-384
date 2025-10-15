"""Medication models for Open Dental SDK."""

from datetime import datetime, date
from typing import Optional, List

from pydantic import Field

from ...base.models import BaseModel


class Medication(BaseModel):
    """Medication model."""
    
    # Primary identifiers
    id: int = Field(..., alias="MedicationNum", description="Medication number (primary key)")
    medication_num: int = Field(..., alias="MedicationNum", description="Medication number")
    
    # Patient information
    pat_num: int = Field(..., alias="PatNum", description="Patient number")
    
    # Medication details
    med_name: str = Field(..., alias="MedName", description="Medication name")
    generic_name: Optional[str] = Field(None, alias="GenericName", description="Generic medication name")
    med_note: Optional[str] = Field(None, alias="MedNote", description="Medication notes")
    rx_cui: Optional[str] = Field(None, alias="RxCui", description="RxNorm CUI identifier")
    
    # Dosage information
    dosage_amt: Optional[str] = Field(None, alias="DosageAmt", description="Dosage amount")
    dosage_unit: Optional[str] = Field(None, alias="DosageUnit", description="Dosage unit")
    directions: Optional[str] = Field(None, alias="Directions", description="Medication directions")
    
    # Dates
    date_start: Optional[date] = Field(None, alias="DateStart", description="Start date")
    date_stop: Optional[date] = Field(None, alias="DateStop", description="Stop date")
    
    # Status
    is_active: bool = Field(True, alias="IsActive", description="Active status")
    
    # Timestamps
    date_created: Optional[datetime] = Field(None, alias="DateCreated", description="Creation timestamp")
    date_modified: Optional[datetime] = Field(None, alias="DateModified", description="Last modification timestamp")


class CreateMedicationRequest(BaseModel):
    """Request model for creating a new medication."""
    
    # Required fields
    pat_num: int = Field(..., alias="PatNum", description="Patient number")
    med_name: str = Field(..., alias="MedName", description="Medication name")
    
    # Optional fields
    generic_name: Optional[str] = Field(None, alias="GenericName", description="Generic medication name")
    med_note: Optional[str] = Field(None, alias="MedNote", description="Medication notes")
    rx_cui: Optional[str] = Field(None, alias="RxCui", description="RxNorm CUI identifier")
    dosage_amt: Optional[str] = Field(None, alias="DosageAmt", description="Dosage amount")
    dosage_unit: Optional[str] = Field(None, alias="DosageUnit", description="Dosage unit")
    directions: Optional[str] = Field(None, alias="Directions", description="Medication directions")
    date_start: Optional[date] = Field(None, alias="DateStart", description="Start date")
    date_stop: Optional[date] = Field(None, alias="DateStop", description="Stop date")
    is_active: bool = Field(True, alias="IsActive", description="Active status")


class UpdateMedicationRequest(BaseModel):
    """Request model for updating an existing medication."""
    
    # All fields are optional for updates
    med_name: Optional[str] = Field(None, alias="MedName", description="Medication name")
    generic_name: Optional[str] = Field(None, alias="GenericName", description="Generic medication name")
    med_note: Optional[str] = Field(None, alias="MedNote", description="Medication notes")
    rx_cui: Optional[str] = Field(None, alias="RxCui", description="RxNorm CUI identifier")
    dosage_amt: Optional[str] = Field(None, alias="DosageAmt", description="Dosage amount")
    dosage_unit: Optional[str] = Field(None, alias="DosageUnit", description="Dosage unit")
    directions: Optional[str] = Field(None, alias="Directions", description="Medication directions")
    date_start: Optional[date] = Field(None, alias="DateStart", description="Start date")
    date_stop: Optional[date] = Field(None, alias="DateStop", description="Stop date")
    is_active: Optional[bool] = Field(None, alias="IsActive", description="Active status")


class MedicationListResponse(BaseModel):
    """Response model for medication list operations."""
    
    medications: List[Medication]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class MedicationSearchRequest(BaseModel):
    """Request model for searching medications."""
    
    pat_num: Optional[int] = Field(None, alias="PatNum", description="Patient number")
    med_name: Optional[str] = Field(None, alias="MedName", description="Medication name")
    generic_name: Optional[str] = Field(None, alias="GenericName", description="Generic medication name")
    rx_cui: Optional[str] = Field(None, alias="RxCui", description="RxNorm CUI identifier")
    is_active: Optional[bool] = Field(None, alias="IsActive", description="Active status")
    
    # Pagination
    page: Optional[int] = Field(1, alias="Page", description="Page number")
    per_page: Optional[int] = Field(50, alias="PerPage", description="Results per page")
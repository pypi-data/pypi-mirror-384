"""Allergy models for Open Dental SDK."""

from datetime import datetime, date
from typing import Optional, List

from ...base.models import BaseModel


class Allergy(BaseModel):
    """Allergy model."""
    
    # Primary identifiers
    id: int
    allergy_num: int
    
    # Patient information
    pat_num: int
    
    # Allergy details
    allergen: str
    allergy_def_num: Optional[int] = None
    severity: Optional[str] = None
    reaction: Optional[str] = None
    
    # Status
    is_active: bool = True
    
    # Timestamps
    date_adverse_reaction: Optional[date] = None
    date_created: Optional[datetime] = None
    date_modified: Optional[datetime] = None


class CreateAllergyRequest(BaseModel):
    """Request model for creating a new allergy."""
    
    # Required fields
    pat_num: int
    allergen: str
    
    # Optional fields
    allergy_def_num: Optional[int] = None
    severity: Optional[str] = None
    reaction: Optional[str] = None
    is_active: bool = True
    date_adverse_reaction: Optional[date] = None


class UpdateAllergyRequest(BaseModel):
    """Request model for updating an existing allergy."""
    
    # All fields are optional for updates
    allergen: Optional[str] = None
    allergy_def_num: Optional[int] = None
    severity: Optional[str] = None
    reaction: Optional[str] = None
    is_active: Optional[bool] = None
    date_adverse_reaction: Optional[date] = None


class AllergyListResponse(BaseModel):
    """Response model for allergy list operations."""
    
    allergies: List[Allergy]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class AllergySearchRequest(BaseModel):
    """Request model for searching allergies."""
    
    pat_num: Optional[int] = None
    allergen: Optional[str] = None
    allergy_def_num: Optional[int] = None
    severity: Optional[str] = None
    is_active: Optional[bool] = None
    
    # Pagination
    page: Optional[int] = 1
    per_page: Optional[int] = 50
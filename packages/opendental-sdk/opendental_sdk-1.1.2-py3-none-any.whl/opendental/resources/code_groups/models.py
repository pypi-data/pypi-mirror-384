"""Code groups models for Open Dental SDK."""

from typing import Optional, List
from pydantic import Field

from ...base.models import BaseModel


class CodeGroup(BaseModel):
    """Code group model."""
    
    # Primary identifier
    id: Optional[int] = Field(None, alias="CodeGroupNum")
    code_group_num: Optional[int] = Field(None, alias="CodeGroupNum")
    
    # Group details
    group_name: str = Field(..., alias="GroupName")
    proc_codes: Optional[str] = Field(None, alias="ProcCodes")  # Comma-delimited string
    code_group_fixed: Optional[str] = Field(None, alias="CodeGroupFixed")
    
    # Visibility settings
    is_hidden: Optional[bool] = Field(False, alias="IsHidden")
    show_in_age_limit: Optional[bool] = Field(False, alias="ShowInAgeLimit")
    show_in_frequency: Optional[bool] = Field(False, alias="ShowInFrequency")
    show_in_other: Optional[bool] = Field(False, alias="ShowInOther")


class CreateCodeGroupRequest(BaseModel):
    """Request model for creating a new code group."""
    
    # Required field
    group_name: str = Field(..., alias="GroupName")
    
    # Optional fields
    proc_codes: Optional[str] = Field(None, alias="ProcCodes")  # Comma-delimited string
    code_group_fixed: Optional[str] = Field(None, alias="CodeGroupFixed")
    is_hidden: Optional[bool] = Field(False, alias="IsHidden")
    show_in_age_limit: Optional[bool] = Field(False, alias="ShowInAgeLimit")
    show_in_frequency: Optional[bool] = Field(False, alias="ShowInFrequency")
    show_in_other: Optional[bool] = Field(False, alias="ShowInOther")


class UpdateCodeGroupRequest(BaseModel):
    """Request model for updating an existing code group."""
    
    # All fields are optional for updates
    group_name: Optional[str] = Field(None, alias="GroupName")
    proc_codes: Optional[str] = Field(None, alias="ProcCodes")  # Comma-delimited string
    code_group_fixed: Optional[str] = Field(None, alias="CodeGroupFixed")
    is_hidden: Optional[bool] = Field(None, alias="IsHidden")
    show_in_age_limit: Optional[bool] = Field(None, alias="ShowInAgeLimit")
    show_in_frequency: Optional[bool] = Field(None, alias="ShowInFrequency")
    show_in_other: Optional[bool] = Field(None, alias="ShowInOther")


class CodeGroupListResponse(BaseModel):
    """Response model for code group list operations."""
    
    code_groups: List[CodeGroup]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None
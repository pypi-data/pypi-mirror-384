"""Fee models for Open Dental SDK."""

from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
from pydantic import Field

from ...base.models import BaseModel


class Fee(BaseModel):
    """Fee model."""
    
    # Primary identifiers
    id: int = Field(..., alias="FeeNum", description="Fee number (primary key)")
    fee_num: int = Field(..., alias="FeeNum", description="Fee number")
    
    # Fee details
    code_num: int = Field(..., alias="CodeNum", description="Procedure code number")
    fee_amount: Decimal = Field(..., alias="Amount", description="Fee amount")
    
    # Fee schedule
    fee_sched: int = Field(..., alias="FeeSched", description="Fee schedule number")
    
    # Provider and clinic
    prov_num: Optional[int] = Field(None, alias="ProvNum", description="Provider number")
    clinic_num: Optional[int] = Field(None, alias="ClinicNum", description="Clinic number")
    
    # Timestamps
    date_created: Optional[datetime] = Field(None, alias="DateCreated", description="Date created")
    date_modified: Optional[datetime] = Field(None, alias="DateModified", description="Date modified")


class CreateFeeRequest(BaseModel):
    """Request model for creating a new fee."""
    
    # Required fields
    code_num: int = Field(..., alias="CodeNum", description="Procedure code number")
    fee_amount: Decimal = Field(..., alias="Amount", description="Fee amount")
    fee_sched: int = Field(..., alias="FeeSched", description="Fee schedule number")
    
    # Optional fields
    prov_num: Optional[int] = Field(None, alias="ProvNum", description="Provider number")
    clinic_num: Optional[int] = Field(None, alias="ClinicNum", description="Clinic number")


class UpdateFeeRequest(BaseModel):
    """Request model for updating an existing fee."""
    
    # All fields are optional for updates
    code_num: Optional[int] = Field(None, alias="CodeNum", description="Procedure code number")
    fee_amount: Optional[Decimal] = Field(None, alias="Amount", description="Fee amount")
    fee_sched: Optional[int] = Field(None, alias="FeeSched", description="Fee schedule number")
    prov_num: Optional[int] = Field(None, alias="ProvNum", description="Provider number")
    clinic_num: Optional[int] = Field(None, alias="ClinicNum", description="Clinic number")


class FeeListResponse(BaseModel):
    """Response model for fee list operations."""
    
    fees: List[Fee]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class FeeSearchRequest(BaseModel):
    """Request model for searching fees."""
    
    code_num: Optional[int] = Field(None, alias="CodeNum", description="Procedure code number")
    fee_sched: Optional[int] = Field(None, alias="FeeSched", description="Fee schedule number")
    prov_num: Optional[int] = Field(None, alias="ProvNum", description="Provider number")
    clinic_num: Optional[int] = Field(None, alias="ClinicNum", description="Clinic number")
    
    # Pagination
    page: Optional[int] = Field(1, description="Page number for pagination")
    per_page: Optional[int] = Field(50, description="Number of items per page")


class FeeSchedule(BaseModel):
    """Fee schedule model."""
    
    # Primary identifiers
    id: int = Field(..., alias="FeeSchedNum", description="Fee schedule number (primary key)")
    fee_sched_num: int = Field(..., alias="FeeSchedNum", description="Fee schedule number")
    
    # Schedule details
    description: str = Field(..., alias="Description", description="Fee schedule description")
    fee_sched_type: Optional[str] = Field(None, alias="FeeSchedType", description="Fee schedule type")
    
    # Status
    is_hidden: bool = Field(False, alias="IsHidden", description="Whether the fee schedule is hidden")
    
    # Timestamps
    date_created: Optional[datetime] = Field(None, alias="DateCreated", description="Date created")
    date_modified: Optional[datetime] = Field(None, alias="DateModified", description="Date modified")


class CreateFeeScheduleRequest(BaseModel):
    """Request model for creating a new fee schedule."""
    
    # Required fields
    description: str = Field(..., alias="Description", description="Fee schedule description")
    
    # Optional fields
    fee_sched_type: Optional[str] = Field(None, alias="FeeSchedType", description="Fee schedule type")
    is_hidden: bool = Field(False, alias="IsHidden", description="Whether the fee schedule is hidden")


class UpdateFeeScheduleRequest(BaseModel):
    """Request model for updating an existing fee schedule."""
    
    # All fields are optional for updates
    description: Optional[str] = Field(None, alias="Description", description="Fee schedule description")
    fee_sched_type: Optional[str] = Field(None, alias="FeeSchedType", description="Fee schedule type")
    is_hidden: Optional[bool] = Field(None, alias="IsHidden", description="Whether the fee schedule is hidden")
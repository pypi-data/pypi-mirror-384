"""Insurance Plan models for Open Dental SDK."""

from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
from pydantic import Field

from ...base.models import BaseModel


class InsurancePlan(BaseModel):
    """Insurance plan model."""
    
    # Primary identifiers
    id: int = Field(..., alias="InsurancePlanNum", description="Insurance plan number (primary key)")
    plan_num: int = Field(..., alias="PlanNum", description="Plan number")
    
    # Plan details
    group_name: str = Field(..., alias="GroupName", description="Group name")
    group_num: Optional[str] = Field(None, alias="GroupNum", description="Group number")
    plan_note: Optional[str] = Field(None, alias="PlanNote", description="Plan notes")
    
    # Carrier information
    carrier_num: int = Field(..., alias="CarrierNum", description="Carrier number")
    
    # Employment information
    employer: Optional[str] = Field(None, alias="Employer", description="Employer name")
    
    # Coverage details
    benefits_note: Optional[str] = Field(None, alias="BenefitsNote", description="Benefits notes")
    fee_sched: Optional[int] = Field(None, alias="FeeSchedNum", description="Fee schedule number")
    plan_type: Optional[str] = Field(None, alias="PlanType", description="Plan type")
    
    # Deductibles and maximums
    deductible: Optional[Decimal] = Field(None, alias="Deductible", description="Individual deductible amount")
    deductible_family: Optional[Decimal] = Field(None, alias="DeductibleFamily", description="Family deductible amount")
    annual_max: Optional[Decimal] = Field(None, alias="AnnualMax", description="Annual maximum amount")
    annual_max_family: Optional[Decimal] = Field(None, alias="AnnualMaxFamily", description="Family annual maximum amount")
    
    # Percentage coverages
    percent_primary: Optional[int] = Field(None, alias="PercentPrimary", description="Primary coverage percentage")
    percent_secondary: Optional[int] = Field(None, alias="PercentSecondary", description="Secondary coverage percentage")
    
    # Waiting periods
    months_general: Optional[int] = Field(None, alias="MonthsGeneral", description="General waiting period in months")
    months_preventive: Optional[int] = Field(None, alias="MonthsPreventive", description="Preventive waiting period in months")
    months_basic: Optional[int] = Field(None, alias="MonthsBasic", description="Basic services waiting period in months")
    months_major: Optional[int] = Field(None, alias="MonthsMajor", description="Major services waiting period in months")
    months_accident: Optional[int] = Field(None, alias="MonthsAccident", description="Accident waiting period in months")
    
    # Status
    is_hidden: bool = Field(False, alias="IsHidden", description="Whether the plan is hidden")
    
    # Timestamps
    date_created: Optional[datetime] = Field(None, alias="DateCreated", description="Date the plan was created")
    date_modified: Optional[datetime] = Field(None, alias="DateModified", description="Date the plan was last modified")


class CreateInsurancePlanRequest(BaseModel):
    """Request model for creating a new insurance plan."""
    
    # Required fields
    group_name: str = Field(..., alias="GroupName", description="Group name")
    carrier_num: int = Field(..., alias="CarrierNum", description="Carrier number")
    
    # Optional fields
    group_num: Optional[str] = Field(None, alias="GroupNum", description="Group number")
    plan_note: Optional[str] = Field(None, alias="PlanNote", description="Plan notes")
    employer: Optional[str] = Field(None, alias="Employer", description="Employer name")
    benefits_note: Optional[str] = Field(None, alias="BenefitsNote", description="Benefits notes")
    fee_sched: Optional[int] = Field(None, alias="FeeSchedNum", description="Fee schedule number")
    plan_type: Optional[str] = Field(None, alias="PlanType", description="Plan type")
    
    # Financial details
    deductible: Optional[Decimal] = Field(None, alias="Deductible", description="Individual deductible amount")
    deductible_family: Optional[Decimal] = Field(None, alias="DeductibleFamily", description="Family deductible amount")
    annual_max: Optional[Decimal] = Field(None, alias="AnnualMax", description="Annual maximum amount")
    annual_max_family: Optional[Decimal] = Field(None, alias="AnnualMaxFamily", description="Family annual maximum amount")
    
    # Coverage percentages
    percent_primary: Optional[int] = Field(None, alias="PercentPrimary", description="Primary coverage percentage")
    percent_secondary: Optional[int] = Field(None, alias="PercentSecondary", description="Secondary coverage percentage")
    
    # Waiting periods
    months_general: Optional[int] = Field(None, alias="MonthsGeneral", description="General waiting period in months")
    months_preventive: Optional[int] = Field(None, alias="MonthsPreventive", description="Preventive waiting period in months")
    months_basic: Optional[int] = Field(None, alias="MonthsBasic", description="Basic services waiting period in months")
    months_major: Optional[int] = Field(None, alias="MonthsMajor", description="Major services waiting period in months")
    months_accident: Optional[int] = Field(None, alias="MonthsAccident", description="Accident waiting period in months")
    
    # Status
    is_hidden: bool = Field(False, alias="IsHidden", description="Whether the plan is hidden")


class UpdateInsurancePlanRequest(BaseModel):
    """Request model for updating an existing insurance plan."""
    
    # All fields are optional for updates
    group_name: Optional[str] = Field(None, alias="GroupName", description="Group name")
    group_num: Optional[str] = Field(None, alias="GroupNum", description="Group number")
    plan_note: Optional[str] = Field(None, alias="PlanNote", description="Plan notes")
    carrier_num: Optional[int] = Field(None, alias="CarrierNum", description="Carrier number")
    employer: Optional[str] = Field(None, alias="Employer", description="Employer name")
    benefits_note: Optional[str] = Field(None, alias="BenefitsNote", description="Benefits notes")
    fee_sched: Optional[int] = Field(None, alias="FeeSchedNum", description="Fee schedule number")
    plan_type: Optional[str] = Field(None, alias="PlanType", description="Plan type")
    
    # Financial details
    deductible: Optional[Decimal] = Field(None, alias="Deductible", description="Individual deductible amount")
    deductible_family: Optional[Decimal] = Field(None, alias="DeductibleFamily", description="Family deductible amount")
    annual_max: Optional[Decimal] = Field(None, alias="AnnualMax", description="Annual maximum amount")
    annual_max_family: Optional[Decimal] = Field(None, alias="AnnualMaxFamily", description="Family annual maximum amount")
    
    # Coverage percentages
    percent_primary: Optional[int] = Field(None, alias="PercentPrimary", description="Primary coverage percentage")
    percent_secondary: Optional[int] = Field(None, alias="PercentSecondary", description="Secondary coverage percentage")
    
    # Waiting periods
    months_general: Optional[int] = Field(None, alias="MonthsGeneral", description="General waiting period in months")
    months_preventive: Optional[int] = Field(None, alias="MonthsPreventive", description="Preventive waiting period in months")
    months_basic: Optional[int] = Field(None, alias="MonthsBasic", description="Basic services waiting period in months")
    months_major: Optional[int] = Field(None, alias="MonthsMajor", description="Major services waiting period in months")
    months_accident: Optional[int] = Field(None, alias="MonthsAccident", description="Accident waiting period in months")
    
    # Status
    is_hidden: Optional[bool] = Field(None, alias="IsHidden", description="Whether the plan is hidden")


class InsurancePlanListResponse(BaseModel):
    """Response model for insurance plan list operations."""
    
    insurance_plans: List[InsurancePlan] = Field(..., alias="InsurancePlans", description="List of insurance plans")
    total: int = Field(..., alias="Total", description="Total number of insurance plans")
    page: Optional[int] = Field(None, alias="Page", description="Current page number")
    per_page: Optional[int] = Field(None, alias="PerPage", description="Number of items per page")


class InsurancePlanSearchRequest(BaseModel):
    """Request model for searching insurance plans."""
    
    group_name: Optional[str] = Field(None, alias="GroupName", description="Group name to search for")
    group_num: Optional[str] = Field(None, alias="GroupNum", description="Group number to search for")
    carrier_num: Optional[int] = Field(None, alias="CarrierNum", description="Carrier number to search for")
    employer: Optional[str] = Field(None, alias="Employer", description="Employer name to search for")
    plan_type: Optional[str] = Field(None, alias="PlanType", description="Plan type to search for")
    is_hidden: Optional[bool] = Field(None, alias="IsHidden", description="Whether to include hidden plans")
    
    # Pagination
    page: Optional[int] = Field(1, alias="Page", description="Page number for pagination")
    per_page: Optional[int] = Field(50, alias="PerPage", description="Number of items per page")
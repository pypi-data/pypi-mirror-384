"""Benefits models for Open Dental SDK."""

from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
from pydantic import Field

from ...base.models import BaseModel


class Benefit(BaseModel):
    """Benefit model."""
    
    # Primary identifiers
    id: Optional[int] = Field(None, alias="BenefitNum")
    benefit_num: Optional[int] = Field(None, alias="BenefitNum")
    
    # Plan association
    plan_num: Optional[int] = Field(None, alias="PlanNum")
    pat_plan_num: Optional[int] = Field(None, alias="PatPlanNum")
    
    # Benefit details
    code_num: Optional[int] = Field(None, alias="CodeNum")
    cov_cat_num: Optional[int] = Field(None, alias="CovCatNum")
    benefit_type: Optional[str] = Field(None, alias="BenefitType")
    percent: Optional[int] = Field(-1, alias="Percent")
    monetary_amt: Optional[float] = Field(None, alias="MonetaryAmt")
    time_period: Optional[str] = Field(None, alias="TimePeriod")  # Changed to str
    quantity_qualifier: Optional[str] = Field(None, alias="QuantityQualifier")  # Changed to str
    quantity: Optional[int] = Field(None, alias="Quantity")
    coverage_level: Optional[str] = Field(None, alias="CoverageLevel")  # Changed to str
    code_group_num: Optional[int] = Field(None, alias="CodeGroupNum")
    treat_area: Optional[str] = Field(None, alias="TreatArea")
    paint_type: Optional[str] = Field(None, alias="PaintType")
    proc_code: Optional[str] = Field(None, alias="procCode")
    
    
    # Timestamps
    date_created: Optional[datetime] = None
    date_modified: Optional[datetime] = None


class CreateBenefitRequest(BaseModel):
    """Request model for creating a new benefit."""
    
    # Plan association (at least one required)
    plan_num: Optional[int] = Field(None, alias="PlanNum")
    pat_plan_num: Optional[int] = Field(None, alias="PatPlanNum")
    
    # Benefit details
    code_num: Optional[int] = Field(0, alias="CodeNum")
    proc_code: Optional[str] = Field(None, alias="procCode")  # FK to procedurecode.ProcCode
    cov_cat_num: Optional[int] = Field(0, alias="CovCatNum")
    benefit_type: Optional[str] = Field(None, alias="BenefitType")
    coverage_level: Optional[str] = Field(None, alias="CoverageLevel")
    
    # Financial values
    percent: Optional[int] = Field(-1, alias="Percent")
    monetary_amt: Optional[float] = Field(None, alias="MonetaryAmt")
    
    # Time constraints
    time_period: Optional[str] = Field(None, alias="TimePeriod")
    quantity_qualifier: Optional[str] = Field(None, alias="QuantityQualifier")
    quantity: Optional[int] = Field(0, alias="Quantity")
    
    # Additional fields (v25.3.7)
    code_group_num: Optional[int] = Field(None, alias="CodeGroupNum")  # FK to codegroup.CodeGroupNum
    treat_area: Optional[str] = Field(None, alias="TreatArea")  # For Frequency Limitation benefits
    
    class Config:
        use_enum_values = True
        allow_population_by_field_name = True
        populate_by_name = True


class UpdateBenefitRequest(BaseModel):
    """Request model for updating an existing benefit."""
    
    # Benefit ID (required for update)
    benefit_num: Optional[int] = Field(None, alias="BenefitNum")
    
    # All other fields are optional for updates
    plan_num: Optional[int] = Field(None, alias="PlanNum")
    pat_plan_num: Optional[int] = Field(None, alias="PatPlanNum")
    code_num: Optional[int] = Field(None, alias="CodeNum")
    proc_code: Optional[str] = Field(None, alias="procCode")  # FK to procedurecode.ProcCode
    benefit_type: Optional[str] = Field(None, alias="BenefitType")
    coverage_level: Optional[str] = Field(None, alias="CoverageLevel")
    cov_cat_num: Optional[int] = Field(None, alias="CovCatNum")
    # Financial values
    percent: Optional[int] = Field(None, alias="Percent")
    monetary_amt: Optional[float] = Field(None, alias="MonetaryAmt")
    # Time constraints
    time_period: Optional[str] = Field(None, alias="TimePeriod")
    quantity_qualifier: Optional[str] = Field(None, alias="QuantityQualifier")
    quantity: Optional[int] = Field(None, alias="Quantity")
    # Additional fields (v25.3.7)
    code_group_num: Optional[int] = Field(None, alias="CodeGroupNum")  # FK to codegroup.CodeGroupNum
    treat_area: Optional[str] = Field(None, alias="TreatArea")  # For Frequency Limitation benefits
    
    class Config:
        use_enum_values = True
        allow_population_by_field_name = True
        populate_by_name = True


class BenefitListResponse(BaseModel):
    """Response model for benefit list operations."""
    
    benefits: List[Benefit]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class BenefitSearchRequest(BaseModel):
    """Request model for searching benefits."""
    
    plan_num: Optional[int] = None
    patient_num: Optional[int] = None
    procedure_code: Optional[str] = None
    coverage_level: Optional[str] = None
    benefit_type: Optional[str] = None
    benefit_year: Optional[int] = None
    
    # Pagination
    page: Optional[int] = 1
    per_page: Optional[int] = 50
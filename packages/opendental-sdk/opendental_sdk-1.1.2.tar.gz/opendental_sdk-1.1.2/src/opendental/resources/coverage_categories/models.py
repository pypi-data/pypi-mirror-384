"""Coverage Category models for the Open Dental API."""

from typing import Optional, List
from pydantic import Field
from ...base.models import BaseModel
from .types import EbenefitCat


class CoverageCategory(BaseModel):
    """
    Coverage Category (CovCat) model.
    
    Insurance categories are global and changes may affect all plans.
    Each Electronic Benefit Category must be assigned to a corresponding coverage category.
    """
    
    cov_cat_num: int = Field(..., alias="CovCatNum")
    description: str = Field(..., alias="Description")
    default_percent: int = Field(..., alias="DefaultPercent")  # -1 to 100, -1 means no percentage
    cov_order: int = Field(..., alias="CovOrder")  # Display order, lower = more general, higher = more specific
    is_hidden: str = Field(..., alias="IsHidden")  # "true" or "false"
    ebenefit_cat: str = Field(..., alias="EbenefitCat")  # Electronic Benefit Category

    class Config:
        populate_by_name = True


class CreateCoverageCategoryRequest(BaseModel):
    """
    Request model for creating a new coverage category.
    
    Important: Do not alter Insurance Categories without a full understanding of what this does
    as insurance categories are global and changes may affect all plans.
    
    One of each Electronic Benefit Category (EbenefitCat) must be assigned to a corresponding
    coverage category. There can be no duplicates and no missing categories in order for
    Open Dental Benefit Processing and Electronic Eligibility and Benefits to function properly.
    """
    
    description: str = Field(..., alias="Description")
    default_percent: Optional[int] = Field(-1, alias="DefaultPercent")  # -1 to 100, default -1
    is_hidden: Optional[str] = Field("false", alias="IsHidden")  # "true" or "false"
    ebenefit_cat: Optional[EbenefitCat] = Field(EbenefitCat.NONE, alias="EbenefitCat")

    class Config:
        use_enum_values = True
        populate_by_name = True


class UpdateCoverageCategoryRequest(BaseModel):
    """
    Request model for updating an existing coverage category.
    
    This affects all benefits that are currently tied to this CovCat.
    
    CovOrder is important as multiple benefits can apply to a single procedure code.
    If some benefits are of the same type, there is a hierarchy to determine which
    benefits affect insurance estimates.
    """
    
    description: Optional[str] = Field(None, alias="Description")
    default_percent: Optional[int] = Field(None, alias="DefaultPercent")  # -1 to 100
    cov_order: Optional[int] = Field(None, alias="CovOrder")
    is_hidden: Optional[str] = Field(None, alias="IsHidden")  # "true" or "false"
    ebenefit_cat: Optional[EbenefitCat] = Field(None, alias="EbenefitCat")

    class Config:
        use_enum_values = True
        populate_by_name = True


class CoverageCategoryListResponse(BaseModel):
    """Response model for coverage category list operations."""
    
    coverage_categories: List[CoverageCategory]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


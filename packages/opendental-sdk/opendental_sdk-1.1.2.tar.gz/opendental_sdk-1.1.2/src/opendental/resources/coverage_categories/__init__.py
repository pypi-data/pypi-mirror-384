"""Coverage Category resource for the Open Dental API."""

from .client import CoverageCategoryClient
from .models import (
    CoverageCategory,
    CreateCoverageCategoryRequest,
    UpdateCoverageCategoryRequest,
    CoverageCategoryListResponse,
)
from .types import EbenefitCat

__all__ = [
    "CoverageCategoryClient",
    "CoverageCategory",
    "CreateCoverageCategoryRequest",
    "UpdateCoverageCategoryRequest",
    "CoverageCategoryListResponse",
    "EbenefitCat",
]


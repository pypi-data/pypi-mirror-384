"""Benefits resource module."""

from .client import BenefitsClient
from .models import Benefit, CreateBenefitRequest, UpdateBenefitRequest

__all__ = ["BenefitsClient", "Benefit", "CreateBenefitRequest", "UpdateBenefitRequest"]
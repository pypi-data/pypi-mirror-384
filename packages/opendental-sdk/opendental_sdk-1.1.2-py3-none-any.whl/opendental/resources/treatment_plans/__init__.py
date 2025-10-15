"""Treatment Plans resource module."""

from .client import TreatmentPlansClient
from .models import TreatmentPlan, CreateTreatmentPlanRequest, UpdateTreatmentPlanRequest

__all__ = ["TreatmentPlansClient", "TreatmentPlan", "CreateTreatmentPlanRequest", "UpdateTreatmentPlanRequest"]
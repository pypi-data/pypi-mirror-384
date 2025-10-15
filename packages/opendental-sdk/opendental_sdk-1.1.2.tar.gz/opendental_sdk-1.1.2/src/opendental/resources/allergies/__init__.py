"""Allergies resource module."""

from .client import AllergiesClient
from .models import Allergy, CreateAllergyRequest, UpdateAllergyRequest

__all__ = ["AllergiesClient", "Allergy", "CreateAllergyRequest", "UpdateAllergyRequest"]
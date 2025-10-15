"""Clinics resource module."""

from .client import ClinicsClient
from .models import Clinic, CreateClinicRequest, UpdateClinicRequest

__all__ = ["ClinicsClient", "Clinic", "CreateClinicRequest", "UpdateClinicRequest"]
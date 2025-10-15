"""Appointment types resource module."""

from .client import AppointmentTypesClient
from .models import AppointmentType, CreateAppointmentTypeRequest, UpdateAppointmentTypeRequest

__all__ = ["AppointmentTypesClient", "AppointmentType", "CreateAppointmentTypeRequest", "UpdateAppointmentTypeRequest"]
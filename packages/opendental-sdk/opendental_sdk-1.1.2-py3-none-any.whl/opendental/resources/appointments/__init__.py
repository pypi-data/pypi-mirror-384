"""Appointments resource module."""

from .client import AppointmentsClient
from .models import Appointment, CreateAppointmentRequest, UpdateAppointmentRequest

__all__ = ["AppointmentsClient", "Appointment", "CreateAppointmentRequest", "UpdateAppointmentRequest"]
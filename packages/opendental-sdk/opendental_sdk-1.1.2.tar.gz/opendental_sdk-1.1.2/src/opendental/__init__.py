"""
Open Dental Python SDK

A simple, domain-driven Python SDK for the Open Dental API with full type safety.
Each resource is self-contained and owns its models.

Example usage:
    from opendental import OpenDentalClient
    from opendental.resources.patients.models import CreatePatientRequest
    from opendental.resources.procedures.models import CreateProcedureRequest
    from decimal import Decimal
    from datetime import date
    
    client = OpenDentalClient()
    
    # Get patient
    patient = client.patients.get(123)
    
    # Create patient with type safety
    new_patient = client.patients.create(
        CreatePatientRequest(
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        )
    )
    
    # Get appointments for patient
    appointments = client.appointments.get_by_patient(123)
    
    # Create a procedure
    procedure = client.procedures.create(
        CreateProcedureRequest(
            pat_num=123,
            prov_num=1,
            proc_code="D0120",
            proc_date=date.today(),
            proc_fee=Decimal("85.00")
        )
    )
    
    # Process a payment
    payment = client.payments.create_cash_payment(
        pat_num=123,
        amount=Decimal("100.00")
    )
"""

__version__ = "1.0.0"
__author__ = "Open Dental SDK Team"

from .client import OpenDentalClient
from .exceptions import (
    OpenDentalAPIError,
    OpenDentalValidationError,
    OpenDentalAuthenticationError,
    OpenDentalNotFoundError,
)

__all__ = [
    "OpenDentalClient",
    "OpenDentalAPIError",
    "OpenDentalValidationError",
    "OpenDentalAuthenticationError",
    "OpenDentalNotFoundError",
]

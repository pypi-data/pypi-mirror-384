"""Employees resource module."""

from .client import EmployeesClient
from .models import Employee, CreateEmployeeRequest, UpdateEmployeeRequest

__all__ = ["EmployeesClient", "Employee", "CreateEmployeeRequest", "UpdateEmployeeRequest"]
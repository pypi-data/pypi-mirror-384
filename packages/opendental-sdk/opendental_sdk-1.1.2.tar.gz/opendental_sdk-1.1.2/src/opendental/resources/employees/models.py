"""Employee models for Open Dental SDK."""

from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
from pydantic import Field

from ...base.models import BaseModel


class Employee(BaseModel):
    """Employee model with exact Open Dental database field mapping."""
    
    # Primary identifiers (exact database field mapping)
    id: int = Field(..., alias="EmployeeNum", description="Employee number (primary key)")
    emp_num: int = Field(..., alias="EmployeeNum", description="Employee number")
    
    # Personal information
    first_name: str = Field(..., alias="FName", description="Employee first name")
    last_name: str = Field(..., alias="LName", description="Employee last name")
    middle_name: Optional[str] = Field(None, alias="MiddleI", description="Middle initial")
    
    # Contact information
    email: Optional[str] = Field(None, alias="EmailWork", description="Work email address")
    phone: Optional[str] = Field(None, alias="PhoneExt", description="Phone extension")
    
    # Employment information
    employee_id: Optional[str] = Field(None, alias="EmpID", description="Employee ID")
    is_working: bool = Field(True, alias="IsWorking", description="Currently working flag")
    is_hidden: bool = Field(False, alias="IsHidden", description="Hidden from lists")
    
    # Login information
    user_name: Optional[str] = Field(None, alias="UserName", description="Username for login")
    password_hash: Optional[str] = Field(None, alias="PasswordHash", description="Password hash")
    
    # Payroll information
    payroll_id: Optional[str] = Field(None, alias="PayrollID", description="Payroll ID")
    
    # Timestamps
    date_hired: Optional[date] = Field(None, alias="DateHired", description="Date hired")
    date_terminated: Optional[date] = Field(None, alias="DateTerminated", description="Date terminated")
    date_created: Optional[datetime] = Field(None, alias="DateTStamp", description="Creation timestamp")
    date_modified: Optional[datetime] = Field(None, alias="DateTStamp", description="Last modified timestamp")
    
    # Clinic information
    clinic_num: Optional[int] = Field(None, alias="ClinicNum", description="Clinic number")
    
    # Schedule information
    is_instructor: bool = Field(False, alias="IsInstructor", description="Instructor flag")
    is_dentist: bool = Field(False, alias="IsDentist", description="Dentist flag")
    is_hygienist: bool = Field(False, alias="IsHygienist", description="Hygienist flag")
    
    # Additional Open Dental fields
    reports_to: Optional[int] = Field(None, alias="ReportsTo", description="Reports to employee number")
    wireless_phone: Optional[str] = Field(None, alias="WirelessPhone", description="Wireless phone number")
    email_personal: Optional[str] = Field(None, alias="EmailPersonal", description="Personal email address")
    is_clock_in: bool = Field(False, alias="IsClockIn", description="Clock in flag")
    
    # Security
    user_num: Optional[int] = Field(None, alias="UserNum", description="User number")
    
    # Employee color for scheduling
    employee_color: Optional[str] = Field(None, alias="EmployeeColor", description="Employee color")
    
    # Additional employee flags
    is_active: bool = Field(True, alias="IsActive", description="Active employee flag")
    is_provider: bool = Field(False, alias="IsProvider", description="Provider flag")
    
    # Employment details
    employee_note: Optional[str] = Field(None, alias="EmployeeNote", description="Employee note")
    
    # Custom fields
    custom1: Optional[str] = Field(None, alias="Custom1", description="Custom field 1")
    custom2: Optional[str] = Field(None, alias="Custom2", description="Custom field 2")
    custom3: Optional[str] = Field(None, alias="Custom3", description="Custom field 3")


class CreateEmployeeRequest(BaseModel):
    """Request model for creating a new employee."""
    
    # Required fields
    first_name: str
    last_name: str
    
    # Optional personal information
    middle_name: Optional[str] = None
    
    # Contact information
    email: Optional[str] = None
    phone: Optional[str] = None
    
    # Employment information
    employee_id: Optional[str] = None
    is_working: bool = True
    is_hidden: bool = False
    
    # Login information
    user_name: Optional[str] = None
    password_hash: Optional[str] = None
    
    # Payroll information
    payroll_id: Optional[str] = None
    
    # Dates
    date_hired: Optional[date] = None
    
    # Clinic information
    clinic_num: Optional[int] = None
    
    # Schedule information
    is_instructor: bool = False
    is_dentist: bool = False
    is_hygienist: bool = False


class UpdateEmployeeRequest(BaseModel):
    """Request model for updating an existing employee."""
    
    # All fields are optional for updates
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    
    # Contact information
    email: Optional[str] = None
    phone: Optional[str] = None
    
    # Employment information
    employee_id: Optional[str] = None
    is_working: Optional[bool] = None
    is_hidden: Optional[bool] = None
    
    # Login information
    user_name: Optional[str] = None
    password_hash: Optional[str] = None
    
    # Payroll information
    payroll_id: Optional[str] = None
    
    # Dates
    date_hired: Optional[date] = None
    date_terminated: Optional[date] = None
    
    # Clinic information
    clinic_num: Optional[int] = None
    
    # Schedule information
    is_instructor: Optional[bool] = None
    is_dentist: Optional[bool] = None
    is_hygienist: Optional[bool] = None


class EmployeeListResponse(BaseModel):
    """Response model for employee list operations."""
    
    employees: List[Employee]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class EmployeeSearchRequest(BaseModel):
    """Request model for searching employees."""
    
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    employee_id: Optional[str] = None
    is_working: Optional[bool] = None
    is_hidden: Optional[bool] = None
    clinic_num: Optional[int] = None
    
    # Pagination
    page: Optional[int] = 1
    per_page: Optional[int] = 50
"""schedules models for Open Dental SDK."""

from datetime import datetime, date, time
from typing import Optional, List
from pydantic import Field

from ...base.models import BaseModel


class Schedule(BaseModel):
    """Schedule model."""
    
    # Primary identifiers
    id: int = Field(..., alias="ScheduleNum", description="Schedule number (primary key)")
    
    # Schedule timing
    schedule_date: date = Field(..., alias="SchedDate", description="Schedule date")
    start_time: time = Field(..., alias="StartTime", description="Start time")
    stop_time: time = Field(..., alias="StopTime", description="Stop time")
    
    # Provider and operatory
    prov_num: int = Field(..., alias="ProvNum", description="Provider number")
    operatory_num: Optional[int] = Field(None, alias="OperatoryNum", description="Operatory number")
    
    # Schedule details
    block_text: Optional[str] = Field(None, alias="BlockText", description="Block text description")
    note: Optional[str] = Field(None, alias="Note", description="Schedule note")
    
    # Schedule type and status
    schedule_type: Optional[int] = Field(None, alias="ScheduleType", description="Schedule type")
    status: Optional[int] = Field(None, alias="Status", description="Schedule status")
    
    # Employee assignment
    employee_num: Optional[int] = Field(None, alias="EmployeeNum", description="Employee number")
    
    # Timestamps
    date_created: Optional[datetime] = Field(None, alias="DateTStamp", description="Date created timestamp")
    sec_date_t_edit: Optional[datetime] = Field(None, alias="SecDateTEdit", description="Security date edited")


class CreateScheduleRequest(BaseModel):
    """Request model for creating a new schedule."""
    
    # Required fields
    schedule_date: date = Field(..., alias="SchedDate", description="Schedule date")
    start_time: time = Field(..., alias="StartTime", description="Start time")
    stop_time: time = Field(..., alias="StopTime", description="Stop time")
    prov_num: int = Field(..., alias="ProvNum", description="Provider number")
    
    # Optional fields
    operatory_num: Optional[int] = Field(None, alias="OperatoryNum", description="Operatory number")
    block_text: Optional[str] = Field(None, alias="BlockText", description="Block text description")
    note: Optional[str] = Field(None, alias="Note", description="Schedule note")
    schedule_type: Optional[int] = Field(None, alias="ScheduleType", description="Schedule type")
    status: Optional[int] = Field(None, alias="Status", description="Schedule status")
    employee_num: Optional[int] = Field(None, alias="EmployeeNum", description="Employee number")


class UpdateScheduleRequest(BaseModel):
    """Request model for updating an existing schedule."""
    
    # All fields are optional for updates
    schedule_date: Optional[date] = Field(None, alias="SchedDate", description="Schedule date")
    start_time: Optional[time] = Field(None, alias="StartTime", description="Start time")
    stop_time: Optional[time] = Field(None, alias="StopTime", description="Stop time")
    prov_num: Optional[int] = Field(None, alias="ProvNum", description="Provider number")
    operatory_num: Optional[int] = Field(None, alias="OperatoryNum", description="Operatory number")
    block_text: Optional[str] = Field(None, alias="BlockText", description="Block text description")
    note: Optional[str] = Field(None, alias="Note", description="Schedule note")
    schedule_type: Optional[int] = Field(None, alias="ScheduleType", description="Schedule type")
    status: Optional[int] = Field(None, alias="Status", description="Schedule status")
    employee_num: Optional[int] = Field(None, alias="EmployeeNum", description="Employee number")


class ScheduleListResponse(BaseModel):
    """Response model for schedule list operations."""
    
    schedules: List[Schedule]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class ScheduleSearchRequest(BaseModel):
    """Request model for searching schedules."""
    
    # Search criteria
    schedule_date: Optional[date] = Field(None, alias="SchedDate", description="Schedule date")
    prov_num: Optional[int] = Field(None, alias="ProvNum", description="Provider number")
    operatory_num: Optional[int] = Field(None, alias="OperatoryNum", description="Operatory number")
    schedule_type: Optional[int] = Field(None, alias="ScheduleType", description="Schedule type")
    status: Optional[int] = Field(None, alias="Status", description="Schedule status")
    employee_num: Optional[int] = Field(None, alias="EmployeeNum", description="Employee number")
    
    # Date range search
    date_start: Optional[date] = Field(None, alias="DateStart", description="Start date for range search")
    date_end: Optional[date] = Field(None, alias="DateEnd", description="End date for range search")
    
    # Pagination
    page: Optional[int] = 1
    per_page: Optional[int] = 50

"""recalls models for Open Dental SDK."""

from datetime import datetime, date
from typing import Optional, List

from pydantic import Field

from ...base.models import BaseModel


class Recall(BaseModel):
    """Recall model."""
    
    # Primary identifiers
    id: int = Field(..., alias="RecallNum", description="Recall number (primary key)")
    patient_num: int = Field(..., alias="PatNum", description="Patient number")
    recall_type_num: int = Field(..., alias="RecallTypeNum", description="Recall type number")
    
    # Date fields
    date_due: date = Field(..., alias="DateDue", description="Recall due date")
    date_previous: Optional[date] = Field(None, alias="DatePrevious", description="Previous recall date")
    date_scheduled: Optional[date] = Field(None, alias="DateScheduled", description="Scheduled date")
    date_done: Optional[date] = Field(None, alias="DateDone", description="Date recall was completed")
    
    # Status and priority
    recall_status: int = Field(0, alias="RecallStatus", description="Recall status (0=Active, 1=Inactive)")
    priority: int = Field(0, alias="Priority", description="Priority level (0=Normal, 1=High)")
    
    # Notes and description
    note: Optional[str] = Field(None, alias="Note", description="Recall note")
    disable_until: Optional[date] = Field(None, alias="DisableUntil", description="Disable recall until this date")
    
    # Interval settings
    recall_interval: int = Field(0, alias="RecallInterval", description="Recall interval in days/months")
    default_interval: int = Field(0, alias="DefaultInterval", description="Default interval for this recall type")
    
    # Timestamps
    date_t_stamp: Optional[datetime] = Field(None, alias="DateTStamp", description="Timestamp of last modification")
    
    # Additional fields
    is_disabled: bool = Field(False, alias="IsDisabled", description="Whether recall is disabled")
    date_balance_zero: Optional[date] = Field(None, alias="DateBalanceZero", description="Date when balance was zero")
    
    # Security and audit
    sec_user_num_entry: Optional[int] = Field(None, alias="SecUserNumEntry", description="Security user number for entry")
    sec_date_t_entry: Optional[datetime] = Field(None, alias="SecDateTEntry", description="Security date time entry")


class CreateRecallRequest(BaseModel):
    """Request model for creating a new recall."""
    
    # Required fields
    patient_num: int = Field(..., alias="PatNum", description="Patient number")
    recall_type_num: int = Field(..., alias="RecallTypeNum", description="Recall type number")
    date_due: date = Field(..., alias="DateDue", description="Recall due date")
    
    # Optional fields
    date_previous: Optional[date] = Field(None, alias="DatePrevious", description="Previous recall date")
    date_scheduled: Optional[date] = Field(None, alias="DateScheduled", description="Scheduled date")
    recall_status: int = Field(0, alias="RecallStatus", description="Recall status (0=Active, 1=Inactive)")
    priority: int = Field(0, alias="Priority", description="Priority level (0=Normal, 1=High)")
    note: Optional[str] = Field(None, alias="Note", description="Recall note")
    disable_until: Optional[date] = Field(None, alias="DisableUntil", description="Disable recall until this date")
    recall_interval: int = Field(0, alias="RecallInterval", description="Recall interval in days/months")
    is_disabled: bool = Field(False, alias="IsDisabled", description="Whether recall is disabled")


class UpdateRecallRequest(BaseModel):
    """Request model for updating an existing recall."""
    
    # All fields are optional for updates
    patient_num: Optional[int] = Field(None, alias="PatNum", description="Patient number")
    recall_type_num: Optional[int] = Field(None, alias="RecallTypeNum", description="Recall type number")
    date_due: Optional[date] = Field(None, alias="DateDue", description="Recall due date")
    date_previous: Optional[date] = Field(None, alias="DatePrevious", description="Previous recall date")
    date_scheduled: Optional[date] = Field(None, alias="DateScheduled", description="Scheduled date")
    date_done: Optional[date] = Field(None, alias="DateDone", description="Date recall was completed")
    recall_status: Optional[int] = Field(None, alias="RecallStatus", description="Recall status (0=Active, 1=Inactive)")
    priority: Optional[int] = Field(None, alias="Priority", description="Priority level (0=Normal, 1=High)")
    note: Optional[str] = Field(None, alias="Note", description="Recall note")
    disable_until: Optional[date] = Field(None, alias="DisableUntil", description="Disable recall until this date")
    recall_interval: Optional[int] = Field(None, alias="RecallInterval", description="Recall interval in days/months")
    is_disabled: Optional[bool] = Field(None, alias="IsDisabled", description="Whether recall is disabled")


class RecallListResponse(BaseModel):
    """Response model for recall list operations."""
    
    recalls: List[Recall]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class RecallSearchRequest(BaseModel):
    """Request model for searching recalls."""
    
    # Search criteria
    patient_num: Optional[int] = Field(None, alias="PatNum", description="Patient number")
    recall_type_num: Optional[int] = Field(None, alias="RecallTypeNum", description="Recall type number")
    recall_status: Optional[int] = Field(None, alias="RecallStatus", description="Recall status (0=Active, 1=Inactive)")
    date_due_start: Optional[date] = Field(None, alias="DateDueStart", description="Start date for due date range")
    date_due_end: Optional[date] = Field(None, alias="DateDueEnd", description="End date for due date range")
    is_disabled: Optional[bool] = Field(None, alias="IsDisabled", description="Whether recall is disabled")
    
    # Pagination
    page: Optional[int] = 1
    per_page: Optional[int] = 50

"""User models for Open Dental SDK."""

from datetime import datetime, date
from typing import Optional, List
from pydantic import Field

from ...base.models import BaseModel


class User(BaseModel):
    """User model with exact Open Dental database field mapping."""
    
    # Primary identifiers (exact database field mapping)
    id: int = Field(..., alias="UserNum", description="User number (primary key)")
    user_num: int = Field(..., alias="UserNum", description="User number")
    
    # Login information
    user_name: str = Field(..., alias="UserName", description="Username for login")
    password_hash: Optional[str] = Field(None, alias="PasswordHash", description="Password hash")
    
    # Personal information
    first_name: Optional[str] = Field(None, alias="FName", description="First name")
    last_name: Optional[str] = Field(None, alias="LName", description="Last name")
    email: Optional[str] = Field(None, alias="EmailAddress", description="Email address")
    
    # Employee association
    employee_num: Optional[int] = Field(None, alias="EmployeeNum", description="Employee number")
    
    # Provider association
    prov_num: Optional[int] = Field(None, alias="ProvNum", description="Provider number")
    
    # Status
    is_hidden: bool = Field(False, alias="IsHidden", description="Hidden from lists")
    is_password_strong: bool = Field(False, alias="IsPasswordStrong", description="Strong password flag")
    
    # Login tracking
    date_last_login: Optional[datetime] = Field(None, alias="DateTLastLogin", description="Last login timestamp")
    failed_attempts: int = Field(0, alias="FailedAttempts", description="Failed login attempts")
    is_locked: bool = Field(False, alias="IsLocked", description="Account locked flag")
    
    # Security
    user_group_num: Optional[int] = Field(None, alias="UserGroupNum", description="User group number")
    
    # Timestamps
    date_created: Optional[datetime] = Field(None, alias="DateTStamp", description="Creation timestamp")
    date_modified: Optional[datetime] = Field(None, alias="DateTStamp", description="Last modified timestamp")
    
    # Clinic information
    clinic_num: Optional[int] = Field(None, alias="ClinicNum", description="Clinic number")
    clinic_is_restricted: bool = Field(False, alias="ClinicIsRestricted", description="Clinic restricted flag")
    
    # Additional Open Dental fields
    task_list_in_box: Optional[int] = Field(None, alias="TaskListInBox", description="Task list in box")
    default_hide_popup: bool = Field(False, alias="DefaultHidePopups", description="Default hide popups")
    
    # Password management
    password_is_strong: bool = Field(False, alias="PasswordIsStrong", description="Password is strong flag")
    date_password_changed: Optional[date] = Field(None, alias="DateTPasswordChanged", description="Password change date")
    
    # User preferences
    inbox_hide_done: bool = Field(False, alias="InboxHideDone", description="Hide done tasks in inbox")
    
    # Security settings
    is_password_reset_required: bool = Field(False, alias="IsPasswordResetRequired", description="Password reset required")
    
    # Additional user settings
    user_email_alert_address: Optional[str] = Field(None, alias="UserEmailAlertAddress", description="Email alert address")
    
    # User web settings
    user_web_lb_password: Optional[str] = Field(None, alias="UserWebLBPassword", description="Web LB password")
    
    # Domain login
    domain_user: Optional[str] = Field(None, alias="DomainUser", description="Domain user")
    
    # Additional flags
    is_web_mail_enabled: bool = Field(False, alias="IsWebMailEnabled", description="Web mail enabled flag")
    
    # User color
    user_color: Optional[str] = Field(None, alias="UserColor", description="User color")
    
    # Custom fields
    custom1: Optional[str] = Field(None, alias="Custom1", description="Custom field 1")
    custom2: Optional[str] = Field(None, alias="Custom2", description="Custom field 2")


class CreateUserRequest(BaseModel):
    """Request model for creating a new user."""
    
    # Required fields
    user_name: str
    
    # Optional fields
    password_hash: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    employee_num: Optional[int] = None
    prov_num: Optional[int] = None
    is_hidden: bool = False
    user_group_num: Optional[int] = None
    clinic_num: Optional[int] = None
    clinic_is_restricted: bool = False


class UpdateUserRequest(BaseModel):
    """Request model for updating an existing user."""
    
    # All fields are optional for updates
    user_name: Optional[str] = None
    password_hash: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    employee_num: Optional[int] = None
    prov_num: Optional[int] = None
    is_hidden: Optional[bool] = None
    user_group_num: Optional[int] = None
    clinic_num: Optional[int] = None
    clinic_is_restricted: Optional[bool] = None
    failed_attempts: Optional[int] = None
    is_locked: Optional[bool] = None


class UserListResponse(BaseModel):
    """Response model for user list operations."""
    
    users: List[User]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class UserSearchRequest(BaseModel):
    """Request model for searching users."""
    
    user_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    employee_num: Optional[int] = None
    prov_num: Optional[int] = None
    is_hidden: Optional[bool] = None
    is_locked: Optional[bool] = None
    user_group_num: Optional[int] = None
    clinic_num: Optional[int] = None
    
    # Pagination
    page: Optional[int] = 1
    per_page: Optional[int] = 50
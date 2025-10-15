"""User types and enums for Open Dental SDK."""

from enum import Enum


class UserStatus(str, Enum):
    """User status enum."""
    ACTIVE = "active"
    HIDDEN = "hidden"
    LOCKED = "locked"
    INACTIVE = "inactive"


class UserRole(str, Enum):
    """User role enum."""
    ADMIN = "admin"
    PROVIDER = "provider"
    EMPLOYEE = "employee"
    FRONT_DESK = "front_desk"
    HYGIENIST = "hygienist"
    ASSISTANT = "assistant"
    BILLING = "billing"
    REPORTS = "reports"
    LIMITED = "limited"


class LoginResult(str, Enum):
    """Login result enum."""
    SUCCESS = "success"
    INVALID_CREDENTIALS = "invalid_credentials"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_DISABLED = "account_disabled"
    PASSWORD_EXPIRED = "password_expired"
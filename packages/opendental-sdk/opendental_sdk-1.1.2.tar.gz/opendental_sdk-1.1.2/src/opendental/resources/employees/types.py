"""Employee types and enums for Open Dental SDK."""

from enum import Enum


class EmployeeStatus(str, Enum):
    """Employee status enum."""
    ACTIVE = "active"
    TERMINATED = "terminated"
    HIDDEN = "hidden"


class EmployeeType(str, Enum):
    """Employee type enum."""
    DENTIST = "dentist"
    HYGIENIST = "hygienist"
    ASSISTANT = "assistant"
    FRONT_DESK = "front_desk"
    OFFICE_MANAGER = "office_manager"
    INSTRUCTOR = "instructor"
    OTHER = "other"
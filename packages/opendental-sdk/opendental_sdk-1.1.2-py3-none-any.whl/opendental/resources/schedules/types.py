"""schedule types and enums for Open Dental SDK."""

from enum import Enum


class ScheduleStatus(str, Enum):
    """Status enum."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"

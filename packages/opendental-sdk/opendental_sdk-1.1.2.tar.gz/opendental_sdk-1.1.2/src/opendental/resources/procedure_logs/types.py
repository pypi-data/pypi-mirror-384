"""procedurelog types and enums for Open Dental SDK."""

from enum import Enum


class ProcedureLogStatus(str, Enum):
    """Status enum."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"

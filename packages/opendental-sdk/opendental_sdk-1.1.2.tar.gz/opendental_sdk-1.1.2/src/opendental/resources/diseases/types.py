"""disease types and enums for Open Dental SDK."""

from enum import Enum


class DiseaseStatus(str, Enum):
    """Status enum."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"

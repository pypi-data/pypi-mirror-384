"""Account modules types and enums for Open Dental SDK."""

from enum import Enum


class ModuleStatus(str, Enum):
    """Module status enum."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    TRIAL = "trial"
    EXPIRED = "expired"
    SUSPENDED = "suspended"


class ModuleType(str, Enum):
    """Module type enum."""
    CORE = "core"
    OPTIONAL = "optional"
    ADDON = "addon"
    INTEGRATION = "integration"
    THIRD_PARTY = "third_party"
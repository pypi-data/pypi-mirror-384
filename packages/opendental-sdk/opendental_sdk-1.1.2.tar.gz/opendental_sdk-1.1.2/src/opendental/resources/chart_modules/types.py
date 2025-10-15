"""Chart modules types and enums for Open Dental SDK."""

from enum import Enum


class ChartModuleType(str, Enum):
    """Chart module type enum."""
    CHART = "chart"
    PROGRESS = "progress"
    TREATMENT = "treatment"
    PERIO = "perio"
    IMAGING = "imaging"
    FORMS = "forms"


class ChartModuleStatus(str, Enum):
    """Chart module status enum."""
    ENABLED = "enabled"
    DISABLED = "disabled"
    HIDDEN = "hidden"
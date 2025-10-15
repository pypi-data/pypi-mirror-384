"""Insurance Plan types and enums for Open Dental SDK."""

from enum import Enum


class InsurancePlanType(str, Enum):
    """Insurance plan type enum."""
    PPO = "ppo"
    HMO = "hmo"
    INDEMNITY = "indemnity"
    CAPITATION = "capitation"
    MEDICAID = "medicaid"
    MEDICARE = "medicare"
    DISCOUNT = "discount"
    OTHER = "other"


class CoverageLevel(str, Enum):
    """Coverage level enum."""
    INDIVIDUAL = "individual"
    FAMILY = "family"
    EMPLOYEE_PLUS_ONE = "employee_plus_one"
    EMPLOYEE_PLUS_CHILDREN = "employee_plus_children"


class PlanStatus(str, Enum):
    """Plan status enum."""
    ACTIVE = "active"
    HIDDEN = "hidden"
    INACTIVE = "inactive"
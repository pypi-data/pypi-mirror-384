"""Patient types and enums for Open Dental SDK."""

from enum import Enum


class PatientStatus(str, Enum):
    """Patient status enum."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Gender(str, Enum):
    """Gender enum."""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"


class CreditType(str, Enum):
    """Credit type enum."""
    NONE = "none"
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    INSURANCE = "insurance"
    PAYMENT_PLAN = "payment_plan"


class Salutation(str, Enum):
    """Salutation enum."""
    MR = "Mr."
    MRS = "Mrs."
    MS = "Ms."
    DR = "Dr."
    PROF = "Prof."
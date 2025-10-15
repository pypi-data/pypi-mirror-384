"""Payment types and enums for Open Dental SDK."""

from enum import Enum


class PaymentType(str, Enum):
    """Payment type enum."""
    CASH = "cash"
    CHECK = "check"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    INSURANCE = "insurance"
    ELECTRONIC = "electronic"
    MONEY_ORDER = "money_order"
    OTHER = "other"


class PaymentStatus(str, Enum):
    """Payment status enum."""
    RECEIVED = "received"
    DEPOSITED = "deposited"
    CLEARED = "cleared"
    RETURNED = "returned"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    """Payment method enum."""
    CASH = "cash"
    CHECK = "check"
    VISA = "visa"
    MASTERCARD = "mastercard"
    AMEX = "amex"
    DISCOVER = "discover"
    DEBIT = "debit"
    ACH = "ach"
    WIRE = "wire"
    PAYPAL = "paypal"
    OTHER = "other"
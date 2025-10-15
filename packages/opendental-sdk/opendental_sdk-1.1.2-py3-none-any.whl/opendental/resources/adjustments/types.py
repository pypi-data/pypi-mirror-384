"""Adjustment types and enums for Open Dental SDK."""

from enum import Enum


class AdjustmentType(str, Enum):
    """Adjustment type enum."""
    DISCOUNT = "discount"
    WRITEOFF = "writeoff"
    FINANCE_CHARGE = "finance_charge"
    SALES_TAX = "sales_tax"
    REFUND = "refund"
    MISC_CREDIT = "misc_credit"
    MISC_DEBIT = "misc_debit"
"""Benefits types and enums for Open Dental SDK."""

from enum import Enum


class BenefitType(str, Enum):
    """Benefit type enum."""
    ACTIVE_COVERAGE = "ActiveCoverage"
    COINSURANCE = "CoInsurance"
    DEDUCTIBLE = "Deductible"
    COPAY = "CoPayment"
    EXCLUSION = "Exclusions"
    LIMITATION = "Limitations"
    WAITING_PERIOD = "WaitingPeriod"


class CoverageLevel(str, Enum):
    """Coverage level enum."""
    INDIVIDUAL = "Individual"
    FAMILY = "Family"
    NONE = "None"


class CoverageType(str, Enum):
    """Coverage type enum."""
    PREVENTIVE = "Preventive"
    BASIC = "Basic"
    MAJOR = "Major"
    ORTHODONTIC = "Orthodontic"
    EMERGENCY = "Emergency"
    DIAGNOSTIC = "Diagnostic"


class BenefitTimePeriod(str, Enum):
    """Benefit time period enum."""
    NONE = "None"
    SERVICE_YEAR = "ServiceYear"
    CALENDAR_YEAR = "CalendarYear"
    LIFETIME = "Lifetime"
    YEARS = "Years"
    NUMBER_IN_LAST_12_MONTHS = "NumberInLast12Months"


class QuantityQualifier(str, Enum):
    """Quantity qualifier enum for benefits."""
    NONE = "None"
    NUMBER_OF_SERVICES = "NumberOfServices"
    AGE_LIMIT = "AgeLimit"
    VISITS = "Visits"
    YEARS = "Years"
    MONTHS = "Months"


class TreatmentArea(str, Enum):
    """Treatment area enum."""
    NONE = "None"
    SURF = "Surf"
    TOOTH = "Tooth"
    MOUTH = "Mouth"
    QUAD = "Quad"
    SEXTANT = "Sextant"
    ARCH = "Arch"
    TOOTH_RANGE = "ToothRange"

class CategoryCodes(str, Enum):
    """Category codes enum."""
    DIAGNOSTIC = '2'
    PERIODONTICS = '3'
    RESTORATIVE = '4'
    ENDODONTICS = '5'
    MAXILLOFACIAL_PROSTHETICS = '6'
    CROWNS = '7'
    ACCIDENTS = '8'
    ORTHODONTICS = '9'
    PROSTHODONTICS = '10'
    ORAL_SURGERY = '11'
    PREVENTIVE = '12'  # routine_preventive
    DIAGNOSTIC_XRAY = '13'
    ADJUNCTIVE_SERVICES = '14'

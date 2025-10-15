"""Provider types and enums for Open Dental SDK."""

from enum import Enum


class ProviderType(str, Enum):
    """Provider type enum."""
    DENTIST = "dentist"
    HYGIENIST = "hygienist"
    ASSISTANT = "assistant"
    ANESTHESIA = "anesthesia"
    OTHER = "other"


class ProviderSpecialty(str, Enum):
    """Provider specialty enum."""
    GENERAL_DENTISTRY = "General Dentistry"
    ORTHODONTICS = "Orthodontics"
    ORAL_SURGERY = "Oral Surgery"
    ENDODONTICS = "Endodontics"
    PERIODONTICS = "Periodontics"
    PROSTHODONTICS = "Prosthodontics"
    PEDIATRIC_DENTISTRY = "Pediatric Dentistry"
    ORAL_PATHOLOGY = "Oral Pathology"
    DENTAL_HYGIENE = "Dental Hygiene"
    DENTAL_ASSISTING = "Dental Assisting"


class BillingType(str, Enum):
    """Billing type enum."""
    PROVIDER = "provider"
    CLINIC = "clinic"
    PRACTICE = "practice"


class TaxonomyCode(str, Enum):
    """Common dental taxonomy codes."""
    GENERAL_PRACTICE = "122300000X"  # General Practice
    ORAL_MAXILLOFACIAL_SURGERY = "122400000X"  # Oral and Maxillofacial Surgery
    ORTHODONTICS = "1223D0001X"  # Orthodontics and Dentofacial Orthopedics
    PEDIATRIC_DENTISTRY = "1223P0001X"  # Pediatric Dentistry
    PERIODONTICS = "1223P0300X"  # Periodontics
    PROSTHODONTICS = "1223P0700X"  # Prosthodontics
    ENDODONTICS = "1223E0200X"  # Endodontics
    ORAL_PATHOLOGY = "1223P0106X"  # Oral Pathology
    DENTAL_HYGIENIST = "124Q00000X"  # Dental Hygienist
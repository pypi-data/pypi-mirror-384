"""Coverage Category types and enums."""

from enum import Enum


class EbenefitCat(str, Enum):
    """
    Electronic Benefit Category enum.
    
    One of each Electronic Benefit Category must be assigned to a corresponding
    coverage category. There can be no duplicates and no missing categories in order
    for Open Dental Benefit Processing and Electronic Eligibility and Benefits to
    function properly.
    """
    
    NONE = "None"
    GENERAL = "General"
    DIAGNOSTIC = "Diagnostic"
    PERIODONTICS = "Periodontics"
    RESTORATIVE = "Restorative"
    ENDODONTICS = "Endodontics"
    MAXILLOFACIAL_PROSTH = "MaxillofacialProsth"
    CROWNS = "Crowns"
    ACCIDENT = "Accident"
    ORTHODONTICS = "Orthodontics"
    PROSTHODONTICS = "Prosthodontics"
    ORAL_SURGERY = "OralSurgery"
    ROUTINE_PREVENTIVE = "RoutinePreventive"
    DIAGNOSTIC_XRAY = "DiagnosticXRay"
    ADJUNCTIVE = "Adjunctive"


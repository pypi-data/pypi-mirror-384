"""Validators for Benefits API requests."""

from typing import List, Optional
from .exceptions import BenefitValidationError
from .types import (
    BenefitType, 
    CoverageLevel, 
    BenefitTimePeriod, 
    QuantityQualifier, 
    TreatmentArea
)


def validate_create_benefit_request(request) -> Optional[List[str]]:
    """
    Validate a CreateBenefitRequest according to API rules.
    
    Returns:
        List of validation error messages, or None if valid
    """
    errors = []
    
    # Rule 1: Either PlanNum or PatPlanNum must be provided
    if not request.plan_num and not request.pat_plan_num:
        errors.append("Either PlanNum or PatPlanNum must be provided")
    
    # Rule 2: BenefitType is required
    if not request.benefit_type:
        errors.append("BenefitType is required")
    else:
        # Check if it's a valid benefit type
        valid_types = [t.value for t in BenefitType]
        if request.benefit_type not in valid_types:
            errors.append(f"Invalid BenefitType: {request.benefit_type}. Must be one of: {', '.join(valid_types)}")
    
    # Rule 3: CoverageLevel is required
    if not request.coverage_level:
        errors.append("CoverageLevel is required")
    else:
        # Check if it's a valid coverage level
        valid_levels = [c.value for c in CoverageLevel]
        if request.coverage_level not in valid_levels:
            errors.append(f"Invalid CoverageLevel: {request.coverage_level}. Must be one of: {', '.join(valid_levels)}")
    
    # Conditional validations based on BenefitType
    if request.benefit_type:
        # Percent validation
        if request.percent is not None and request.percent != -1:
            if request.benefit_type != BenefitType.COINSURANCE.value:
                errors.append("Percent is only allowed for CoInsurance benefit type")
            elif not (0 <= request.percent <= 100):
                errors.append("Percent must be between 0 and 100")
        
        # MonetaryAmt validation
        if request.monetary_amt is not None and request.monetary_amt != -1:
            allowed_types = [BenefitType.COPAY.value, BenefitType.LIMITATION.value, BenefitType.DEDUCTIBLE.value]
            if request.benefit_type not in allowed_types:
                errors.append("MonetaryAmt is only allowed for CoPayment, Limitations, or Deductible")
        
        # QuantityQualifier validation for WaitingPeriod
        if request.benefit_type == BenefitType.WAITING_PERIOD.value and request.quantity_qualifier:
            allowed_qualifiers = [QuantityQualifier.MONTHS.value, QuantityQualifier.YEARS.value]
            if request.quantity_qualifier not in allowed_qualifiers:
                errors.append("QuantityQualifier must be Months or Years for WaitingPeriod")
    
    # TimePeriod validation
    if request.time_period:
        valid_periods = [t.value for t in BenefitTimePeriod]
        if request.time_period not in valid_periods:
            errors.append(f"Invalid TimePeriod: {request.time_period}. Must be one of: {', '.join(valid_periods)}")
    
    # QuantityQualifier validation
    if request.quantity_qualifier:
        valid_qualifiers = [q.value for q in QuantityQualifier]
        if request.quantity_qualifier not in valid_qualifiers:
            errors.append(f"Invalid QuantityQualifier: {request.quantity_qualifier}. Must be one of: {', '.join(valid_qualifiers)}")
        
        # AgeLimit specific validation
        if request.quantity_qualifier == QuantityQualifier.AGE_LIMIT.value:
            if request.quantity is None or request.quantity <= 0:
                errors.append("Quantity must be greater than 0 when QuantityQualifier is AgeLimit")
        
        # NumberOfServices specific validation
        if request.quantity_qualifier == QuantityQualifier.NUMBER_OF_SERVICES.value:
            if request.time_period and request.time_period not in [
                BenefitTimePeriod.CALENDAR_YEAR.value,
                BenefitTimePeriod.NUMBER_IN_LAST_12_MONTHS.value
            ]:
                errors.append(
                    "TimePeriod must be CalendarYear or NumberInLast12Months when "
                    "QuantityQualifier is NumberOfServices"
                )
    
    # Quantity validation
    if request.quantity is not None:
        if not (0 <= request.quantity <= 100):
            errors.append("Quantity must be between 0 and 100")
    
    # CodeNum/procCode validation
    if (request.code_num or request.proc_code) and request.cov_cat_num and request.cov_cat_num != 0:
        errors.append("CodeNum and procCode are only allowed when CovCatNum is 0")
    
    # TreatArea validation
    if request.treat_area:
        # This is a complex validation - TreatArea is only for Frequency Limitations
        # which seems to be a specific configuration of Limitations benefit type
        if request.benefit_type != BenefitType.LIMITATION.value:
            errors.append("TreatArea is only allowed for Frequency Limitation benefits")
        
        valid_areas = [t.value for t in TreatmentArea]
        if request.treat_area not in valid_areas:
            errors.append(f"Invalid TreatArea: {request.treat_area}. Must be one of: {', '.join(valid_areas)}")
    
    return errors if errors else None


def validate_update_benefit_request(request) -> Optional[List[str]]:
    """
    Validate an UpdateBenefitRequest according to API rules.
    
    Returns:
        List of validation error messages, or None if valid
    """
    errors = []
    
    # Most validations are similar to create, but all fields are optional
    
    # BenefitType validation if provided
    if request.benefit_type:
        valid_types = [t.value for t in BenefitType]
        if request.benefit_type not in valid_types:
            errors.append(f"Invalid BenefitType: {request.benefit_type}. Must be one of: {', '.join(valid_types)}")
    
    # CoverageLevel validation if provided
    if request.coverage_level:
        valid_levels = [c.value for c in CoverageLevel]
        if request.coverage_level not in valid_levels:
            errors.append(f"Invalid CoverageLevel: {request.coverage_level}. Must be one of: {', '.join(valid_levels)}")
    
    # Conditional validations based on BenefitType
    if request.benefit_type:
        # Percent validation
        if request.percent is not None and request.percent != -1:
            if request.benefit_type != BenefitType.COINSURANCE.value:
                errors.append("Percent is only allowed for CoInsurance benefit type")
            elif not (0 <= request.percent <= 100):
                errors.append("Percent must be between 0 and 100")
        
        # MonetaryAmt validation
        if request.monetary_amt is not None and request.monetary_amt != -1:
            allowed_types = [BenefitType.COPAY.value, BenefitType.LIMITATION.value, BenefitType.DEDUCTIBLE.value]
            if request.benefit_type not in allowed_types:
                errors.append("MonetaryAmt is only allowed for CoPayment, Limitations, or Deductible")
        
        # QuantityQualifier validation for WaitingPeriod
        if request.benefit_type == BenefitType.WAITING_PERIOD.value and request.quantity_qualifier:
            allowed_qualifiers = [QuantityQualifier.MONTHS.value, QuantityQualifier.YEARS.value]
            if request.quantity_qualifier not in allowed_qualifiers:
                errors.append("QuantityQualifier must be Months or Years for WaitingPeriod")
    
    # TimePeriod validation
    if request.time_period:
        valid_periods = [t.value for t in BenefitTimePeriod]
        if request.time_period not in valid_periods:
            errors.append(f"Invalid TimePeriod: {request.time_period}. Must be one of: {', '.join(valid_periods)}")
    
    # QuantityQualifier validation
    if request.quantity_qualifier:
        if request.quantity_qualifier not in [
            "None", "NumberOfServices", "AgeLimit", "Visits", "Years", "Months"
        ]:
            errors.append(f"Invalid QuantityQualifier: {request.quantity_qualifier}")
        
        # AgeLimit specific validation
        if request.quantity_qualifier == "AgeLimit":
            if request.quantity is not None and request.quantity <= 0:
                errors.append("Quantity must be greater than 0 when QuantityQualifier is AgeLimit")
        
        # NumberOfServices specific validation
        if request.quantity_qualifier == "NumberOfServices":
            if request.time_period and request.time_period not in [
                BenefitTimePeriod.CALENDAR_YEAR.value,
                BenefitTimePeriod.NUMBER_IN_LAST_12_MONTHS.value
            ]:
                errors.append(
                    "TimePeriod must be CalendarYear or NumberInLast12Months when "
                    "QuantityQualifier is NumberOfServices"
                )
    
    # Quantity validation
    if request.quantity is not None:
        if not (0 <= request.quantity <= 100):
            errors.append("Quantity must be between 0 and 100")
    
    # CodeNum/procCode validation
    if (request.code_num or request.proc_code) and request.cov_cat_num and request.cov_cat_num != 0:
        errors.append("CodeNum and procCode are only allowed when CovCatNum is 0")
    
    # TreatArea validation
    if request.treat_area:
        valid_areas = [t.value for t in TreatmentArea]
        if request.treat_area not in valid_areas:
            errors.append(f"Invalid TreatArea: {request.treat_area}. Must be one of: {', '.join(valid_areas)}")
    
    return errors if errors else None
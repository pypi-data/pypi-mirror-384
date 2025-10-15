"""procedurecodes models for Open Dental SDK."""

from datetime import datetime
from typing import Optional, List, Union
from pydantic import Field

from ...base.models import BaseModel


class ProcedureCode(BaseModel):
    """ProcedureCode model."""
    
    # Primary identifiers
    id: int = Field(..., alias="CodeNum", description="Procedure code number (primary key)")
    procedure_codes_num: Optional[int] = Field(None, alias="ProcCodeNum", description="Procedure code number")
    
    # Basic information
    proc_code: str = Field(..., alias="ProcCode", description="Procedure code")
    descript: Optional[str] = Field(None, alias="Descript", description="Procedure description")
    abbr: Optional[str] = Field(None, alias="Abbr", description="Procedure abbreviation")
    proc_time: Optional[str] = Field(None, alias="ProcTime", description="Procedure time")
    
    # Classification and categorization
    proc_cat: Optional[int] = Field(None, alias="ProcCat", description="Procedure category")
    proc_cat_descript: Optional[str] = Field(None, alias="ProcCatDescript", description="Procedure category description")
    default_note: Optional[str] = Field(None, alias="DefaultNote", description="Default note for procedure")
    
    # Financial information
    fee_sched: Optional[int] = Field(None, alias="FeeSched", description="Fee schedule")
    base_units: Optional[int] = Field(None, alias="BaseUnits", description="Base units")
    subst_code: Optional[str] = Field(None, alias="SubstCode", description="Substitute code")
    alternate_code1: Optional[str] = Field(None, alias="AlternateCode1", description="Alternate code 1")
    medical_code: Optional[str] = Field(None, alias="MedicalCode", description="Medical code")
    
    # Treatment area
    treat_area: Optional[Union[int, str]] = Field(None, alias="TreatArea")
    
    # Status and flags
    is_active: bool = Field(True, alias="IsActive", description="Whether the procedure code is active")
    is_hygiene: Optional[bool] = Field(None, alias="IsHygiene", description="Whether this is a hygiene procedure")
    is_timed: Optional[bool] = Field(None, alias="IsTimed", description="Whether this procedure is timed")
    is_canon: Optional[bool] = Field(None, alias="IsCanon", description="Whether this is a canonical procedure")
    is_radiology: Optional[bool] = Field(None, alias="IsRadiology", description="Whether this is a radiology procedure")
    
    # Paint and color coding
    paint_type: Optional[Union[int, str]] = Field(None, alias="PaintType", description="Paint type for procedure")
    graph_vorder: Optional[int] = Field(None, alias="GraphVorder", description="Graph view order")
    
    # Timestamps
    date_created: Optional[datetime] = Field(None, alias="DateCreated", description="Date when the procedure code was created")
    date_modified: Optional[datetime] = Field(None, alias="DateModified", description="Date when the procedure code was last modified")
    sec_date_t_edit: Optional[datetime] = Field(None, alias="SecDateTEdit", description="Security date/time edit")
    
    # Clinical information
    diagnostic: Optional[bool] = Field(None, alias="Diagnostic", description="Whether this is a diagnostic procedure")
    no_lab: Optional[bool] = Field(None, alias="NoLab", description="Whether lab work is not required")
    pre_auth: Optional[bool] = Field(None, alias="PreAuth", description="Whether pre-authorization is required")
    
    # Insurance and claim information
    layman_term: Optional[str] = Field(None, alias="LaymanTerm", description="Layman's term for the procedure")
    is_multivis: Optional[bool] = Field(None, alias="IsMultivis", description="Whether this is a multi-visit procedure")
    
    # Additional codes and references
    drg_code: Optional[str] = Field(None, alias="DrgCode", description="DRG code")
    revenue_code: Optional[str] = Field(None, alias="RevenueCode", description="Revenue code")
    
    # Specialty and provider information
    prov_num_default: Optional[int] = Field(None, alias="ProvNumDefault", description="Default provider number")
    clinic_num: Optional[int] = Field(None, alias="ClinicNum", description="Clinic number")
    
    # Bypass and override flags
    bypass_global_lock: Optional[bool] = Field(None, alias="BypassGlobalLock", description="Whether to bypass global lock")
    tax_code: Optional[str] = Field(None, alias="TaxCode", description="Tax code for procedure")


class CreateProcedureCodeRequest(BaseModel):
    """Request model for creating a new procedure code."""
    
    # Required fields
    proc_code: str = Field(..., alias="ProcCode", description="Procedure code")
    
    # Optional fields
    descript: Optional[str] = Field(None, alias="Descript", description="Procedure description")
    abbr: Optional[str] = Field(None, alias="Abbr", description="Procedure abbreviation")
    proc_time: Optional[str] = Field(None, alias="ProcTime", description="Procedure time")
    proc_cat: Optional[int] = Field(None, alias="ProcCat", description="Procedure category")
    default_note: Optional[str] = Field(None, alias="DefaultNote", description="Default note for procedure")
    fee_sched: Optional[int] = Field(None, alias="FeeSched", description="Fee schedule")
    base_units: Optional[int] = Field(None, alias="BaseUnits", description="Base units")
    subst_code: Optional[str] = Field(None, alias="SubstCode", description="Substitute code")
    alternate_code1: Optional[str] = Field(None, alias="AlternateCode1", description="Alternate code 1")
    medical_code: Optional[str] = Field(None, alias="MedicalCode", description="Medical code")
    treat_area: Optional[Union[int, str]] = Field(None, alias="TreatArea", description="Treatment area")
    paint_type: Optional[Union[int, str]] = Field(None, alias="PaintType", description="Paint type")
    is_active: bool = Field(True, alias="IsActive", description="Whether the procedure code is active")
    is_hygiene: Optional[bool] = Field(None, alias="IsHygiene", description="Whether this is a hygiene procedure")
    is_timed: Optional[bool] = Field(None, alias="IsTimed", description="Whether this procedure is timed")
    is_canon: Optional[bool] = Field(None, alias="IsCanon", description="Whether this is a canonical procedure")
    is_radiology: Optional[bool] = Field(None, alias="IsRadiology", description="Whether this is a radiology procedure")
    graph_vorder: Optional[int] = Field(None, alias="GraphVorder", description="Graph view order")
    diagnostic: Optional[bool] = Field(None, alias="Diagnostic", description="Whether this is a diagnostic procedure")
    no_lab: Optional[bool] = Field(None, alias="NoLab", description="Whether lab work is not required")
    pre_auth: Optional[bool] = Field(None, alias="PreAuth", description="Whether pre-authorization is required")
    layman_term: Optional[str] = Field(None, alias="LaymanTerm", description="Layman's term for the procedure")
    is_multivis: Optional[bool] = Field(None, alias="IsMultivis", description="Whether this is a multi-visit procedure")
    drg_code: Optional[str] = Field(None, alias="DrgCode", description="DRG code")
    revenue_code: Optional[str] = Field(None, alias="RevenueCode", description="Revenue code")
    prov_num_default: Optional[int] = Field(None, alias="ProvNumDefault", description="Default provider number")
    clinic_num: Optional[int] = Field(None, alias="ClinicNum", description="Clinic number")
    bypass_global_lock: Optional[bool] = Field(None, alias="BypassGlobalLock", description="Whether to bypass global lock")
    tax_code: Optional[str] = Field(None, alias="TaxCode", description="Tax code for procedure")


class UpdateProcedureCodeRequest(BaseModel):
    """Request model for updating an existing procedure code."""
    
    # All fields are optional for updates
    proc_code: Optional[str] = Field(None, alias="ProcCode", description="Procedure code")
    descript: Optional[str] = Field(None, alias="Descript", description="Procedure description")
    abbr: Optional[str] = Field(None, alias="Abbr", description="Procedure abbreviation")
    proc_time: Optional[str] = Field(None, alias="ProcTime", description="Procedure time")
    proc_cat: Optional[int] = Field(None, alias="ProcCat", description="Procedure category")
    default_note: Optional[str] = Field(None, alias="DefaultNote", description="Default note for procedure")
    fee_sched: Optional[int] = Field(None, alias="FeeSched", description="Fee schedule")
    base_units: Optional[int] = Field(None, alias="BaseUnits", description="Base units")
    subst_code: Optional[str] = Field(None, alias="SubstCode", description="Substitute code")
    alternate_code1: Optional[str] = Field(None, alias="AlternateCode1", description="Alternate code 1")
    medical_code: Optional[str] = Field(None, alias="MedicalCode", description="Medical code")
    treat_area: Optional[Union[int, str]] = Field(None, alias="TreatArea", description="Treatment area")
    paint_type: Optional[Union[int, str]] = Field(None, alias="PaintType", description="Paint type")
    is_active: Optional[bool] = Field(None, alias="IsActive", description="Whether the procedure code is active")
    is_hygiene: Optional[bool] = Field(None, alias="IsHygiene", description="Whether this is a hygiene procedure")
    is_timed: Optional[bool] = Field(None, alias="IsTimed", description="Whether this procedure is timed")
    is_canon: Optional[bool] = Field(None, alias="IsCanon", description="Whether this is a canonical procedure")
    is_radiology: Optional[bool] = Field(None, alias="IsRadiology", description="Whether this is a radiology procedure")
    graph_vorder: Optional[int] = Field(None, alias="GraphVorder", description="Graph view order")
    diagnostic: Optional[bool] = Field(None, alias="Diagnostic", description="Whether this is a diagnostic procedure")
    no_lab: Optional[bool] = Field(None, alias="NoLab", description="Whether lab work is not required")
    pre_auth: Optional[bool] = Field(None, alias="PreAuth", description="Whether pre-authorization is required")
    layman_term: Optional[str] = Field(None, alias="LaymanTerm", description="Layman's term for the procedure")
    is_multivis: Optional[bool] = Field(None, alias="IsMultivis", description="Whether this is a multi-visit procedure")
    drg_code: Optional[str] = Field(None, alias="DrgCode", description="DRG code")
    revenue_code: Optional[str] = Field(None, alias="RevenueCode", description="Revenue code")
    prov_num_default: Optional[int] = Field(None, alias="ProvNumDefault", description="Default provider number")
    clinic_num: Optional[int] = Field(None, alias="ClinicNum", description="Clinic number")
    bypass_global_lock: Optional[bool] = Field(None, alias="BypassGlobalLock", description="Whether to bypass global lock")
    tax_code: Optional[str] = Field(None, alias="TaxCode", description="Tax code for procedure")


class ProcedureCodeListResponse(BaseModel):
    """Response model for procedure code list operations."""
    
    procedure_codes: List[ProcedureCode]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class ProcedureCodeSearchRequest(BaseModel):
    """Request model for searching procedure codes."""
    
    proc_code: Optional[str] = Field(None, alias="ProcCode", description="Procedure code to search for")
    descript: Optional[str] = Field(None, alias="Descript", description="Procedure description to search for")
    abbr: Optional[str] = Field(None, alias="Abbr", description="Procedure abbreviation to search for")
    proc_cat: Optional[int] = Field(None, alias="ProcCat", description="Procedure category to filter by")
    is_active: Optional[bool] = Field(None, alias="IsActive", description="Whether to filter by active status")
    is_hygiene: Optional[bool] = Field(None, alias="IsHygiene", description="Whether to filter by hygiene procedures")
    is_timed: Optional[bool] = Field(None, alias="IsTimed", description="Whether to filter by timed procedures")
    is_canon: Optional[bool] = Field(None, alias="IsCanon", description="Whether to filter by canonical procedures")
    is_radiology: Optional[bool] = Field(None, alias="IsRadiology", description="Whether to filter by radiology procedures")
    treat_area: Optional[Union[int, str]] = Field(None, alias="TreatArea", description="Treatment area to filter by")
    paint_type: Optional[Union[int, str]] = Field(None, alias="PaintType", description="Paint type to filter by")
    
    # Pagination
    page: Optional[int] = Field(1, description="Page number for pagination")
    per_page: Optional[int] = Field(50, description="Number of items per page")

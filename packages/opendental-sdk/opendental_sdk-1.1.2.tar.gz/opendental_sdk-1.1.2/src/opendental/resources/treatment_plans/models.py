"""Treatment Plan models for Open Dental SDK."""

from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
from pydantic import Field

from ...base.models import BaseModel
from ..patients.models import Patient
from ..providers.models import Provider


class TreatmentPlan(BaseModel):
    """Treatment Plan model."""
    
    # Primary identifiers
    id: int = Field(..., alias="TreatPlanNum", description="Treatment plan number (primary key)")
    tp_num: int = Field(..., alias="TPNum", description="Treatment plan identifier")
    
    # Related entities
    patient: Patient = Field(..., alias="PatNum", description="Patient information")
    provider: Provider = Field(..., alias="ProvNum", description="Provider information")
    
    # Treatment plan details
    date_tp: date = Field(..., alias="DateTP", description="Treatment plan date")
    heading: Optional[str] = Field(None, alias="Heading", description="Treatment plan heading")
    note: Optional[str] = Field(None, alias="Note", description="Treatment plan note")
    
    # Status
    tp_status: str = Field("active", alias="TPStatus", description="Treatment plan status (active, inactive, saved, completed)")
    
    # Signature information
    signature: Optional[str] = Field(None, alias="Signature", description="Digital signature")
    sig_date: Optional[date] = Field(None, alias="SigDate", description="Date signature was applied")
    
    # Timestamps
    date_created: Optional[datetime] = Field(None, alias="DateCreated", description="Date treatment plan was created")
    date_modified: Optional[datetime] = Field(None, alias="DateModified", description="Date treatment plan was last modified")
    
    # Responsible party
    responsible_party: Optional[int] = Field(None, alias="ResponsParty", description="Responsible party patient number")
    
    # User information
    user_num: Optional[int] = Field(None, alias="UserNum", description="User who created the treatment plan")
    
    # Security
    sec_user_num_edit: Optional[int] = Field(None, alias="SecUserNumEdit", description="Security user who last edited")
    sec_date_edit: Optional[datetime] = Field(None, alias="SecDateEdit", description="Date of last security edit")
    
    # Treatment plan type
    tp_type: Optional[str] = Field(None, alias="TPType", description="Treatment plan type")


class TreatmentPlanAttach(BaseModel):
    """Treatment Plan Attachment model."""
    
    id: int = Field(..., alias="TreatPlanAttachNum", description="Treatment plan attachment number (primary key)")
    tp_num: int = Field(..., alias="TreatPlanNum", description="Treatment plan number")
    proc_num: int = Field(..., alias="ProcNum", description="Procedure number")
    priority: Optional[int] = Field(None, alias="Priority", description="Priority order")
    
    # Procedure details
    proc_code: str = Field(..., alias="ProcCode", description="Procedure code")
    description: Optional[str] = Field(None, alias="Descript", description="Procedure description")
    fee: Decimal = Field(..., alias="Fee", description="Procedure fee")
    
    # Status
    tp_attach_status: str = Field("attached", alias="TPAttachStatus", description="Attachment status")
    
    # Provider information
    provider_id: int = Field(..., alias="ProvNum", description="Provider number")
    
    # Timestamps
    date_created: Optional[datetime] = Field(None, alias="DateCreated", description="Date attachment was created")


class CreateTreatmentPlanRequest(BaseModel):
    """Request model for creating a new treatment plan."""
    
    # Required fields
    patient_id: int = Field(..., alias="PatNum", description="Patient number")
    provider_id: int = Field(..., alias="ProvNum", description="Provider number")
    date_tp: date = Field(..., alias="DateTP", description="Treatment plan date")
    
    # Optional fields
    heading: Optional[str] = Field(None, alias="Heading", description="Treatment plan heading")
    note: Optional[str] = Field(None, alias="Note", description="Treatment plan note")
    tp_status: str = Field("active", alias="TPStatus", description="Treatment plan status")
    responsible_party: Optional[int] = Field(None, alias="ResponsParty", description="Responsible party patient number")
    user_num: Optional[int] = Field(None, alias="UserNum", description="User number")
    tp_type: Optional[str] = Field(None, alias="TPType", description="Treatment plan type")


class UpdateTreatmentPlanRequest(BaseModel):
    """Request model for updating an existing treatment plan."""
    
    # All fields are optional for updates
    patient_id: Optional[int] = Field(None, alias="PatNum", description="Patient number")
    provider_id: Optional[int] = Field(None, alias="ProvNum", description="Provider number")
    date_tp: Optional[date] = Field(None, alias="DateTP", description="Treatment plan date")
    heading: Optional[str] = Field(None, alias="Heading", description="Treatment plan heading")
    note: Optional[str] = Field(None, alias="Note", description="Treatment plan note")
    tp_status: Optional[str] = Field(None, alias="TPStatus", description="Treatment plan status")
    signature: Optional[str] = Field(None, alias="Signature", description="Digital signature")
    sig_date: Optional[date] = Field(None, alias="SigDate", description="Date signature was applied")
    responsible_party: Optional[int] = Field(None, alias="ResponsParty", description="Responsible party patient number")
    user_num: Optional[int] = Field(None, alias="UserNum", description="User number")
    tp_type: Optional[str] = Field(None, alias="TPType", description="Treatment plan type")


class TreatmentPlanListResponse(BaseModel):
    """Response model for treatment plan list operations."""
    
    treatment_plans: List[TreatmentPlan]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class TreatmentPlanSearchRequest(BaseModel):
    """Request model for searching treatment plans."""
    
    patient_id: Optional[int] = Field(None, alias="PatNum", description="Patient number")
    provider_id: Optional[int] = Field(None, alias="ProvNum", description="Provider number")
    tp_status: Optional[str] = Field(None, alias="TPStatus", description="Treatment plan status")
    date_tp_start: Optional[date] = Field(None, alias="DateTPStart", description="Start date for treatment plan search")
    date_tp_end: Optional[date] = Field(None, alias="DateTPEnd", description="End date for treatment plan search")
    
    # Pagination
    page: Optional[int] = Field(1, description="Page number for pagination")
    per_page: Optional[int] = Field(50, description="Number of results per page")


class AttachProcedureRequest(BaseModel):
    """Request model for attaching a procedure to a treatment plan."""
    
    tp_num: int = Field(..., alias="TreatPlanNum", description="Treatment plan number")
    proc_num: int = Field(..., alias="ProcNum", description="Procedure number")
    priority: Optional[int] = Field(None, alias="Priority", description="Priority order")
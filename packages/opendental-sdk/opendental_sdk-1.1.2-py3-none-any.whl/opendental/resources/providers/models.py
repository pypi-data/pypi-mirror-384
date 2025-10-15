"""Provider models for Open Dental SDK."""

from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
from pydantic import Field

from ...base.models import BaseModel


class Provider(BaseModel):
    """Provider model with exact Open Dental database field mapping."""
    
    # Primary identifiers (exact database field mapping)
    id: int = Field(..., alias="ProvNum", description="Provider number (primary key)")
    prov_num: int = Field(..., alias="ProvNum", description="Provider number")
    
    # Personal information
    first_name: str = Field(..., alias="FName", description="Provider first name")
    last_name: str = Field(..., alias="LName", description="Provider last name")
    middle_name: Optional[str] = Field(None, alias="MI", description="Middle initial")
    abbreviation: Optional[str] = Field(None, alias="Abbr", description="Provider abbreviation")
    suffix: Optional[str] = Field(None, alias="Suffix", description="Name suffix")
    
    # Professional information
    dea_num: Optional[str] = Field(None, alias="DEANum", description="DEA number")
    state_license: Optional[str] = Field(None, alias="StateLicense", description="State license number")
    npi: Optional[str] = Field(None, alias="NationalProvID", description="National Provider Identifier")
    taxonomy: Optional[str] = Field(None, alias="TaxonomyCodeOverride", description="Taxonomy code")
    
    # Contact information
    email: Optional[str] = Field(None, alias="EmailAddress", description="Email address")
    phone: Optional[str] = Field(None, alias="Phone", description="Phone number")
    address: Optional[str] = Field(None, alias="Address", description="Street address")
    address2: Optional[str] = Field(None, alias="Address2", description="Address line 2")
    city: Optional[str] = Field(None, alias="City", description="City")
    state: Optional[str] = Field(None, alias="State", description="State")
    zip: Optional[str] = Field(None, alias="Zip", description="ZIP code")
    
    # Practice information
    specialty: Optional[str] = Field(None, alias="Specialty", description="Provider specialty")
    is_secondary: bool = Field(False, alias="IsSecondary", description="Secondary provider flag")
    is_hidden: bool = Field(False, alias="IsHidden", description="Hidden from lists")
    is_active: bool = Field(True, alias="IsActive", description="Active provider flag")
    
    # Scheduling
    hourly_prod_goal: Optional[Decimal] = Field(None, alias="HourlyProdGoal", description="Hourly production goal")
    
    # Provider colors for scheduling
    outline_color: Optional[str] = Field(None, alias="OutlineColor", description="Outline color for scheduling")
    inner_color: Optional[str] = Field(None, alias="InnerColor", description="Inner color for scheduling")
    
    # Electronic health records
    ehr_key: Optional[str] = Field(None, alias="EhrKey", description="EHR key")
    state_rx_id: Optional[str] = Field(None, alias="StateRxID", description="State prescription ID")
    
    # Billing information
    billing_type: Optional[str] = Field(None, alias="BillingType", description="Billing type")
    
    # Timestamps
    date_created: Optional[datetime] = Field(None, alias="DateTStamp", description="Creation timestamp")
    date_modified: Optional[datetime] = Field(None, alias="DateTStamp", description="Last modified timestamp")
    
    # Custom fields
    custom1: Optional[str] = Field(None, alias="Custom1", description="Custom field 1")
    custom2: Optional[str] = Field(None, alias="Custom2", description="Custom field 2")
    custom3: Optional[str] = Field(None, alias="Custom3", description="Custom field 3")
    
    # Security
    user_num: Optional[int] = Field(None, alias="UserNum", description="User number")
    
    # Provider type
    is_dentist: bool = Field(True, alias="IsDentist", description="Dentist flag")
    is_hygienist: bool = Field(False, alias="IsHygienist", description="Hygienist flag")
    is_assistant: bool = Field(False, alias="IsAssistant", description="Assistant flag")
    
    # Fee schedule
    fee_sched: Optional[int] = Field(None, alias="FeeSched", description="Fee schedule number")
    
    # Signature
    sig_on_file: bool = Field(False, alias="SigOnFile", description="Signature on file flag")
    
    # Anesthesia provider
    is_anesthesia_provider: bool = Field(False, alias="IsAnesthesiaProvider", description="Anesthesia provider flag")
    
    # Electronic claims
    claiming_provider: Optional[bool] = Field(None, alias="ClaimingProvider", description="Claiming provider flag")
    
    # WebSchedRecall settings
    web_sched_recall: Optional[bool] = Field(None, alias="WebSchedRecall", description="Web schedule recall flag")
    
    # Additional Open Dental fields
    is_instructor: bool = Field(False, alias="IsInstructor", description="Instructor flag")
    is_provider_inactive: bool = Field(False, alias="IsProviderInactive", description="Provider inactive flag")
    custom_id: Optional[str] = Field(None, alias="CustomID", description="Custom ID")
    
    # Provider category
    provider_category: Optional[int] = Field(None, alias="ProviderCategory", description="Provider category")
    
    # Provider color
    provider_color: Optional[str] = Field(None, alias="ProviderColor", description="Provider color")
    
    # Electronic signature
    e_sig_on_file: bool = Field(False, alias="ESigOnFile", description="Electronic signature on file")
    
    # Provider status
    is_not_person: bool = Field(False, alias="IsNotPerson", description="Not a person flag")
    
    # Custom provider ID
    prov_num_billing: Optional[int] = Field(None, alias="ProvNumBilling", description="Billing provider number")
    
    # Provider type specific fields
    is_card_reader: bool = Field(False, alias="IsCardReader", description="Card reader flag")
    use_ecw: bool = Field(False, alias="UseEcw", description="Use ECW flag")
    
    # Provider schedule
    is_available: bool = Field(True, alias="IsAvailable", description="Available for scheduling")
    
    # Provider preference
    pref_provider: bool = Field(False, alias="PrefProvider", description="Preferred provider flag")


class CreateProviderRequest(BaseModel):
    """Request model for creating a new provider."""
    
    # Required fields
    first_name: str
    last_name: str
    abbreviation: str
    
    # Optional personal information
    middle_name: Optional[str] = None
    suffix: Optional[str] = None
    
    # Professional information
    dea_num: Optional[str] = None
    state_license: Optional[str] = None
    npi: Optional[str] = None
    taxonomy: Optional[str] = None
    
    # Contact information
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    
    # Practice information
    specialty: Optional[str] = None
    is_secondary: bool = False
    is_hidden: bool = False
    is_active: bool = True
    
    # Scheduling
    hourly_prod_goal: Optional[Decimal] = None
    
    # Provider colors
    outline_color: Optional[str] = None
    inner_color: Optional[str] = None
    
    # Electronic health records
    ehr_key: Optional[str] = None
    state_rx_id: Optional[str] = None
    
    # Billing information
    billing_type: Optional[str] = None
    
    # Custom fields
    custom1: Optional[str] = None
    custom2: Optional[str] = None
    custom3: Optional[str] = None
    
    # Security
    user_num: Optional[int] = None
    
    # Provider type
    is_dentist: bool = True
    is_hygienist: bool = False
    is_assistant: bool = False
    
    # Fee schedule
    fee_sched: Optional[int] = None
    
    # Signature
    sig_on_file: bool = False
    
    # Anesthesia provider
    is_anesthesia_provider: bool = False
    
    # Electronic claims
    claiming_provider: Optional[bool] = None
    
    # WebSchedRecall settings
    web_sched_recall: Optional[bool] = None


class UpdateProviderRequest(BaseModel):
    """Request model for updating an existing provider."""
    
    # All fields are optional for updates
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    abbreviation: Optional[str] = None
    suffix: Optional[str] = None
    
    # Professional information
    dea_num: Optional[str] = None
    state_license: Optional[str] = None
    npi: Optional[str] = None
    taxonomy: Optional[str] = None
    
    # Contact information
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    
    # Practice information
    specialty: Optional[str] = None
    is_secondary: Optional[bool] = None
    is_hidden: Optional[bool] = None
    is_active: Optional[bool] = None
    
    # Scheduling
    hourly_prod_goal: Optional[Decimal] = None
    
    # Provider colors
    outline_color: Optional[str] = None
    inner_color: Optional[str] = None
    
    # Electronic health records
    ehr_key: Optional[str] = None
    state_rx_id: Optional[str] = None
    
    # Billing information
    billing_type: Optional[str] = None
    
    # Custom fields
    custom1: Optional[str] = None
    custom2: Optional[str] = None
    custom3: Optional[str] = None
    
    # Security
    user_num: Optional[int] = None
    
    # Provider type
    is_dentist: Optional[bool] = None
    is_hygienist: Optional[bool] = None
    is_assistant: Optional[bool] = None
    
    # Fee schedule
    fee_sched: Optional[int] = None
    
    # Signature
    sig_on_file: Optional[bool] = None
    
    # Anesthesia provider
    is_anesthesia_provider: Optional[bool] = None
    
    # Electronic claims
    claiming_provider: Optional[bool] = None
    
    # WebSchedRecall settings
    web_sched_recall: Optional[bool] = None


class ProviderListResponse(BaseModel):
    """Response model for provider list operations."""
    
    providers: List[Provider]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class ProviderSearchRequest(BaseModel):
    """Request model for searching providers."""
    
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    abbreviation: Optional[str] = None
    specialty: Optional[str] = None
    is_active: Optional[bool] = None
    is_dentist: Optional[bool] = None
    is_hygienist: Optional[bool] = None
    
    # Pagination
    page: Optional[int] = 1
    per_page: Optional[int] = 50
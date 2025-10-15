"""documents models for Open Dental SDK."""

from datetime import datetime
from typing import Optional, List
from pydantic import Field

from ...base.models import BaseModel


class Document(BaseModel):
    """Document model."""
    
    # Primary identifiers
    id: int = Field(..., alias="DocNum", description="Document number (primary key)")
    patient_num: int = Field(..., alias="PatNum", description="Patient number")
    
    # File information
    file_name: str = Field(..., alias="FileName", description="Document filename")
    doc_category: int = Field(..., alias="DocCategory", description="Document category")
    
    # Basic information
    name: str = Field(..., alias="Description", description="Document description/name")
    description: Optional[str] = Field(None, alias="Note", description="Additional notes")
    
    # File details
    raw_base64: Optional[str] = Field(None, alias="RawBase64", description="Base64 encoded file content")
    thumbnail: Optional[str] = Field(None, alias="Thumbnail", description="Thumbnail image data")
    
    # Status and flags
    is_active: bool = Field(True, alias="IsActive", description="Whether document is active")
    is_flipped: bool = Field(False, alias="IsFlipped", description="Whether document is flipped")
    crop_x: int = Field(0, alias="CropX", description="Crop X coordinate")
    crop_y: int = Field(0, alias="CropY", description="Crop Y coordinate")
    crop_w: int = Field(0, alias="CropW", description="Crop width")
    crop_h: int = Field(0, alias="CropH", description="Crop height")
    window_level: int = Field(0, alias="WindowLevel", description="Window level for imaging")
    window_width: int = Field(0, alias="WindowWidth", description="Window width for imaging")
    mount_item_num: int = Field(0, alias="MountItemNum", description="Mount item number")
    degree_rotated: int = Field(0, alias="DegreeRotated", description="Degrees rotated")
    
    # Timestamps
    date_created: Optional[datetime] = Field(None, alias="DateCreated", description="Date document was created")
    date_modified: Optional[datetime] = Field(None, alias="DateTStamp", description="Date document was last modified")
    
    # Additional metadata
    image_type: Optional[str] = Field(None, alias="ImageType", description="Type of image (e.g., jpeg, png)")
    size_actual: Optional[int] = Field(None, alias="SizeActual", description="Actual file size in bytes")
    doc_server_num: int = Field(0, alias="DocServerNum", description="Document server number")
    provider_num: int = Field(0, alias="ProvNum", description="Provider number")
    user_num: int = Field(0, alias="UserNum", description="User number who created document")
    sig_is_topaz: bool = Field(False, alias="SigIsTopaz", description="Whether signature is Topaz format")
    signature: Optional[str] = Field(None, alias="Signature", description="Digital signature data")
    print_heading: Optional[str] = Field(None, alias="PrintHeading", description="Print heading text")
    show_date_time: bool = Field(False, alias="ShowDateTime", description="Whether to show date/time on document")
    external_guid: Optional[str] = Field(None, alias="ExternalGUID", description="External GUID reference")


class CreateDocumentRequest(BaseModel):
    """Request model for creating a new document."""
    
    # Required fields
    patient_num: int = Field(..., alias="PatNum", description="Patient number")
    file_name: str = Field(..., alias="FileName", description="Document filename")
    doc_category: int = Field(..., alias="DocCategory", description="Document category")
    
    # Optional fields
    name: Optional[str] = Field(None, alias="Description", description="Document description/name")
    description: Optional[str] = Field(None, alias="Note", description="Additional notes")
    raw_base64: Optional[str] = Field(None, alias="RawBase64", description="Base64 encoded file content")
    is_active: bool = Field(True, alias="IsActive", description="Whether document is active")
    provider_num: int = Field(0, alias="ProvNum", description="Provider number")
    user_num: int = Field(0, alias="UserNum", description="User number who created document")
    date_created: Optional[datetime] = Field(None, alias="DateCreated", description="Date document was created")
    image_type: Optional[str] = Field(None, alias="ImageType", description="Type of image (e.g., jpeg, png)")
    print_heading: Optional[str] = Field(None, alias="PrintHeading", description="Print heading text")
    show_date_time: bool = Field(False, alias="ShowDateTime", description="Whether to show date/time on document")


class UpdateDocumentRequest(BaseModel):
    """Request model for updating an existing document."""
    
    # All fields are optional for updates
    patient_num: Optional[int] = Field(None, alias="PatNum", description="Patient number")
    file_name: Optional[str] = Field(None, alias="FileName", description="Document filename")
    doc_category: Optional[int] = Field(None, alias="DocCategory", description="Document category")
    name: Optional[str] = Field(None, alias="Description", description="Document description/name")
    description: Optional[str] = Field(None, alias="Note", description="Additional notes")
    raw_base64: Optional[str] = Field(None, alias="RawBase64", description="Base64 encoded file content")
    is_active: Optional[bool] = Field(None, alias="IsActive", description="Whether document is active")
    is_flipped: Optional[bool] = Field(None, alias="IsFlipped", description="Whether document is flipped")
    crop_x: Optional[int] = Field(None, alias="CropX", description="Crop X coordinate")
    crop_y: Optional[int] = Field(None, alias="CropY", description="Crop Y coordinate")
    crop_w: Optional[int] = Field(None, alias="CropW", description="Crop width")
    crop_h: Optional[int] = Field(None, alias="CropH", description="Crop height")
    window_level: Optional[int] = Field(None, alias="WindowLevel", description="Window level for imaging")
    window_width: Optional[int] = Field(None, alias="WindowWidth", description="Window width for imaging")
    degree_rotated: Optional[int] = Field(None, alias="DegreeRotated", description="Degrees rotated")
    provider_num: Optional[int] = Field(None, alias="ProvNum", description="Provider number")
    user_num: Optional[int] = Field(None, alias="UserNum", description="User number who created document")
    image_type: Optional[str] = Field(None, alias="ImageType", description="Type of image (e.g., jpeg, png)")
    print_heading: Optional[str] = Field(None, alias="PrintHeading", description="Print heading text")
    show_date_time: Optional[bool] = Field(None, alias="ShowDateTime", description="Whether to show date/time on document")
    external_guid: Optional[str] = Field(None, alias="ExternalGUID", description="External GUID reference")


class DocumentListResponse(BaseModel):
    """Response model for document list operations."""
    
    documents: List[Document]
    total: int
    page: Optional[int] = None
    per_page: Optional[int] = None


class DocumentSearchRequest(BaseModel):
    """Request model for searching documents."""
    
    patient_num: Optional[int] = Field(None, alias="PatNum", description="Patient number")
    doc_category: Optional[int] = Field(None, alias="DocCategory", description="Document category")
    name: Optional[str] = Field(None, alias="Description", description="Document description/name")
    file_name: Optional[str] = Field(None, alias="FileName", description="Document filename")
    is_active: Optional[bool] = Field(None, alias="IsActive", description="Whether document is active")
    provider_num: Optional[int] = Field(None, alias="ProvNum", description="Provider number")
    user_num: Optional[int] = Field(None, alias="UserNum", description="User number who created document")
    date_created_start: Optional[datetime] = Field(None, alias="DateCreatedStart", description="Search documents created after this date")
    date_created_end: Optional[datetime] = Field(None, alias="DateCreatedEnd", description="Search documents created before this date")
    
    # Pagination
    page: Optional[int] = 1
    per_page: Optional[int] = 50

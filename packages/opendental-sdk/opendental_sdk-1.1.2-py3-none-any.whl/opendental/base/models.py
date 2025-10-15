"""Base Pydantic models for Open Dental SDK."""

from pydantic import BaseModel as PydanticBaseModel


class BaseModel(PydanticBaseModel):
    """Base model for all Open Dental SDK models."""
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True
        arbitrary_types_allowed = True
        # Support for field aliases (Python names -> database field names)
        allow_population_by_field_name = True
        populate_by_name = True
        json_encoders = {
            # Add custom encoders here if needed
        }
        
    def model_dump(self, **kwargs):
        """Convert model to dictionary, excluding None values by default."""
        kwargs.setdefault('exclude_none', True)
        return super().model_dump(**kwargs)
    
    def dict(self, **kwargs):
        """Deprecated: use model_dump instead."""
        return self.model_dump(**kwargs)
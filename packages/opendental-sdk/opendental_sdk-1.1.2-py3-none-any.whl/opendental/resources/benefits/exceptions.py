"""Custom exceptions for Benefits resource."""

from typing import List, Optional


class BenefitValidationError(Exception):
    """Raised when benefit validation fails."""
    
    def __init__(self, errors: List[str], message: str = "Benefit validation failed"):
        """
        Initialize the validation error.
        
        Args:
            errors: List of validation error messages
            message: Optional custom message
        """
        self.errors = errors
        self.message = message
        super().__init__(self.message)
    
    def __str__(self):
        """String representation of the error."""
        error_list = "\n- ".join(self.errors)
        return f"{self.message}:\n- {error_list}"
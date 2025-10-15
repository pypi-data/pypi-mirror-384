"""diseases resource module."""

from .client import DiseasesClient
from .models import Disease, CreateDiseaseRequest, UpdateDiseaseRequest

__all__ = ["DiseasesClient", "Disease", "CreateDiseaseRequest", "UpdateDiseaseRequest"]

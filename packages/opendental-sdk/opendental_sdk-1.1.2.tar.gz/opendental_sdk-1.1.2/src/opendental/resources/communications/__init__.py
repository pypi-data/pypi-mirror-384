"""communications resource module."""

from .client import CommunicationsClient
from .models import Communication, CreateCommunicationRequest, UpdateCommunicationRequest

__all__ = ["CommunicationsClient", "Communication", "CreateCommunicationRequest", "UpdateCommunicationRequest"]

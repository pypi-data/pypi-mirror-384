"""Auto notes resource module."""

from .client import AutoNotesClient
from .models import AutoNote, CreateAutoNoteRequest, UpdateAutoNoteRequest

__all__ = ["AutoNotesClient", "AutoNote", "CreateAutoNoteRequest", "UpdateAutoNoteRequest"]
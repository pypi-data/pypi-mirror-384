"""procedurelogs resource module."""

from .client import ProcedureLogsClient
from .models import ProcedureLog, CreateProcedureLogRequest, UpdateProcedureLogRequest

__all__ = ["ProcedureLogsClient", "ProcedureLog", "CreateProcedureLogRequest", "UpdateProcedureLogRequest"]

"""Open Dental API resources."""

from .patients import PatientsClient
from .appointments import AppointmentsClient
from .claims import ClaimsClient
from .providers import ProvidersClient
from .procedures import ProceduresClient
from .employees import EmployeesClient
from .adjustments import AdjustmentsClient
from .allergies import AllergiesClient
from .carriers import CarriersClient
from .clinics import ClinicsClient
from .fees import FeesClient
from .insurance_plans import InsurancePlansClient
from .medications import MedicationsClient
from .payments import PaymentsClient
from .users import UsersClient

# New resource modules
from .account_modules import AccountModulesClient
from .appointment_types import AppointmentTypesClient
from .auto_notes import AutoNotesClient
from .benefits import BenefitsClient
from .chart_modules import ChartModulesClient
from .clock_events import ClockEventsClient
from .communications import CommunicationsClient
from .computers import ComputersClient
from .definitions import DefinitionsClient
from .diseases import DiseasesClient
from .documents import DocumentsClient
from .employers import EmployersClient
from .family_modules import FamilyModulesClient
from .lab_cases import LabCasesClient
from .operatories import OperatorysClient
from .patient_fields import PatientFieldsClient
from .pay_plans import PayPlansClient
from .pharmacies import PharmacysClient
from .procedure_codes import ProcedureCodesClient
from .procedure_logs import ProcedureLogsClient
from .recalls import RecallsClient
from .referrals import ReferralsClient
from .schedules import SchedulesClient
from .sheets import SheetsClient
from .statements import StatementsClient
from .tasks import TasksClient

__all__ = [
    "PatientsClient",
    "AppointmentsClient", 
    "ClaimsClient",
    "ProvidersClient",
    "ProceduresClient",
    "EmployeesClient",
    "AdjustmentsClient",
    "AllergiesClient",
    "CarriersClient",
    "ClinicsClient",
    "FeesClient",
    "InsurancePlansClient",
    "MedicationsClient",
    "PaymentsClient",
    "UsersClient",
    # New resource clients
    "AccountModulesClient",
    "AppointmentTypesClient",
    "AutoNotesClient",
    "BenefitsClient",
    "ChartModulesClient",
    "ClockEventsClient",
    "CommunicationsClient",
    "ComputersClient",
    "DefinitionsClient",
    "DiseasesClient",
    "DocumentsClient",
    "EmployersClient",
    "FamilyModulesClient",
    "LabCasesClient",
    "OperatorysClient",
    "PatientFieldsClient",
    "PayPlansClient",
    "PharmacysClient",
    "ProcedureCodesClient",
    "ProcedureLogsClient",
    "RecallsClient",
    "ReferralsClient",
    "SchedulesClient",
    "SheetsClient",
    "StatementsClient",
    "TasksClient"
]
"""
Open Dental API Client

Main client class for interacting with the Open Dental API with resource-based architecture.
"""

import os
import logging
from typing import Optional, Dict, Any, Union, List
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .exceptions import OpenDentalAPIError


logger = logging.getLogger(__name__)


class OpenDentalClient:
    """
    Main client for interacting with the Open Dental API.

    Provides resource-based access to all Open Dental API endpoints with proper
    authentication, error handling, and retry logic.

    Example:
        client = OpenDentalClient()
        
        # Patient operations
        patients = client.patients.search(last_name="Smith")
        patient = client.patients.create(first_name="John", last_name="Doe")
        
        # Appointment operations
        appointment = client.appointments.create(patient_id=123, provider_id=1)
        
        # Procedure operations
        procedures = client.procedures.get_by_patient(patient_id=123)
        
        # Payment operations
        payment = client.payments.create_cash_payment(patient_id=123, amount=100.00)
        
        # Other resources: employees, adjustments, allergies, carriers, 
        # clinics, fees, insurance_plans, medications, users, account_modules,
        # appointment_types, auto_notes, benefits, chart_modules, clock_events,
        # communications, computers, definitions, diseases, documents, employers,
        # family_modules, lab_cases, operatories, patient_fields, pay_plans,
        # pharmacies, procedure_codes, procedure_logs, recalls, referrals,
        # schedules, sheets, statements, tasks, code_groups, coverage_categories
    """

    def __init__(
        self,
        developer_key: Optional[str] = None,
        customer_key: Optional[str] = None,
        base_url: str = "https://api.opendental.com/api/v1",
        timeout: int = 30,
        max_retries: int = 3,
        debug: bool = False,
    ):
        """
        Initialize the Open Dental API client.

        Args:
            developer_key: Developer API key (can be set via OPENDENTAL_DEVELOPER_KEY env var)
            customer_key: Customer API key (can be set via OPENDENTAL_CUSTOMER_KEY env var)
            base_url: Base URL for the Open Dental API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts for failed requests
            debug: Enable debug logging
        """
        self.developer_key = developer_key or os.getenv("OPENDENTAL_DEVELOPER_KEY")
        self.customer_key = customer_key or os.getenv("OPENDENTAL_CUSTOMER_KEY")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.debug = debug

        if self.debug:
            logging.basicConfig(level=logging.DEBUG)

        if not self.developer_key or not self.customer_key:
            raise ValueError(
                "Both developer_key and customer_key are required. "
                "Set them directly or via OPENDENTAL_DEVELOPER_KEY and OPENDENTAL_CUSTOMER_KEY environment variables."
            )

        # Set up session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=[
                "HEAD",
                "GET",
                "PUT",
                "DELETE",
                "OPTIONS",
                "TRACE",
                "POST",
            ],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set Open Dental API headers (using ODFHIR format)
        self.session.headers.update(
            {
                "Authorization": f"ODFHIR {self.developer_key}/{self.customer_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "opendental-python-sdk/1.0.0",
            }
        )

        # Initialize resource managers
        self._init_resources()

    def _init_resources(self):
        """Initialize all resource managers."""
        # Import here to avoid circular imports
        from .resources.patients.client import PatientsClient
        from .resources.appointments.client import AppointmentsClient
        from .resources.claims.client import ClaimsClient
        from .resources.providers.client import ProvidersClient
        from .resources.procedures.client import ProceduresClient
        from .resources.employees.client import EmployeesClient
        from .resources.adjustments.client import AdjustmentsClient
        from .resources.allergies.client import AllergiesClient
        from .resources.carriers.client import CarriersClient
        from .resources.clinics.client import ClinicsClient
        from .resources.fees.client import FeesClient
        from .resources.insurance_plans.client import InsurancePlansClient
        from .resources.medications.client import MedicationsClient
        from .resources.payments.client import PaymentsClient
        from .resources.users.client import UsersClient
        
        # New resource clients
        from .resources.account_modules.client import AccountModulesClient
        from .resources.appointment_types.client import AppointmentTypesClient
        from .resources.auto_notes.client import AutoNotesClient
        from .resources.benefits.client import BenefitsClient
        from .resources.chart_modules.client import ChartModulesClient
        from .resources.clock_events.client import ClockEventsClient
        from .resources.communications.client import CommunicationsClient
        from .resources.computers.client import ComputersClient
        from .resources.definitions.client import DefinitionsClient
        from .resources.diseases.client import DiseasesClient
        from .resources.documents.client import DocumentsClient
        from .resources.employers.client import EmployersClient
        from .resources.family_modules.client import FamilyModulesClient
        from .resources.lab_cases.client import LabCasesClient
        from .resources.patient_fields.client import PatientFieldsClient
        from .resources.pay_plans.client import PayPlansClient
        from .resources.pharmacies.client import PharmacysClient
        from .resources.operatories.client import OperatorysClient
        from .resources.procedure_codes.client import ProcedureCodesClient
        from .resources.procedure_logs.client import ProcedureLogsClient
        from .resources.recalls.client import RecallsClient
        from .resources.referrals.client import ReferralsClient
        from .resources.schedules.client import SchedulesClient
        from .resources.sheets.client import SheetsClient
        from .resources.statements.client import StatementsClient
        from .resources.tasks.client import TasksClient
        from .resources.treatment_plans.client import TreatmentPlansClient
        from .resources.code_groups.client import CodeGroupsClient
        from .resources.coverage_categories.client import CoverageCategoryClient

        # Initialize original resource clients
        self.patients = PatientsClient(self)
        self.appointments = AppointmentsClient(self)
        self.claims = ClaimsClient(self)
        self.providers = ProvidersClient(self)
        self.procedures = ProceduresClient(self)
        self.employees = EmployeesClient(self)
        self.adjustments = AdjustmentsClient(self)
        self.allergies = AllergiesClient(self)
        self.carriers = CarriersClient(self)
        self.clinics = ClinicsClient(self)
        self.fees = FeesClient(self)
        self.insurance_plans = InsurancePlansClient(self)
        self.medications = MedicationsClient(self)
        self.payments = PaymentsClient(self)
        self.users = UsersClient(self)
        
        # Initialize new resource clients
        self.account_modules = AccountModulesClient(self)
        self.appointment_types = AppointmentTypesClient(self)
        self.auto_notes = AutoNotesClient(self)
        self.benefits = BenefitsClient(self)
        self.chart_modules = ChartModulesClient(self)
        self.clock_events = ClockEventsClient(self)
        self.communications = CommunicationsClient(self)
        self.computers = ComputersClient(self)
        self.definitions = DefinitionsClient(self)
        self.diseases = DiseasesClient(self)
        self.documents = DocumentsClient(self)
        self.employers = EmployersClient(self)
        self.family_modules = FamilyModulesClient(self)
        self.lab_cases = LabCasesClient(self)
        self.operatories = OperatorysClient(self)
        self.patient_fields = PatientFieldsClient(self)
        self.pay_plans = PayPlansClient(self)
        self.pharmacies = PharmacysClient(self)
        self.procedure_codes = ProcedureCodesClient(self)
        self.procedure_logs = ProcedureLogsClient(self)
        self.recalls = RecallsClient(self)
        self.referrals = ReferralsClient(self)
        self.schedules = SchedulesClient(self)
        self.sheets = SheetsClient(self)
        self.statements = StatementsClient(self)
        self.tasks = TasksClient(self)
        self.treatment_plans = TreatmentPlansClient(self)
        self.code_groups = CodeGroupsClient(self)
        self.coverage_categories = CoverageCategoryClient(self)

    def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Union[Dict, list, None]:
        """
        Make an authenticated request to the Open Dental API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            params: Query parameters
            json_data: JSON request body
            headers: Additional headers

        Returns:
            Parsed JSON response or None for empty responses

        Raises:
            OpenDentalAPIError: When API returns an error
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        request_headers = self.session.headers.copy()
        if headers:
            request_headers.update(headers)

        if self.debug:
            logger.debug(f"Making {method} request to {url}")
            if params:
                logger.debug(f"Query params: {params}")
            if json_data:
                logger.debug(f"JSON data: {json_data}")

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=request_headers,
                timeout=self.timeout,
            )

            if self.debug:
                logger.debug(f"Response status: {response.status_code}")
                logger.debug(f"Response headers: {dict(response.headers)}")

            # Handle different response status codes
            if response.status_code == 204:  # No Content
                return None

            response.raise_for_status()

            # Parse JSON response
            try:
                json_response = response.json()
                return json_response
            except ValueError:
                # Handle non-JSON responses
                if response.text:
                    # If we get a text response, it's likely an error
                    raise OpenDentalAPIError(
                        f"API returned non-JSON response: {response.text[:200]}",
                        status_code=response.status_code
                    )
                return None

        except requests.exceptions.HTTPError as e:
            error_message = f"HTTP {e.response.status_code} error"
            error_data = None
            
            try:
                error_data = e.response.json()
                # Extract message from JSON response
                if isinstance(error_data, dict):
                    error_message = error_data.get("message", error_message)
                elif isinstance(error_data, str):
                    error_message = error_data
            except (ValueError, AttributeError):
                # For non-JSON responses, use status text
                if hasattr(e.response, 'text') and e.response.text:
                    # Limit error text to prevent huge error messages
                    error_text = e.response.text[:200]
                    if not (error_text.startswith('<!DOCTYPE') or error_text.startswith('<html')):
                        error_message = error_text

            raise OpenDentalAPIError(
                error_message,
                status_code=e.response.status_code if hasattr(e, 'response') else None,
                response_data=error_data,
            )
        except requests.exceptions.RequestException as e:
            raise OpenDentalAPIError(f"Request failed: {str(e)}")

    def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict, list, None]:
        """Make a GET request."""
        return self.request("GET", endpoint, params=params)

    def post(
        self, endpoint: str, json_data: Optional[Dict[str, Any]] = None
    ) -> Union[Dict, list, None]:
        """Make a POST request."""
        return self.request("POST", endpoint, json_data=json_data)

    def put(
        self, endpoint: str, json_data: Optional[Dict[str, Any]] = None
    ) -> Union[Dict, list, None]:
        """Make a PUT request."""
        return self.request("PUT", endpoint, json_data=json_data)

    def delete(self, endpoint: str) -> Union[Dict, list, None]:
        """Make a DELETE request."""
        return self.request("DELETE", endpoint)

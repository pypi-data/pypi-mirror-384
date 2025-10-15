# Open Dental Python SDK

A comprehensive Python SDK for the Open Dental API, providing 100% endpoint coverage, type safety, and easy integration with your Python applications.

## Installation

Install the SDK using your preferred Python package manager:

### pip

```bash
pip install opendental-sdk
```

### rye

```bash
rye add opendental-sdk
```

### uv

```bash
uv pip install opendental-sdk
```

## Quick Start

```python
from opendental import OpenDentalClient

# Initialize the client with your API keys
client = OpenDentalClient(
    developer_key="your_developer_key_here",
    customer_key="your_customer_key_here"
)

# Or use environment variables
# export OPENDENTAL_DEVELOPER_KEY=your_developer_key_here
# export OPENDENTAL_CUSTOMER_KEY=your_customer_key_here
client = OpenDentalClient()

# Get all patients
patients = client.patients.get()

# Get a specific patient
patient = client.patients.get(patient_id=123)

# Create a new patient
new_patient = client.patients.create({
    "firstName": "John",
    "lastName": "Doe",
    "email": "john.doe@example.com"
})

# Update a patient
updated_patient = client.patients.update(123, {
    "email": "newemail@example.com"
})

# Delete a patient
client.patients.delete(123)
```

## Authentication

The Open Dental API requires both a Developer API Key and a Customer API Key. You can obtain these from the Open Dental Developer Portal.

Set your keys in one of the following ways:

1. **Environment Variables** (Recommended):

```bash
export OPENDENTAL_DEVELOPER_KEY=your_developer_key
export OPENDENTAL_CUSTOMER_KEY=your_customer_key
```

2. **Direct Initialization**:

```python
client = OpenDentalClient(
    developer_key="your_developer_key",
    customer_key="your_customer_key"
)
```

## Error Handling

The SDK provides comprehensive error handling:

```python
from opendental import OpenDentalClient, OpenDentalAPIError

try:
    client = OpenDentalClient()
    patients = client.patients.get()
except OpenDentalAPIError as e:
    print(f"API Error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Available Resources

The SDK provides access to all Open Dental API resources:

- **Patients**: `client.patients`
- **Appointments**: `client.appointments`
- **Procedures**: `client.procedures`
- **Insurance**: `client.insurance`
- **Billing**: `client.billing`
- And many more...

## Configuration

You can customize the client behavior:

```python
client = OpenDentalClient(
    developer_key="your_key",
    customer_key="your_key",
    base_url="https://api.opendental.com",  # Custom API base URL
    timeout=30  # Request timeout in seconds
)
```

## Type Safety

The SDK includes full type annotations and supports modern Python type checking:

```python
from opendental import OpenDentalClient
from opendental.models import Patient

client: OpenDentalClient = OpenDentalClient()
patient: Patient = client.patients.get(123)
```

## Development

To set up the development environment:

```bash
git clone https://github.com/opendental/python-sdk
cd python-sdk/python
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black src/
isort src/
```

### Type Checking

```bash
mypy src/
```

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

## Support

For support and questions:

- Check the [API Documentation](https://www.opendental.com/site/apidocumentation.html)
- Open an issue on [GitHub](https://github.com/opendental/python-sdk/issues)
- Contact Open Dental support

## HIPAA Compliance

⚠️ **Important**: This SDK handles sensitive patient data. Ensure you have a Business Associate Agreement (BAA) in place with Open Dental and follow all HIPAA compliance requirements when using this SDK in production.

## Using uv for Dependency Management

We recommend using [uv](https://github.com/astral-sh/uv) for fast dependency management and environment setup.

### Install uv

You can install uv with pipx:

```bash
pipx install uv
```

Or with Homebrew (on macOS):

```bash
brew install astral-sh/uv/uv
```

### Create a Virtual Environment and Install Dependencies

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

Or install directly from `pyproject.toml`:

```bash
uv pip install -r <(uv pip compile pyproject.toml)
```

### Running Tests

```bash
uv pip install -r requirements.txt --extra dev
pytest
```

For more, see the [uv documentation](https://github.com/astral-sh/uv).

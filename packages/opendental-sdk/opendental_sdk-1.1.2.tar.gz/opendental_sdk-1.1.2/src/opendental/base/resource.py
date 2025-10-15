"""Base resource class for Open Dental SDK."""

from typing import Optional, Dict, Any, Union, List, Type, TypeVar
from ..exceptions import OpenDentalAPIError

T = TypeVar('T')


class BaseResource:
    """Base class for all Open Dental API resources."""
    
    def __init__(self, client, resource_name: str):
        """
        Initialize the resource.
        
        Args:
            client: The OpenDentalClient instance
            resource_name: The name of the resource (e.g., 'patients', 'appointments')
        """
        self.client = client
        self.resource_name = resource_name
        self.base_endpoint = f"/{resource_name}"
    
    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Union[Dict, List, None]:
        """Make a GET request to the API."""
        return self.client.get(endpoint, params=params)
    
    def _post(self, endpoint: str, json_data: Optional[Dict[str, Any]] = None) -> Union[Dict, List, None]:
        """Make a POST request to the API."""
        response = self.client.post(endpoint, json_data=json_data)
        # The client.post() already handles string responses properly
        return response
    
    def _put(self, endpoint: str, json_data: Optional[Dict[str, Any]] = None) -> Union[Dict, List, None]:
        """Make a PUT request to the API."""
        return self.client.put(endpoint, json_data=json_data)
    
    def _delete(self, endpoint: str) -> Union[Dict, List, None]:
        """Make a DELETE request to the API."""
        return self.client.delete(endpoint)
    
    def _build_endpoint(self, path: str = "") -> str:
        """Build the full endpoint path."""
        if path:
            return f"{self.base_endpoint}/{path.lstrip('/')}"
        return self.base_endpoint
    
    def _validate_id(self, resource_id: Union[int, str]) -> str:
        """Validate and convert resource ID to string."""
        if resource_id is None:
            raise ValueError("Resource ID cannot be None")
        return str(resource_id)
    
    def _handle_response(self, response: Union[Dict, List, str, None], model_class: Type[T]) -> T:
        """Handle API response and convert to model."""
        if response is None:
            raise OpenDentalAPIError("No response received from API")
        
        if isinstance(response, str):
            # String responses are usually error messages
            raise OpenDentalAPIError(f"API error: {response}")
        
        if isinstance(response, dict):
            return model_class(**response)
        elif isinstance(response, list) and len(response) > 0:
            return model_class(**response[0])
        else:
            raise OpenDentalAPIError(f"Invalid response format: {type(response)}")
    
    def _handle_list_response(self, response: Union[Dict, List, None], model_class: Type[T]) -> List[T]:
        """Handle API response and convert to list of models."""
        if response is None:
            return []
        
        if isinstance(response, list):
            return [model_class(**item) for item in response]
        elif isinstance(response, dict):
            # Sometimes APIs return a dict with a 'data' or 'items' key
            if 'data' in response:
                return [model_class(**item) for item in response['data']]
            elif 'items' in response:
                return [model_class(**item) for item in response['items']]
            else:
                # Single item response
                return [model_class(**response)]
        else:
            return []
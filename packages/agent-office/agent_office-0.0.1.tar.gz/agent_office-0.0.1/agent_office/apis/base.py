"""Base API client."""

import json
from typing import Any, Dict, Optional
import requests
from ..exceptions import (
    AgentOfficeError,
    AuthenticationError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    ServerError,
)


class BaseAPI:
    """Base class for all API clients."""
    
    def __init__(self, base_url: str, api_key: str, timeout: int = 60):
        """Initialize base API client.
        
        Args:
            base_url: Base URL for the API
            api_key: API key for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
        })
    
    def _handle_response(self, response: requests.Response) -> Any:
        """Handle API response and raise appropriate exceptions.
        
        Args:
            response: Response from API
            
        Returns:
            Parsed JSON response
            
        Raises:
            AgentOfficeError: For various error conditions
        """
        try:
            data = response.json()
        except json.JSONDecodeError:
            data = None
        
        if response.status_code == 200:
            return data
        elif response.status_code == 401:
            raise AuthenticationError(
                "Authentication failed. Check your API key.",
                status_code=401
            )
        elif response.status_code == 404:
            raise NotFoundError(
                data.get("detail", "Resource not found") if data else "Resource not found",
                status_code=404
            )
        elif response.status_code == 422:
            raise ValidationError(
                data.get("detail", "Validation error") if data else "Validation error",
                status_code=422
            )
        elif response.status_code == 429:
            raise RateLimitError(
                "Rate limit exceeded. Please try again later.",
                status_code=429
            )
        elif response.status_code >= 500:
            raise ServerError(
                data.get("detail", "Server error") if data else "Server error",
                status_code=response.status_code
            )
        else:
            raise AgentOfficeError(
                data.get("detail", f"Request failed with status {response.status_code}") if data 
                else f"Request failed with status {response.status_code}",
                status_code=response.status_code
            )
    
    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Make GET request.
        
        Args:
            path: API path
            params: Query parameters
            
        Returns:
            Parsed response
        """
        url = f"{self.base_url}{path}"
        response = self.session.get(url, params=params, timeout=self.timeout)
        return self._handle_response(response)
    
    def _post(
        self,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Make POST request.
        
        Args:
            path: API path
            json_data: JSON data to send
            files: Files to upload
            data: Form data to send
            
        Returns:
            Parsed response
        """
        url = f"{self.base_url}{path}"
        response = self.session.post(
            url,
            json=json_data,
            files=files,
            data=data,
            timeout=self.timeout
        )
        return self._handle_response(response)


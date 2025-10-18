from dataclasses import dataclass
from typing import Any, Dict, Optional, Union

import requests

from .. import logger


@dataclass
class HttpResponse:
    """Represents an HTTP response."""
    
    success: bool
    status_code: int
    data: Optional[Union[Dict[str, Any], list, str]] = None
    error: Optional[str] = None
    headers: Optional[Dict[str, str]] = None

    @property
    def is_success(self) -> bool:
        """Check if the response indicates success (status code < 400)."""
        return self.status_code < 400


class HttpClient:
    """General HTTP client abstraction for making authenticated and non-authenticated requests."""

    def __init__(self, base_url: str = "", timeout: int = 30, auth_token: Optional[str] = None, auth_type: str = "Bearer") -> None:
        """Initialize HTTP client.
        
        Args:
            base_url (str): Base URL for all requests. Optional.
            timeout (int): Request timeout in seconds.
            auth_token (str, optional): Authentication token to use for all requests.
            auth_type (str): Authentication type (Bearer, Basic, etc.).
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.auth_token = auth_token
        self.auth_type = auth_type
        self.default_headers: Dict[str, str] = {
            "User-Agent": "EasyRunner-CLI/1.0"
        }

    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint."""
        if endpoint.startswith("http"):
            return endpoint

        endpoint = endpoint.lstrip("/")
        if self.base_url:
            return f"{self.base_url}/{endpoint}"
        return endpoint

    def _prepare_headers(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Prepare headers for request."""
        final_headers = self.default_headers.copy()

        if headers:
            final_headers.update(headers)

        # Add authentication if configured
        if self.auth_token:
            final_headers["Authorization"] = f"{self.auth_type} {self.auth_token}"

        return final_headers

    def _make_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Union[Dict[str, Any], str]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> HttpResponse:
        """Make HTTP request and return standardized response."""
        try:
            kwargs = {
                "url": url,
                "headers": headers,
                "timeout": self.timeout
            }

            if json_data is not None:
                kwargs["json"] = json_data
            elif data is not None:
                kwargs["data"] = data

            response = requests.request(method, **kwargs)

            logger.debug(
                f"[{response.status_code}] HTTP {method} {url} -> {response.content}"
            )

            # Parse response data
            response_data = None
            if response.content:
                try:
                    response_data = response.json()
                except ValueError:
                    # If JSON parsing fails, store as text
                    response_data = response.text

            return HttpResponse(
                success=response.status_code < 400,
                status_code=response.status_code,
                data=response_data,
                error=response_data.get("message") if isinstance(response_data, dict) and response.status_code >= 400 else None,
                headers=dict(response.headers)
            )

        except requests.exceptions.RequestException as e:
            return HttpResponse(
                success=False,
                status_code=0,
                error=f"Request failed: {str(e)}"
            )

    def get(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None
    ) -> HttpResponse:
        """Make GET request."""
        url = self._build_url(endpoint)
        final_headers = self._prepare_headers(headers)
        return self._make_request("GET", url, final_headers)

    def post(
        self,
        endpoint: str,
        data: Optional[Union[Dict[str, Any], str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> HttpResponse:
        """Make POST request."""
        url = self._build_url(endpoint)
        final_headers = self._prepare_headers(headers)

        if json_data is not None:
            final_headers["Content-Type"] = "application/json"

        return self._make_request("POST", url, final_headers, data, json_data)

    def put(
        self,
        endpoint: str,
        data: Optional[Union[Dict[str, Any], str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> HttpResponse:
        """Make PUT request."""
        url = self._build_url(endpoint)
        final_headers = self._prepare_headers(headers)

        if json_data is not None:
            final_headers["Content-Type"] = "application/json"

        return self._make_request("PUT", url, final_headers, data, json_data)

    def delete(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None
    ) -> HttpResponse:
        """Make DELETE request."""
        url = self._build_url(endpoint)
        final_headers = self._prepare_headers(headers)
        return self._make_request("DELETE", url, final_headers)

    def patch(
        self,
        endpoint: str,
        data: Optional[Union[Dict[str, Any], str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> HttpResponse:
        """Make PATCH request."""
        url = self._build_url(endpoint)
        final_headers = self._prepare_headers(headers)

        if json_data is not None:
            final_headers["Content-Type"] = "application/json"

        return self._make_request("PATCH", url, final_headers, data, json_data)

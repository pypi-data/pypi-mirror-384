import httpx
from typing import Optional, Dict, Any

from .exceptions import APIError, AuthenticationError, NotFoundError, InvalidRequestError

class BaseClient:
    """
    A base client for making requests to the Datacenter API.
    """
    def __init__(self, base_url: str, token: Optional[str] = None, timeout: int = 30):
        """
        Initializes the API client.

        Args:
            base_url: The base URL for the API, e.g., "http://localhost:10000".
            token: An optional token for authentication.
            timeout: The request timeout in seconds.
        """
        self._base_url = base_url.rstrip('/')
        self._token = token
        self._timeout = timeout
        
        headers = {"Content-Type": "application/json"}
        if self._token:
            headers["X-API-Key"] = self._token
            
        self._http_client = httpx.Client(base_url=self._base_url, headers=headers, timeout=self._timeout)

    def _request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None) -> Any:
        """
        Makes an HTTP request and handles potential errors.
        """
        try:
            response = self._http_client.request(method, endpoint, params=params, json=json)
            response.raise_for_status()
            
            response_data = response.json()
            if response_data.get("status") == "success":
                return response_data
            
            raise APIError(f"API returned non-success status: {response_data.get('status', 'N/A')}", status_code=response.status_code)

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            try:
                detail = e.response.json().get("detail", e.response.text)
            except Exception:
                detail = e.response.text

            if status_code == 404:
                raise NotFoundError(detail) from e
            elif status_code in [401, 403]:
                raise AuthenticationError(detail) from e
            elif status_code == 400:
                raise InvalidRequestError(detail) from e
            else:
                raise APIError(f"HTTP Error: {detail}", status_code=status_code) from e
        except httpx.RequestError as e:
            raise APIError(f"Request failed: {e}") from e

    def close(self):
        """Closes the underlying HTTP client."""
        self._http_client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
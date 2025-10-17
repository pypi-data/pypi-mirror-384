"""
HTTP client utilities with retry logic and error handling.
"""

import json
import time
from typing import Any, Dict, Optional, Union
from urllib.parse import urljoin

import httpx

from ..config import NetIntConfig
from ..exceptions import (
    AuthenticationError,
    ConnectionError,
    NetIntAPIError,
    PermissionError,
    RateLimitError,
    ResourceNotFoundError,
    ServerError,
    TimeoutError,
    ValidationError,
)


class HTTPClient:
    """
    HTTP client with automatic retry and error handling.

    Handles authentication, retries, and converts HTTP errors
    to appropriate SDK exceptions.
    """

    def __init__(self, config: NetIntConfig):
        """
        Initialize HTTP client.

        Args:
            config: NetInt configuration
        """
        self.config = config
        self.client = httpx.Client(
            timeout=config.timeout,
            verify=config.verify_ssl,
            headers=self._get_headers(),
        )

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "netint-agents-sdk/0.1.6",
        }
        if self.config.api_token:
            headers["Authorization"] = f"Bearer {self.config.api_token}"
        return headers

    def _build_url(self, path: str) -> str:
        """Build full URL from path."""
        # Handle absolute URLs (for instance-specific endpoints)
        if path.startswith("http://") or path.startswith("https://"):
            return path

        # Remove leading slash to avoid double slashes
        path = path.lstrip("/")
        return urljoin(self.config.base_url + "/backend/", path)

    def _log_request(self, method: str, url: str, headers: Dict[str, str], body: Any = None) -> None:
        """
        Log request details for debugging.

        Args:
            method: HTTP method
            url: Full URL
            headers: Request headers
            body: Request body (if any)
        """
        if not self.config.debug:
            return

        print("\n" + "=" * 80)
        print(f"🔵 REQUEST: {method} {url}")
        print("=" * 80)

        # Print headers (mask sensitive data)
        print("\n📋 HEADERS:")
        for key, value in headers.items():
            if key.lower() in ("authorization", "x-api-key"):
                # Mask token but show prefix
                if value.startswith("Bearer "):
                    token = value[7:]
                    masked = f"Bearer {token[:10]}...{token[-4:]}" if len(token) > 14 else "Bearer ***"
                    print(f"  {key}: {masked}")
                else:
                    print(f"  {key}: ***MASKED***")
            else:
                print(f"  {key}: {value}")

        # Print body
        if body is not None:
            print("\n📦 BODY:")
            try:
                if isinstance(body, dict):
                    print(json.dumps(body, indent=2))
                else:
                    print(body)
            except Exception:
                print(f"  {body}")

        print("=" * 80 + "\n")

    def _log_response(self, response: httpx.Response) -> None:
        """
        Log response details for debugging.

        Args:
            response: HTTP response object
        """
        if not self.config.debug:
            return

        print("\n" + "=" * 80)
        print(f"🟢 RESPONSE: {response.status_code} {response.reason_phrase}")
        print("=" * 80)

        # Print response headers
        print("\n📋 RESPONSE HEADERS:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")

        # Print response body
        print("\n📦 RESPONSE BODY:")
        try:
            body = response.json()
            print(json.dumps(body, indent=2))
        except Exception:
            text = response.text
            if len(text) > 500:
                print(text[:500] + "...")
            else:
                print(text if text else "(empty)")

        print("=" * 80 + "\n")

    def _handle_error(self, response: httpx.Response) -> None:
        """
        Convert HTTP errors to SDK exceptions.

        Args:
            response: HTTP response object

        Raises:
            AuthenticationError: For 401 errors
            PermissionError: For 403 errors
            ResourceNotFoundError: For 404 errors
            ValidationError: For 422 errors
            RateLimitError: For 429 errors
            ServerError: For 5xx errors
            NetIntAPIError: For other errors
        """
        try:
            error_data = response.json()
            message = error_data.get("detail", str(error_data))
        except Exception:
            message = response.text or f"HTTP {response.status_code}"

        status_code = response.status_code

        if status_code == 401:
            raise AuthenticationError(message, status_code, error_data if 'error_data' in locals() else None)
        elif status_code == 403:
            raise PermissionError(message, status_code, error_data if 'error_data' in locals() else None)
        elif status_code == 404:
            raise ResourceNotFoundError(message, status_code, error_data if 'error_data' in locals() else None)
        elif status_code == 422:
            validation_errors = error_data.get("detail", []) if 'error_data' in locals() else []
            raise ValidationError(message, validation_errors, status_code, error_data if 'error_data' in locals() else None)
        elif status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            raise RateLimitError(message, retry_after, status_code, error_data if 'error_data' in locals() else None)
        elif status_code >= 500:
            raise ServerError(message, status_code, error_data if 'error_data' in locals() else None)
        else:
            raise NetIntAPIError(message, status_code, error_data if 'error_data' in locals() else None)

    def _request_with_retry(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method
            path: URL path
            **kwargs: Additional request parameters

        Returns:
            HTTP response

        Raises:
            TimeoutError: If request times out
            ConnectionError: If connection fails
            NetIntAPIError: For API errors
        """
        url = self._build_url(path)
        last_exception = None

        # Log request details
        headers = kwargs.get("headers", self._get_headers())
        body = kwargs.get("json")
        if self.config.debug:
            print(f"URL: {url}")
            print(f"Headers: {headers}")
            print(f"Body: {body}")
        self._log_request(method, url, headers, body)

        for attempt in range(self.config.max_retries):
            try:
                response = self.client.request(method, url, **kwargs)

                if self.config.debug:
                    print(f"Response:")
                    print(response.text)

                # Log response details
                self._log_response(response)

                # Check for errors
                if response.status_code >= 400:
                    self._handle_error(response)

                return response

            except httpx.TimeoutException as e:
                last_exception = TimeoutError(f"Request timed out after {self.config.timeout}s")
                if attempt < self.config.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                raise last_exception from e

            except httpx.ConnectError as e:
                last_exception = ConnectionError(f"Failed to connect to {url}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise last_exception from e

            except (AuthenticationError, PermissionError, ResourceNotFoundError, ValidationError):
                # Don't retry these errors
                raise

            except RateLimitError as e:
                # Wait and retry for rate limit
                if attempt < self.config.max_retries - 1:
                    time.sleep(e.retry_after or 60)
                    continue
                raise

            except NetIntAPIError:
                # Retry server errors but not client errors
                raise

        if last_exception:
            raise last_exception

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make GET request.

        Args:
            path: URL path
            params: Query parameters

        Returns:
            Response data as dictionary
        """
        response = self._request_with_retry("GET", path, params=params)
        return response.json()

    def post(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make POST request.

        Args:
            path: URL path
            data: Request body data
            params: Query parameters

        Returns:
            Response data as dictionary
        """
        response = self._request_with_retry("POST", path, json=data, params=params)
        return response.json()

    def put(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make PUT request.

        Args:
            path: URL path
            data: Request body data

        Returns:
            Response data as dictionary
        """
        response = self._request_with_retry("PUT", path, json=data)
        return response.json()

    def delete(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Make DELETE request.

        Args:
            path: URL path

        Returns:
            Response data as dictionary (or None for 204 responses)
        """
        response = self._request_with_retry("DELETE", path)
        if response.status_code == 204:
            return None
        return response.json()

    def close(self) -> None:
        """Close HTTP client."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, *args):
        """Context manager exit."""
        self.close()

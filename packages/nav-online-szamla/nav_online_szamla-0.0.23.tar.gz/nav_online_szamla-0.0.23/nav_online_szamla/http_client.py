"""
HTTP client for NAV Online Számla API.

This module provides the HTTP client functionality for making requests 
to the NAV Online Számla API with proper error handling and retry logic.
"""

import logging
from typing import Dict, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry as Urllib3Retry
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from .config import (
    DEFAULT_HEADERS,
    DEFAULT_TIMEOUT,
    MAX_RETRY_ATTEMPTS,
    RETRY_BACKOFF_MULTIPLIER,
    RETRY_BACKOFF_MIN,
    RETRY_BACKOFF_MAX,
    RETRYABLE_HTTP_STATUS_CODES,
)
from .exceptions import NavNetworkException, NavApiException, NavRateLimitException

logger = logging.getLogger(__name__)


class NavHttpClient:
    """HTTP client for NAV API requests with retry logic and error handling."""

    def __init__(self, base_url: str, timeout: int = DEFAULT_TIMEOUT):
        """
        Initialize the HTTP client.

        Args:
            base_url: Base URL for the API
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        
        # Configure connection pooling with proper DNS handling
        # This prevents DNS exhaustion issues in high-volume scenarios
        adapter = HTTPAdapter(
            pool_connections=10,  # Number of connection pools to cache
            pool_maxsize=20,      # Max connections per pool
            max_retries=0,        # We handle retries with tenacity
            pool_block=False      # Don't block when pool is full
        )
        
        # Mount adapter for both HTTP and HTTPS
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # Set connection keep-alive header to prevent connection exhaustion
        self.session.headers.update({
            'Connection': 'keep-alive'
        })

    @retry(
        stop=stop_after_attempt(MAX_RETRY_ATTEMPTS),
        wait=wait_exponential(
            multiplier=RETRY_BACKOFF_MULTIPLIER,
            min=RETRY_BACKOFF_MIN,
            max=RETRY_BACKOFF_MAX,
        ),
        retry=retry_if_exception_type(
            (
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.HTTPError,
                requests.exceptions.RequestException,
            )
        ),
        reraise=True,
    )
    def _make_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> requests.Response:
        """
        Make an HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL for the request
            headers: Additional headers
            data: Request body data
            params: URL parameters

        Returns:
            requests.Response: HTTP response object

        Raises:
            NavNetworkException: For network-related errors
            NavApiException: For API-related errors
        """
        try:
            request_headers = dict(DEFAULT_HEADERS)
            if headers:
                request_headers.update(headers)

            logger.debug(f"Making {method} request to {url}")
            logger.debug(f"data: {data}")
            if method.upper() == "POST":
                response = self.session.post(
                    url,
                    headers=request_headers,
                    data=data,
                    params=params,
                    timeout=self.timeout,
                )
            else:
                response = self.session.request(
                    method,
                    url,
                    headers=request_headers,
                    data=data,
                    params=params,
                    timeout=self.timeout,
                )

            # Check for rate limiting
            if response.status_code == 429:
                raise NavRateLimitException("Rate limit exceeded")

            # Check for server errors that should be retried
            if response.status_code in RETRYABLE_HTTP_STATUS_CODES:
                response.raise_for_status()

            return response

        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.HTTPError,
            requests.exceptions.RequestException,
        ) as e:
            logger.warning(
                f"NAV API request failed (will retry if attempts remaining): {e}"
            )
            raise  # Let tenacity handle the retry

    def post(
        self, endpoint: str, data: str, headers: Optional[Dict[str, str]] = None
    ) -> requests.Response:
        """
        Make a POST request to the NAV API.

        Args:
            endpoint: API endpoint (without base URL)
            data: Request body data
            headers: Additional headers

        Returns:
            requests.Response: HTTP response object

        Raises:
            NavNetworkException: For network-related errors
            NavApiException: For API-related errors
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            response = self._make_request("POST", url, headers, data)
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {response.headers}")
            logger.debug(f"Response content: {response.content}")
            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            if isinstance(
                e, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)
            ):
                raise NavNetworkException(f"Network error: {str(e)}")
            elif hasattr(e, "response") and e.response is not None:
                status_code = e.response.status_code
                
                # Try to get response content in different ways
                try:
                    response_content = e.response.text
                except:
                    try:
                        response_content = e.response.content.decode('utf-8')
                    except:
                        response_content = str(e.response.content)
                
                # Print detailed error information
                print(f"\n=== NAV API ERROR RESPONSE ===")
                print(f"Status Code: {status_code}")
                print(f"URL: {url}")
                print(f"Request Headers: {headers}")
                print(f"Request Data (first 1000 chars): {data[:1000]}...")
                print(f"Response Headers: {dict(e.response.headers)}")
                print(f"Response Content: {response_content}")
                print(f"Response Content Length: {len(response_content)}")
                print(f"=== END ERROR RESPONSE ===\n")
                
                if status_code == 429:
                    raise NavRateLimitException("Rate limit exceeded")
                else:
                    raise NavApiException(
                        f"HTTP {status_code}: {str(e)}, response_data: {response_content}"
                    )
            else:
                raise NavApiException(f"Request failed: {str(e)}")

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> requests.Response:
        """
        Make a GET request to the NAV API.

        Args:
            endpoint: API endpoint (without base URL)
            params: URL parameters
            headers: Additional headers

        Returns:
            requests.Response: HTTP response object

        Raises:
            NavNetworkException: For network-related errors
            NavApiException: For API-related errors
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            response = self._make_request("GET", url, headers, params=params)
            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            if isinstance(
                e, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)
            ):
                raise NavNetworkException(f"Network error: {str(e)}")
            elif hasattr(e, "response") and e.response is not None:
                status_code = e.response.status_code
                if status_code == 429:
                    raise NavRateLimitException("Rate limit exceeded")
                else:
                    raise NavApiException(f"HTTP {status_code}: {str(e)}")
            else:
                raise NavApiException(f"Request failed: {str(e)}")

    def close(self):
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

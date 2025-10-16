"""
Custom exceptions for NAV Online Számla API.

This module defines custom exception classes used throughout the NAV Online Számla API client.
"""


class NavApiException(Exception):
    """Base exception class for NAV API related errors."""

    def __init__(
        self, message: str, error_code: str = None, response_data: dict = None
    ):
        super().__init__(message)
        self.error_code = error_code
        self.response_data = response_data or {}


class NavAuthenticationException(NavApiException):
    """Exception raised for authentication related errors."""

    pass


class NavValidationException(NavApiException):
    """Exception raised for validation errors."""

    pass


class NavNetworkException(NavApiException):
    """Exception raised for network related errors."""

    pass


class NavRateLimitException(NavApiException):
    """Exception raised when rate limit is exceeded."""

    pass


class NavXmlParsingException(NavApiException):
    """Exception raised for XML parsing errors."""

    pass


class NavConfigurationException(NavApiException):
    """Exception raised for configuration errors."""

    pass


class NavInvoiceNotFoundException(NavApiException):
    """Exception raised when an invoice is not found."""

    pass


class NavRequestSignatureException(NavApiException):
    """Exception raised for request signature generation errors."""

    pass

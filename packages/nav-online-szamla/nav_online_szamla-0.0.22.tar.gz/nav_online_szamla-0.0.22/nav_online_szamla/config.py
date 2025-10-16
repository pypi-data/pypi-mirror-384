"""
Configuration and constants for NAV Online Számla API.

This module contains configuration settings, constants, and default values 
used throughout the NAV Online Számla API client.
"""

"""
Configuration and constants for NAV Online Számla API.

This module contains configuration settings, constants, and default values 
used throughout the NAV Online Számla API client.
"""

import os
from enum import Enum
from typing import Dict

# Environment Configuration
class NavEnvironment(Enum):
    """NAV Online Számla API environments."""
    PRODUCTION = "production"
    TEST = "test"

# Environment URLs based on official NAV documentation (Section 6)
ENVIRONMENT_URLS: Dict[NavEnvironment, str] = {
    NavEnvironment.PRODUCTION: "https://api.onlineszamla.nav.gov.hu/invoiceService/v3",
    NavEnvironment.TEST: "https://api-test.onlineszamla.nav.gov.hu/invoiceService/v3"
}

# Default environment (can be overridden by ENV variable or client parameter)
DEFAULT_ENVIRONMENT = NavEnvironment.PRODUCTION

# Get environment from environment variable (supports both string and enum values)
def get_default_environment() -> NavEnvironment:
    """Get the default environment from environment variable or fallback to production."""
    env_var = os.getenv('NAV_ENVIRONMENT', DEFAULT_ENVIRONMENT.value).lower()
    
    # Support both string values and enum names
    if env_var in ['test', 'testing', 'development', 'dev']:
        return NavEnvironment.TEST
    elif env_var in ['prod', 'production', 'live']:
        return NavEnvironment.PRODUCTION
    else:
        return DEFAULT_ENVIRONMENT

# API Base URL (backward compatibility - will be overridden by environment selection)
ONLINE_SZAMLA_URL = ENVIRONMENT_URLS[DEFAULT_ENVIRONMENT]

# HTTP Headers
DEFAULT_HEADERS = {"Content-Type": "application/xml", "Accept": "application/xml"}

# Default timeout for HTTP requests (seconds)
DEFAULT_TIMEOUT = 30

# Maximum retry attempts for failed API calls
MAX_RETRY_ATTEMPTS = 5

# Exponential backoff configuration
# Wait times will be: 4s, 8s, 16s, 32s, 64s
RETRY_BACKOFF_MULTIPLIER = 2  # Exponential growth factor
RETRY_BACKOFF_MIN = 4  # Start with 4 seconds
RETRY_BACKOFF_MAX = 64  # Cap at 64 seconds

# Date range limits
MAX_DATE_RANGE_DAYS = 35

# API Version
API_VERSION = "3.0"

# Request signature algorithm
SIGNATURE_ALGORITHM = "SHA3-512"
PASSWORD_HASH_ALGORITHM = "SHA-512"

# Character set for custom ID generation
CUSTOM_ID_CHARACTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
CUSTOM_ID_LENGTH = 30

# Error handling
NETWORK_ERROR_KEYWORDS = ["connection", "timeout", "network", "resolve"]
RETRYABLE_HTTP_STATUS_CODES = [500, 502, 503, 504]

# XML Namespaces (if needed for parsing)
XML_NAMESPACES = {
    "ns2": "http://schemas.nav.gov.hu/OSA/3.0/api",
    "base": "http://schemas.nav.gov.hu/OSA/3.0/base",
}

# Customer VAT status mappings
CUSTOMER_VAT_STATUS_MAPPING = {
    "DOMESTIC": "Belföldi ÁFA alany",
    "PRIVATE_PERSON": "Nem ÁFA alany (belföldi vagy külföldi) természetes személy",
    "OTHER": "Egyéb (belföldi nem ÁFA alany, nem természetes személy, külföldi Áfa alany és külföldi nem ÁFA alany, nem természetes személy)",
}

# Source type mappings
INVOICE_SOURCE_MAPPING = {
    "PAPER": "Papír",
    "ELECTRONIC": "Elektronikus",
    "EDI": "EDI",
    "UNKNOWN": "Ismeretlen",
}

# Operation type mappings
INVOICE_OPERATION_MAPPING = {
    "CREATE": "Létrehozás",
    "MODIFY": "Módosítás",
    "STORNO": "Stornó",
}

# Logging configuration
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = "INFO"

# Software identification for NAV API
# Must be exactly 18 characters: [0-9A-Z\-]{18}
SOFTWARE_ID = "NAVPYTHONCLIENT123"  # 18 characters, uppercase letters and numbers
SOFTWARE_NAME = "NAV Python Client"
SOFTWARE_VERSION = "1.0"
SOFTWARE_DEV_NAME = "Python NAV Client"
SOFTWARE_DEV_CONTACT = "support@example.com"
SOFTWARE_DEV_COUNTRY = "HU"

"""
NAV Online Számla Python client library.

This package provides a Python client for interacting with the Hungarian NAV 
(National Tax and Customs Administration) Online Invoice API.
"""

from .client import NavOnlineInvoiceClient
# Import only essential custom classes that don't exist in generated models
from .models_legacy import (
    NavCredentials,  # Custom credentials class
)
# Import file storage for streaming operations
from .file_storage import InvoiceFileStorage
# Import Excel functionality
from .excel import (
    InvoiceExcelExporter,
    InvoiceExcelImporter,
    StreamingInvoiceExcelExporter,
    ExcelProcessingException,
)
# Import official API models (primary usage)
from .models import (
    # Response types
    BasicOnlineInvoiceResponseType,
    QueryInvoiceDigestResponseType,
    QueryInvoiceCheckResponseType,
    QueryInvoiceDataResponseType,
    QueryInvoiceChainDigestResponseType,
    # Data types
    InvoiceDigestType,
    InvoiceDataType,
    BasicResultType,
    BasicHeaderType,
)
from .exceptions import (
    NavApiException,
    NavAuthenticationException,
    NavValidationException,
    NavNetworkException,
    NavRateLimitException,
    NavXmlParsingException,
    NavConfigurationException,
    NavInvoiceNotFoundException,
    NavRequestSignatureException,
)

__version__ = "0.0.1"
__author__ = "Gergo Emmert"
__email__ = "gergo.emmert@fxltech.com"

__all__ = [
    # Main client
    "NavOnlineInvoiceClient",
    # File storage for streaming
    "InvoiceFileStorage",
    # Excel functionality
    "InvoiceExcelExporter",
    "InvoiceExcelImporter",
    "StreamingInvoiceExcelExporter",
    "ExcelProcessingException",
    # Models and data classes
    "NavCredentials",
    "InvoiceDirection",
    "InvoiceOperation",
    "CustomerVatStatus",
    "InvoiceDigest",
    "InvoiceDetail",
    "ApiResponse",
    # API-compliant request types
    "QueryInvoiceDigestRequest",
    "QueryInvoiceCheckRequest",
    "QueryInvoiceDataRequest",
    "QueryInvoiceChainDigestRequest",
    "MandatoryQueryParams",
    "AdditionalQueryParams",
    "RelationalQueryParams",
    "TransactionQueryParams",
    "InvoiceQueryParams",
    "DateRange",
    "DateTimeRange",
    "OriginalInvoiceNumber",
    "RelationalQueryParam",
    # API-compliant response types
    "BasicOnlineInvoiceResponseType",
    "QueryInvoiceDigestResponseType",
    "QueryInvoiceCheckResponseType",
    "QueryInvoiceDataResponseType",
    "QueryInvoiceChainDigestResponseType",
    "InvoiceDigestType",
    "InvoiceCheckResultType",
    "InvoiceDataType",
    "InvoiceChainDigestType",
    "BasicResultType",
    "BasicHeaderType",
    "SoftwareType",
    "NotificationType",
    # Enums
    "InvoiceCategory",
    "PaymentMethod",
    "InvoiceAppearance",
    "Source",
    "QueryOperator",
    # Exceptions
    "NavApiException",
    "NavAuthenticationException",
    "NavValidationException",
    "NavNetworkException",
    "NavRateLimitException",
    "NavXmlParsingException",
    "NavConfigurationException",
    "NavInvoiceNotFoundException",
    "NavRequestSignatureException",
]

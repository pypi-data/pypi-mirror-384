"""
Main NAV Online Számla API client.

This module provides the main client class for interacting with the NAV Online Számla API.
"""

import gzip
import logging
import time
import concurrent.futures
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Dict

import pandas as pd

from xsdata.formats.dataclass.context import XmlContext
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig
from xsdata.formats.dataclass.parsers import XmlParser

from .config import (
    ONLINE_SZAMLA_URL,
    MAX_DATE_RANGE_DAYS,
    SOFTWARE_ID,
    SOFTWARE_NAME,
    SOFTWARE_VERSION,
    SOFTWARE_DEV_NAME,
    SOFTWARE_DEV_CONTACT,
    SOFTWARE_DEV_COUNTRY,
    NavEnvironment,
    ENVIRONMENT_URLS,
    get_default_environment,
)
from .models import (
    # Official API types from generated models
    InvoiceDirectionType,
    BasicHeaderType,
    # Additional types from generated models
    InvoiceDetailType,
    DateIntervalParamType,
    MandatoryQueryParamsType,
    InvoiceQueryParamsType,
    CryptoType,
    ManageInvoiceOperationType,
    # Query parameter types
    InvoiceNumberQueryType,
    # Request wrappers (root elements)
    QueryInvoiceDigestRequest,
    QueryInvoiceCheckRequest,
    QueryInvoiceDataRequest,
    QueryInvoiceChainDigestRequest,
    QueryTransactionStatusRequest,
    # Token exchange
    TokenExchangeRequest,
    TokenExchangeResponse,
    # Response wrappers 
    QueryInvoiceDataResponse,
    QueryInvoiceDigestResponse,
    QueryInvoiceCheckResponse,
    QueryInvoiceChainDigestResponse,
    QueryTransactionStatusResponse,
    # Invoice data types
    InvoiceData,
    # Common types
    UserHeaderType,
    SoftwareType,
    SoftwareOperationType,
    # Annulment types
    ManageAnnulmentRequest,
    ManageAnnulmentResponse,
    ManageAnnulmentOperationType,
    AnnulmentOperationType,
    AnnulmentOperationListType,
    # Invoice management types
    ManageInvoiceRequest,
    ManageInvoiceResponse,
    InvoiceOperationType,
    InvoiceOperationListType,
    # Invoice annulment data types
    InvoiceAnnulment,
    InvoiceAnnulmentType,
    AnnulmentCodeType,
    # Status types
    InvoiceStatusType,
)

# Import only essential custom classes
from .models_legacy import (
    NavCredentials,
)
from .exceptions import (
    NavApiException,
    NavValidationException,
    NavXmlParsingException,
    NavInvoiceNotFoundException,
)
from .utils import (
    generate_password_hash,
    generate_custom_id,
    calculate_request_signature,
    calculate_complex_request_signature,
    calculate_electronic_invoice_hash,
    validate_tax_number,
    format_timestamp_for_nav,
    decode_exchange_token,
    encode_annulment_data_to_base64,
    serialize_annulment_data_to_xml,
    split_date_range,
    # Additional utility functions used in methods
    serialize_invoice_data_to_xml, 
    encode_invoice_data_to_base64,
)
from .http_client import NavHttpClient

# Excel functionality
from .excel import InvoiceExcelExporter, InvoiceExcelImporter, StreamingInvoiceExcelExporter

# File storage for streaming operations
from .file_storage import InvoiceFileStorage

logger = logging.getLogger(__name__)


class NavOnlineInvoiceClient:
    """
    Main client for interacting with the NAV Online Számla API.

    This client provides methods for querying invoice data, getting invoice details,
    and managing invoice operations through the NAV API.
    
    Supports both test and production environments for development and deployment.
    """

    def __init__(
        self, 
        credentials: NavCredentials, 
        environment: Optional[NavEnvironment] = None,
        timeout: int = 30,
        validate_api: bool = True
    ):
        """
        Initialize the NAV API client.

        Args:
            credentials: NAV API credentials
            environment: Environment to use (TEST or PRODUCTION). If None, uses environment 
                        variable NAV_ENVIRONMENT or defaults to PRODUCTION
            timeout: Request timeout in seconds
            validate_api: Whether to validate credentials against NAV API. Set to False for unit tests.
            
        Examples:
            # Use production environment (default)
            client = NavOnlineInvoiceClient(credentials)
            
            # Use test environment
            client = NavOnlineInvoiceClient(credentials, environment=NavEnvironment.TEST)
            
            # Skip API validation for unit tests
            client = NavOnlineInvoiceClient(credentials, validate_api=False)
            
            # Use environment variable NAV_ENVIRONMENT=test
            os.environ['NAV_ENVIRONMENT'] = 'test'
            client = NavOnlineInvoiceClient(credentials)
        """
        self.validate_credentials(credentials)
        self.credentials = credentials
        
        self.environment = environment or get_default_environment()
        self.base_url = ENVIRONMENT_URLS[self.environment]
        self.timeout = timeout
        self.http_client = NavHttpClient(self.base_url, timeout)
        
        # Initialize xsdata XML context, serializer, and parser
        self.xml_context = XmlContext()
        self.xml_serializer = XmlSerializer(context=self.xml_context)
        self.xml_parser = XmlParser(context=self.xml_context)
        
        # Validate credentials by testing API connectivity (unless disabled for tests)
        if validate_api:
            try:
                self.get_token()
                logger.info(f"Credentials validated successfully for user {credentials.login} in {self.environment.value} environment")
            except NavApiException as e:
                raise NavValidationException(f"Credential validation failed: {str(e)}")
            except Exception as e:
                raise NavValidationException(f"Unable to validate credentials due to network/API error: {str(e)}")
        else:
            logger.debug(f"API validation skipped for user {credentials.login} in {self.environment.value} environment")
        
        # Log environment information for debugging
        logger.info(f"Initialized NAV client for {self.environment.value} environment: {self.base_url}")

    def validate_credentials(self, credentials: NavCredentials) -> None:
        """
        Validate NAV API credentials format.

        Args:
            credentials: NAV API credentials

        Raises:
            NavValidationException: If credentials format is invalid
        """
        if not all([credentials.login, credentials.password, credentials.signer_key]):
            raise NavValidationException(
                "Missing required credentials: login, password, or signer_key"
            )

        if not validate_tax_number(credentials.tax_number):
            raise NavValidationException(
                f"Invalid tax number format: {credentials.tax_number}"
            )

    def _create_basic_header(self) -> BasicHeaderType:
        """Create basic header for requests."""
        return BasicHeaderType(
            request_id=generate_custom_id(),
            timestamp=format_timestamp_for_nav(datetime.now()),
            request_version="3.0",
            header_version="1.0"
        )

    def _create_basic_header_with_timestamp(self, timestamp: str) -> BasicHeaderType:
        """Create basic header for requests with a specific timestamp."""
        return BasicHeaderType(
            request_id=generate_custom_id(),
            timestamp=timestamp,
            request_version="3.0",
            header_version="1.0"
        )

    def _create_user_header(self, credentials: NavCredentials, header: BasicHeaderType) -> UserHeaderType:
        """Create user header with authentication data using the provided header."""
        password_hash = generate_password_hash(credentials.password)
        request_signature = calculate_request_signature(
            header.request_id, 
            header.timestamp, 
            credentials.signer_key
        )
        
        return UserHeaderType(
            login=credentials.login,
            password_hash=CryptoType(
                value=password_hash,
                crypto_type="SHA-512"
            ),
            tax_number=credentials.tax_number,
            request_signature=CryptoType(
                value=request_signature,
                crypto_type="SHA3-512"
            )
        )

    def _create_user_header_with_complex_signature(
        self, 
        credentials: NavCredentials, 
        header: BasicHeaderType,
        operation_data: List[Tuple[str, str]]
    ) -> UserHeaderType:
        """Create user header with complex signature for manageInvoice/manageAnnulment operations."""
        password_hash = generate_password_hash(credentials.password)
        request_signature = calculate_complex_request_signature(
            header.request_id, 
            header.timestamp, 
            credentials.signer_key,
            operation_data
        )
        
        return UserHeaderType(
            login=credentials.login,
            password_hash=CryptoType(
                value=password_hash,
                crypto_type="SHA-512"
            ),
            tax_number=credentials.tax_number,
            request_signature=CryptoType(
                value=request_signature,
                crypto_type="SHA3-512"
            )
        )

    def _create_software_info(self, credentials: NavCredentials) -> SoftwareType:
        """Create software information."""
        return SoftwareType(
            software_id=SOFTWARE_ID,
            software_name=SOFTWARE_NAME,
            software_operation=SoftwareOperationType.LOCAL_SOFTWARE,
            software_main_version=SOFTWARE_VERSION,
            software_dev_name=SOFTWARE_DEV_NAME,
            software_dev_contact=SOFTWARE_DEV_CONTACT,
            software_dev_country_code=SOFTWARE_DEV_COUNTRY,
            software_dev_tax_number=credentials.tax_number
        )

    def _serialize_request_to_xml(self, request_obj) -> str:
        """Serialize a request object to XML using xsdata with proper namespace formatting."""
        config = SerializerConfig(
            indent="  ",  # Use indent instead of pretty_print
            xml_declaration=True,
            encoding="UTF-8"
        )
        
        serializer = XmlSerializer(context=self.xml_context, config=config)
        xml_output = serializer.render(request_obj)
        
        # Format with custom namespace prefixes to match NAV expected format
        return self._format_xml_with_custom_namespaces(xml_output)
    
    def _parse_response_from_xml(self, xml_response: str, response_class):
        """
        Generic function for parsing XML responses using xsdata.
        
        This function provides automatic parsing of NAV API responses to typed dataclasses:
        1. Takes raw XML response string
        2. Uses xsdata parser with the provided response class
        3. Returns fully typed response object
        4. Handles parsing errors appropriately
        
        Args:
            xml_response: Raw XML response string from NAV API
            response_class: The dataclass type to parse into (e.g., QueryInvoiceDataResponse)
            
        Returns:
            Parsed response object of the specified type
            
        Raises:
            NavXmlParsingException: If XML parsing fails
            NavApiException: If response contains API errors
        """
        try:
            # Parse XML to response object using xsdata
            response_obj = self.xml_parser.from_string(xml_response, response_class)
            
            # Check for API errors in the response
            if hasattr(response_obj, 'result') and response_obj.result:
                func_code = response_obj.result.func_code
                # Handle both enum and string values
                func_code_value = func_code.value if hasattr(func_code, 'value') else str(func_code)
                
                if func_code_value != 'OK':
                    error_code = getattr(response_obj.result, 'error_code', 'UNKNOWN_ERROR')
                    message = getattr(response_obj.result, 'message', 'No error message provided')
                    raise NavApiException(f"API Error: {error_code} - {message}")
            
            return response_obj
            
        except Exception as e:
            if isinstance(e, NavApiException):
                raise
            logger.error(f"Failed to parse XML response: {e}")
            raise NavXmlParsingException(f"Failed to parse response XML: {e}")
    
    def _format_xml_with_custom_namespaces(self, xml_string: str) -> str:
        """
        Convert xsdata generated XML to match NAV expected format:
        - ns0 -> default namespace
        - ns1 -> common prefix
        """
        # Replace namespace declarations and prefixes
        xml_string = xml_string.replace(
            'xmlns:ns0="http://schemas.nav.gov.hu/OSA/3.0/api"',
            'xmlns="http://schemas.nav.gov.hu/OSA/3.0/api" xmlns:common="http://schemas.nav.gov.hu/NTCA/1.0/common"'
        )
        
        # Remove redundant namespace declarations
        xml_string = xml_string.replace(
            ' xmlns:ns1="http://schemas.nav.gov.hu/NTCA/1.0/common"',
            ''
        )
        
        # Replace element prefixes
        xml_string = xml_string.replace('ns0:', '')  # Remove ns0 prefix (default namespace)
        xml_string = xml_string.replace('ns1:', 'common:')  # Replace ns1 with common
        
        return xml_string

    def _format_annulment_xml_with_custom_namespaces(self, xml_string: str) -> str:
        """
        Convert xsdata generated annulment XML to match NAV expected format.
        Converts from:
        <ns0:InvoiceAnnulment xmlns:ns0="http://schemas.nav.gov.hu/OSA/3.0/annul">
        
        To:
        <InvoiceAnnulment xmlns="http://schemas.nav.gov.hu/OSA/3.0/annul">
        """
        # Replace namespace declarations - convert ns0 to default namespace
        xml_string = xml_string.replace(
            'xmlns:ns0="http://schemas.nav.gov.hu/OSA/3.0/annul"',
            'xmlns="http://schemas.nav.gov.hu/OSA/3.0/annul"'
        )
        
        # Add standalone="yes" attribute to XML declaration if not present
        if 'standalone=' not in xml_string:
            xml_string = xml_string.replace(
                '<?xml version="1.0" encoding="UTF-8"?>',
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            )
        
        # Remove ns0 prefix from all elements (make them use default namespace)
        xml_string = xml_string.replace('ns0:', '')
        
        return xml_string

    def create_query_invoice_digest_request(
        self, 
        credentials: NavCredentials, 
        page: int,
        invoice_direction: InvoiceDirectionType,
        invoice_query_params: InvoiceQueryParamsType
    ) -> QueryInvoiceDigestRequest:
        """Create a QueryInvoiceDigestRequest using generated models."""
        
        header = self._create_basic_header()
        user = self._create_user_header(credentials, header)
        software = self._create_software_info(credentials)
        
        return QueryInvoiceDigestRequest(
            header=header,
            user=user,
            software=software,
            page=page,
            invoice_direction=invoice_direction,
            invoice_query_params=invoice_query_params
        )

    def create_token_exchange_request(self) -> TokenExchangeRequest:
        """Create a TokenExchangeRequest using generated models."""
        
        header = self._create_basic_header()
        user = self._create_user_header(self.credentials, header)
        software = self._create_software_info(self.credentials)
        
        return TokenExchangeRequest(
            header=header,
            user=user,
            software=software
        )

    def create_query_invoice_data_request(
        self,
        credentials: NavCredentials,
        invoice_number: str,
        invoice_direction: InvoiceDirectionType,
        batch_index: Optional[int] = None,
        supplier_tax_number: Optional[str] = None
    ) -> QueryInvoiceDataRequest:
        """Create a QueryInvoiceDataRequest using generated models."""
        
        header = self._create_basic_header()
        user = self._create_user_header(credentials, header)
        software = self._create_software_info(credentials)
        
        invoice_number_query = InvoiceNumberQueryType(
            invoice_number=invoice_number,
            invoice_direction=invoice_direction,
            batch_index=batch_index,
            supplier_tax_number=supplier_tax_number
        )
        
        return QueryInvoiceDataRequest(
            header=header,
            user=user,
            software=software,
            invoice_number_query=invoice_number_query
        )

    def create_query_invoice_check_request(
        self,
        invoice_number: str,
        invoice_direction: InvoiceDirectionType,
        batch_index: Optional[int] = None,
        supplier_tax_number: Optional[str] = None
    ) -> QueryInvoiceCheckRequest:
        """Create a QueryInvoiceCheckRequest using generated models."""
        
        header = self._create_basic_header()
        user = self._create_user_header(self.credentials, header)
        software = self._create_software_info(self.credentials)
        
        invoice_number_query = InvoiceNumberQueryType(
            invoice_number=invoice_number,
            invoice_direction=invoice_direction,
            batch_index=batch_index,
            supplier_tax_number=supplier_tax_number
        )
        
        return QueryInvoiceCheckRequest(
            header=header,
            user=user,
            software=software,
            invoice_number_query=invoice_number_query
        )

    def create_query_invoice_chain_digest_request(
        self,
        page: int,
        invoice_number: str,
        invoice_direction: InvoiceDirectionType,
        tax_number: Optional[str] = None
    ) -> QueryInvoiceChainDigestRequest:
        """Create a QueryInvoiceChainDigestRequest using generated models."""
        
        header = self._create_basic_header()
        user = self._create_user_header(self.credentials, header)
        software = self._create_software_info(self.credentials)
        
        return QueryInvoiceChainDigestRequest(
            header=header,
            user=user,
            software=software,
            page=page,
            invoice_number=invoice_number,
            invoice_direction=invoice_direction,
            tax_number=tax_number
        )

    def create_query_transaction_status_request(
        self,
        transaction_id: str,
        return_original_request: Optional[bool] = None
    ) -> QueryTransactionStatusRequest:
        """Create a QueryTransactionStatusRequest using generated models."""
        
        header = self._create_basic_header()
        user = self._create_user_header(self.credentials, header)
        software = self._create_software_info(self.credentials)
        
        return QueryTransactionStatusRequest(
            header=header,
            user=user,
            software=software,
            transaction_id=transaction_id,
            return_original_request=return_original_request
        )

    def query_invoice_digest(
        self,
        page: int,
        invoice_direction: InvoiceDirectionType,
        invoice_query_params: InvoiceQueryParamsType
    ) -> QueryInvoiceDigestResponse:
        """
        Query invoice digest using xsdata-generated dataclasses.
        This uses automatic XML serialization and parsing for type-safe API interactions.
        
        Args:
            page: Page number for pagination (1-based)
            invoice_direction: Invoice direction (OUTBOUND/INBOUND)
            invoice_query_params: Query parameters (date range, supplier info, etc.)
            
        Returns:
            QueryInvoiceDigestResponse: Fully parsed response with typed invoice digests
            
        Raises:
            NavValidationException: If parameters are invalid
            NavApiException: If API request fails
            NavXmlParsingException: If XML parsing fails
        """
        if page < 1:
            raise NavValidationException("Page number must be >= 1")

        if not invoice_query_params:
            raise NavValidationException("Invoice query parameters are required")

        try:
            # Create request using xsdata dataclasses
            request = self.create_query_invoice_digest_request(
                credentials=self.credentials,
                page=page,
                invoice_direction=invoice_direction,
                invoice_query_params=invoice_query_params
            )
            
            # Serialize request to XML
            xml_request = self._serialize_request_to_xml(request)
            
            # Make API call
            with self.http_client as client:
                response = client.post("queryInvoiceDigest", xml_request)
                xml_response = response.text
            
            # Parse response using generic parsing function
            parsed_response = self._parse_response_from_xml(xml_response, QueryInvoiceDigestResponse)
            
            logger.info(f"Successfully queried invoice digest for page {page}")
            return parsed_response

        except Exception as e:
            if isinstance(e, (NavValidationException, NavApiException, NavXmlParsingException)):
                raise
            logger.error(f"Unexpected error querying invoice digest: {e}")
            raise NavApiException(f"Failed to query invoice digest: {e}")
      
    def query_invoice_data(
        self,
        invoice_number: str,
        invoice_direction: InvoiceDirectionType,
        batch_index: Optional[int] = None,
        supplier_tax_number: Optional[str] = None
    ) -> QueryInvoiceDataResponse:
        """
        Query invoice data using xsdata-generated dataclasses.
        This uses automatic XML serialization and parsing for type-safe API interactions.
        
        Args:
            invoice_number: Invoice number to query
            invoice_direction: Invoice direction (OUTBOUND/INBOUND)
            batch_index: Optional batch index for batched invoices
            supplier_tax_number: Optional supplier tax number
            
        Returns:
            QueryInvoiceDataResponse: Fully parsed response with typed invoice data
            
        Raises:
            NavValidationException: If parameters are invalid
            NavInvoiceNotFoundException: If invoice not found
            NavApiException: If API request fails
            NavXmlParsingException: If XML parsing fails
        """
        if not invoice_number:
            raise NavValidationException("Invoice number is required")

        try:
            # Create request using xsdata dataclasses
            request = self.create_query_invoice_data_request(
                credentials=self.credentials,
                invoice_number=invoice_number,
                invoice_direction=invoice_direction,
                batch_index=batch_index,
                supplier_tax_number=supplier_tax_number
            )
            
            # Serialize request to XML
            xml_request = self._serialize_request_to_xml(request)
            
            # Make API call
            with self.http_client as client:
                response = client.post("queryInvoiceData", xml_request)
                xml_response = response.text
            
            # Parse response using generic parsing function
            parsed_response = self._parse_response_from_xml(xml_response, QueryInvoiceDataResponse)
            
            # Check if invoice was found
            if not parsed_response.invoice_data_result or not parsed_response.invoice_data_result.invoice_data:
                raise NavInvoiceNotFoundException(f"Invoice {invoice_number} not found")

            # Parse the Base64 encoded invoice data
            if parsed_response.invoice_data_result.invoice_data:
                try:
                    # The invoice_data field is already decoded from Base64 by xsdata, 
                    # but it's in bytes format containing XML (possibly compressed)
                    xml_bytes = parsed_response.invoice_data_result.invoice_data
                    
                    # Check if it's already a parsed object
                    if isinstance(xml_bytes, InvoiceData):
                        logger.info(f"Invoice data is already parsed as InvoiceData object")
                        return parsed_response
                    
                    # If it's bytes, check if it's compressed or not
                    if isinstance(xml_bytes, bytes):
                        # Check for gzip compression based on response indicator or magic bytes
                        is_compressed = False
                        if (hasattr(parsed_response.invoice_data_result, 'compressed_content_indicator') and 
                            parsed_response.invoice_data_result.compressed_content_indicator):
                            is_compressed = True
                            logger.debug("Data marked as compressed in response")
                        elif xml_bytes.startswith(b'\x1f\x8b'):  # GZIP magic bytes
                            is_compressed = True
                            logger.debug("Data appears to be gzipped (magic bytes detected)")
                        
                        # Decompress if needed
                        if is_compressed:
                            try:
                                xml_bytes = gzip.decompress(xml_bytes)
                                logger.debug(f"Successfully decompressed data, new length: {len(xml_bytes)}")
                            except Exception as decomp_error:
                                logger.error(f"Failed to decompress data: {decomp_error}")
                                raise NavXmlParsingException(f"Failed to decompress invoice data: {decomp_error}")
                        
                        # Try UTF-8 first, then fall back to other encodings
                        try:
                            xml_content = xml_bytes.decode('utf-8')
                        except UnicodeDecodeError:
                            try:
                                # Try latin-1 which can handle any byte sequence
                                xml_content = xml_bytes.decode('latin-1')
                            except UnicodeDecodeError:
                                # Last resort - decode with error replacement
                                xml_content = xml_bytes.decode('utf-8', errors='replace')
                        
                        # Parse the decoded XML into InvoiceData object
                        parsed_invoice_data = self._parse_response_from_xml(xml_content, InvoiceData)
                        # Replace the bytes with the parsed object
                        parsed_response.invoice_data_result.invoice_data = parsed_invoice_data
                    else:
                        # If it's not bytes, log what it is and keep it
                        logger.warning(f"Invoice data is not bytes, it's {type(xml_bytes)}. Keeping as-is.")
                    
                except Exception as e:
                    logger.warning(f"Failed to parse invoice data XML: {e}")
                    # Keep the original bytes data if parsing fails
            
            return parsed_response

        except Exception as e:
            if isinstance(e, (NavValidationException, NavInvoiceNotFoundException, NavApiException, NavXmlParsingException)):
                raise
            logger.error(f"Unexpected error querying invoice data: {e}")
            raise NavApiException(f"Failed to query invoice data: {e}")

    def query_invoice_check(
        self, request: QueryInvoiceCheckRequest
    ) -> QueryInvoiceCheckResponse:
        """
        Check if an invoice exists using xsdata-generated dataclasses.
        This uses automatic XML serialization and parsing for type-safe API interactions.

        Args:
            request: QueryInvoiceCheckRequest with proper API structure

        Returns:
            QueryInvoiceCheckResponse: Fully parsed response with typed check results

        Raises:
            NavValidationException: If request validation fails
            NavApiException: If API call fails
            NavXmlParsingException: If XML parsing fails
        """
        try:
            # Serialize request to XML
            xml_request = self._serialize_request_to_xml(request)
            
            # Make API call
            with self.http_client as client:
                response = client.post("queryInvoiceCheck", xml_request)
                xml_response = response.text

            # Parse response using generic parsing function
            parsed_response = self._parse_response_from_xml(xml_response, QueryInvoiceCheckResponse)
            
            logger.info(f"Successfully checked invoice: {request.invoice_number_query.invoice_number}")
            return parsed_response

        except Exception as e:
            if isinstance(e, (NavApiException, NavValidationException, NavXmlParsingException)):
                raise
            logger.error(f"Unexpected error in query_invoice_check: {e}")
            raise NavApiException(f"Failed to check invoice: {str(e)}")

    def query_invoice_chain_digest(
        self, request: QueryInvoiceChainDigestRequest
    ) -> QueryInvoiceChainDigestResponse:
        """
        Query invoice chain digests using xsdata-generated dataclasses.
        This uses automatic XML serialization and parsing for type-safe API interactions.

        Args:
            request: QueryInvoiceChainDigestRequest with proper API structure

        Returns:
            QueryInvoiceChainDigestResponse: Fully parsed response with typed chain digest data

        Raises:
            NavValidationException: If request validation fails
            NavApiException: If API call fails
            NavXmlParsingException: If XML parsing fails
        """
        try:
            # Serialize request to XML
            xml_request = self._serialize_request_to_xml(request)
            
            # Make API call
            with self.http_client as client:
                response = client.post("queryInvoiceChainDigest", xml_request)
                xml_response = response.text

            # Parse response using generic parsing function
            parsed_response = self._parse_response_from_xml(xml_response, QueryInvoiceChainDigestResponse)
            
            logger.info(f"Successfully queried invoice chain digest for: {request.invoice_number}")
            return parsed_response

        except Exception as e:
            if isinstance(e, (NavApiException, NavValidationException, NavXmlParsingException)):
                raise
            logger.error(f"Unexpected error in query_invoice_chain_digest: {e}")
            raise NavApiException(f"Failed to query invoice chain digest: {str(e)}")

    def query_transaction_status(
        self,
        transaction_id: str,
        return_original_request: Optional[bool] = None
    ) -> QueryTransactionStatusResponse:
        """
        Query transaction status using xsdata-generated dataclasses.
        This uses automatic XML serialization and parsing for type-safe API interactions.

        Args:
            transaction_id: The transaction ID to query status for
            return_original_request: Whether to return the original request data

        Returns:
            QueryTransactionStatusResponse: Fully parsed response with processing results

        Raises:
            NavValidationException: If parameters are invalid
            NavApiException: If API call fails
            NavXmlParsingException: If XML parsing fails
        """
        if not transaction_id or not transaction_id.strip():
            raise NavValidationException("Transaction ID is required and cannot be empty")

        if len(transaction_id) > 30:
            raise NavValidationException("Transaction ID cannot be longer than 30 characters")

        try:
            # Create request using helper method
            request = self.create_query_transaction_status_request(
                transaction_id=transaction_id,
                return_original_request=return_original_request
            )
            
            # Serialize request to XML
            xml_request = self._serialize_request_to_xml(request)
            
            # Make API call
            with self.http_client as client:
                response = client.post("queryTransactionStatus", xml_request)
                xml_response = response.text

            # Parse response using generic parsing function
            parsed_response = self._parse_response_from_xml(xml_response, QueryTransactionStatusResponse)
            
            logger.info(f"Successfully queried transaction status for: {transaction_id}")
            return parsed_response

        except Exception as e:
            if isinstance(e, (NavApiException, NavValidationException, NavXmlParsingException)):
                raise
            logger.error(f"Unexpected error in query_transaction_status: {e}")
            raise NavApiException(f"Failed to query transaction status: {str(e)}")

    def get_token(self) -> TokenExchangeResponse:
        """
        Get exchange token from NAV API using xsdata-generated dataclasses.
        This uses automatic XML serialization and parsing for type-safe API interactions.

        Returns:
            TokenExchangeResponse: Complete response with token and validity information

        Raises:
            NavValidationException: If credentials are invalid
            NavApiException: If API call fails
            NavXmlParsingException: If XML parsing fails
        """
        try:
            # Create request using helper method
            request = self.create_token_exchange_request()
            
            # Serialize request to XML
            xml_request = self._serialize_request_to_xml(request)
            
            # Make API call
            with self.http_client as client:
                response = client.post("tokenExchange", xml_request)
                xml_response = response.text

            # Parse response using generic parsing function
            parsed_response = self._parse_response_from_xml(xml_response, TokenExchangeResponse)
            
            logger.info("Successfully obtained exchange token")
            return parsed_response

        except Exception as e:
            if isinstance(e, (NavApiException, NavValidationException, NavXmlParsingException)):
                raise
            logger.error(f"Unexpected error in get_token: {e}")
            raise NavApiException(f"Failed to get token: {str(e)}")

    def get_invoice_chain_digest(
        self,
        page: int,
        invoice_number: str,
        invoice_direction: InvoiceDirectionType = InvoiceDirectionType.OUTBOUND,
        tax_number: Optional[str] = None
    ) -> QueryInvoiceChainDigestResponse:
        """
        Convenience method to get invoice chain digest with automatic request creation.
        
        Args:
            page: Page number for pagination
            invoice_number: Invoice number to query
            invoice_direction: Direction of the invoice (default: OUTBOUND)
            tax_number: Optional tax number filter
        
        Returns:
            QueryInvoiceChainDigestResponse: Complete response with chain digest data
        """
        request = self.create_query_invoice_chain_digest_request(
            page=page,
            invoice_number=invoice_number,
            invoice_direction=invoice_direction,
            tax_number=tax_number
        )
        return self.query_invoice_chain_digest(request)

    def get_invoice_data(
        self,
        invoice_number: str,
        invoice_direction: InvoiceDirectionType = InvoiceDirectionType.OUTBOUND,
        batch_index: Optional[int] = None,
        supplier_tax_number: Optional[str] = None
    ) -> InvoiceData:
        """
        Get invoice data and return a fully parsed InvoiceData dataclass.
        
        This function provides a high-level interface that:
        1. Uses query_invoice_data to get the API response
        2. Extracts and decodes the base64 invoice data
        3. Returns a typed InvoiceData dataclass
        
        Args:
            invoice_number: Invoice number to query
            invoice_direction: Invoice direction (default: OUTBOUND)
            batch_index: Optional batch index for batched invoices
            supplier_tax_number: Optional supplier tax number
            
        Returns:
            InvoiceData: Fully parsed invoice data as a dataclass
            
        Raises:
            NavValidationException: If parameters are invalid
            NavInvoiceNotFoundException: If invoice not found
            NavApiException: If API request fails
            NavXmlParsingException: If XML parsing fails
        """
        try:
            # Use query_invoice_data to get the full API response
            response = self.query_invoice_data(
                invoice_number=invoice_number,
                invoice_direction=invoice_direction,
                batch_index=batch_index,
                supplier_tax_number=supplier_tax_number
            )
            
            # Extract the already-parsed invoice data from the response
            if not response.invoice_data_result or not response.invoice_data_result.invoice_data:
                raise NavInvoiceNotFoundException(f"No invoice data found for invoice {invoice_number}")
            
            # query_invoice_data already parsed the XML into an InvoiceData object
            invoice_data = response.invoice_data_result.invoice_data
            
            # Ensure it's an InvoiceData object (should be after query_invoice_data processing)
            if not isinstance(invoice_data, InvoiceData):
                raise NavXmlParsingException(f"Expected InvoiceData object, got {type(invoice_data)}")
            
            return invoice_data

        except Exception as e:
            if isinstance(e, (NavApiException, NavValidationException, NavInvoiceNotFoundException, NavXmlParsingException)):
                raise
            logger.error(f"Unexpected error in get_invoice_data: {e}")
            raise NavApiException(f"Failed to get invoice data: {str(e)}")

    def get_exchange_token(self) -> str:
        """
        Convenience method to get and decode the exchange token string.
        
        Returns:
            str: The decoded exchange token
        """
        response = self.get_token()
        return decode_exchange_token(response.encoded_exchange_token, self.credentials.exchange_key)

    def check_invoice_exists(
        self,
        invoice_number: str,
        invoice_direction: InvoiceDirectionType = InvoiceDirectionType.OUTBOUND,
        batch_index: Optional[int] = None,
        supplier_tax_number: Optional[str] = None
    ) -> bool:
        """
        Check if an invoice exists with a simplified interface.
        
        This function provides a high-level interface that:
        1. Creates the request using the provided parameters
        2. Calls query_invoice_check to get the API response
        3. Returns a simple boolean result
        
        Args:
            invoice_number: Invoice number to check
            invoice_direction: Invoice direction (default: OUTBOUND)
            batch_index: Optional batch index for batched invoices
            supplier_tax_number: Optional supplier tax number
            
        Returns:
            bool: True if invoice exists, False otherwise
            
        Raises:
            NavValidationException: If parameters are invalid
            NavApiException: If API request fails
            NavXmlParsingException: If XML parsing fails
        """
        try:
            # Create request using xsdata dataclasses
            request = self.create_query_invoice_check_request(
                invoice_number=invoice_number,
                invoice_direction=invoice_direction,
                batch_index=batch_index,
                supplier_tax_number=supplier_tax_number
            )
            
            # Get full response
            response = self.query_invoice_check(request)
            
            # Extract boolean result
            return response.invoice_check_result or False

        except Exception as e:
            if isinstance(e, (NavApiException, NavValidationException, NavXmlParsingException)):
                raise
            logger.error(f"Unexpected error in check_invoice_exists: {e}")
            raise NavApiException(f"Failed to check if invoice exists: {str(e)}")

    def _process_single_invoice_digest(
        self,
        digest,
        invoice_direction: InvoiceDirectionType
    ) -> Optional[Tuple[InvoiceData, ManageInvoiceOperationType]]:
        """
        Process a single invoice digest to get detailed data.
        
        This method can be used by both threaded and non-threaded implementations.
        
        Args:
            digest: Invoice digest from queryInvoiceDigest response
            invoice_direction: Direction of the invoice (OUTBOUND/INBOUND)
            
        Returns:
            Tuple of (InvoiceData, ManageInvoiceOperationType) if successful, None otherwise
        """
        try:
            logger.debug(f"Fetching details for invoice: {digest.invoice_number}")

            # For OUTBOUND invoices, don't include supplier_tax_number as it causes API error
            # For INBOUND invoices, include supplier_tax_number if available
            supplier_tax_for_request = None
            if invoice_direction == InvoiceDirectionType.INBOUND:
                supplier_tax_for_request = digest.supplier_tax_number

            # Get detailed invoice data using the get_invoice_data method
            invoice_data = self.get_invoice_data(
                invoice_number=digest.invoice_number,
                invoice_direction=invoice_direction,
                batch_index=digest.batch_index,
                supplier_tax_number=supplier_tax_for_request
            )

            if invoice_data:
                return (invoice_data, digest.invoice_operation)
            else:
                logger.warning(f"No detail data found for invoice: {digest.invoice_number}")
                return None

        except NavInvoiceNotFoundException:
            logger.warning(f"Invoice details not found for: {digest.invoice_number}")
            return None
        except Exception as e:
            logger.error(f"Error processing invoice {digest.invoice_number}: {str(e)}")
            return None

    def _process_invoice_digests(
        self,
        invoice_digests: list,
        invoice_direction: InvoiceDirectionType,
        use_threading: bool = False,
        max_workers: int = 4
    ) -> List[Tuple[InvoiceData, ManageInvoiceOperationType]]:
        """
        Process a list of invoice digests to get detailed data.
        
        Args:
            invoice_digests: List of invoice digests from queryInvoiceDigest response
            invoice_direction: Direction of the invoices (OUTBOUND/INBOUND)
            use_threading: Whether to use threading for parallel processing
            max_workers: Maximum number of threads (only used if use_threading=True)
            
        Returns:
            List of tuples containing (InvoiceData, ManageInvoiceOperationType)
        """
        if not invoice_digests:
            return []
            
        logger.info(f"Processing {len(invoice_digests)} invoice digests (threading: {use_threading})")
        
        all_invoice_data = []
        processed_count = 0
        failed_count = 0
        
        if use_threading:
            # Use threading for parallel processing
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_digest = {
                    executor.submit(self._process_single_invoice_digest, digest, invoice_direction): digest 
                    for digest in invoice_digests
                }

                # Collect results as they complete
                for future in concurrent.futures.as_completed(future_to_digest):
                    try:
                        result = future.result()
                        if result is not None:
                            all_invoice_data.append(result)
                            processed_count += 1

                            # Show progress more frequently for larger datasets
                            if processed_count % 50 == 0 or processed_count == len(invoice_digests):
                                logger.info(f"📊 Progress: {processed_count}/{len(invoice_digests)} invoices processed ({processed_count/len(invoice_digests)*100:.1f}%)")
                        else:
                            failed_count += 1

                    except Exception as e:
                        failed_count += 1
                        digest = future_to_digest[future]
                        logger.error(f"Failed to process invoice {digest.invoice_number}: {e}")
        else:
            # Sequential processing
            for i, digest in enumerate(invoice_digests, 1):
                try:
                    logger.debug(f"Processing invoice {i}/{len(invoice_digests)}: {digest.invoice_number}")
                    
                    result = self._process_single_invoice_digest(digest, invoice_direction)
                    
                    if result:
                        all_invoice_data.append(result)
                        processed_count += 1

                        # Show progress more frequently for larger datasets
                        if processed_count % 50 == 0 or processed_count == len(invoice_digests):
                            logger.info(f"📊 Progress: {processed_count}/{len(invoice_digests)} invoices processed ({processed_count/len(invoice_digests)*100:.1f}%)")
                    else:
                        failed_count += 1

                except Exception as e:
                    failed_count += 1
                    logger.error(f"Error processing invoice {digest.invoice_number}: {str(e)}")
        
        logger.info(
            f"Completed processing {len(invoice_digests)} invoice digests. "
            f"Successfully processed: {processed_count}, Failed: {failed_count}"
        )
        
        return all_invoice_data

    def _process_invoice_digests_to_storage(
        self,
        invoice_digests: list,
        invoice_direction: InvoiceDirectionType,
        file_storage: InvoiceFileStorage,
        use_threading: bool = False,
        max_workers: int = 4
    ) -> Tuple[int, int]:
        """
        Process invoice digests and save directly to file storage (memory-efficient).
        
        This method fetches invoice details and immediately saves them to disk
        without keeping them in memory, making it suitable for large datasets.
        
        Args:
            invoice_digests: List of invoice digests from queryInvoiceDigest response
            invoice_direction: Direction of the invoices (OUTBOUND/INBOUND)
            file_storage: InvoiceFileStorage instance to save invoices to
            use_threading: Whether to use threading for parallel processing
            max_workers: Maximum number of threads (only used if use_threading=True)
            
        Returns:
            Tuple[int, int]: (successfully_processed, failed_count)
        """
        if not invoice_digests:
            return 0, 0
            
        logger.info(
            f"Processing {len(invoice_digests)} invoice digests to file storage "
            f"(threading: {use_threading})"
        )
        
        processed_count = 0
        failed_count = 0
        
        # Thread-safe counters
        from threading import Lock
        counter_lock = Lock()
        
        def process_and_save(digest):
            """Process a single digest and save to storage."""
            nonlocal processed_count, failed_count
            
            try:
                result = self._process_single_invoice_digest(digest, invoice_direction)
                
                if result:
                    invoice_data, operation_type = result
                    file_storage.save_invoice(invoice_data, operation_type)
                    
                    with counter_lock:
                        processed_count += 1
                        
                        # Show progress
                        if processed_count % 100 == 0:
                            logger.info(
                                f"📊 Progress: {processed_count}/{len(invoice_digests)} "
                                f"invoices saved to storage ({processed_count/len(invoice_digests)*100:.1f}%)"
                            )
                    return True
                else:
                    with counter_lock:
                        failed_count += 1
                    return False
                    
            except Exception as e:
                logger.error(f"Failed to process and save invoice {digest.invoice_number}: {e}")
                with counter_lock:
                    failed_count += 1
                return False
        
        if use_threading:
            # Use threading for parallel processing
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                futures = [executor.submit(process_and_save, digest) for digest in invoice_digests]
                
                # Wait for completion
                concurrent.futures.wait(futures)
        else:
            # Sequential processing
            for i, digest in enumerate(invoice_digests, 1):
                process_and_save(digest)
        
        logger.info(
            f"✅ Completed processing to storage: {processed_count} saved, {failed_count} failed"
        )
        
        return processed_count, failed_count

    def get_all_invoice_data_for_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        invoice_direction: InvoiceDirectionType = InvoiceDirectionType.OUTBOUND,
        use_threading: bool = False,
        max_workers: int = 4
    ) -> List[tuple[InvoiceData, ManageInvoiceOperationType]]:
        """
        Get all invoice data for a given date range with configurable threading.

        Args:
            start_date: Start date for the query range
            end_date: End date for the query range
            invoice_direction: Invoice direction to query (default: OUTBOUND)
            use_threading: Whether to use threading for improved performance (default: False)
            max_workers: Maximum number of threads for parallel processing (default: 4, used only if use_threading=True)

        Returns:
            List[tuple[InvoiceData, ManageInvoiceOperationType]]: List of tuples containing 
            complete invoice data objects and their operation types

        Raises:
            NavValidationException: If parameters are invalid
            NavApiException: If API requests fail
        """
        if start_date > end_date:
            raise NavValidationException("Start date must be before end date")

        # Check if date range needs to be split
        date_diff = (end_date - start_date).days
        if date_diff > MAX_DATE_RANGE_DAYS:
            logger.info(
                f"Date range ({date_diff} days) exceeds maximum ({MAX_DATE_RANGE_DAYS} days). "
                "Splitting into smaller ranges."
            )
            
            # Split date range into chunks
            date_ranges = split_date_range(
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
                MAX_DATE_RANGE_DAYS
            )
            
            logger.info(f"Split into {len(date_ranges)} date ranges")
            
            # Phase 1: Collect ALL invoice digests from ALL date ranges
            all_invoice_digests = []
            for i, (range_start_str, range_end_str) in enumerate(date_ranges):
                logger.info(
                    f"Collecting digests from range {i+1}/{len(date_ranges)}: "
                    f"{range_start_str} to {range_end_str}"
                )
                
                # Collect digests for this date range
                range_digests = self._collect_invoice_digests_for_range(
                    range_start_str, range_end_str, invoice_direction
                )
                all_invoice_digests.extend(range_digests)
                logger.info(f"Found {len(range_digests)} invoices in range {i+1}")
            
            if not all_invoice_digests:
                logger.info("No invoices found in any of the date ranges")
                return []
                
            logger.info(f"🎯 Collected total of {len(all_invoice_digests)} invoice digests from all ranges")
            
            # Phase 2: Process all collected invoice digests to get complete invoice data
            all_invoice_data = self._process_invoice_digests(
                invoice_digests=all_invoice_digests,
                invoice_direction=invoice_direction,
                use_threading=use_threading,
                max_workers=max_workers
            )

            logger.info(
                f"Completed processing all {len(date_ranges)} date ranges. "
                f"Total invoices processed: {len(all_invoice_data)}"
            )
            return all_invoice_data

        # For single date range (≤ 35 days), use the original logic
        return self._get_invoice_data_for_single_range(
            start_date, end_date, invoice_direction, use_threading, max_workers
        )

    def _collect_invoice_digests_for_range(
        self, 
        start_date_str: str, 
        end_date_str: str, 
        invoice_direction: InvoiceDirectionType
    ) -> list:
        """Collect all invoice digests for a specific date range."""
        invoice_digests = []
        page = 1

        while True:
            # Create invoice query params
            invoice_query_params = InvoiceQueryParamsType(
                mandatory_query_params=MandatoryQueryParamsType(
                    invoice_issue_date=DateIntervalParamType(
                        date_from=start_date_str,
                        date_to=end_date_str,
                    )
                )
            )

            # Query invoice digests
            digest_response = self.query_invoice_digest(
                page=page,
                invoice_direction=invoice_direction,
                invoice_query_params=invoice_query_params
            )

            if not digest_response.invoice_digest_result or not digest_response.invoice_digest_result.invoice_digest:
                break

            page_digests = digest_response.invoice_digest_result.invoice_digest
            invoice_digests.extend(page_digests)

            # Check if there are more pages
            if (
                digest_response.invoice_digest_result.available_page is None
                or page >= digest_response.invoice_digest_result.available_page
            ):
                break

            page += 1

        return invoice_digests

    def _get_invoice_data_for_single_range(
        self,
        start_date: datetime,
        end_date: datetime,
        invoice_direction: InvoiceDirectionType,
        use_threading: bool,
        max_workers: int
    ) -> List[tuple[InvoiceData, ManageInvoiceOperationType]]:
        """Get invoice data for a single date range (≤ 35 days)."""
        # Validate max_workers if threading is enabled
        if use_threading and (max_workers < 1 or max_workers > 20):
            raise NavValidationException("max_workers must be between 1 and 20")

        logger.info(
            f"Starting invoice data retrieval for date range: {start_date.date()} to {end_date.date()}"
            f" (threading: {'enabled' if use_threading else 'disabled'}"
            f"{f', max_workers: {max_workers}' if use_threading else ''})"
        )

        try:
            # Step 1: Collect all invoice digests first (always sequential)
            invoice_digests = []
            page = 1

            while True:
                logger.info(f"Querying invoice digests - page {page}")
                
                # Create invoice query params
                invoice_query_params = InvoiceQueryParamsType(
                    mandatory_query_params=MandatoryQueryParamsType(
                        invoice_issue_date=DateIntervalParamType(
                            date_from=start_date.strftime("%Y-%m-%d"),
                            date_to=end_date.strftime("%Y-%m-%d"),
                        )
                    )
                )

                # Query invoice digests
                digest_response = self.query_invoice_digest(
                    page=page,
                    invoice_direction=invoice_direction,
                    invoice_query_params=invoice_query_params
                )

                if not digest_response.invoice_digest_result or not digest_response.invoice_digest_result.invoice_digest:
                    logger.info(f"No more invoices found on page {page}")
                    break

                page_digests = digest_response.invoice_digest_result.invoice_digest
                invoice_digests.extend(page_digests)
                
                logger.info(
                    f"Found {len(page_digests)} invoices on page {page} (total so far: {len(invoice_digests)})"
                )

                # Check if there are more pages
                if (
                    digest_response.invoice_digest_result.available_page is None
                    or page >= digest_response.invoice_digest_result.available_page
                ):
                    logger.info("All pages processed")
                    break

                page += 1

            if not invoice_digests:
                logger.info("No invoices found in the specified date range")
                return []

            logger.info(f"🎯 Found total of {len(invoice_digests)} invoices to process")

            # Step 2: Process invoices (threaded or non-threaded)
            all_invoice_data = self._process_invoice_digests(
                invoice_digests=invoice_digests,
                invoice_direction=invoice_direction,
                use_threading=use_threading,
                max_workers=max_workers
            )

            logger.info(
                f"Completed invoice data retrieval. Total processed: {len(all_invoice_data)} invoices"
            )
            
            return all_invoice_data

        except (NavValidationException, NavApiException):
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error in _get_invoice_data_for_single_range: {str(e)}"
            )
            raise NavApiException(
                f"Unexpected error during data retrieval: {str(e)}"
            )

    def create_manage_annulment_request(
        self,
        exchange_token: str,
        annulment_operations: List[Tuple[InvoiceAnnulment, int]],
        header_timestamp: Optional[str] = None
    ) -> ManageAnnulmentRequest:
        """
        Create a ManageAnnulmentRequest using generated models.
        
        Args:
            exchange_token: Decoded exchange token from /tokenExchange
            annulment_operations: List of tuples containing (InvoiceAnnulment, index)
            header_timestamp: Optional pre-generated timestamp to ensure consistency
            
        Returns:
            ManageAnnulmentRequest: Complete request ready for submission
        """
        # Create header with consistent timestamp
        if header_timestamp:
            header = self._create_basic_header_with_timestamp(header_timestamp)
        else:
            header = self._create_basic_header()
        software = self._create_software_info(self.credentials)
        
        # Create annulment operation list and prepare operation data for signature
        operations = []
        operation_data = []
        
        for annulment_data, index in annulment_operations:
            # Encode annulment data to base64 for signature calculation
            base64_data = encode_annulment_data_to_base64(annulment_data)
            
            # For the actual request, we need the raw XML bytes (xsdata will base64-encode it)
            xml_data = serialize_annulment_data_to_xml(annulment_data)
            
            operation = AnnulmentOperationType(
                index=index,
                annulment_operation=ManageAnnulmentOperationType.ANNUL,
                invoice_annulment=xml_data.encode('utf-8')  # Raw XML bytes for xsdata
            )
            operations.append(operation)
            
            # Prepare operation data for complex signature calculation
            # According to NAV API docs: annulmentOperation + base64 content
            operation_data.append(("ANNUL", base64_data))
        
        # Create user header with complex signature calculation
        user = self._create_user_header_with_complex_signature(
            self.credentials, 
            header, 
            operation_data
        )
        
        annulment_operation_list = AnnulmentOperationListType(
            annulment_operation=operations
        )
        
        return ManageAnnulmentRequest(
            header=header,
            user=user,
            software=software,
            exchange_token=exchange_token,
            annulment_operations=annulment_operation_list
        )

    def manage_annulment(
        self, request: ManageAnnulmentRequest
    ) -> ManageAnnulmentResponse:
        """
        Submit technical annulment request using xsdata-generated dataclasses.
        
        This operation is used to technically annul previously submitted invoices.
        Technical annulment can only be submitted for invoices that have DONE status
        and contain only warnings (WARN) or no validation messages.
        
        Args:
            request: ManageAnnulmentRequest with proper API structure
            
        Returns:
            ManageAnnulmentResponse: Fully parsed response with transaction ID
            
        Raises:
            NavValidationException: If request validation fails
            NavApiException: If API call fails
            NavXmlParsingException: If XML parsing fails
        """
        try:
            # Serialize request to XML
            xml_request = self._serialize_request_to_xml(request)
            
            logger.debug(f"Serialized ManageAnnulmentRequest XML: {xml_request}")
            
            # Make API call
            with self.http_client as client:
                response = client.post("manageAnnulment", xml_request)
                xml_response = response.text

            # Parse response using generic parsing function
            parsed_response = self._parse_response_from_xml(xml_response, ManageAnnulmentResponse)
            
            logger.info(f"Successfully submitted technical annulment request. Transaction ID: {parsed_response.transaction_id}")
            return parsed_response

        except Exception as e:
            if isinstance(e, (NavApiException, NavValidationException, NavXmlParsingException)):
                raise
            logger.error(f"Unexpected error in manage_annulment: {e}")
            raise NavApiException(f"Failed to submit technical annulment: {str(e)}")

    def submit_technical_annulment(
        self,
        invoice_references: List[Tuple[str, AnnulmentCodeType, str]],
        exchange_key: str
    ) -> ManageAnnulmentResponse:
        """
        High-level method to submit technical annulment for invoices.
        
        This method handles the complete workflow:
        1. Get exchange token
        2. Decode exchange token
        3. Create annulment data
        4. Submit annulment request
        
        Args:
            invoice_references: List of tuples (invoice_number, annulment_code, reason)
            exchange_key: Technical user's exchange key for token decoding
            
        Returns:
            ManageAnnulmentResponse: API response with transaction details
            
        Raises:
            NavValidationException: If parameters are invalid
            NavApiException: If API call fails
        """
        try:
            # Generate single timestamp for consistency across request
            request_timestamp = format_timestamp_for_nav()
            
            # Step 1: Get exchange token
            logger.info("Requesting exchange token for technical annulment")
            token_response = self.get_token()
            
            # Step 2: Decode exchange token
            logger.info("Decoding exchange token")
            decoded_token = decode_exchange_token(
                token_response.encoded_exchange_token, 
                exchange_key
            )
            
            # Step 3: Create annulment operations using the same timestamp
            annulment_operations = []
            for index, (invoice_ref, code, reason) in enumerate(invoice_references, 1):
                annulment_data = InvoiceAnnulment(
                    annulment_reference=invoice_ref,
                    annulment_timestamp=request_timestamp,  # Use consistent timestamp
                    annulment_code=code,
                    annulment_reason=reason
                )
                annulment_operations.append((annulment_data, index))
            
            # Step 4: Create and submit request with consistent timestamp
            logger.info(f"Creating annulment request for {len(invoice_references)} invoices")
            request = self.create_manage_annulment_request(
                exchange_token=decoded_token,
                annulment_operations=annulment_operations,
                header_timestamp=request_timestamp  # Use same timestamp for header
            )
            
            # Submit the request
            response = self.manage_annulment(request)
            
            logger.info(f"Technical annulment submitted successfully. Transaction ID: {response.transaction_id}")
            return response
            
        except Exception as e:
            if isinstance(e, (NavValidationException, NavApiException, NavXmlParsingException)):
                raise
            logger.error(f"Failed to submit technical annulment: {e}")
            raise NavApiException(f"Technical annulment failed: {e}")

    def create_manage_invoice_request(
        self,
        exchange_token: str,
        invoice_operations: List[Tuple[InvoiceData, ManageInvoiceOperationType, int]],
        header_timestamp: Optional[str] = None
    ) -> ManageInvoiceRequest:
        """
        Create a manage invoice request with proper structure and complex signature.
        
        Args:
            exchange_token: Decoded exchange token from NAV
            invoice_operations: List of tuples (invoice_data, operation_type, index)
            header_timestamp: Optional timestamp for consistent request timing
            
        Returns:
            ManageInvoiceRequest: Properly structured request for NAV API
            
        Raises:
            NavValidationException: If parameters are invalid
        """
        
        if not exchange_token:
            raise NavValidationException("Exchange token is required")
        if not invoice_operations:
            raise NavValidationException("At least one invoice operation is required")
        
        # Use provided timestamp or generate new one for consistency
        if header_timestamp is None:
            header_timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')[:-3] + 'Z'
        
        # Create invoice operation list
        invoice_operation_list = []
        index_hash_inputs = []  # For complex signature calculation
        
        for invoice_data, operation_type, index in invoice_operations:
            # Serialize and encode invoice data
            xml_data = serialize_invoice_data_to_xml(invoice_data)
            
            base64_data = encode_invoice_data_to_base64(xml_data)
            
            # Calculate electronic invoice hash for electronic invoices
            # According to NAV docs, this is required when completenessIndicator is true
            electronic_hash = calculate_electronic_invoice_hash(base64_data)
            electronic_invoice_hash = CryptoType(
                value=electronic_hash,
                crypto_type="SHA3-512"
            )
            
            # Create invoice operation
            operation = InvoiceOperationType(
                index=index,
                invoice_operation=operation_type,
                invoice_data=base64_data,
                electronic_invoice_hash=electronic_invoice_hash
            )
            invoice_operation_list.append(operation)
            
            # Collect data for complex signature calculation
            index_hash_inputs.append((operation_type.value, base64_data))
        
        # Create invoice operations list
        operations_list = InvoiceOperationListType(
            compressed_content=False,
            invoice_operation=invoice_operation_list
        )
        
        # Create basic header first to get request_id and timestamp
        header = self._create_basic_header()
        
        # Create user header with complex signature calculation
        user_header = self._create_user_header_with_complex_signature(
            self.credentials,
            header,
            index_hash_inputs
        )
        
        # Create complete request
        request = ManageInvoiceRequest(
            header=header,
            user=user_header,
            software=self._create_software_info(self.credentials),
            exchange_token=exchange_token,
            invoice_operations=operations_list
        )
        
        return request

    def manage_invoice(self, request: ManageInvoiceRequest) -> ManageInvoiceResponse:
        """
        Submit invoice data using xsdata-generated dataclasses.
        
        This operation is used to submit new invoices, modifications, or storno operations.
        
        Args:
            request: ManageInvoiceRequest with proper API structure
            
        Returns:
            ManageInvoiceResponse: Fully parsed response with transaction ID
            
        Raises:
            NavValidationException: If request validation fails
            NavApiException: If API call fails
            NavXmlParsingException: If XML parsing fails
        """
        if not request:
            raise NavValidationException("Request is required")
        
        try:
            # Serialize request to XML
            xml_request = self._serialize_request_to_xml(request)
            
            # Make API call
            with self.http_client as client:
                response = client.post("manageInvoice", xml_request)
                xml_response = response.text
                
            # Log the response for debugging
            logger.info(f"Received response from manageInvoice API")
            logger.debug(f"Raw response XML: {xml_response[:1000]}...")

            # Parse response
            parsed_response = self._parse_response_from_xml(xml_response, ManageInvoiceResponse)
            
            return parsed_response
            
        except Exception as e:
            if isinstance(e, (NavValidationException, NavApiException, NavXmlParsingException)):
                raise
            logger.error(f"Failed to manage invoice: {e}")
            raise NavApiException(f"Invoice management failed: {e}")

    def submit_invoice(
        self,
        invoice_data: InvoiceData,
        operation_type: ManageInvoiceOperationType = ManageInvoiceOperationType.CREATE,
        exchange_key: str = None
    ) -> ManageInvoiceResponse:
        """
        High-level method to submit a single invoice to NAV.
        
        This method handles the complete workflow:
        1. Get exchange token
        2. Decode exchange token  
        3. Create invoice request
        4. Submit invoice
        
        Args:
            invoice_data: InvoiceData object to submit
            operation_type: Type of operation (CREATE, MODIFY, STORNO)
            exchange_key: Technical user's exchange key for token decoding
            
        Returns:
            ManageInvoiceResponse: API response with transaction details
            
        Raises:
            NavValidationException: If parameters are invalid
            NavApiException: If API call fails
        """
        if not invoice_data:
            raise NavValidationException("Invoice data is required")
        
        # Use provided exchange key or fall back to credentials
        if exchange_key is None:
            if hasattr(self.credentials, 'exchange_key'):
                exchange_key = self.credentials.exchange_key
            else:
                raise NavValidationException("Exchange key is required for invoice submission")
        
        try:
            # Generate consistent timestamp for the entire operation
            request_timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')[:-3] + 'Z'
            
            # Step 1: Get exchange token
            logger.info("Requesting exchange token for invoice submission")
            token_response = self.get_token()
            
            # Step 2: Decode exchange token
            logger.info("Decoding exchange token")
            decoded_token = decode_exchange_token(
                token_response.encoded_exchange_token, 
                exchange_key
            )
            
            # Step 3: Create invoice operations
            invoice_operations = [(invoice_data, operation_type, 1)]
            
            # Step 4: Create and submit request
            logger.info(f"Creating invoice request with operation: {operation_type.value}")
            request = self.create_manage_invoice_request(
                exchange_token=decoded_token,
                invoice_operations=invoice_operations,
                header_timestamp=request_timestamp
            )
            
            # Submit the request
            response = self.manage_invoice(request)
            
            logger.info(f"Invoice submitted successfully. Transaction ID: {response.transaction_id}")
            return response
            
        except Exception as e:
            if isinstance(e, (NavValidationException, NavApiException, NavXmlParsingException)):
                raise
            logger.error(f"Failed to submit invoice: {e}")
            raise NavApiException(f"Invoice submission failed: {e}")

    def submit_multiple_invoices(
        self,
        invoice_operations: List[Tuple[InvoiceData, ManageInvoiceOperationType]],
        exchange_key: str = None
    ) -> ManageInvoiceResponse:
        """
        High-level method to submit multiple invoices in a single batch to NAV.
        
        Args:
            invoice_operations: List of tuples (invoice_data, operation_type)
            exchange_key: Technical user's exchange key for token decoding
            
        Returns:
            ManageInvoiceResponse: API response with transaction details
            
        Raises:
            NavValidationException: If parameters are invalid
            NavApiException: If API call fails
        """
        if not invoice_operations:
            raise NavValidationException("At least one invoice operation is required")
        
        if len(invoice_operations) > 100:
            raise NavValidationException("Maximum 100 invoice operations allowed per batch")
        
        # Use provided exchange key or fall back to credentials
        if exchange_key is None:
            if hasattr(self.credentials, 'exchange_key'):
                exchange_key = self.credentials.exchange_key
            else:
                raise NavValidationException("Exchange key is required for invoice submission")
        
        try:
            # Generate consistent timestamp for the entire operation
            request_timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')[:-3] + 'Z'
            
            # Step 1: Get exchange token
            logger.info("Requesting exchange token for batch invoice submission")
            token_response = self.get_token()
            
            # Step 2: Decode exchange token
            logger.info("Decoding exchange token")
            decoded_token = decode_exchange_token(
                token_response.encoded_exchange_token, 
                exchange_key
            )
            
            # Step 3: Add index to each operation
            indexed_operations = []
            for index, (invoice_data, operation_type) in enumerate(invoice_operations, 1):
                indexed_operations.append((invoice_data, operation_type, index))
            
            # Step 4: Create and submit request
            logger.info(f"Creating batch invoice request with {len(invoice_operations)} operations")
            request = self.create_manage_invoice_request(
                exchange_token=decoded_token,
                invoice_operations=indexed_operations,
                header_timestamp=request_timestamp
            )
            
            # Submit the request
            response = self.manage_invoice(request)
            
            logger.info(f"Batch invoice submitted successfully. Transaction ID: {response.transaction_id}")
            return response
            
        except Exception as e:
            if isinstance(e, (NavValidationException, NavApiException, NavXmlParsingException)):
                raise
            logger.error(f"Failed to submit batch invoice: {e}")
            raise NavApiException(f"Batch invoice submission failed: {e}")

    def get_environment_info(self) -> dict:
        """
        Get information about the current environment configuration.
        
        Returns:
            dict: Environment information including URLs and settings
        """
        info = {
            "base_url": self.base_url,
            "timeout": self.timeout,
            "environment": self.environment.value
        }
        
        info.update({
            "is_test_environment": self.environment == NavEnvironment.TEST,
            "is_production_environment": self.environment == NavEnvironment.PRODUCTION
        })
        
        return info
    
    def is_test_environment(self) -> bool:
        """Check if the client is configured for the test environment."""
        return self.environment == NavEnvironment.TEST
    
    def is_production_environment(self) -> bool:
        """Check if the client is configured for the production environment."""
        return self.environment == NavEnvironment.PRODUCTION

    def export_invoices_to_excel(
        self,
        start_date: datetime,
        end_date: datetime,
        output_file: str,
        invoice_direction: InvoiceDirectionType = InvoiceDirectionType.OUTBOUND,
        use_threading: bool = False,
        max_workers: int = 4
    ) -> int:
        """
        Export invoice data to Excel file for a given date range with configurable threading.
        
        This is a convenience method that combines get_all_invoice_data_for_date_range
        with Excel export functionality.
        
        Args:
            start_date: Start date for the query range
            end_date: End date for the query range
            output_file: Path where the Excel file should be saved
            invoice_direction: Invoice direction to query (default: OUTBOUND)
            use_threading: Whether to use threading for improved performance (default: False)
            max_workers: Maximum number of threads for parallel processing (default: 4)
            
        Returns:
            int: Number of invoices exported
            
        Raises:
            NavValidationException: If parameters are invalid
            NavApiException: If API requests fail
            ExcelProcessingException: If Excel export fails
        """
        try:
            logger.info(f"Starting Excel export for date range: {start_date.date()} to {end_date.date()}")
            
            # Get invoice data with configurable threading
            invoice_data_list = self.get_all_invoice_data_for_date_range(
                start_date=start_date,
                end_date=end_date,
                invoice_direction=invoice_direction,
                use_threading=use_threading,
                max_workers=max_workers
            )
            
            if not invoice_data_list:
                logger.info("No invoices found to export")
                return 0
                
            logger.info(f"📄 Starting Excel export of {len(invoice_data_list)} invoices...")
            
            # Export to Excel
            exporter = InvoiceExcelExporter()
            exporter.export_to_excel(invoice_data_list, output_file)
            
            logger.info(f"✅ Successfully exported {len(invoice_data_list)} invoices to {output_file}")
            return len(invoice_data_list)
            
        except Exception as e:
            if isinstance(e, (NavValidationException, NavApiException)):
                raise
            logger.error(f"Excel export failed: {e}")
            raise NavApiException(f"Failed to export to Excel: {e}")

    def export_invoices_to_excel_streaming(
        self,
        start_date: datetime,
        end_date: datetime,
        output_file: str,
        invoice_direction: InvoiceDirectionType = InvoiceDirectionType.OUTBOUND,
        use_threading: bool = True,
        max_workers: int = 4,
        temp_storage_dir: Optional[str] = None
    ) -> int:
        """
        Export invoice data to Excel file using streaming mode (memory-efficient).
        
        This method is designed for very large datasets (millions of invoices) where
        loading all data into memory would cause OOM errors. It works in two phases:
        
        Phase 1: Fetch invoice data from NAV and save directly to disk (parallel)
        Phase 2: Read from disk and write to Excel one-by-one (sequential, memory-efficient)
        
        Memory usage: Only ~1-2 invoices in memory at any time, regardless of dataset size.
        
        Args:
            start_date: Start date for the query range
            end_date: End date for the query range
            output_file: Path where the Excel file should be saved
            invoice_direction: Invoice direction to query (default: OUTBOUND)
            use_threading: Whether to use threading for Phase 1 (default: True for performance)
            max_workers: Maximum number of threads for parallel processing (default: 4)
            temp_storage_dir: Directory for temporary storage. If None, auto-creates in ~/.nav_invoice_temp
            
        Returns:
            int: Number of invoices exported
            
        Raises:
            NavValidationException: If parameters are invalid
            NavApiException: If API requests fail
            ExcelProcessingException: If Excel export fails
            ImportError: If xlsxwriter is not installed
            
        Example:
            >>> client = NavOnlineInvoiceClient(credentials)
            >>> # Export 1 million invoices without OOM
            >>> count = client.export_invoices_to_excel_streaming(
            ...     start_date=datetime(2023, 1, 1),
            ...     end_date=datetime(2024, 12, 31),
            ...     output_file="invoices_2023_2024.xlsx",
            ...     use_threading=True,
            ...     max_workers=4
            ... )
            >>> print(f"Exported {count} invoices")
        """
        try:
            logger.info(
                f"🚀 Starting STREAMING Excel export for date range: "
                f"{start_date.date()} to {end_date.date()}"
            )
            logger.info(
                f"Memory-efficient mode: invoices will be saved to disk, "
                f"then written to Excel one-by-one"
            )
            
            # Phase 1: Collect invoice digests and save details to file storage
            logger.info("=" * 80)
            logger.info("PHASE 1: Fetching invoice data from NAV and saving to disk")
            logger.info("=" * 80)
            
            # Validate date range
            if start_date > end_date:
                raise NavValidationException("Start date must be before end date")
            
            # Check if date range needs to be split
            date_diff = (end_date - start_date).days
            
            # Create file storage with context manager for auto-cleanup
            with InvoiceFileStorage(temp_storage_dir) as file_storage:
                logger.info(f"📁 Temporary storage location: {file_storage.base_dir}")
                
                if date_diff > MAX_DATE_RANGE_DAYS:
                    # Split into smaller date ranges
                    logger.info(
                        f"Date range ({date_diff} days) exceeds maximum ({MAX_DATE_RANGE_DAYS} days). "
                        "Splitting into smaller ranges."
                    )
                    
                    date_ranges = split_date_range(
                        start_date.strftime("%Y-%m-%d"),
                        end_date.strftime("%Y-%m-%d"),
                        MAX_DATE_RANGE_DAYS
                    )
                    
                    logger.info(f"Split into {len(date_ranges)} date ranges")
                    
                    # Process each date range
                    total_processed = 0
                    total_failed = 0
                    
                    for i, (range_start_str, range_end_str) in enumerate(date_ranges, 1):
                        logger.info(f"\n📅 Processing date range {i}/{len(date_ranges)}: {range_start_str} to {range_end_str}")
                        
                        # Collect digests for this range
                        invoice_digests = self._collect_invoice_digests_for_range(
                            range_start_str, range_end_str, invoice_direction
                        )
                        
                        if invoice_digests:
                            # Process digests and save to storage
                            processed, failed = self._process_invoice_digests_to_storage(
                                invoice_digests=invoice_digests,
                                invoice_direction=invoice_direction,
                                file_storage=file_storage,
                                use_threading=use_threading,
                                max_workers=max_workers
                            )
                            total_processed += processed
                            total_failed += failed
                    
                    logger.info(
                        f"\n✅ Phase 1 complete: {total_processed} invoices saved to disk, "
                        f"{total_failed} failed"
                    )
                else:
                    # Single date range
                    logger.info("Date range fits within maximum, processing as single range")
                    
                    # Collect all digests
                    invoice_digests = self._collect_invoice_digests_for_range(
                        start_date.strftime("%Y-%m-%d"),
                        end_date.strftime("%Y-%m-%d"),
                        invoice_direction
                    )
                    
                    if not invoice_digests:
                        logger.info("No invoices found to export")
                        return 0
                    
                    # Process digests and save to storage
                    total_processed, total_failed = self._process_invoice_digests_to_storage(
                        invoice_digests=invoice_digests,
                        invoice_direction=invoice_direction,
                        file_storage=file_storage,
                        use_threading=use_threading,
                        max_workers=max_workers
                    )
                    
                    logger.info(
                        f"✅ Phase 1 complete: {total_processed} invoices saved to disk, "
                        f"{total_failed} failed"
                    )
                
                # Check storage size
                storage_size_mb = file_storage.get_storage_size() / (1024 * 1024)
                logger.info(f"💾 Temporary storage size: {storage_size_mb:.2f} MB")
                
                if total_processed == 0:
                    logger.info("No invoices to export")
                    return 0
                
                # Phase 2: Stream from file storage to Excel
                logger.info("\n" + "=" * 80)
                logger.info("PHASE 2: Reading from disk and writing to Excel (streaming)")
                logger.info("=" * 80)
                
                logger.info(
                    f"📄 Starting streaming Excel export of {total_processed} invoices to {output_file}"
                )
                
                # Create streaming exporter
                streaming_exporter = StreamingInvoiceExcelExporter()
                
                # Export using iterator (memory-efficient)
                headers_written, lines_written = streaming_exporter.export_to_excel_streaming(
                    invoice_iterator=file_storage.iterate_invoices(),
                    file_path=output_file,
                    include_operation_type=False,
                    total_count=total_processed
                )
                
                logger.info(
                    f"\n✅ STREAMING EXPORT COMPLETE!\n"
                    f"   📊 Invoices exported: {headers_written}\n"
                    f"   📋 Line items exported: {lines_written}\n"
                    f"   📁 Output file: {output_file}\n"
                    f"   💾 File size: {Path(output_file).stat().st_size / (1024*1024):.2f} MB"
                )
                
                # Cleanup happens automatically via context manager
                logger.info(f"🧹 Cleaning up temporary storage...")
                
                return headers_written
                
        except Exception as e:
            if isinstance(e, (NavValidationException, NavApiException)):
                raise
            logger.error(f"Streaming Excel export failed: {e}")
            raise NavApiException(f"Failed to export to Excel (streaming): {e}")

    def import_invoices_from_excel(
        self,
        excel_file: str,
        submit_to_nav: bool = False
    ) -> List[Tuple[InvoiceData, ManageInvoiceOperationType]]:
        """
        Import invoice data from Excel file.
        
        This is a convenience method that imports Excel data and optionally
        submits it to NAV using submit_multiple_invoices.
        
        Args:
            excel_file: Path to the Excel file to import
            submit_to_nav: Whether to automatically submit to NAV after import
            
        Returns:
            List[Tuple[InvoiceData, ManageInvoiceOperationType]]: Imported invoice data
            
        Raises:
            NavApiException: If import or submission fails
            ExcelProcessingException: If Excel import fails
            
        Note:
            Import functionality is not yet fully implemented.
        """
        try:
            logger.info(f"Starting Excel import from {excel_file}")
            
            # Import from Excel
            importer = InvoiceExcelImporter()
            invoice_data_list = importer.import_from_excel(excel_file)
            
            logger.info(f"Successfully imported {len(invoice_data_list)} invoices from Excel")
            
            # Optionally submit to NAV
            if submit_to_nav and invoice_data_list:
                logger.info("Submitting imported invoices to NAV")
                response = self.submit_multiple_invoices(invoice_data_list)
                logger.info(f"Submitted to NAV with transaction ID: {response.transaction_id}")
            
            return invoice_data_list
            
        except NotImplementedError as e:
            logger.warning(f"Excel import not yet fully implemented: {e}")
            raise NavApiException(f"Excel import not yet available: {e}")
        except Exception as e:
            logger.error(f"Excel import failed: {e}")
            raise NavApiException(f"Failed to import from Excel: {e}")

    def _poll_transaction_status_until_complete(
        self,
        transaction_id: str,
        polling_interval_seconds: int,
        max_polling_attempts: int
    ) -> Optional['QueryTransactionStatusResponse']:
        """
        Poll transaction status until it's no longer PROCESSING.
        
        Args:
            transaction_id: Transaction ID to check
            polling_interval_seconds: Time to wait between polling attempts
            max_polling_attempts: Maximum number of polling attempts
            
        Returns:
            QueryTransactionStatusResponse or None if all attempts failed
        """
        for polling_attempt in range(max_polling_attempts):
            try:
                transaction_response = self.query_transaction_status(
                    transaction_id=transaction_id,
                    return_original_request=False
                )
            except Exception as e:
                logger.warning(f"Transaction {transaction_id} status check attempt {polling_attempt + 1} failed: {e}")
                # If we've reached max polling attempts, return None
                if polling_attempt == max_polling_attempts - 1:
                    logger.error(f"Failed to get status for transaction {transaction_id} after {max_polling_attempts} attempts")
                    return None
                # Wait before retrying
                time.sleep(polling_interval_seconds)
                continue
            
            # Check if we have any processing results to examine
            has_processing_status = False
            if (transaction_response.processing_results and 
                transaction_response.processing_results.processing_result and 
                len(transaction_response.processing_results.processing_result) > 0):
                
                # Check if any invoice is still processing
                for processing_result in transaction_response.processing_results.processing_result:
                    if (hasattr(processing_result, 'invoice_status') and 
                        processing_result.invoice_status and
                        processing_result.invoice_status.value == 'PROCESSING'):
                        has_processing_status = True
                        break
            
            logger.debug(f"Transaction {transaction_id} polling attempt {polling_attempt + 1}/{max_polling_attempts}: has_processing_status = {has_processing_status}")
            
            # If no invoice is in PROCESSING status, we're done
            if not has_processing_status:
                logger.info(f"Transaction {transaction_id} completed - no invoices in PROCESSING status")
                return transaction_response
            
            # If we've reached max polling attempts, return the last response
            if polling_attempt == max_polling_attempts - 1:
                logger.warning(f"Transaction {transaction_id} still has PROCESSING invoices after {max_polling_attempts} attempts, stopping polling")
                return transaction_response
            
            # Wait before next polling attempt
            logger.debug(f"Transaction {transaction_id} still has invoices PROCESSING, waiting {polling_interval_seconds} seconds before next check")
            time.sleep(polling_interval_seconds)
        
        return transaction_response

    def process_excel_to_nav_results(
        self,
        input_excel_file: str,
        output_excel_file: str,
        max_invoices_per_batch: int = 10,
        polling_interval_seconds: int = 3,
        max_polling_attempts: int = 10
    ) -> str:
        """
        Process Excel file by submitting invoices to NAV and return results in Excel.
        
        Reads an Excel file with invoice data, submits invoices to NAV in batches,
        queries transaction status for all batches, and exports results to a new Excel file.
        
        Args:
            input_excel_file: Path to input Excel file with 'Fejléc adatok' and 'Tétel adatok' sheets
            output_excel_file: Path to output Excel file with results
            max_invoices_per_batch: Maximum number of invoices per batch (default: 10, max: 100)
            polling_interval_seconds: Time to wait between polling attempts when status is PROCESSING (default: 3 seconds)
            max_polling_attempts: Maximum number of polling attempts for PROCESSING status (default: 10)
            
        Returns:
            str: Path to the output Excel file with results
            
        Raises:
            NavValidationException: If parameters are invalid
            NavApiException: If NAV operations fail
            ExcelProcessingException: If Excel processing fails
        """
        if not input_excel_file or not output_excel_file:
            raise NavValidationException("Both input and output Excel file paths are required")
            
        # Validate batch size
        if max_invoices_per_batch < 1:
            raise NavValidationException("max_invoices_per_batch must be at least 1")
        if max_invoices_per_batch > 100:
            raise NavValidationException("max_invoices_per_batch cannot exceed 100 (NAV API limit)")
            
        try:
            logger.info(f"Starting Excel to NAV processing: {input_excel_file} -> {output_excel_file}")
            
            # Step 1: Import invoice data from Excel
            logger.info("Step 1: Importing invoice data from Excel")
            importer = InvoiceExcelImporter()
            invoice_data_list = importer.import_from_excel(input_excel_file)
            
            if not invoice_data_list:
                raise NavValidationException("No invoice data found in Excel file")
                
            logger.info(f"Successfully imported {len(invoice_data_list)} invoices from Excel")
            
            # Step 2: Process invoices in batches
            logger.info("Step 2: Processing invoices in batches")
            
            # Split invoices into batches
            total_invoices = len(invoice_data_list)
            batches = []
            for i in range(0, total_invoices, max_invoices_per_batch):
                batch = invoice_data_list[i:i + max_invoices_per_batch]
                batches.append(batch)
            
            batch_results = []  # Store results from all batches
            
            logger.info(f"Processing {total_invoices} invoices in {len(batches)} batches (max {max_invoices_per_batch} per batch)")
            
            for batch_num, batch in enumerate(batches, 1):
                start_invoice = (batch_num - 1) * max_invoices_per_batch + 1
                end_invoice = min(batch_num * max_invoices_per_batch, total_invoices)
                logger.info(f"Processing batch {batch_num}/{len(batches)}: invoices {start_invoice}-{end_invoice}")
                
                try:
                    # Submit current batch
                    batch_response = self.submit_multiple_invoices(batch)
                    batch_transaction_id = batch_response.transaction_id
                    logger.info(f"Batch {batch_num} submitted successfully. Transaction ID: {batch_transaction_id}")
                    
                    # Store batch info for later status checking
                    batch_results.append({
                        'batch_num': batch_num,
                        'transaction_id': batch_transaction_id,
                        'invoice_data': batch,
                        'start_index': start_invoice,
                        'end_index': end_invoice
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to submit batch {batch_num}: {e}")
                    # Store failed batch info
                    batch_results.append({
                        'batch_num': batch_num,
                        'transaction_id': None,
                        'invoice_data': batch,
                        'start_index': start_invoice,
                        'end_index': end_invoice,
                        'error': str(e)
                    })
            
            # Step 3: Query transaction status for all batches with polling
            logger.info(f"Step 3: Checking transaction status for {len(batch_results)} batches")
            
            # Query status for each batch
            all_results_data = []
            
            for batch_info in batch_results:
                if batch_info.get('error'):
                    # Handle failed batch submission
                    logger.warning(f"Batch {batch_info['batch_num']} failed during submission: {batch_info['error']}")
                    for i, (invoice_data, _) in enumerate(batch_info['invoice_data']):
                        invoice_number = ""
                        if hasattr(invoice_data, 'invoice_number') and invoice_data.invoice_number:
                            invoice_number = invoice_data.invoice_number
                            
                        result_row = {
                            'Számlaszám': invoice_number,
                            'Tranzakció azonosító': "FAILED",
                            'Index': batch_info['start_index'] + i,
                            'Status': "ERROR",
                            'Warnings': f"Batch submission failed: {batch_info['error']}"
                        }
                        all_results_data.append(result_row)
                    continue
                
                batch_transaction_id = batch_info['transaction_id']
                logger.info(f"Checking status for batch {batch_info['batch_num']}, transaction: {batch_transaction_id}")
                
                # Use polling method to wait for transaction to complete
                transaction_response = self._poll_transaction_status_until_complete(
                    transaction_id=batch_transaction_id,
                    polling_interval_seconds=polling_interval_seconds,
                    max_polling_attempts=max_polling_attempts
                )
                
                if not transaction_response:
                    # Handle failed status query
                    logger.warning(f"Could not retrieve status for batch {batch_info['batch_num']}")
                    for i, (invoice_data, _) in enumerate(batch_info['invoice_data']):
                        invoice_number = ""
                        if hasattr(invoice_data, 'invoice_number') and invoice_data.invoice_number:
                            invoice_number = invoice_data.invoice_number
                            
                        result_row = {
                            'Számlaszám': invoice_number,
                            'Tranzakció azonosító': batch_transaction_id,
                            'Index': batch_info['start_index'] + i,
                            'Status': "UNKNOWN",
                            'Warnings': "Failed to retrieve transaction status"
                        }
                        all_results_data.append(result_row)
                    continue
                
                # Process successful status response
                logger.info(f"Successfully retrieved status for batch {batch_info['batch_num']}")
                
                if transaction_response.processing_results and transaction_response.processing_results.processing_result:
                    for processing_result in transaction_response.processing_results.processing_result:
                        # Use the index directly from ProcessingResultType
                        batch_relative_index = processing_result.index - 1  # Convert to 0-based for array access
                        
                        # Get invoice data
                        invoice_number = ""
                        if 0 <= batch_relative_index < len(batch_info['invoice_data']):
                            invoice_data, _ = batch_info['invoice_data'][batch_relative_index]
                            if hasattr(invoice_data, 'invoice_number') and invoice_data.invoice_number:
                                invoice_number = invoice_data.invoice_number
                        
                        # Collect warnings
                        warnings = []
                        
                        if processing_result.technical_validation_messages:
                            for msg in processing_result.technical_validation_messages:
                                if hasattr(msg, 'message') and msg.message:
                                    warnings.append(f"TECH: {msg.message}")
                        
                        if processing_result.business_validation_messages:
                            for msg in processing_result.business_validation_messages:
                                if hasattr(msg, 'message') and msg.message:
                                    warnings.append(f"BIZ: {msg.message}")
                        
                        warnings_text = "; ".join(warnings) if warnings else ""
                        
                        result_row = {
                            'Számlaszám': invoice_number,
                            'Tranzakció azonosító': batch_transaction_id,
                            'Index': processing_result.index,  # Use the index directly from ProcessingResultType
                            'Status': processing_result.invoice_status.value if processing_result.invoice_status else "",
                            'Warnings': warnings_text
                        }
                        
                        all_results_data.append(result_row)
                else:
                    # No processing results for this batch
                    logger.warning(f"No processing results found for batch {batch_info['batch_num']}")
                    for i, (invoice_data, _) in enumerate(batch_info['invoice_data']):
                        invoice_number = ""
                        if hasattr(invoice_data, 'invoice_number') and invoice_data.invoice_number:
                            invoice_number = invoice_data.invoice_number
                            
                        result_row = {
                            'Számlaszám': invoice_number,
                            'Tranzakció azonosító': batch_transaction_id,
                            'Index': batch_info['start_index'] + i,
                            'Status': "UNKNOWN",
                            'Warnings': "No processing results returned from NAV"
                        }
                        all_results_data.append(result_row)
            
            # Step 4: Create output Excel file
            logger.info("Step 4: Creating output Excel file")
            df_results = pd.DataFrame(all_results_data)
            
            # Ensure output directory exists
            output_path = Path(output_excel_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to Excel
            with pd.ExcelWriter(output_excel_file, engine='openpyxl') as writer:
                df_results.to_excel(writer, sheet_name='NAV Results', index=False)
            
            logger.info(f"Successfully created output Excel file: {output_excel_file}")
            logger.info(f"Processed {len(all_results_data)} result records from {len(batches)} batches")
            
            return output_excel_file
            
        except Exception as e:
            if isinstance(e, (NavValidationException, NavApiException)):
                raise
            logger.error(f"Excel to NAV processing failed: {e}")
            raise NavApiException(f"Failed to process Excel to NAV results: {e}")

    def _process_annulment_batch_with_rescue(
        self,
        batch_data: List[Dict],
        polling_interval_seconds: int,
        max_polling_attempts: int,
        max_rescue_attempts: int = 2
    ) -> List[Dict]:
        """
        Process a batch of annulment data with rescue logic for failed transactions.
        
        When a batch transaction fails, this method identifies items that would have
        succeeded and resubmits them in a new transaction, while preserving the
        original order of results.
        
        Args:
            batch_data: List of annulment data dictionaries
            polling_interval_seconds: Seconds to wait between status checks
            max_polling_attempts: Maximum attempts to check transaction status
            max_rescue_attempts: Maximum rescue attempts for failed transactions
            
        Returns:
            List of result dictionaries maintaining original order
        """
        attempt = 0
        current_batch_data = batch_data.copy()
        
        # Create mapping from original_index to results
        # Use a dict instead of list to handle non-contiguous indices
        final_results = {}
        
        while attempt < max_rescue_attempts and current_batch_data:
            attempt += 1
            logger.info(f"Processing batch attempt {attempt} with {len(current_batch_data)} items")
            
            try:
                # Prepare invoice references for current batch
                invoice_references = []
                for data in current_batch_data:
                    invoice_references.append((
                        data['annulment_reference'],
                        data['annulment_code'],
                        data['annulment_reason']
                    ))
                
                # Submit technical annulment batch
                response = self.submit_technical_annulment(
                    invoice_references=invoice_references,
                    exchange_key=self.credentials.exchange_key
                )
                
                batch_transaction_id = response.transaction_id
                logger.info(f"Submitted batch with transaction ID: {batch_transaction_id}")
                
                # Poll transaction status until complete
                status_response = self._poll_transaction_status_until_complete(
                    batch_transaction_id,
                    polling_interval_seconds,
                    max_polling_attempts
                )
                
                # Process the results
                successful_items = []
                failed_items = []
                
                if status_response and hasattr(status_response, 'processing_results') and status_response.processing_results:
                    processing_results_list = getattr(status_response.processing_results, 'processing_result', [])
                    if not processing_results_list:
                        # Fallback if processing_result is not a list
                        processing_results_list = [status_response.processing_results] if status_response.processing_results else []
                    
                    for i, processing_result in enumerate(processing_results_list):
                        if i < len(current_batch_data):
                            original_index = current_batch_data[i]['original_index']
                            
                            # Fix status mapping: ABORTED should be ERROR, not DONE
                            if processing_result.invoice_status in [InvoiceStatusType.RECEIVED, InvoiceStatusType.PROCESSING, InvoiceStatusType.SAVED, InvoiceStatusType.DONE]:
                                status = 'DONE'
                            elif processing_result.invoice_status == InvoiceStatusType.ABORTED:
                                status = 'ERROR'
                            else:
                                status = 'ERROR'
                            
                            result_data = {
                                'transaction_id': batch_transaction_id,
                                'index': original_index + 1,  # 1-based index
                                'status': status,
                                'business_validation_messages': getattr(processing_result, 'business_validation_messages', ''),
                                'technical_validation_messages': getattr(processing_result, 'technical_validation_messages', ''),
                                'error_message': f"Invoice status: {processing_result.invoice_status}" if status == 'ERROR' else ''
                            }
                            print(f"Result for item {original_index}: {processing_result.invoice_status} -> {status} {result_data}")
                            # Store result using original_index as key
                            final_results[original_index] = result_data
                            
                            # Categorize items for potential rescue
                            if processing_result.invoice_status in [InvoiceStatusType.RECEIVED, InvoiceStatusType.PROCESSING, InvoiceStatusType.SAVED, InvoiceStatusType.DONE]:
                                successful_items.append(current_batch_data[i])
                            else:
                                logger.warning(f"Failed item detected: {current_batch_data[i]} with status {processing_result.invoice_status}")
                                failed_items.append(current_batch_data[i])
                
                else:
                    # No processing results - treat as all successful
                    for i, data in enumerate(current_batch_data):
                        original_index = data['original_index']
                        result_data = {
                            'transaction_id': batch_transaction_id,
                            'index': original_index + 1,
                            'status': 'DONE',
                            'business_validation_messages': '',
                            'technical_validation_messages': '',
                            'error_message': ''
                        }
                        final_results[original_index] = result_data
                        successful_items.append(data)
                
                # Transaction completed successfully, check if we need rescue
                if successful_items and failed_items and attempt < max_rescue_attempts:
                    # We have both successful and failed items - this might cause the whole transaction to fail
                    # Let's resubmit only the successful items in the next attempt
                    logger.info(f"Mixed results detected: {len(successful_items)} successful, {len(failed_items)} failed. Will rescue successful items.")
                    current_batch_data = successful_items  # Next iteration will only process successful items
                    continue  # Continue to next attempt with rescued items
                else:
                    # Either all succeeded, all failed, or no more rescue attempts - we're done
                    logger.info(f"Batch completed: {len(successful_items)} successful, {len(failed_items)} failed")
                    break
                
            except Exception as e:
                logger.error(f"Batch attempt {attempt} failed: {e}")
                
                # This is where rescue logic happens!
                # When transaction fails, we need to identify items that would have succeeded
                # and resubmit them in the next attempt
                
                if attempt < max_rescue_attempts and len(current_batch_data) > 1:
                    logger.info(f"Transaction failed, attempting rescue. Will analyze transaction status to identify successful items.")
                    
                    # Try to get transaction status even though submission failed
                    rescue_successful_items = []
                    rescue_failed_items = []
                    
                    if hasattr(e, 'response') or 'transaction_id' in str(e):
                        # If we got a transaction ID before the error, try to check status
                        try:
                            if 'batch_transaction_id' in locals() and batch_transaction_id:
                                logger.info(f"Checking failed transaction {batch_transaction_id} for successful items")
                                status_response = self._poll_transaction_status_until_complete(
                                    batch_transaction_id,
                                    polling_interval_seconds,
                                    max_polling_attempts
                                )
                                
                                if status_response and hasattr(status_response, 'processing_results') and status_response.processing_results:
                                    processing_results_list = getattr(status_response.processing_results, 'processing_result', [])
                                    if not processing_results_list:
                                        processing_results_list = [status_response.processing_results] if status_response.processing_results else []
                                    
                                    for i, processing_result in enumerate(processing_results_list):
                                        if i < len(current_batch_data):
                                            original_index = current_batch_data[i]['original_index']
                                            
                                            if processing_result.invoice_status in [InvoiceStatusType.RECEIVED, InvoiceStatusType.PROCESSING, InvoiceStatusType.SAVED, InvoiceStatusType.DONE]:
                                                # This item would have succeeded - rescue it!
                                                rescue_successful_items.append(current_batch_data[i])
                                                logger.debug(f"Item {original_index} would have succeeded (status: {processing_result.invoice_status}), adding to rescue list")
                                            else:
                                                # This item failed (ABORTED) - mark it as failed
                                                rescue_failed_items.append(current_batch_data[i])
                                                result_data = {
                                                    'transaction_id': batch_transaction_id,
                                                    'index': original_index + 1,
                                                    'status': 'ERROR',
                                                    'business_validation_messages': getattr(processing_result, 'business_validation_messages', ''),
                                                    'technical_validation_messages': getattr(processing_result, 'technical_validation_messages', ''),
                                                    'error_message': f"Invoice status: {processing_result.invoice_status}"
                                                }
                                                final_results[original_index] = result_data
                        except Exception as status_error:
                            logger.warning(f"Could not check status of failed transaction: {status_error}")
                    
                    if rescue_successful_items:
                        logger.info(f"Found {len(rescue_successful_items)} items that would have succeeded. Will resubmit them.")
                        current_batch_data = rescue_successful_items  # Retry with only successful items
                    else:
                        logger.info(f"No successful items found for rescue. Marking all as failed.")
                        # Mark all remaining items as failed
                        for i, data in enumerate(current_batch_data):
                            original_index = data['original_index']
                            if original_index not in final_results:
                                result_data = {
                                    'transaction_id': 'ERROR',
                                    'index': original_index + 1,
                                    'status': 'ERROR',
                                    'business_validation_messages': '',
                                    'technical_validation_messages': '',
                                    'error_message': str(e)
                                }
                                final_results[original_index] = result_data
                        break
                else:
                    # Final attempt failed - mark all remaining items as failed
                    logger.error(f"Final rescue attempt failed. Marking all remaining items as failed.")
                    for i, data in enumerate(current_batch_data):
                        original_index = data['original_index']
                        if original_index not in final_results:  # Not yet processed
                            result_data = {
                                'transaction_id': 'ERROR',
                                'index': original_index + 1,
                                'status': 'ERROR',
                                'business_validation_messages': '',
                                'technical_validation_messages': '',
                                'error_message': str(e)
                            }
                            final_results[original_index] = result_data
                    break
        
        # Convert dictionary back to list, sorted by original_index
        # Ensure we have results for all items in the original batch_data
        result_list = []
        for data in batch_data:
            original_index = data['original_index']
            if original_index in final_results:
                result_list.append(final_results[original_index])
            else:
                # Fallback for missing results
                result_list.append({
                    'transaction_id': 'ERROR',
                    'index': original_index + 1,
                    'status': 'ERROR',
                    'business_validation_messages': '',
                    'technical_validation_messages': '',
                    'error_message': 'Processing incomplete'
                })
        
        return result_list

    # Split data into batches
    def split_into_batches(self, data: list, batch_size: int) -> list:
        batches = []
        for i in range(0, len(data), batch_size):
            batches.append(data[i:i + batch_size])
        return batches

    def process_excel_to_nav_annulment_results(
        self,
        input_excel_file: str,
        output_excel_file: str,
        max_annulments_per_batch: int = 50,
        polling_interval_seconds: int = 3,
        max_polling_attempts: int = 10
    ) -> str:
        """
        Process Excel file containing technical annulment data and submit to NAV.
        
        This method reads an Excel file with annulment data, validates it, submits
        technical annulments to NAV in batches, and writes detailed results to an output Excel file.
        
        Args:
            input_excel_file: Path to input Excel file with annulment data
            output_excel_file: Path where results Excel file will be saved
            max_annulments_per_batch: Maximum number of annulments per batch (default: 50)
            polling_interval_seconds: Seconds to wait between status checks (default: 3)
            max_polling_attempts: Maximum attempts to check transaction status (default: 10)
            
        Returns:
            Path to the created results Excel file
            
        Raises:
            NavValidationException: If Excel format is invalid or data validation fails
            NavApiException: If NAV API errors occur
            FileNotFoundError: If input file doesn't exist
            
        Expected Excel format:
            - 'érvénytelenítési hivatkozás': Invoice reference to annul
            - 'érvénytelenítési kód': Annulment code (ERRATIC, CANCEL, etc.)
            - 'érvénytelenítési ok': Reason for annulment
        """
        try:
            # Validate input file exists
            if not Path(input_excel_file).exists():
                raise FileNotFoundError(f"Input Excel file not found: {input_excel_file}")
            
            # Read and validate Excel file
            try:
                df = pd.read_excel(input_excel_file)
            except Exception as e:
                raise NavValidationException(f"Failed to read Excel file: {e}")
            
            if df.empty:
                raise NavValidationException("Excel file is empty")
            
            # Check required columns
            required_columns = ['érvénytelenítési hivatkozás', 'érvénytelenítési kód', 'érvénytelenítési ok']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise NavValidationException(f"Missing required columns: {', '.join(missing_columns)}")
            
            # Basic validation - check if we have reasonable data
            if len(df.columns) < 3:
                raise NavValidationException("Excel file does not contain the expected minimum number of columns")
            
            # Prepare annulment data
            annulment_data = []
            for index, row in df.iterrows():
                # Convert to string and strip whitespace
                reference = str(row['érvénytelenítési hivatkozás']).strip()
                code_str = str(row['érvénytelenítési kód']).strip().upper()
                reason = str(row['érvénytelenítési ok']).strip()
                
                # Skip empty rows
                if not reference or reference == 'nan' or not code_str or code_str == 'NAN' or not reason or reason == 'nan':
                    continue
                
                try:
                    annulment_code = AnnulmentCodeType(code_str)
                except ValueError:
                    valid_codes = [code.value for code in AnnulmentCodeType]
                    raise NavValidationException(f"Invalid annulment code in row {index + 2}: {code_str}. Valid codes: {', '.join(valid_codes)}")
                
                annulment_data.append({
                    'annulment_reference': reference,
                    'annulment_code': annulment_code,
                    'annulment_reason': reason,
                    'original_index': len(annulment_data)  # Use the current length as index for valid items
                })
            
            if not annulment_data:
                raise NavValidationException("No valid annulment data found in Excel file")
            
            # Get authentication token
            token_response = self.get_token()
            logger.info("Authentication successful")
            
            # Split data into batches and process with rescue logic
            batches = self.split_into_batches(annulment_data, max_annulments_per_batch)
            total_batches = len(batches)
            all_results = []
            
            logger.info(f"Processing {len(annulment_data)} annulments in {total_batches} batches")
            
            # Process each batch with rescue logic
            for batch_num, batch_data in enumerate(batches, 1):
                logger.info(f"Processing batch {batch_num}/{total_batches} with {len(batch_data)} annulments")
                
                batch_results = self._process_annulment_batch_with_rescue(
                    batch_data=batch_data,
                    polling_interval_seconds=polling_interval_seconds,
                    max_polling_attempts=max_polling_attempts,
                    max_rescue_attempts=2
                )
                
                all_results.extend(batch_results)
            
            # Convert results to DataFrame
            df_results = pd.DataFrame(all_results)
            
            # Create output directory if it doesn't exist
            output_path = Path(output_excel_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write results to Excel
            with pd.ExcelWriter(output_excel_file, engine='openpyxl') as writer:
                df_results.to_excel(writer, sheet_name='Annulment Results', index=False)
                
                # Auto-adjust column widths
                worksheet = writer.sheets['Annulment Results']
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            logger.info(f"Results written to {output_excel_file}")
            logger.info(f"Processed {len(all_results)} annulments in {total_batches} batches")
            
            return output_excel_file
            
        except Exception as e:
            if isinstance(e, (NavValidationException, NavApiException)):
                raise
            logger.error(f"Excel to NAV annulment processing failed: {e}")
            raise NavApiException(f"Failed to process Excel to NAV annulment results: {e}")

    def close(self):
        """Close the HTTP client."""
        self.http_client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

"""
Utility functions for NAV Online Számla API.

This module contains utility functions for hashing, date manipulation, 
XML processing, and other common tasks.
"""

import base64
import hashlib
import random
import re
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from datetime import datetime, timedelta, timezone
from typing import List, Tuple, Optional, TYPE_CHECKING
import xml.dom.minidom
from xsdata.formats.dataclass.context import XmlContext
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig

if TYPE_CHECKING:
    from .models import InvoiceAnnulment

from .config import (
    CUSTOM_ID_CHARACTERS,
    CUSTOM_ID_LENGTH,
    MAX_DATE_RANGE_DAYS,
)
from .exceptions import NavValidationException, NavXmlParsingException


def generate_password_hash(password: str) -> str:
    """
    Generate SHA-512 hash of password in uppercase hexadecimal format.

    Args:
        password: The password to hash

    Returns:
        str: SHA-512 hash in uppercase hexadecimal format
    """
    hash_object = hashlib.sha512(password.encode("utf-8"))
    return hash_object.hexdigest().upper()


def generate_custom_id(length: int = CUSTOM_ID_LENGTH) -> str:
    """
    Generate a random custom ID string.

    Args:
        length: Length of the generated ID

    Returns:
        str: Random ID string
    """
    return "".join(random.choice(CUSTOM_ID_CHARACTERS) for _ in range(length))


def calculate_request_signature(
    request_id: str, timestamp: str, signer_key: str
) -> str:
    """
    Calculate request signature for NAV API calls (simple calculation).
    
    This is used for operations other than manageInvoice and manageAnnulment.

    Args:
        request_id: Unique request ID
        timestamp: Timestamp in ISO format
        signer_key: Signer key for authentication

    Returns:
        str: SHA3-512 hash signature in uppercase
    """
    # Convert timestamp to YYYYMMDDHHMMSS format
    dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
    timestamp_str = dt.strftime("%Y%m%d%H%M%S")

    # Create partial authentication string
    partial_auth = f"{request_id}{timestamp_str}{signer_key}"

    # Generate SHA3-512 hash
    hash_object = hashlib.sha3_512(partial_auth.encode("utf-8"))
    return hash_object.hexdigest().upper()


def calculate_complex_request_signature(
    request_id: str, 
    timestamp: str, 
    signer_key: str,
    operation_data: List[Tuple[str, str]]
) -> str:
    """
    Calculate complex request signature for manageInvoice and manageAnnulment operations.
    
    This implements the complex signature calculation described in section 1.5.1 of the 
    NAV API documentation. The signature is calculated from:
    1. Partial authentication (request_id + timestamp + signer_key)
    2. Index hash values (operation type + base64 data for each operation)
    3. Final SHA3-512 hash of the concatenated string
    
    Args:
        request_id: Unique request ID
        timestamp: Timestamp in ISO format
        signer_key: Signer key for authentication
        operation_data: List of tuples (operation_type, base64_data) for each index
        
    Returns:
        str: SHA3-512 hash signature in uppercase
        
    Example:
        From the documentation example:
        - requestId = TSTKFT1222564
        - timestamp = 2017-12-30T18:25:45.000Z
        - signer_key = ce-8f5e-215119fa7dd621DLMRHRLH2S
        - operations = [("CREATE", "QWJjZDEyMzQ="), ("MODIFY", "RGNiYTQzMjE=")]
    """
    # Convert timestamp to YYYYMMDDHHMMSS format
    dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
    timestamp_str = dt.strftime("%Y%m%d%H%M%S")

    # Create partial authentication string
    partial_auth = f"{request_id}{timestamp_str}{signer_key}"

    # Calculate index hashes for each operation
    index_hashes = []
    for operation_type, base64_data in operation_data:
        # Concatenate operation type and base64 data
        hash_base = f"{operation_type}{base64_data}"
        
        # Generate SHA3-512 hash and convert to uppercase
        hash_object = hashlib.sha3_512(hash_base.encode("utf-8"))
        index_hash = hash_object.hexdigest().upper()
        index_hashes.append(index_hash)

    # Concatenate partial auth with all index hashes in order
    full_signature_base = partial_auth + "".join(index_hashes)

    # Generate final SHA3-512 hash
    final_hash = hashlib.sha3_512(full_signature_base.encode("utf-8"))
    return final_hash.hexdigest().upper()


def calculate_electronic_invoice_hash(base64_invoice_data: str) -> str:
    """
    Calculate SHA3-512 hash of base64 encoded invoice data for electronic invoices.
    
    According to NAV documentation, when completenessIndicator is true,
    the electronic invoice hash should be the SHA3-512 hash of the BASE64
    encoded invoiceData in uppercase format.
    
    Args:
        base64_invoice_data: Base64 encoded invoice data string
        
    Returns:
        str: SHA3-512 hash in uppercase hexadecimal format
    """
    hash_object = hashlib.sha3_512(base64_invoice_data.encode("utf-8"))
    return hash_object.hexdigest().upper()


def validate_tax_number(tax_number: str) -> bool:
    """
    Validate Hungarian tax number format (8 digits).

    Args:
        tax_number: Tax number to validate

    Returns:
        bool: True if valid, False otherwise
    """
    return tax_number.isdigit() and len(tax_number) == 8


def split_date_range(
    start_date: str, end_date: str, max_days: int = MAX_DATE_RANGE_DAYS
) -> List[Tuple[str, str]]:
    """
    Split a date range into chunks of maximum days.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        max_days: Maximum days per chunk

    Returns:
        List[Tuple[str, str]]: List of date range tuples
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    date_ranges = []
    current_start = start

    while current_start <= end:
        current_end = min(current_start + timedelta(days=max_days - 1), end)
        date_ranges.append(
            (current_start.strftime("%Y-%m-%d"), current_end.strftime("%Y-%m-%d"))
        )
        current_start = current_end + timedelta(days=1)

    return date_ranges


def get_xml_element_value(
    xml_doc: xml.dom.minidom.Document, tag_name: str, default_value: str = ""
) -> str:
    """
    Get text content of an XML element.
    Handles namespace inconsistencies by trying multiple namespace prefixes.

    Args:
        xml_doc: XML document or element
        tag_name: Tag name to search for
        default_value: Default value if element not found

    Returns:
        str: Element text content or default value
    """
    try:
        # First try the exact tag name (no namespace)
        elements = xml_doc.getElementsByTagName(tag_name)
        if elements and elements[0].firstChild:
            return elements[0].firstChild.data.strip()

        # If not found, try with common namespace prefixes in order of likelihood
        # Based on the NAV API response patterns
        for prefix in ["ns2:", "ns3:", "ns4:", "common:", "base:"]:
            namespaced_tag = f"{prefix}{tag_name}"
            elements = xml_doc.getElementsByTagName(namespaced_tag)
            if elements and elements[0].firstChild:
                return elements[0].firstChild.data.strip()

        return default_value
    except Exception:
        return default_value


def find_xml_elements_with_namespace_aware(
    xml_doc: xml.dom.minidom.Document, tag_name: str
) -> list:
    """
    Find XML elements by tag name, trying multiple namespace prefixes.

    Args:
        xml_doc: XML document or element
        tag_name: Tag name to search for

    Returns:
        list: List of found elements
    """
    # First try the exact tag name (no namespace)
    elements = xml_doc.getElementsByTagName(tag_name)
    if elements:
        return elements

    # If not found, try with common namespace prefixes
    for prefix in ["ns2:", "ns3:", "ns4:", "common:", "base:"]:
        namespaced_tag = f"{prefix}{tag_name}"
        elements = xml_doc.getElementsByTagName(namespaced_tag)
        if elements:
            return elements

    return []


def format_timestamp_for_nav(dt: Optional[datetime] = None) -> str:
    """
    Format datetime for NAV API requests.

    Args:
        dt: Datetime to format, uses current UTC time if None

    Returns:
        str: Formatted timestamp string with max 3 decimal places
    """
    if dt is None:
        dt = datetime.now(timezone.utc)

    # Format with microseconds and then truncate to 3 decimal places
    timestamp_str = dt.strftime("%Y-%m-%dT%H:%M:%S.%f")
    # Keep only first 3 decimal places (microseconds -> milliseconds)
    timestamp_str = timestamp_str[:-3] + "Z"
    return timestamp_str


def decode_exchange_token(encoded_token: bytes, exchange_key: str) -> str:
    """
    Decode an exchange token using AES-128 ECB encryption with the provided exchange key.
    
    According to NAV API documentation, the exchange token received from /tokenExchange
    is encrypted with AES-128 ECB algorithm using the technical user's exchange key.
    
    Args:
        encoded_token: The base64-encoded token from the API response
        exchange_key: The technical user's exchange key for decryption
        
    Returns:
        str: The decoded exchange token value
        
    Raises:
        NavValidationException: If decryption fails
    """
    try:
        # The exchange key should be 16 bytes for AES-128
        if len(exchange_key) != 16:
            raise NavValidationException(f"Exchange key must be exactly 16 characters, got {len(exchange_key)}")
        
        key_bytes = exchange_key.encode('utf-8')
        
        # Create AES cipher in ECB mode
        cipher = Cipher(algorithms.AES(key_bytes), modes.ECB(), backend=default_backend())
        decryptor = cipher.decryptor()
        
        # Decrypt the token
        decrypted_data = decryptor.update(encoded_token) + decryptor.finalize()
        
        # Remove PKCS7 padding and decode as UTF-8
        padding_length = decrypted_data[-1]
        unpadded_data = decrypted_data[:-padding_length]
        
        return unpadded_data.decode('utf-8')
        
    except Exception as e:
        raise NavValidationException(f"Failed to decode exchange token: {e}")


def serialize_annulment_data_to_xml(annulment_data: 'InvoiceAnnulment') -> str:
    """
    Serialize annulment data to XML format.
    
    Args:
        annulment_data: InvoiceAnnulment object with annulment details
        
    Returns:
        str: XML data as string
        
    Raises:
        NavXmlParsingException: If XML serialization fails
    """
    try:
        # Create XML context and serializer
        context = XmlContext()
        config = SerializerConfig(
            indent="  ",
            xml_declaration=True,
            encoding="UTF-8"
        )
        serializer = XmlSerializer(context=context, config=config)
        
        # Serialize the annulment data to XML
        xml_data = serializer.render(annulment_data)
        
        # Format the XML with correct namespaces for NAV API
        xml_data = _format_annulment_xml_with_custom_namespaces(xml_data)
        
        return xml_data
        
    except Exception as e:
        raise NavXmlParsingException(f"Failed to serialize annulment data to XML: {e}")


def encode_annulment_data_to_base64(annulment_data: 'InvoiceAnnulment') -> str:
    """
    Encode annulment data to base64 format required by the API.
    
    Args:
        annulment_data: InvoiceAnnulment object with annulment details
        
    Returns:
        str: Base64 encoded XML data
        
    Raises:
        NavXmlParsingException: If XML serialization fails
    """
    try:
        # Create XML context and serializer
        context = XmlContext()
        config = SerializerConfig(
            indent="  ",
            xml_declaration=True,
            encoding="UTF-8"
        )
        serializer = XmlSerializer(context=context, config=config)
        
        # Serialize the annulment data to XML
        xml_data = serializer.render(annulment_data)
        
        # Format the XML with correct namespaces for NAV API
        xml_data = _format_annulment_xml_with_custom_namespaces(xml_data)
        
        # Encode to base64
        xml_bytes = xml_data.encode('utf-8')
        base64_data = base64.b64encode(xml_bytes)
        
        return base64_data.decode('utf-8')
        
    except Exception as e:
        raise NavXmlParsingException(f"Failed to encode annulment data to base64: {e}")


def _format_annulment_xml_with_custom_namespaces(xml_string: str) -> str:
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


def serialize_invoice_data_to_xml(invoice_data) -> str:
    """
    Serialize InvoiceData object to XML string with proper NAV namespaces.
    
    Args:
        invoice_data: InvoiceData object to serialize
        
    Returns:
        str: XML representation of the invoice data with proper namespaces
        
    Raises:
        NavXmlParsingException: If serialization fails
    """
    try:
        # Create XML context and serializer
        context = XmlContext()
        config = SerializerConfig(
            indent="  ",
            xml_declaration=True,
            encoding="UTF-8"
        )
        serializer = XmlSerializer(context=context, config=config)
        
        # Serialize the invoice data to XML
        xml_data = serializer.render(invoice_data)
        
        # Fix namespace declarations to match NAV expected format
        xml_data = _fix_invoice_data_namespaces(xml_data)
        
        return xml_data
        
    except Exception as e:
        raise NavXmlParsingException(f"Failed to serialize invoice data to XML: {e}")


def _fix_invoice_data_namespaces(xml_string: str) -> str:
    """
    Fix namespace declarations in invoice data XML to match NAV expectations.
    
    NAV expects:
    - Root element: InvoiceData with data namespace
    - Some elements in base namespace: taxpayerId, vatCode, countyCode, simpleAddress, etc.
    - Most elements in data namespace (default)
    """
    
    # First, handle the root element and add proper namespace declarations
    if 'InvoiceDataType' in xml_string:
        # Replace InvoiceDataType with InvoiceData and add proper namespaces
        xml_string = xml_string.replace(
            '<InvoiceDataType',
            '<InvoiceData xmlns="http://schemas.nav.gov.hu/OSA/3.0/data" xmlns:base="http://schemas.nav.gov.hu/OSA/3.0/base"'
        )
        xml_string = xml_string.replace('</InvoiceDataType>', '</InvoiceData>')
    elif '<ns0:InvoiceData' in xml_string:
        # Replace ns0:InvoiceData with InvoiceData and proper namespaces
        xml_string = re.sub(
            r'<ns0:InvoiceData([^>]*?)>',
            '<InvoiceData xmlns="http://schemas.nav.gov.hu/OSA/3.0/data" xmlns:base="http://schemas.nav.gov.hu/OSA/3.0/base">',
            xml_string
        )
        xml_string = xml_string.replace('</ns0:InvoiceData>', '</InvoiceData>')
    elif '<InvoiceData xmlns="http://schemas.nav.gov.hu/OSA/3.0/data">' in xml_string:
        # Add base namespace if only data namespace is present
        xml_string = xml_string.replace(
            '<InvoiceData xmlns="http://schemas.nav.gov.hu/OSA/3.0/data">',
            '<InvoiceData xmlns="http://schemas.nav.gov.hu/OSA/3.0/data" xmlns:base="http://schemas.nav.gov.hu/OSA/3.0/base">'
        )
    elif '<InvoiceData>' in xml_string:
        # Add both namespaces if missing
        xml_string = xml_string.replace(
            '<InvoiceData>',
            '<InvoiceData xmlns="http://schemas.nav.gov.hu/OSA/3.0/data" xmlns:base="http://schemas.nav.gov.hu/OSA/3.0/base">'
        )
    
    # Fix xsi:type attributes first (these need proper namespace prefixes)
    xml_string = re.sub(r'xsi:type="ns1:([^"]+)"', r'xsi:type="base:\1"', xml_string)
    xml_string = re.sub(r'xsi:type="ns0:([^"]+)"', r'xsi:type="\1"', xml_string)
    
    # Replace ns1: with base: for opening tags
    xml_string = re.sub(r'<ns1:([^>\s]+)', r'<base:\1', xml_string)
    # Replace ns1: with base: for closing tags  
    xml_string = re.sub(r'</ns1:([^>]+)', r'</base:\1', xml_string)
    
    # Remove base namespace declarations since we declared it at root
    xml_string = re.sub(r' xmlns:ns1="http://schemas\.nav\.gov\.hu/OSA/3\.0/base"', '', xml_string)
    
    # Remove data namespace elements (ns0) - they become default namespace
    xml_string = re.sub(r'<ns0:([^>\s]+)', r'<\1', xml_string)
    xml_string = re.sub(r'</ns0:([^>]+)', r'</\1', xml_string)
    
    # Remove data namespace declarations since we declared it as default at root
    xml_string = re.sub(r' xmlns:ns0="http://schemas\.nav\.gov\.hu/OSA/3\.0/data"', '', xml_string)
    
    # Clean up any remaining numbered namespace prefixes
    xml_string = re.sub(r'<ns\d+:', '<', xml_string)
    xml_string = re.sub(r'</ns\d+:', '</', xml_string)
    xml_string = re.sub(r' xmlns:ns\d+="[^"]*"', '', xml_string)
    
    # Fix VAT rate issues: when vatPercentage is present, remove conflicting default fields
    xml_string = _fix_vat_rate_elements(xml_string)
    
    return xml_string
    xml_string = re.sub(r'<ns\d+:', '<', xml_string)
    xml_string = re.sub(r'</ns\d+:', '</', xml_string)
    xml_string = re.sub(r' xmlns:ns\d+="[^"]*"', '', xml_string)
    
    # Fix VAT rate issues: when vatPercentage is present, remove conflicting default fields
    xml_string = _fix_vat_rate_elements(xml_string)
    
    return xml_string


def _fix_vat_rate_elements(xml_string: str) -> str:
    """
    Fix VAT rate elements that conflict with schema constraints.
    
    When vatPercentage is present (normal VAT), remove the default elements
    that have schema constraints requiring specific values.
    """
    
    # Find all vatRate blocks (both <vatRate> and <lineVatRate>) that contain vatPercentage
    vat_rate_patterns = [
        r'(<vatRate>.*?</vatRate>)',
        r'(<lineVatRate>.*?</lineVatRate>)'
    ]
    
    def fix_vat_rate_block(match):
        vat_rate_content = match.group(1)
        
        # If this vatRate block contains vatPercentage, remove the problematic default elements
        if '<vatPercentage>' in vat_rate_content:
            # Remove vatDomesticReverseCharge and noVatCharge elements
            vat_rate_content = re.sub(r'<vatDomesticReverseCharge>.*?</vatDomesticReverseCharge>\s*', '', vat_rate_content)
            vat_rate_content = re.sub(r'<noVatCharge>.*?</noVatCharge>\s*', '', vat_rate_content)
        
        return vat_rate_content
    
    # Apply the fix to all vatRate blocks (both types)
    for pattern in vat_rate_patterns:
        xml_string = re.sub(pattern, fix_vat_rate_block, xml_string, flags=re.DOTALL)
    
    return xml_string


def encode_invoice_data_to_base64(xml_data: str) -> str:
    """
    Encode XML string to base64 string.
    
    Args:
        xml_data: XML string to encode
        
    Returns:
        str: Base64 encoded data as string
        
    Raises:
        NavXmlParsingException: If encoding fails
    """
    try:
        # Encode to base64
        xml_bytes = xml_data.encode('utf-8')
        base64_bytes = base64.b64encode(xml_bytes)
        base64_string = base64_bytes.decode('ascii')
        
        return base64_string
        
    except Exception as e:
        raise NavXmlParsingException(f"Failed to encode invoice data to base64: {e}")

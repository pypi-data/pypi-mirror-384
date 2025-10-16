"""
Field mapping logic for converting between InvoiceData and Excel row structures.

This module provides mapping functionality between the complex nested InvoiceData
objects and flat Excel row representations.
"""

import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Tuple, Union

from ..models import InvoiceData, ManageInvoiceOperationType
from ..models.invoice_data import (
    InvoiceType, InvoiceHeadType, SupplierInfoType, CustomerInfoType,
    LineType, VatRateGrossDataType, VatRateType, LineVatDataType, LinesType,
    SummaryType, SummaryNormalType, SummaryByVatRateType, InvoiceReferenceType, InvoiceMainType,
    LineNetAmountDataType, LineGrossAmountDataType,
    LineAmountsNormalType, LineOperationType,
    CustomerVatStatusType, UnitOfMeasureType,
    InvoiceDetailType, LineModificationReferenceType,
    VatRateNetDataType, VatRateVatDataType,
    CustomerTaxNumberType, CustomerVatDataType, SummarySimplifiedType,
    DetailedReasonType, LineAmountsSimplifiedType, SummaryGrossDataType
)
from ..models.invoice_base import (
    TaxNumberType, AddressType, SimpleAddressType,
    PaymentMethodType, InvoiceCategoryType, InvoiceAppearanceType
)
from .models import InvoiceHeaderRow, InvoiceLineRow
from .exceptions import ExcelMappingException

logger = logging.getLogger(__name__)


class ExcelFieldMapper:
    """
    Handles bidirectional mapping between InvoiceData objects and Excel row structures.
    """
    
    # Value replacement mappings for proper localization
    VALUE_REPLACEMENTS = {
        # Boolean values
        'boolean_hu': {
            True: 'Igen',
            False: 'Nem',
            'true': 'Igen',
            'false': 'Nem',
            'TRUE': 'Igen',
            'FALSE': 'Nem',
        },
        
        # Customer VAT status
        'customer_vat_status': {
            'DOMESTIC': 'Belföldi ÁFA alany',
            'PRIVATE_PERSON': 'Nem ÁFA alany (belföldi vagy külföldi) természetes személy',
            'OTHER': 'Egyéb (belföldi nem ÁFA alany, nem természetes személy, külföldi Áfa alany és külföldi nem ÁFA alany, nem természetes személy)'
        },
        
        # Payment methods
        'payment_method': {
            'TRANSFER': 'Banki átutalás',
            'CASH': 'Készpénz',
            'CARD': 'Bankkártya, hitelkártya, egyéb készpénz helyettesítő eszköz',
        },
        
        # Invoice categories
        'invoice_category': {
            'NORMAL': 'Normál',
            'SIMPLIFIED': 'Egyszerűsített',
            'AGGREGATE': 'Gyűjtőszámla'
        },
        
        # Line operations
        'line_operation': {
            'CREATE': 'Új sor felvétele',
            'MODIFY': 'Sor módosítás',
            'DELETE': 'Sor törlés'
        },
        
        # VAT exemption cases
        'vat_exemption_case': {
            'AAM': 'Alanyi adómentes',
            'TAM': 'Tárgyi adómentes ill. a tevékenység közérdekű vagy speciális jellegére tekintettel adómentes',
            'KBAET': 'Adómentes Közösségen belüli termékértékesítés, új közlekedési eszköz nélkül',
            'KBAUK': 'Adómentes Közösségen belüli új közlekedési eszköz értékesítés',
            'EAM': 'Adómentes termékértékesítés a Közösség területén kívülre (termékexport harmadik országba)',
            'NAM': 'Egyéb nemzetközi ügyletekhez kapcsolódó jogcímen megállapított adómentesség',
            'UNKNOWN': '3.0 előtti számlára hivatkozó, illetve előzmény nélküli módosító és sztornó számlák esetén használható'
        },
        
        # VAT out of scope cases
        # 'vat_out_of_scope_case': {
        #     'ATK': 'Áfa tárgyi hatályán kívül',
        #     'EUFAD37': 'Áfa tv. 37. §-a alapján másik tagállamban teljesített, fordítottan adózó ügylet',
        #     'EUFADE': 'Másik tagállamban teljesített, nem az Áfa tv. 37. §-a alá tartozó, fordítottan adózó ügylet',
        #     'EUE': 'Másik tagállamban teljesített, nem fordítottan adózó ügylet',
        #     'HO': 'Harmadik országban teljesített ügylet',
        #     'UNKNOWN': '3.0 előtti számlára hivatkozó, illetve előzmény nélküli módosító és sztornó számlák esetén használható'
        # },
        
        # Tax base deviation cases
        'tax_base_deviation_case': {
            'REFUNDABLE_VAT': 'Az áfa felszámítása a 11. vagy 14. § alapján történt és az áfát a számla címzettjének meg kell térítenie',
            'NONREFUNDABLE_VAT': 'Az áfa felszámítása a 11. vagy 14. § alapján történt és az áfát a számla címzettjének nem kell megtérítenie',
            'UNKNOWN': '3.0 előtti számlára hivatkozó, illetve előzmény nélküli módosító és sztornó számlák esetén használható'
        },
        
        # Margin scheme indicators
        'margin_scheme': {
            'TRAVEL_AGENCY': 'Utazási irodák',
            'SECOND_HAND': 'Használt cikkek',
            'ARTWORK': 'Műalkotások',
            'ANTIQUES': 'Gyűjteménydarabok és régiségek'
        }
    }
    
    @classmethod
    def _apply_value_replacement(cls, value, replacement_type: str):
        """Apply value replacement based on type with proper defaults."""
        # Handle None values with appropriate defaults based on type
        if value is None:
            # Only set default for cash_accounting_indicator, not for other boolean fields
            if replacement_type == 'boolean_hu':
                # For most boolean fields, None should remain None (becomes nan in Excel)
                # Only set default to 'Nem' for specific fields that need it
                return None
            return None
            
        replacements = cls.VALUE_REPLACEMENTS.get(replacement_type, {})
        return replacements.get(value, value)
    
    # Column mappings constants for tests
    HEADER_COLUMN_MAPPINGS = {
        'Számla sorszáma': 'invoice_number',
        'Számla kelte': 'invoice_issue_date', 
        'Teljesítés dátuma': 'fulfillment_date',
        'Számla pénzneme': 'invoice_currency',
        'Alkalmazott árfolyam': 'exchange_rate',
        'Eladó adószáma (törzsszám)': 'seller_tax_number_main',
        'Eladó adószáma (ÁFA-kód)': 'seller_tax_number_vat',
        'Eladó adószáma (megyekód)': 'seller_tax_number_county',
        'Eladó neve': 'seller_name',
        'Eladó országkódja': 'seller_country_code',
        'Eladó irányítószáma': 'seller_postal_code',
        'Eladó települése': 'seller_city',
        'Eladó többi címadata': 'seller_address_detail',
        'Vevő adószáma (törzsszám)': 'buyer_tax_number_main',
        'Vevő adószáma (ÁFA-kód)': 'buyer_tax_number_vat',
        'Vevő adószáma (megyekód)': 'buyer_tax_number_county',
        'Vevő neve': 'buyer_name',
        'Vevő státusza': 'buyer_vat_status',
        'Vevő közösségi adószáma': 'buyer_community_vat_number',
        'Vevő harmadik országbeli adószáma': 'buyer_third_country_tax_number',
        'Vevő országkódja': 'buyer_country_code',
        'Vevő irányítószáma': 'buyer_postal_code',
        'Vevő települése': 'buyer_city',
        'Vevő többi címadata': 'buyer_address_detail',
        'Eredeti számla száma': 'original_invoice_number',
        'Módosító okirat kelte': 'modification_date',
        'Módosítás sorszáma': 'modification_index',
        'Számla nettó összege (a számla pénznemében)': 'net_amount_original',
        'Számla nettó összege (forintban)': 'net_amount_huf',
        'Számla ÁFA összege (a számla pénznemében)': 'vat_amount_original',
        'Számla ÁFA összege (forintban)': 'vat_amount_huf',
        'Számla bruttó összege (a számla pénznemében)': 'gross_amount_original',
        'Számla bruttó összege (forintban)': 'gross_amount_huf',
        'Fizetési határidő': 'payment_due_date',
        'Fizetési mód': 'payment_method',
        'Kisadózó jelölése': 'small_business_indicator',
        'Pénzforgalmi elszámolás jelölése': 'cash_accounting_indicator',
        'Számla típusa': 'invoice_category',
        'Az adatszolgáltatás maga a számla': 'completeness_indicator',
    }
    
    LINE_COLUMN_MAPPINGS = {
        'Számla sorszáma': 'invoice_number',
        'Tétel sorszáma': 'line_number',
        'Megnevezés': 'description',
        'Mennyiség': 'quantity',
        'Mértékegység': 'unit_of_measure',
        'Egységár': 'unit_price',
        'Nettó összeg (eredeti pénznem)': 'net_amount_original',
        'Nettó összeg (HUF)': 'net_amount_huf',
        'ÁFA kulcs': 'vat_rate',
        'ÁFA összeg (eredeti pénznem)': 'vat_amount_original',
        'ÁFA összeg (HUF)': 'vat_amount_huf',
        'Bruttó összeg (eredeti pénznem)': 'gross_amount_original',
        'Bruttó összeg (HUF)': 'gross_amount_huf',
        'Tétel módosítás típusa': 'line_modification_type',
    }

    # Header field mappings from Excel column names to our dataclass fields
    HEADER_COLUMNS = {
        'Számla sorszáma': 'invoice_number',
        'Számla kelte': 'invoice_issue_date', 
        'Teljesítés dátuma': 'fulfillment_date',
        'Számla pénzneme': 'invoice_currency',
        'Alkalmazott árfolyam': 'exchange_rate',
        'Eladó adószáma (törzsszám)': 'seller_tax_number_main',
        'Eladó adószáma (ÁFA-kód)': 'seller_tax_number_vat',
        'Eladó adószáma (megyekód)': 'seller_tax_number_county',
        'Eladó neve': 'seller_name',
        'Eladó országkódja': 'seller_country_code',
        'Eladó irányítószáma': 'seller_postal_code',
        'Eladó települése': 'seller_city',
        'Eladó többi címadata': 'seller_address_detail',
        'Vevő adószáma (törzsszám)': 'buyer_tax_number_main',
        'Vevő adószáma (ÁFA-kód)': 'buyer_tax_number_vat',
        'Vevő adószáma (megyekód)': 'buyer_tax_number_county',
        'Vevő neve': 'buyer_name',
        'Vevő státusza': 'buyer_vat_status',
        'Vevő közösségi adószáma': 'buyer_community_vat_number',
        'Vevő harmadik országbeli adószáma': 'buyer_third_country_tax_number',
        'Vevő országkódja': 'buyer_country_code',
        'Vevő irányítószáma': 'buyer_postal_code',
        'Vevő települése': 'buyer_city',
        'Vevő többi címadata': 'buyer_address_detail',
        'Eredeti számla száma': 'original_invoice_number',
        'Módosító okirat kelte': 'modification_date',
        'Módosítás sorszáma': 'modification_index',
        'Számla nettó összege (a számla pénznemében)': 'net_amount_original',
        'Számla nettó összege (forintban)': 'net_amount_huf',
        'Számla ÁFA összege (a számla pénznemében)': 'vat_amount_original',
        'Számla ÁFA összege (forintban)': 'vat_amount_huf',
        'Számla bruttó összege (a számla pénznemében)': 'gross_amount_original',
        'Számla bruttó összege (forintban)': 'gross_amount_huf',
        'Fizetési határidő': 'payment_due_date',
        'Fizetési mód': 'payment_method',
        'Kisadózó jelölése': 'small_business_indicator',
        'Pénzforgalmi elszámolás jelölése': 'cash_accounting_indicator',
        'Számla típusa': 'invoice_category',
        'Az adatszolgáltatás maga a számla': 'completeness_indicator',
    }

    # Line item field mappings
    LINE_COLUMNS = {
        'Számla sorszáma': 'invoice_number',
        'Vevő adószáma (törzsszám)': 'buyer_tax_number_main',
        'Vevő neve': 'buyer_name',
        'Eladó adószáma (törzsszám)': 'seller_tax_number_main',
        'Eladó neve': 'seller_name',
        'Tétel sorszáma': 'line_number',
        'Módosítással érintett tétel sorszáma': 'modified_line_number',
        'Módosítás jellege': 'line_modification_type',
        'Megnevezés': 'description',
        'Mennyiség': 'quantity',
        'Mennyiségi egység': 'unit_of_measure',
        'Egységár': 'unit_price',
        'Nettó összeg (a számla pénznemében)': 'net_amount_original',
        'Nettó összeg (forintban)': 'net_amount_huf',
        'Adó mértéke': 'vat_rate',
        'Áfamentesség jelölés': 'vat_exemption_indicator',
        'Áfamentesség esete': 'vat_exemption_case',
        'Áfamentesség leírása': 'vat_exemption_reason',
        'ÁFA törvény hatályán kívüli jelölés': 'out_of_scope_indicator',
        'ÁFA törvény hatályon kívüliségének esete': 'out_of_scope_case',
        'ÁFA törvény hatályon kívüliségének leírása': 'out_of_scope_reason',
        'Adóalap és felszámított adó eltérésének esete': 'tax_base_deviation_case',
        'Eltérő adóalap és felszámított adó adómérték, adótartalom': 'different_tax_rate_content',
        'Belföldi fordított adózás jelölés': 'domestic_reverse_charge_indicator',
        'Áthárított adót tartalmazó különbözet szerinti adózás': 'margin_scheme_with_vat',
        'Áthárított adót nem tartalmazó különbözet szerinti adózás': 'margin_scheme_without_vat',
        'Különbözet szerinti adózás': 'margin_scheme_indicator',
        'ÁFA összeg (a számla pénznemében)': 'vat_amount_original',
        'ÁFA összeg (forintban)': 'vat_amount_huf',
        'Bruttó összeg (a számla pénznemében)': 'gross_amount_original',
        'Bruttó összeg (forintban)': 'gross_amount_huf',
        'ÁFA tartalom': 'vat_content',
        'Előleg jelleg jelölése': 'advance_payment_indicator',
        'Tétel árfolyam': 'line_exchange_rate',
        'Tétel teljesítés dátuma': 'line_fulfillment_date',
        'Nincs felszámított áfa az áfa törvény 17. § alapján': 'no_vat_charge_indicator',
    }

    @classmethod
    def _format_taxpayer_id(cls, taxpayer_id: Optional[str]) -> Optional[str]:
        """Format taxpayer ID to integer string required by NAV."""
        if not taxpayer_id:
            return None
        
        # Remove decimal points from taxpayer ID
        try:
            taxpayer_float = float(taxpayer_id)
            return str(int(taxpayer_float))
        except (ValueError, TypeError):
            return taxpayer_id  # Return as-is if not a number

    @classmethod
    def _format_vat_code(cls, vat_code: Optional[str]) -> Optional[str]:
        """Format VAT code to integer string required by NAV."""
        if not vat_code:
            return None
        
        # Remove decimal points from VAT code
        try:
            vat_float = float(vat_code)
            return str(int(vat_float))
        except (ValueError, TypeError):
            return vat_code  # Return as-is if not a number

    @classmethod
    def _format_county_code(cls, county_code: Optional[str]) -> Optional[str]:
        """Format county code to 2-digit format required by NAV."""
        if not county_code:
            return None
        
        # Ensure county code is 2 digits with leading zero if needed
        try:
            county_float = float(county_code)
            county_int = int(county_float)
            return f"{county_int:02d}"
        except (ValueError, TypeError):
            return county_code  # Return as-is if not a number

    @classmethod
    def _normalize_vat_percentage(cls, vat_percentage: Optional[Decimal]) -> Decimal:
        """Normalize VAT percentage to 0.0-1.0 range required by NAV."""
        if vat_percentage is None:
            return Decimal("0.0")
        
        # If percentage is > 1.0, assume it's in percentage format (e.g., 27.0 for 27%)
        # and convert to decimal format (e.g., 0.27)
        if vat_percentage > 1:
            return vat_percentage / 100
        return vat_percentage

    @classmethod
    def _format_postal_code(cls, postal_code: Optional[str]) -> Optional[str]:
        """Format postal code by removing decimal points if present."""
        if not postal_code:
            return None
        
        postal_code_str = str(postal_code).strip()
        if not postal_code_str or postal_code_str.lower() in ['nan', 'n/a']:
            return None
            
        # Remove decimal point and zeros (e.g., "2191.0" -> "2191")
        if '.' in postal_code_str:
            postal_code_str = postal_code_str.split('.')[0]
            
        return postal_code_str

    @classmethod
    def _map_hungarian_vat_status(cls, hungarian_description: Optional[str]) -> CustomerVatStatusType:
        """Map Hungarian VAT status descriptions to CustomerVatStatusType enum values."""
        if not hungarian_description:
            return CustomerVatStatusType.PRIVATE_PERSON
        
        # Mapping from Hungarian descriptions to enum values
        vat_status_mapping = {
            'Belföldi ÁFA alany': CustomerVatStatusType.DOMESTIC,
            'Egyéb (belföldi nem ÁFA alany, nem természetes személy, külföldi Áfa alany és külföldi nem ÁFA alany, nem természetes személy)': CustomerVatStatusType.OTHER,
            'Nem ÁFA alany (belföldi vagy külföldi) természetes személy': CustomerVatStatusType.PRIVATE_PERSON,
        }
        
        # Try exact match first
        if hungarian_description in vat_status_mapping:
            return vat_status_mapping[hungarian_description]
        
        # Try to match by key parts for flexibility
        description_lower = hungarian_description.lower()
        if 'belföldi áfa alany' in description_lower:
            return CustomerVatStatusType.DOMESTIC
        elif 'egyéb' in description_lower and ('külföldi' in description_lower or 'nem áfa alany' in description_lower):
            return CustomerVatStatusType.OTHER
        elif 'nem áfa alany' in description_lower and 'természetes személy' in description_lower:
            return CustomerVatStatusType.PRIVATE_PERSON
        
        # Default fallback
        logger.warning(f"Unknown Hungarian VAT status description: {hungarian_description}, defaulting to PRIVATE_PERSON")
        return CustomerVatStatusType.PRIVATE_PERSON

    @classmethod
    def _map_hungarian_payment_method(cls, hungarian_description: Optional[str]) -> PaymentMethodType:
        """Map Hungarian payment method descriptions to PaymentMethodType enum values."""
        if not hungarian_description:
            return PaymentMethodType.OTHER
        
        # Mapping from Hungarian descriptions to enum values
        payment_method_mapping = {
            'Készpénz': PaymentMethodType.CASH,
            'Banki átutalás': PaymentMethodType.TRANSFER,
            'Bankártya': PaymentMethodType.CARD,
            'Csekk': PaymentMethodType.VOUCHER,
            'Utalvány': PaymentMethodType.VOUCHER,
            'Váltó': PaymentMethodType.VOUCHER,
        }
        
        # Try exact match first
        if hungarian_description in payment_method_mapping:
            return payment_method_mapping[hungarian_description]
        
        # Try to match by key parts for flexibility
        description_lower = hungarian_description.lower()
        if 'készpénz' in description_lower or 'cash' in description_lower:
            return PaymentMethodType.CASH
        elif 'átutalás' in description_lower or 'transfer' in description_lower:
            return PaymentMethodType.TRANSFER
        elif 'kártya' in description_lower or 'card' in description_lower:
            return PaymentMethodType.CARD
        elif any(word in description_lower for word in ['csekk', 'utalvány', 'váltó', 'voucher']):
            return PaymentMethodType.VOUCHER
        
        # Default fallback
        logger.warning(f"Unknown Hungarian payment method description: {hungarian_description}, defaulting to OTHER")
        return PaymentMethodType.OTHER

    @classmethod
    def _map_hungarian_invoice_category(cls, hungarian_description: Optional[str]) -> InvoiceCategoryType:
        """Map Hungarian invoice category descriptions to InvoiceCategoryType enum values."""
        if not hungarian_description:
            return InvoiceCategoryType.NORMAL
        
        # Mapping from Hungarian descriptions to enum values
        category_mapping = {
            'Normál': InvoiceCategoryType.NORMAL,
            'Egyszerűsített': InvoiceCategoryType.SIMPLIFIED,
            'Összesítő': InvoiceCategoryType.AGGREGATE,
        }
        
        # Try exact match first
        if hungarian_description in category_mapping:
            return category_mapping[hungarian_description]
        
        # Try to match by key parts for flexibility
        description_lower = hungarian_description.lower()
        if 'normál' in description_lower or 'normal' in description_lower:
            return InvoiceCategoryType.NORMAL
        elif 'egyszerűsített' in description_lower or 'simplified' in description_lower:
            return InvoiceCategoryType.SIMPLIFIED
        elif 'összesítő' in description_lower or 'aggregate' in description_lower:
            return InvoiceCategoryType.AGGREGATE
        
        # Default fallback
        logger.warning(f"Unknown Hungarian invoice category description: {hungarian_description}, defaulting to NORMAL")
        return InvoiceCategoryType.NORMAL

    @classmethod
    def _map_hungarian_vat_status(cls, hungarian_description: Optional[str]) -> CustomerVatStatusType:
        """Map Hungarian VAT status descriptions to CustomerVatStatusType enum values."""
        if not hungarian_description:
            return CustomerVatStatusType.PRIVATE_PERSON
        
        # Mapping from Hungarian descriptions to enum values
        vat_status_mapping = {
            'Belföldi ÁFA alany': CustomerVatStatusType.DOMESTIC,
            'Egyéb (belföldi nem ÁFA alany, nem természetes személy, külföldi Áfa alany és külföldi nem ÁFA alany, nem természetes személy)': CustomerVatStatusType.OTHER,
            'Nem ÁFA alany (belföldi vagy külföldi) természetes személy': CustomerVatStatusType.PRIVATE_PERSON,
        }
        
        # Try exact match first
        if hungarian_description in vat_status_mapping:
            return vat_status_mapping[hungarian_description]
        
        # Try to match by key parts for flexibility
        description_lower = hungarian_description.lower()
        if 'belföldi áfa alany' in description_lower:
            return CustomerVatStatusType.DOMESTIC
        elif 'egyéb' in description_lower and ('külföldi' in description_lower or 'nem áfa alany' in description_lower):
            return CustomerVatStatusType.OTHER
        elif 'nem áfa alany' in description_lower and 'természetes személy' in description_lower:
            return CustomerVatStatusType.PRIVATE_PERSON
        
        # Default fallback
        logger.warning(f"Unknown Hungarian VAT status description: {hungarian_description}, defaulting to PRIVATE_PERSON")
        return CustomerVatStatusType.PRIVATE_PERSON

    @classmethod
    def _normalize_header_row_values(cls, row: InvoiceHeaderRow) -> None:
        """Convert None values to appropriate defaults for Excel export."""
        # String fields should be empty strings instead of None
        string_fields = [
            'seller_name', 'seller_country_code', 'seller_postal_code', 'seller_city', 'seller_address_detail',
            'seller_tax_number_main', 'seller_tax_number_vat', 'seller_tax_number_county',
            'buyer_name', 'buyer_country_code', 'buyer_postal_code', 'buyer_city', 'buyer_address_detail',
            'buyer_tax_number_main', 'buyer_tax_number_vat', 'buyer_tax_number_county',
            'buyer_vat_status', 'buyer_community_vat_number', 'buyer_third_country_tax_number',
            'invoice_currency', 'payment_method', 'invoice_category', 'original_invoice_number'
        ]
        
        for field_name in string_fields:
            if getattr(row, field_name) is None:
                setattr(row, field_name, "")

    @classmethod
    def invoice_data_to_header_row(
        cls, 
        invoice_data: InvoiceData, 
        operation_type: ManageInvoiceOperationType
    ) -> InvoiceHeaderRow:
        """
        Convert InvoiceData object to InvoiceHeaderRow for Excel export.
        
        Args:
            invoice_data: The InvoiceData object to convert
            operation_type: The operation type associated with this invoice
            
        Returns:
            InvoiceHeaderRow: Flattened header data for Excel
            
        Raises:
            ExcelMappingException: If mapping fails
        """
        try:
            row = InvoiceHeaderRow()
            
            # Basic invoice data
            row.invoice_number = invoice_data.invoice_number
            row.invoice_issue_date = cls._parse_date(invoice_data.invoice_issue_date)
            row.completeness_indicator = cls._apply_value_replacement(
                invoice_data.completeness_indicator, 'boolean_hu'
            )
            
            # Get the main invoice object
            if not invoice_data.invoice_main or not invoice_data.invoice_main.invoice:
                logger.warning("No invoice main data found")
                cls._normalize_header_row_values(row)
                return row
                
            invoice = invoice_data.invoice_main.invoice
            
            # Invoice head data
            if invoice.invoice_head:
                cls._map_invoice_head_to_header(invoice.invoice_head, row)
            
            # Invoice summary data
            if invoice.invoice_summary:
                cls._map_invoice_summary_to_header(invoice.invoice_summary, row)
                
            # Invoice reference (modification) data
            if invoice.invoice_reference:
                cls._map_invoice_reference_to_header(invoice.invoice_reference, row)
                # For modification invoices, the invoice_issue_date is actually the modification date
                if row.original_invoice_number:  # This indicates it's a modification
                    row.modification_date = row.invoice_issue_date
            
            # Normalize all None values to appropriate defaults
            cls._normalize_header_row_values(row)
            
            return row
            
        except Exception as e:
            logger.error(f"Failed to map InvoiceData to header row: {e}")
            raise ExcelMappingException(f"Header mapping failed: {e}")

    @classmethod
    def invoice_data_to_line_rows(
        cls, 
        invoice_data: InvoiceData, 
        operation_type: ManageInvoiceOperationType
    ) -> List[InvoiceLineRow]:
        """
        Convert InvoiceData object to list of InvoiceLineRow objects for Excel export.
        
        Args:
            invoice_data: The InvoiceData object to convert
            operation_type: The operation type associated with this invoice
            
        Returns:
            List[InvoiceLineRow]: List of line item data for Excel
            
        Raises:
            ExcelMappingException: If mapping fails
        """
        try:
            line_rows = []
            
            if not invoice_data.invoice_main or not invoice_data.invoice_main.invoice:
                return line_rows
                
            invoice = invoice_data.invoice_main.invoice
            
            # Get basic reference data
            seller_name = ""
            seller_tax_main = ""
            buyer_name = ""
            buyer_tax_main = ""
            
            if invoice.invoice_head:
                if invoice.invoice_head.supplier_info:
                    seller_name = invoice.invoice_head.supplier_info.supplier_name or ""
                    if invoice.invoice_head.supplier_info.supplier_tax_number:
                        seller_tax_main = invoice.invoice_head.supplier_info.supplier_tax_number.taxpayer_id or ""
                        
                if invoice.invoice_head.customer_info:
                    buyer_name = invoice.invoice_head.customer_info.customer_name or ""
                    if (invoice.invoice_head.customer_info.customer_vat_data and 
                        invoice.invoice_head.customer_info.customer_vat_data.customer_tax_number):
                        buyer_tax_main = invoice.invoice_head.customer_info.customer_vat_data.customer_tax_number.taxpayer_id or ""
            
            # Process line items
            if invoice.invoice_lines and invoice.invoice_lines.line:
                for line_data in invoice.invoice_lines.line:
                    line_row = InvoiceLineRow()
                    
                    # Basic reference data
                    line_row.invoice_number = invoice_data.invoice_number
                    line_row.seller_name = seller_name
                    line_row.seller_tax_number_main = seller_tax_main
                    line_row.buyer_name = buyer_name
                    line_row.buyer_tax_number_main = buyer_tax_main
                    
                    # Map line data
                    cls._map_line_to_line_row(line_data, line_row)
                    
                    line_rows.append(line_row)
            
            return line_rows
            
        except Exception as e:
            logger.error(f"Failed to map InvoiceData to line rows: {e}")
            raise ExcelMappingException(f"Line mapping failed: {e}")

    @classmethod
    def _map_invoice_head_to_header(cls, head: InvoiceHeadType, row: InvoiceHeaderRow) -> None:
        """Map invoice head data to header row."""
        if head.supplier_info:
            supplier = head.supplier_info
            row.seller_name = supplier.supplier_name
            
            if supplier.supplier_tax_number:
                tax_num = supplier.supplier_tax_number
                row.seller_tax_number_main = tax_num.taxpayer_id
                row.seller_tax_number_vat = tax_num.vat_code
                row.seller_tax_number_county = tax_num.county_code
                
            if supplier.supplier_address:
                cls._map_address_to_seller(supplier.supplier_address, row)
        
        if head.customer_info:
            customer = head.customer_info
            row.buyer_name = customer.customer_name
            row.buyer_vat_status = cls._apply_value_replacement(
                customer.customer_vat_status.value if customer.customer_vat_status else None,
                'customer_vat_status'
            )
            
            # Extract community VAT number and third state tax ID from customer_vat_data
            if customer.customer_vat_data:
                row.buyer_community_vat_number = customer.customer_vat_data.community_vat_number
                row.buyer_third_country_tax_number = customer.customer_vat_data.third_state_tax_id
                
                # Extract tax number from customer_vat_data
                if customer.customer_vat_data.customer_tax_number:
                    tax_num = customer.customer_vat_data.customer_tax_number
                    if hasattr(tax_num, 'taxpayer_id'):
                        row.buyer_tax_number_main = tax_num.taxpayer_id
                    if hasattr(tax_num, 'vat_code'):
                        row.buyer_tax_number_vat = tax_num.vat_code
                    if hasattr(tax_num, 'county_code'):
                        row.buyer_tax_number_county = tax_num.county_code
            else:
                row.buyer_community_vat_number = None
                row.buyer_third_country_tax_number = None
                
            if customer.customer_address:
                cls._map_address_to_buyer(customer.customer_address, row)
        
        # Other head fields
        row.fulfillment_date = cls._parse_date(head.invoice_detail.invoice_delivery_date)
        row.payment_due_date = cls._parse_date(head.invoice_detail.payment_date) 
        row.payment_method = cls._apply_value_replacement(
            head.invoice_detail.payment_method.value if head.invoice_detail.payment_method else None,
            'payment_method'
        )
        row.invoice_currency = head.invoice_detail.currency_code
        row.exchange_rate = head.invoice_detail.exchange_rate
        row.small_business_indicator = cls._apply_value_replacement(
            head.invoice_detail.small_business_indicator, 'boolean_hu'
        )
        # Cash accounting indicator should default to 'Nem' when None
        cash_accounting_value = head.invoice_detail.cash_accounting_indicator
        if cash_accounting_value is None:
            row.cash_accounting_indicator = 'Nem'
        else:
            row.cash_accounting_indicator = cls._apply_value_replacement(
                cash_accounting_value, 'boolean_hu'
            )
        row.invoice_category = cls._apply_value_replacement(
            head.invoice_detail.invoice_category.value if head.invoice_detail.invoice_category else None,
            'invoice_category'
        )

    @classmethod
    def _map_invoice_summary_to_header(cls, summary: SummaryType, row: InvoiceHeaderRow) -> None:
        """Map invoice summary data to header row."""
        if summary.summary_normal:
            row.net_amount_original = summary.summary_normal.invoice_net_amount
            row.net_amount_huf = summary.summary_normal.invoice_net_amount_huf
            row.vat_amount_original = summary.summary_normal.invoice_vat_amount
            row.vat_amount_huf = summary.summary_normal.invoice_vat_amount_huf
            
            # Handle gross amount - first try to get from summary_gross_data, then calculate
            if summary.summary_gross_data and hasattr(summary.summary_gross_data, 'invoice_gross_amount'):
                row.gross_amount_original = summary.summary_gross_data.invoice_gross_amount
                row.gross_amount_huf = summary.summary_gross_data.invoice_gross_amount_huf
            else:
                # Calculate gross amount as net + VAT when summary_gross_data is not available
                net_amount = summary.summary_normal.invoice_net_amount or Decimal('0')
                vat_amount = summary.summary_normal.invoice_vat_amount or Decimal('0')
                net_amount_huf = summary.summary_normal.invoice_net_amount_huf or Decimal('0')
                vat_amount_huf = summary.summary_normal.invoice_vat_amount_huf or Decimal('0')
                
                row.gross_amount_original = net_amount + vat_amount if (net_amount or vat_amount) else None
                row.gross_amount_huf = net_amount_huf + vat_amount_huf if (net_amount_huf or vat_amount_huf) else None

        elif summary.summary_simplified:
            # For simplified invoices, sum up all gross amounts across VAT rates
            total_gross_original = Decimal('0')
            total_gross_huf = Decimal('0')
            
            for simplified_summary in summary.summary_simplified:
                if simplified_summary.vat_content_gross_amount:
                    total_gross_original += simplified_summary.vat_content_gross_amount
                if simplified_summary.vat_content_gross_amount_huf:
                    total_gross_huf += simplified_summary.vat_content_gross_amount_huf
            
            # Set gross amounts directly (simplified invoices don't separate net/vat)
            row.gross_amount_original = total_gross_original if total_gross_original > 0 else None
            row.gross_amount_huf = total_gross_huf if total_gross_huf > 0 else None
            
            # For simplified invoices, net and vat amounts are typically not available
            # They might be calculated from line items if needed, but leave as None for now
            row.net_amount_original = None
            row.net_amount_huf = None
            row.vat_amount_original = None
            row.vat_amount_huf = None
        

    @classmethod
    def _map_invoice_reference_to_header(cls, reference: InvoiceReferenceType, row: InvoiceHeaderRow) -> None:
        """Map invoice reference (modification) data to header row."""
        row.original_invoice_number = reference.original_invoice_number
        # Note: InvoiceReferenceType doesn't have modify_date field
        # The modification date comes from invoice_issue_date in the main invoice head
        # So we skip setting modification_date here - it should be set from the main head
        if reference.modification_index:
            row.modification_index = reference.modification_index

    @classmethod
    def _map_line_to_line_row(cls, line: LineType, row: InvoiceLineRow) -> None:
        """Map line data to line row with comprehensive field mapping."""
        # Basic line information
        row.line_number = line.line_number
        row.description = line.line_description
        
        # Line modification reference
        if line.line_modification_reference:
            line_operation = line.line_modification_reference.line_operation
            # Handle both enum objects and string values
            if line_operation:
                if hasattr(line_operation, 'value'):
                    operation_value = line_operation.value
                else:
                    operation_value = str(line_operation)
            else:
                operation_value = None
                
            row.line_modification_type = cls._apply_value_replacement(
                operation_value,
                'line_operation'
            )
            row.modified_line_number = line.line_modification_reference.line_number_reference
        
        # Quantities and prices
        row.quantity = line.quantity
        
        # Handle unit of measure - could be enum or string
        if line.unit_of_measure:
            if hasattr(line.unit_of_measure, 'value'):
                row.unit_of_measure = line.unit_of_measure.value
            else:
                row.unit_of_measure = str(line.unit_of_measure)
        else:
            row.unit_of_measure = None
            
        row.unit_price = line.unit_price
        
        # Line exchange rate (if different from invoice level)
        row.line_exchange_rate = getattr(line, 'line_exchange_rate', None)
        
        # Line fulfillment date
        if hasattr(line, 'line_delivery_date') and line.line_delivery_date:
            row.line_fulfillment_date = cls._parse_date(line.line_delivery_date)
        
        # Advance payment indicator - leave as None when not specified (should be nan in expected results)
        advance_payment_value = getattr(line, 'advance_indicator', None)
        if advance_payment_value is not None and advance_payment_value is True:
            row.advance_payment_indicator = cls._apply_value_replacement(
                advance_payment_value, 'boolean_hu'
            )
        else:
            row.advance_payment_indicator = None
        
        # Handle normal amounts (most common case)
        if line.line_amounts_normal:
            cls._map_line_amounts_normal(line.line_amounts_normal, row)
            
        # Handle simplified amounts
        elif hasattr(line, 'line_amounts_simplified') and line.line_amounts_simplified:
            cls._map_line_amounts_simplified(line.line_amounts_simplified, row)
    
    @classmethod
    def _map_line_amounts_normal(cls, amounts_normal: LineAmountsNormalType, row: InvoiceLineRow) -> None:
        """Map normal line amounts to row."""
        # Net amounts
        if amounts_normal.line_net_amount_data:
            net_data = amounts_normal.line_net_amount_data
            row.net_amount_original = net_data.line_net_amount
            row.net_amount_huf = net_data.line_net_amount_huf
            
        # VAT information
        if amounts_normal.line_vat_rate:
            vat_rate_info = amounts_normal.line_vat_rate
            
            # VAT rate percentage
            if hasattr(vat_rate_info, 'vat_percentage'):
                row.vat_rate = vat_rate_info.vat_percentage
                
            # VAT exemption information
            if hasattr(vat_rate_info, 'vat_exemption') and vat_rate_info.vat_exemption:
                row.vat_exemption_indicator = cls._apply_value_replacement(True, 'boolean_hu')
                
                # Handle both enum and string values for VAT exemption case
                exemption_case = vat_rate_info.vat_exemption.case if vat_rate_info.vat_exemption.case else None
                if exemption_case:
                    if hasattr(exemption_case, 'value'):
                        exemption_case_value = exemption_case.value
                    else:
                        exemption_case_value = str(exemption_case)
                else:
                    exemption_case_value = None
                    
                row.vat_exemption_case = cls._apply_value_replacement(
                    exemption_case_value,
                    'vat_exemption_case'
                )
                row.vat_exemption_reason = vat_rate_info.vat_exemption.reason
                
            # Out of scope VAT
            if hasattr(vat_rate_info, 'vat_out_of_scope') and vat_rate_info.vat_out_of_scope:
                row.out_of_scope_indicator = None # TODO never see as True
                
                # Handle both enum and string values for out of scope case
                out_of_scope_case = vat_rate_info.vat_out_of_scope.case if vat_rate_info.vat_out_of_scope.case else None
                if out_of_scope_case:
                    if hasattr(out_of_scope_case, 'value'):
                        out_of_scope_case_value = out_of_scope_case.value
                    else:
                        out_of_scope_case_value = str(out_of_scope_case)
                else:
                    out_of_scope_case_value = None
                    
                row.out_of_scope_case = cls._apply_value_replacement(
                    out_of_scope_case_value,
                    'vat_out_of_scope_case'
                )
                row.out_of_scope_reason = vat_rate_info.vat_out_of_scope.reason
                
            # Domestic reverse charge
            if hasattr(vat_rate_info, 'domestic_reverse_charge') and vat_rate_info.domestic_reverse_charge:
                row.domestic_reverse_charge_indicator = cls._apply_value_replacement(True, 'boolean_hu')
                
            # Margin scheme
            if hasattr(vat_rate_info, 'margin_scheme_vat') and vat_rate_info.margin_scheme_vat:
                row.margin_scheme_with_vat = cls._apply_value_replacement(True, 'boolean_hu')
                row.margin_scheme_indicator = cls._apply_value_replacement(
                    vat_rate_info.margin_scheme_vat.value if hasattr(vat_rate_info.margin_scheme_vat, 'value') else None,
                    'margin_scheme'
                )
                
            if hasattr(vat_rate_info, 'margin_scheme_no_vat') and vat_rate_info.margin_scheme_no_vat:
                row.margin_scheme_without_vat = cls._apply_value_replacement(True, 'boolean_hu')
                row.margin_scheme_indicator = cls._apply_value_replacement(
                    vat_rate_info.margin_scheme_no_vat.value if hasattr(vat_rate_info.margin_scheme_no_vat, 'value') else None,
                    'margin_scheme'
                )
                
        # VAT amounts - process this first to get the actual amounts
        actual_vat_amount = None
        if amounts_normal.line_vat_data:
            vat_data = amounts_normal.line_vat_data
            row.vat_amount_original = vat_data.line_vat_amount
            row.vat_amount_huf = vat_data.line_vat_amount_huf
            actual_vat_amount = vat_data.line_vat_amount
            
        # No VAT charge (section 17) - check for the indicator AND actual VAT amount
        if hasattr(vat_rate_info, 'no_vat_charge') and vat_rate_info.no_vat_charge:
            # Only set the indicator if there's truly no VAT charged (amount is 0 or None)
            is_vat_out_of_scope = hasattr(vat_rate_info, 'vat_out_of_scope') and vat_rate_info.vat_out_of_scope is not None
            has_vat_percentage =  vat_rate_info.vat_percentage is not None and vat_rate_info.vat_percentage != 0
            if not has_vat_percentage and not is_vat_out_of_scope:
                row.no_vat_charge_indicator = cls._apply_value_replacement(
                    True, 'boolean_hu'
                )
            else:
                row.no_vat_charge_indicator = None  # Leave as None (becomes nan in Excel)
        else:
            row.no_vat_charge_indicator = None  # Leave as None (becomes nan in Excel)
            
        # Gross amounts
        if amounts_normal.line_gross_amount_data:
            gross_data = amounts_normal.line_gross_amount_data
            row.gross_amount_original = gross_data.line_gross_amount_normal
            row.gross_amount_huf = gross_data.line_gross_amount_normal_huf
            
        # Calculate missing gross amounts if possible
        if not row.gross_amount_original and row.net_amount_original and row.vat_amount_original:
            row.gross_amount_original = row.net_amount_original + row.vat_amount_original
        if not row.gross_amount_huf and row.net_amount_huf and row.vat_amount_huf:
            row.gross_amount_huf = row.net_amount_huf + row.vat_amount_huf
    
    @classmethod
    def _map_line_amounts_simplified(cls, amounts_simplified: LineAmountsSimplifiedType, row: InvoiceLineRow) -> None:
        """Map simplified line amounts to row."""
        if hasattr(amounts_simplified, 'line_vat_rate') and amounts_simplified.line_vat_rate:
            vat_rate_obj = amounts_simplified.line_vat_rate
            
            # Set VAT rate percentage
            if hasattr(vat_rate_obj, 'vat_percentage') and vat_rate_obj.vat_percentage:
                row.vat_rate = vat_rate_obj.vat_percentage
            
            # Set VAT content for simplified invoices
            # VAT content = VAT rate / (1 + VAT rate) for simplified invoices
            if hasattr(vat_rate_obj, 'vat_content') and vat_rate_obj.vat_content is not None:
                row.vat_content = vat_rate_obj.vat_content
            elif hasattr(vat_rate_obj, 'vat_percentage') and vat_rate_obj.vat_percentage is not None:
                # Calculate VAT content from VAT percentage for simplified invoices
                # VAT content = VAT rate / (1 + VAT rate)
                vat_percentage = Decimal(str(vat_rate_obj.vat_percentage))
                if vat_percentage > 0:
                    vat_content = vat_percentage / (Decimal('1') + vat_percentage)
                    row.vat_content = str(vat_content)
                else:
                    row.vat_content = "0"
            
        if hasattr(amounts_simplified, 'line_gross_amount_simplified') and amounts_simplified.line_gross_amount_simplified:
            row.gross_amount_original = amounts_simplified.line_gross_amount_simplified
            
        if hasattr(amounts_simplified, 'line_gross_amount_simplified_huf') and amounts_simplified.line_gross_amount_simplified_huf:
            row.gross_amount_huf = amounts_simplified.line_gross_amount_simplified_huf

    @classmethod
    def _map_address_to_seller(cls, address: AddressType, row: InvoiceHeaderRow) -> None:
        """Map address data to seller fields."""
        if hasattr(address, 'detailed_address') and address.detailed_address:
            addr = address.detailed_address
            row.seller_country_code = addr.country_code
            row.seller_postal_code = addr.postal_code  
            row.seller_city = addr.city
            # Combine address details
            addr_parts = [addr.street_name, addr.public_place_category, addr.number, 
                         addr.building, addr.staircase, addr.floor, addr.door]
            row.seller_address_detail = ' '.join(filter(None, addr_parts))
        elif hasattr(address, 'simple_address') and address.simple_address:
            addr = address.simple_address
            row.seller_country_code = addr.country_code
            row.seller_postal_code = addr.postal_code
            row.seller_city = addr.city
            row.seller_address_detail = addr.additional_address_detail

    @classmethod  
    def _map_address_to_buyer(cls, address: AddressType, row: InvoiceHeaderRow) -> None:
        """Map address data to buyer fields."""
        if hasattr(address, 'detailed_address') and address.detailed_address:
            addr = address.detailed_address
            row.buyer_country_code = addr.country_code
            row.buyer_postal_code = addr.postal_code
            row.buyer_city = addr.city
            # Combine address details
            addr_parts = [addr.street_name, addr.public_place_category, addr.number,
                         addr.building, addr.staircase, addr.floor, addr.door]
            row.buyer_address_detail = ' '.join(filter(None, addr_parts))
        elif hasattr(address, 'simple_address') and address.simple_address:
            addr = address.simple_address
            row.buyer_country_code = addr.country_code
            row.buyer_postal_code = addr.postal_code
            row.buyer_city = addr.city
            row.buyer_address_detail = addr.additional_address_detail

    @classmethod
    def _parse_date(cls, date_str: Optional[str]) -> Optional[str]:
        """Parse date string and return as standardized string format."""
        if not date_str:
            return None
        try:
            # Parse and reformat to standard format
            parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            return parsed_date.strftime('%Y-%m-%d')
        except ValueError:
            try:
                parsed_date = datetime.strptime(date_str[:10], '%Y-%m-%d').date()
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                logger.warning(f"Could not parse date: {date_str}")
                return None

    @classmethod
    def _format_date(cls, date_obj: Optional[Union[date, str]]) -> Optional[str]:
        """Format date object to string."""
        if not date_obj:
            return None
        
        # If it's already a string, return as-is
        if isinstance(date_obj, str):
            return date_obj
            
        # If it's a date object, format it
        if isinstance(date_obj, date):
            return date_obj.strftime('%Y-%m-%d')
            
        # Try to convert other types
        try:
            return str(date_obj)
        except:
            return None

    @classmethod
    def header_row_to_invoice_data(cls, row: InvoiceHeaderRow, line_rows: Optional[List[InvoiceLineRow]] = None) -> Tuple[InvoiceData, ManageInvoiceOperationType]:
        """
        Convert InvoiceHeaderRow back to InvoiceData object (for import).
        
        This is a complex reverse mapping that reconstructs the nested structure.
        
        Args:
            row: InvoiceHeaderRow with flat Excel data
            line_rows: List of InvoiceLineRow objects for VAT rate aggregation
            
        Returns:
            Tuple[InvoiceData, ManageInvoiceOperationType]: Reconstructed invoice data
        """
        try:
            # Create basic InvoiceData structure
            invoice_data = InvoiceData(
                invoice_number=row.invoice_number,
                invoice_issue_date=cls._format_date(row.invoice_issue_date),
                completeness_indicator=row.completeness_indicator or False
            )
            
            # Create invoice head from header row
            invoice_head = cls._build_invoice_head_from_row(row)
            
            # Create invoice summary from header row and lines
            invoice_summary = cls._build_invoice_summary_from_row(row, line_rows)
            
            # Create invoice reference if modification data exists
            invoice_reference = None
            if row.original_invoice_number or row.modification_date or row.modification_index:
                invoice_reference = cls._build_invoice_reference_from_row(row)
            
            # Create main invoice structure
            invoice = InvoiceType(
                invoice_head=invoice_head,
                invoice_summary=invoice_summary,
                invoice_reference=invoice_reference,
                # Lines will be added separately by the importer
                invoice_lines=None
            )
            
            invoice_main = InvoiceMainType(invoice=invoice)
            invoice_data.invoice_main = invoice_main
            
            # Determine operation type based on modification fields
            # If original_invoice_number is present, this is a modification invoice
            if row.original_invoice_number and row.original_invoice_number.strip():
                operation_type = ManageInvoiceOperationType.MODIFY
            else:
                operation_type = ManageInvoiceOperationType.CREATE
            
            return invoice_data, operation_type
            
        except Exception as e:
            logger.error(f"Failed to convert header row to InvoiceData: {e}")
            raise ExcelMappingException(f"Header conversion failed: {e}")

    @classmethod
    def line_rows_to_invoice_lines(cls, rows: List[InvoiceLineRow], is_modification: bool = False, invoice_category: str = None) -> LinesType:
        """
        Convert InvoiceLineRow objects to LinesType structure (for import).
        
        This reconstructs the line items structure from flat Excel data.
        
        Args:
            rows: List of InvoiceLineRow objects
            is_modification: Whether this is a modification invoice (MODIFY operation)
            invoice_category: Invoice category to determine line amounts structure
            
        Returns:
            LinesType: Reconstructed lines structure
        """
        try:
            lines = []
            
            for row in rows:
                line = cls._build_line_from_row(row, is_modification=is_modification, invoice_category=invoice_category)
                if line:
                    lines.append(line)
            
            return LinesType(merged_item_indicator=False, line=lines) if lines else None
            
        except Exception as e:
            logger.error(f"Failed to convert line rows to LinesType: {e}")
            raise ExcelMappingException(f"Lines conversion failed: {e}")

    @classmethod
    def _build_invoice_head_from_row(cls, row: InvoiceHeaderRow) -> InvoiceHeadType:
        """Build InvoiceHeadType from header row data."""
        # Supplier info
        supplier_info = None
        if any([row.seller_name, row.seller_tax_number_main, row.seller_country_code]):
            supplier_tax_number = None
            if row.seller_tax_number_main:
                supplier_tax_number = TaxNumberType(
                    taxpayer_id=cls._format_taxpayer_id(row.seller_tax_number_main),
                    vat_code=cls._format_vat_code(row.seller_tax_number_vat),
                    county_code=cls._format_county_code(row.seller_tax_number_county)
                )
            
            supplier_address = None
            if any([row.seller_country_code, row.seller_postal_code, row.seller_city]):
                supplier_address = cls._build_address_from_seller_fields(row)
            
            supplier_info = SupplierInfoType(
                supplier_tax_number=supplier_tax_number,
                supplier_name=row.seller_name,
                supplier_address=supplier_address
            )
        
        # Customer info - ALWAYS required for CREATE operations per NAV API
        # Create customer VAT data if we have tax info or VAT numbers
        customer_vat_data = None
        if any([row.buyer_tax_number_main, row.buyer_community_vat_number, row.buyer_third_country_tax_number]):
            customer_tax_number = None
            if row.buyer_tax_number_main:
                customer_tax_number = CustomerTaxNumberType(
                    taxpayer_id=cls._format_taxpayer_id(row.buyer_tax_number_main),
                    vat_code=cls._format_vat_code(row.buyer_tax_number_vat),
                    county_code=cls._format_county_code(row.buyer_tax_number_county)
                )
            
            customer_vat_data = CustomerVatDataType(
                customer_tax_number=customer_tax_number,
                community_vat_number=row.buyer_community_vat_number,
                third_state_tax_id=row.buyer_third_country_tax_number
            )

        # Parse VAT status - determine appropriate status based on available data
        customer_vat_status = CustomerVatStatusType.PRIVATE_PERSON  # Default to PRIVATE_PERSON as most permissive
        if row.buyer_vat_status:
            try:
                # First try to map Hungarian descriptions
                customer_vat_status = cls._map_hungarian_vat_status(row.buyer_vat_status)
            except ValueError:
                logger.warning(f"Invalid customer VAT status: {row.buyer_vat_status}")
                customer_vat_status = CustomerVatStatusType.PRIVATE_PERSON
        elif row.buyer_tax_number_main:
            # If we have a Hungarian tax number, likely DOMESTIC
            customer_vat_status = CustomerVatStatusType.DOMESTIC
        elif row.buyer_community_vat_number:
            # If we have EU VAT number, OTHER (foreign VAT subject) 
            customer_vat_status = CustomerVatStatusType.OTHER
        elif any([row.buyer_name, row.buyer_country_code, row.buyer_postal_code]):
            # If we have some customer data but no tax info, use PRIVATE_PERSON
            # This is the safest option for minimal data as NAV is more lenient
            customer_vat_status = CustomerVatStatusType.PRIVATE_PERSON
        # else: keep PRIVATE_PERSON as default for missing data
        
        # Determine customer name - use available data or provide default
        customer_name = row.buyer_name
        if not customer_name or str(customer_name).lower() in ['nan', 'n/a', '']:
            customer_name = "N/A"  # Minimal required data when buyer name is missing
        
        # Customer address - only provide if NOT PRIVATE_PERSON (privacy restrictions)
        customer_address = None
        if customer_vat_status != CustomerVatStatusType.PRIVATE_PERSON:
            if any([row.buyer_country_code, row.buyer_postal_code, row.buyer_city]):
                customer_address = cls._build_address_from_buyer_fields(row)
        
        # For PRIVATE_PERSON: Only provide customerVatStatus, no name or address for privacy
        # For OTHER/DOMESTIC: Can provide address and VAT data as needed
        if customer_vat_status == CustomerVatStatusType.PRIVATE_PERSON:
            # Private person - provide only status, no name or address for privacy protection
            customer_info = CustomerInfoType(
                customer_vat_status=customer_vat_status
            )
        else:
            # Business customer - can provide full data including address and VAT info
            customer_info = CustomerInfoType(
                customer_vat_status=customer_vat_status,
                customer_vat_data=customer_vat_data,
                customer_name=customer_name,
                customer_address=customer_address
            )
        
        # Parse payment method
        payment_method = None
        if row.payment_method:
            try:
                # First try to map Hungarian descriptions
                payment_method = cls._map_hungarian_payment_method(row.payment_method)
            except ValueError:
                logger.warning(f"Invalid payment method: {row.payment_method}")
                payment_method = PaymentMethodType.OTHER
        
        # Parse invoice category - NAV schema requires this field early in structure
        invoice_category = None
        if row.invoice_category:
            try:
                # First try to map Hungarian descriptions
                invoice_category = cls._map_hungarian_invoice_category(row.invoice_category)
            except ValueError:
                logger.warning(f"Invalid invoice category: {row.invoice_category}")
                invoice_category = InvoiceCategoryType.NORMAL
        else:
            # Default to NORMAL if not provided  
            invoice_category = InvoiceCategoryType.NORMAL
        
        # Create invoice detail with proper fields
        payment_method_enum = None
        if row.payment_method:
            try:
                # First try to map Hungarian descriptions
                payment_method_enum = cls._map_hungarian_payment_method(row.payment_method)
            except ValueError:
                payment_method_enum = PaymentMethodType.OTHER
                
        invoice_detail = InvoiceDetailType(
            invoice_category=invoice_category,
            invoice_delivery_date=cls._format_date(row.fulfillment_date),
            payment_date=cls._format_date(row.payment_due_date),
            payment_method=payment_method_enum,
            currency_code=row.invoice_currency or "HUF",
            exchange_rate=row.exchange_rate or Decimal("1.0"),
            small_business_indicator=row.small_business_indicator or False,
            cash_accounting_indicator=row.cash_accounting_indicator or False,
            invoice_appearance=InvoiceAppearanceType.ELECTRONIC  # Required field: indicates electronic invoice
        )
        
        return InvoiceHeadType(
            supplier_info=supplier_info,
            customer_info=customer_info,
            invoice_detail=invoice_detail
        )

    @classmethod
    def _build_invoice_summary_from_row(cls, row: InvoiceHeaderRow, line_rows: Optional[List[InvoiceLineRow]] = None) -> SummaryType:
        """Build SummaryType from header row data and invoice lines."""
        # Determine if this is a simplified invoice
        is_simplified = (row.invoice_category and 
                        ('egyszerűsített' in row.invoice_category.lower() or 
                         'simplified' in row.invoice_category.lower()))
        
        if is_simplified:
            # For simplified invoices, use SummarySimplified structure
            # Calculate VAT content from header amounts, consistent with line-level logic

            summary_simplified_list = []
            
            vat_rate_groups = cls._group_lines_by_vat_rate(line_rows)
            
            if vat_rate_groups:
                # If we have line rows, aggregate by VAT rate
                for vat_key, lines_in_group in vat_rate_groups.items():
                    # Aggregate amounts for this VAT rate group
                    total_gross = sum(line.gross_amount_original or Decimal("0") for line in lines_in_group)
                    total_gross_huf = sum(line.gross_amount_huf or Decimal("0") for line in lines_in_group)
                    
                    if vat_key[0] == 'vat_content' and vat_key[1] is not None:
                        vat_rate = cls._create_vat_rate_from_key(vat_key)
                    else:
                        raise Exception(f"We expect vat_content key for simplified invoices, got: {vat_key}, values: {vat_key[1]}")

                    summary_simplified = SummarySimplifiedType(
                        vat_rate=vat_rate,
                        vat_content_gross_amount=total_gross,
                        vat_content_gross_amount_huf=total_gross_huf
                    )
                    summary_simplified_list.append(summary_simplified)
            else:
                # No line rows provided, create a default entry from header data
                # Assume standard VAT rate for simplified invoices
                default_vat_rate = VatRateType(
                    vat_percentage=None,
                    vat_content=Decimal("0.27"),  # Default 27% VAT content for Hungary
                    vat_exemption=None,
                    vat_out_of_scope=None,
                    margin_scheme_indicator=None,
                    vat_amount_mismatch=None
                )
                object.__setattr__(default_vat_rate, 'vat_domestic_reverse_charge', None)
                object.__setattr__(default_vat_rate, 'no_vat_charge', None)
                
                summary_simplified = SummarySimplifiedType(
                    vat_rate=default_vat_rate,
                    vat_content_gross_amount=row.gross_amount_original or Decimal("0"),
                    vat_content_gross_amount_huf=row.gross_amount_huf or Decimal("0")
                )
                summary_simplified_list.append(summary_simplified)

            summary_gross = SummaryGrossDataType(
                invoice_gross_amount=row.gross_amount_original,
                invoice_gross_amount_huf=row.gross_amount_huf
            )
            
            return SummaryType(
                summary_simplified=summary_simplified_list,
                summary_gross_data=summary_gross
            )
        else:
            # For normal invoices, use SummaryNormal structure
            # If line rows are provided, aggregate by VAT rate, otherwise use header data
            summary_by_vat_rate_list = []
            
            vat_rate_groups = cls._group_lines_by_vat_rate(line_rows)
            
            if vat_rate_groups:
                # If we have line rows, aggregate by VAT rate
                for vat_key, lines_in_group in vat_rate_groups.items():
                    # Aggregate amounts for this VAT rate group
                    total_net = sum(line.net_amount_original or Decimal("0") for line in lines_in_group)
                    total_net_huf = sum(line.net_amount_huf or Decimal("0") for line in lines_in_group)
                    total_vat = sum(line.vat_amount_original or Decimal("0") for line in lines_in_group)
                    total_vat_huf = sum(line.vat_amount_huf or Decimal("0") for line in lines_in_group)
                    total_gross = sum(line.gross_amount_original or Decimal("0") for line in lines_in_group)
                    total_gross_huf = sum(line.gross_amount_huf or Decimal("0") for line in lines_in_group)
                    
                    # Create VatRateType from the VAT key
                    vat_rate = cls._create_vat_rate_from_key(vat_key)
                    
                    # Create the summary entry for this VAT rate
                    summary_by_vat_rate = SummaryByVatRateType(
                        vat_rate=vat_rate,
                        vat_rate_net_data=VatRateNetDataType(
                            vat_rate_net_amount=total_net,
                            vat_rate_net_amount_huf=total_net_huf
                        ),
                        vat_rate_vat_data=VatRateVatDataType(
                            vat_rate_vat_amount=total_vat,
                            vat_rate_vat_amount_huf=total_vat_huf
                        ),
                        vat_rate_gross_data=VatRateGrossDataType(
                            vat_rate_gross_amount=total_gross,
                            vat_rate_gross_amount_huf=total_gross_huf
                        )
                    )
                    summary_by_vat_rate_list.append(summary_by_vat_rate)
            else:
                # No line rows provided, create a default entry from header data
                # Assume standard 27% VAT rate for Hungary
                default_vat_rate = VatRateType(vat_percentage=Decimal("0.27"))
                
                summary_by_vat_rate = SummaryByVatRateType(
                    vat_rate=default_vat_rate,
                    vat_rate_net_data=VatRateNetDataType(
                        vat_rate_net_amount=row.net_amount_original or Decimal("0"),
                        vat_rate_net_amount_huf=row.net_amount_huf or Decimal("0")
                    ),
                    vat_rate_vat_data=VatRateVatDataType(
                        vat_rate_vat_amount=row.vat_amount_original or Decimal("0"),
                        vat_rate_vat_amount_huf=row.vat_amount_huf or Decimal("0")
                    ),
                    vat_rate_gross_data=VatRateGrossDataType(
                        vat_rate_gross_amount=row.gross_amount_original or Decimal("0"),
                        vat_rate_gross_amount_huf=row.gross_amount_huf or Decimal("0")
                    )
                )
                summary_by_vat_rate_list.append(summary_by_vat_rate)
            
            summary_normal = SummaryNormalType(
                summary_by_vat_rate=summary_by_vat_rate_list,  # Now contains multiple entries
                invoice_net_amount=row.net_amount_original,
                invoice_net_amount_huf=row.net_amount_huf,
                invoice_vat_amount=row.vat_amount_original,
                invoice_vat_amount_huf=row.vat_amount_huf
            )
            summary_gross = SummaryGrossDataType(
                invoice_gross_amount=row.gross_amount_original,
                invoice_gross_amount_huf=row.gross_amount_huf
            )
            return SummaryType(
                summary_normal=summary_normal,
                summary_gross_data=summary_gross
            )

    @classmethod
    def _group_lines_by_vat_rate(cls, line_rows: Optional[List[InvoiceLineRow]]) -> dict:
        """
        Group invoice lines by their VAT rate characteristics.
        
        Args:
            line_rows: List of invoice line rows (can be None)
            
        Returns:
            dict: Dictionary with VAT rate key as key and list of lines as value
        """
        groups = {}
        
        # Handle None or empty list case
        if not line_rows:
            return groups
        
        for line in line_rows:
            # Create a key that uniquely identifies the VAT rate characteristics
            vat_key = cls._create_vat_rate_key(line)
            
            if vat_key not in groups:
                groups[vat_key] = []
            groups[vat_key].append(line)
        
        return groups
    
    @classmethod
    def _create_vat_rate_key(cls, line: InvoiceLineRow) -> tuple:
        """
        Create a unique key for grouping lines by VAT rate characteristics.
        
        Args:
            line: Invoice line row
            
        Returns:
            tuple: Unique key representing the VAT rate characteristics
        """
        # Handle no VAT charge (EU transactions)
        if line.no_vat_charge_indicator:
            return ('no_vat_charge',)
        
        # Handle out of scope VAT
        if line.out_of_scope_indicator or line.out_of_scope_case:
            return ('out_of_scope', line.out_of_scope_case, line.out_of_scope_reason or '')
        
        # Handle VAT exemption
        if line.vat_exemption_indicator or line.vat_exemption_case:
            return ('vat_exemption', line.vat_exemption_case, line.vat_exemption_reason or '')
        
        # Handle VAT percentage (most common case)
        if line.vat_rate is not None:
            normalized_rate = cls._normalize_vat_percentage(line.vat_rate)
            return ('vat_percentage', normalized_rate)
        
        # Handle VAT content (for simplified invoices, but can appear in normal invoices too)
        if line.vat_content is not None:
            try:
                if isinstance(line.vat_content, str):
                    vat_content_decimal = Decimal(line.vat_content.strip())
                else:
                    vat_content_decimal = Decimal(str(line.vat_content))
                normalized_content = cls._normalize_vat_percentage(vat_content_decimal)
                return ('vat_content', normalized_content)
            except (ValueError, TypeError, ArithmeticError):
                pass
        
        # Default case - assume 0% VAT
        return ('vat_percentage', Decimal('0.0'))
    
    @classmethod
    def _create_vat_rate_from_key(cls, vat_key: tuple) -> VatRateType:
        """
        Create a VatRateType object from a VAT rate key and sample line.
        
        Args:
            vat_key: Tuple representing VAT rate characteristics
            sample_line: Sample line from the group for extracting detailed information
            
        Returns:
            VatRateType: Properly configured VAT rate object
        """
        key_type = vat_key[0]
        
        if key_type == 'no_vat_charge':
            vat_rate = VatRateType()
            vat_rate.no_vat_charge = True
            # Manually ensure other init=False fields are not serialized
            object.__setattr__(vat_rate, 'vat_domestic_reverse_charge', None)
            return vat_rate
        
        elif key_type == 'out_of_scope':
            case = vat_key[1]
            reason = vat_key[2]
            out_of_scope_reason = DetailedReasonType(case=case, reason=reason)
            vat_rate = VatRateType(
                vat_percentage=None,
                vat_content=None,
                vat_exemption=None,
                vat_out_of_scope=out_of_scope_reason,
                margin_scheme_indicator=None,
                vat_amount_mismatch=None
            )
            # Manually override the init=False fields
            object.__setattr__(vat_rate, 'vat_domestic_reverse_charge', None)
            object.__setattr__(vat_rate, 'no_vat_charge', None)
            return vat_rate
        
        elif key_type == 'vat_exemption':
            case = vat_key[1]
            reason = vat_key[2]
            exemption_reason = DetailedReasonType(case=case, reason=reason)
            vat_rate = VatRateType(
                vat_percentage=None,
                vat_content=None,
                vat_exemption=exemption_reason,
                vat_out_of_scope=None,
                margin_scheme_indicator=None,
                vat_amount_mismatch=None
            )
            # Manually override the init=False fields
            object.__setattr__(vat_rate, 'vat_domestic_reverse_charge', None)
            object.__setattr__(vat_rate, 'no_vat_charge', None)
            return vat_rate
        
        elif key_type == 'vat_percentage':
            percentage = vat_key[1]
            return VatRateType(vat_percentage=percentage)
        
        elif key_type == 'vat_content':
            content = vat_key[1]
            vat_rate = VatRateType(
                vat_percentage=None,
                vat_content=content,
                vat_exemption=None,
                vat_out_of_scope=None,
                margin_scheme_indicator=None,
                vat_amount_mismatch=None
            )
            # Manually ensure other init=False fields are not serialized
            object.__setattr__(vat_rate, 'vat_domestic_reverse_charge', None)
            object.__setattr__(vat_rate, 'no_vat_charge', None)
            return vat_rate
        
        # Default fallback
        return VatRateType(vat_percentage=Decimal('0.0'))

    @classmethod
    def _create_vat_rate_from_line_row(cls, row: InvoiceLineRow, is_simplified: bool = False) -> VatRateType:
        """
        Create a VatRateType object directly from an InvoiceLineRow.
        
        This method consolidates the VAT rate creation logic to avoid duplication
        between line-level and summary-level processing.
        
        Args:
            row: Invoice line row containing VAT information
            is_simplified: Whether this is for a simplified invoice
            
        Returns:
            VatRateType: Properly configured VAT rate object
        """
        # Handle no VAT charge (EU transactions)
        if row.no_vat_charge_indicator:
            line_vat_rate = VatRateType()
            line_vat_rate.no_vat_charge = True
            # Manually ensure other init=False fields are not serialized
            try:
                delattr(line_vat_rate, 'vat_domestic_reverse_charge')
            except AttributeError:
                line_vat_rate.vat_domestic_reverse_charge = None
            return line_vat_rate
        
        # Handle out of scope VAT
        # line.out_of_scope_indicator or line.out_of_scope_case
        elif row.out_of_scope_indicator or row.out_of_scope_case:
            out_of_scope_reason = DetailedReasonType(
                case=row.out_of_scope_case.strip(),
                reason=row.out_of_scope_reason or ""
            )
            line_vat_rate = VatRateType(
                vat_percentage=None,
                vat_content=None,
                vat_exemption=None,
                vat_out_of_scope=out_of_scope_reason,
                margin_scheme_indicator=None,
                vat_amount_mismatch=None
            )
            # Manually override the init=False fields to prevent them from being serialized
            object.__setattr__(line_vat_rate, 'vat_domestic_reverse_charge', None)
            object.__setattr__(line_vat_rate, 'no_vat_charge', None)
            return line_vat_rate
        
        # Handle VAT exemption
        elif row.vat_exemption_indicator or row.vat_exemption_case:
            exemption_reason = DetailedReasonType(
                case=row.vat_exemption_case.strip(),
                reason=row.vat_exemption_reason or ""
            )
            line_vat_rate = VatRateType(
                vat_percentage=None,
                vat_content=None,
                vat_exemption=exemption_reason,
                vat_out_of_scope=None,
                margin_scheme_indicator=None,
                vat_amount_mismatch=None
            )
            object.__setattr__(line_vat_rate, 'vat_domestic_reverse_charge', None)
            object.__setattr__(line_vat_rate, 'no_vat_charge', None)
            return line_vat_rate
        
        # Handle VAT content (for simplified invoices or when explicitly provided)
        elif row.vat_content is not None:
            try:
                # Convert string to Decimal first
                if isinstance(row.vat_content, str):
                    vat_content_decimal = Decimal(row.vat_content.strip())
                else:
                    vat_content_decimal = Decimal(str(row.vat_content))
                
                # Normalize using the existing function
                vat_content_value = cls._normalize_vat_percentage(vat_content_decimal)
                
                line_vat_rate = VatRateType(
                    vat_percentage=None,
                    vat_content=vat_content_value,
                    vat_exemption=None,
                    vat_out_of_scope=None,
                    margin_scheme_indicator=None,
                    vat_amount_mismatch=None
                )
                # Manually ensure other init=False fields are not serialized
                object.__setattr__(line_vat_rate, 'vat_domestic_reverse_charge', None)
                object.__setattr__(line_vat_rate, 'no_vat_charge', None)
                return line_vat_rate
            except (ValueError, TypeError, ArithmeticError) as e:
                logger.warning(f"Invalid vat_content value: {row.vat_content}, error: {e}, using 0.0")
                # Fall through to use vat_rate or default
        
        # Handle standard VAT percentage
        if row.vat_rate is not None:
            normalized_vat_rate = cls._normalize_vat_percentage(row.vat_rate)
            # For simplified invoices, use vatContent instead of vatPercentage
            if is_simplified:
                line_vat_rate = VatRateType(
                    vat_percentage=None,
                    vat_content=normalized_vat_rate,
                    vat_exemption=None,
                    vat_out_of_scope=None,
                    margin_scheme_indicator=None,
                    vat_amount_mismatch=None
                )
                object.__setattr__(line_vat_rate, 'vat_domestic_reverse_charge', None)
                object.__setattr__(line_vat_rate, 'no_vat_charge', None)
                return line_vat_rate
            else:
                return VatRateType(vat_percentage=normalized_vat_rate)
        
        # Default fallback - use 0% VAT
        if is_simplified:
            line_vat_rate = VatRateType(
                vat_percentage=None,
                vat_content=Decimal("0.0"),
                vat_exemption=None,
                vat_out_of_scope=None,
                margin_scheme_indicator=None,
                vat_amount_mismatch=None
            )
            object.__setattr__(line_vat_rate, 'vat_domestic_reverse_charge', None)
            object.__setattr__(line_vat_rate, 'no_vat_charge', None)
            return line_vat_rate
        else:
            return VatRateType(vat_percentage=Decimal('0.0'))

    @classmethod
    def _build_invoice_reference_from_row(cls, row: InvoiceHeaderRow) -> InvoiceReferenceType:
        """Build InvoiceReferenceType from header row data."""
        return InvoiceReferenceType(
            original_invoice_number=row.original_invoice_number,
            modify_without_master=False,  # Default value - assuming we have master data
            modification_index=row.modification_index
        )

    @classmethod
    def _build_line_from_row(cls, row: InvoiceLineRow, is_modification: bool = False, invoice_category: str = None) -> LineType:
        """Build LineType from line row data."""
        # Parse line operation type
        line_operation = None
        if row.line_modification_type:
            try:
                line_operation = LineOperationType(row.line_modification_type)
            except ValueError:
                logger.warning(f"Invalid line operation: {row.line_modification_type}")
                line_operation = LineOperationType.CREATE
        else:
            # For modification invoices, default to MODIFY if no specific type is given
            # For regular invoices, default to CREATE
            if is_modification:
                line_operation = LineOperationType.MODIFY  # #TODO: Hardcoded for modification invoices
            else:
                line_operation = LineOperationType.CREATE
        
        # Parse unit of measure
        unit_of_measure = None
        unit_of_measure_own = None
        if row.unit_of_measure:
            try:
                unit_of_measure = UnitOfMeasureType(row.unit_of_measure)
                # If using OWN unit of measure, we need to provide a custom description
                if unit_of_measure == UnitOfMeasureType.OWN:
                    unit_of_measure_own = "darab"  # Default Hungarian unit, or use description from Excel
            except ValueError:
                logger.warning(f"Invalid unit of measure: {row.unit_of_measure}")
                # Fallback to PIECE if invalid
                unit_of_measure = UnitOfMeasureType.PIECE
        
        # Determine if this is a simplified invoice
        is_simplified = (invoice_category and 
                        ('egyszerűsített' in invoice_category.lower() or 
                         'simplified' in invoice_category.lower()))
        
        # Build line amounts based on invoice category
        line_amounts_normal = None
        line_amounts_simplified = None
        
        if is_simplified:
            # For simplified invoices, use LineAmountsSimplified structure
            if row.gross_amount_original is not None:
                # Create VAT rate using the consolidated helper method
                line_vat_rate = cls._create_vat_rate_from_line_row(row, is_simplified=True)
                
                line_amounts_simplified = LineAmountsSimplifiedType(
                    line_vat_rate=line_vat_rate,
                    line_gross_amount_simplified=row.gross_amount_original,
                    line_gross_amount_simplified_huf=row.gross_amount_huf
                )
        else:
            # For normal invoices, use LineAmountsNormal structure  
            if any([row.net_amount_original, row.vat_amount_original, row.gross_amount_original]):
                # Net amount data
                line_net_amount = None
                if row.net_amount_original is not None or row.net_amount_huf is not None:
                    line_net_amount = LineNetAmountDataType(
                        line_net_amount=row.net_amount_original,
                        line_net_amount_huf=row.net_amount_huf
                    )
                
                # VAT rate - use the consolidated helper method
                line_vat_rate = cls._create_vat_rate_from_line_row(row, is_simplified=False)
                
                # VAT data - only include VAT amount data if NOT out of VAT scope
                line_vat_data = None
                if (row.vat_amount_original is not None or row.vat_amount_huf is not None) and \
                   not (row.out_of_scope_case and row.out_of_scope_case.strip().upper() == 'ATK'):
                    line_vat_data = LineVatDataType(
                        line_vat_amount=row.vat_amount_original,
                        line_vat_amount_huf=row.vat_amount_huf
                    )
                else: 
                    line_vat_data = LineVatDataType(
                        line_vat_amount=0,
                        line_vat_amount_huf=0
                    )
                
                # Gross amount data
                line_gross_amount_data = None
                if row.gross_amount_original is not None or row.gross_amount_huf is not None:
                    line_gross_amount_data = LineGrossAmountDataType(
                        line_gross_amount_normal=row.gross_amount_original,
                        line_gross_amount_normal_huf=row.gross_amount_huf
                    )
                
                line_amounts_normal = LineAmountsNormalType(
                    line_net_amount_data=line_net_amount,
                    line_vat_rate=line_vat_rate,
                    line_vat_data=line_vat_data,
                    line_gross_amount_data=line_gross_amount_data
                )
        
        # Build line modification reference if needed
        line_modification_reference = None
        if is_modification:
            # For modification invoices, always create modification reference - NAV requirement
            # Use modified_line_number (from "Módosítással érintett tétel sorszáma") as the reference
            reference_line_number = row.modified_line_number if row.modified_line_number else (row.line_number or 1)  # #TODO: Fallback to current line number
            line_modification_reference = LineModificationReferenceType(
                line_number_reference=reference_line_number,
                line_operation=line_operation or LineOperationType.MODIFY  # #TODO: Hardcoded modification type
            )
        elif line_operation and line_operation != LineOperationType.CREATE:
            # For non-modification invoices, only create if explicitly set
            line_modification_reference = LineModificationReferenceType(
                line_number_reference=row.line_number or 1,
                line_operation=line_operation
            )
        
        return LineType(
            line_number=row.line_number or 1,
            line_modification_reference=line_modification_reference,
            line_expression_indicator=False,  # Required field: indicates if line has quantity expression
            line_description=row.description,
            quantity=row.quantity,
            unit_of_measure=unit_of_measure,
            unit_of_measure_own=unit_of_measure_own,  # Required when unit_of_measure = OWN
            unit_price=row.unit_price,
            line_amounts_normal=line_amounts_normal,
            line_amounts_simplified=line_amounts_simplified
        )

    @classmethod
    def _build_address_from_seller_fields(cls, row: InvoiceHeaderRow) -> AddressType:
        """Build AddressType from seller fields."""
        if not any([row.seller_country_code, row.seller_postal_code, row.seller_city]):
            return None
        
        # Use simple address for basic data
        simple_address = SimpleAddressType(
            country_code=row.seller_country_code,
            postal_code=cls._format_postal_code(row.seller_postal_code) or "0000",
            city=row.seller_city,
            additional_address_detail=row.seller_address_detail
        )
        
        return AddressType(simple_address=simple_address)

    @classmethod
    def _build_address_from_buyer_fields(cls, row: InvoiceHeaderRow) -> AddressType:
        """Build AddressType from buyer fields."""
        if not any([row.buyer_country_code, row.buyer_postal_code, row.buyer_city]):
            return None
        
        # Use simple address for basic data
        simple_address = SimpleAddressType(
            country_code=row.buyer_country_code,
            postal_code=cls._format_postal_code(row.buyer_postal_code) or "0000",
            city=row.buyer_city,
            additional_address_detail=row.buyer_address_detail
        )
        
        return AddressType(simple_address=simple_address)
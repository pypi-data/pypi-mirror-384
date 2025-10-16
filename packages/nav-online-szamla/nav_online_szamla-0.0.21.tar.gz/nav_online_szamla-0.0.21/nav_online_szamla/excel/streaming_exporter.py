"""
Streaming Excel exporter for memory-efficient invoice export.

This module provides functionality to export large volumes of invoice data
to Excel files without loading all data into memory at once.
"""

import logging
from pathlib import Path
from typing import Iterator, Tuple, Optional

try:
    import xlsxwriter
    XLSXWRITER_AVAILABLE = True
except ImportError:
    XLSXWRITER_AVAILABLE = False
    xlsxwriter = None

from ..models import InvoiceData, ManageInvoiceOperationType
from .exceptions import ExcelProcessingException
from .mapper import ExcelFieldMapper
from .models import InvoiceHeaderRow, InvoiceLineRow

logger = logging.getLogger(__name__)


class StreamingInvoiceExcelExporter:
    """
    Memory-efficient streaming Excel exporter for large invoice datasets.
    
    This exporter writes invoice data directly to Excel file without loading
    all data into memory. It processes invoices one at a time from an iterator.
    
    Uses xlsxwriter for better streaming performance compared to openpyxl.
    """
    
    def __init__(self):
        """Initialize the streaming Excel exporter."""
        if not XLSXWRITER_AVAILABLE:
            raise ImportError(
                "xlsxwriter is required for streaming export. "
                "Install it with: pip install xlsxwriter"
            )
        
        self.mapper = ExcelFieldMapper()
    
    def export_to_excel_streaming(
        self,
        invoice_iterator: Iterator[Tuple[InvoiceData, ManageInvoiceOperationType]],
        file_path: str,
        include_operation_type: bool = False,
        total_count: Optional[int] = None
    ) -> Tuple[int, int]:
        """
        Export invoice data to Excel file using streaming/append mode.
        
        This method processes invoices one at a time without loading all data
        into memory, making it suitable for very large datasets (millions of invoices).
        
        Args:
            invoice_iterator: Iterator that yields (InvoiceData, operation_type) tuples
            file_path: Path where the Excel file should be saved
            include_operation_type: Whether to include operation type as a column
            total_count: Optional total count for progress logging
            
        Returns:
            Tuple[int, int]: (number of headers written, number of lines written)
            
        Raises:
            ExcelProcessingException: If export fails
        """
        try:
            logger.info(f"Starting streaming Excel export to {file_path}")
            if total_count:
                logger.info(f"Expected to process approximately {total_count} invoices")
            
            # Create parent directory if needed
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Create workbook with xlsxwriter
            workbook = xlsxwriter.Workbook(file_path, {'constant_memory': True})
            
            # Create worksheets
            header_sheet = workbook.add_worksheet("Fejléc adatok")
            lines_sheet = workbook.add_worksheet("Tétel adatok")
            
            # Define column mappings
            header_columns = self._get_header_columns(include_operation_type)
            lines_columns = self._get_lines_columns(include_operation_type)
            
            # Write headers to both sheets
            self._write_sheet_headers(header_sheet, list(header_columns.values()))
            self._write_sheet_headers(lines_sheet, list(lines_columns.values()))
            
            # Track row numbers (1-indexed, 0 is header)
            header_row = 1
            line_row = 1
            
            # Process invoices one at a time
            processed_count = 0
            error_count = 0
            
            for invoice_data, operation_type in invoice_iterator:
                try:
                    # Convert to row structures
                    header_row_obj = self.mapper.invoice_data_to_header_row(
                        invoice_data, operation_type
                    )
                    line_row_objs = self.mapper.invoice_data_to_line_rows(
                        invoice_data, operation_type
                    )
                    
                    # Write header row
                    self._write_header_row(
                        header_sheet, header_row, header_row_obj, 
                        header_columns, include_operation_type
                    )
                    header_row += 1
                    
                    # Write line rows
                    for line_row_obj in line_row_objs:
                        self._write_line_row(
                            lines_sheet, line_row, line_row_obj,
                            lines_columns, include_operation_type
                        )
                        line_row += 1
                    
                    processed_count += 1
                    
                    # Log progress every 1000 invoices
                    if processed_count % 1000 == 0:
                        if total_count:
                            progress_pct = (processed_count / total_count) * 100
                            logger.info(
                                f"Progress: {processed_count}/{total_count} "
                                f"({progress_pct:.1f}%) invoices processed"
                            )
                        else:
                            logger.info(f"Progress: {processed_count} invoices processed")
                
                except Exception as e:
                    # Log error but continue processing
                    error_count += 1
                    invoice_id = getattr(invoice_data, 'invoice_number', 'unknown')
                    logger.warning(
                        f"Failed to process invoice {invoice_id}: {e}. "
                        f"Continuing with next invoice..."
                    )
            
            # Close workbook (finalizes the file)
            workbook.close()
            
            headers_written = header_row - 1  # Subtract header row
            lines_written = line_row - 1  # Subtract header row
            
            logger.info(
                f"Streaming export completed: {headers_written} headers, "
                f"{lines_written} line items written to {file_path}"
            )
            
            if error_count > 0:
                logger.warning(f"Encountered {error_count} errors during export")
            
            return headers_written, lines_written
            
        except Exception as e:
            logger.error(f"Streaming Excel export failed: {e}")
            raise ExcelProcessingException(f"Failed to export to Excel: {e}")
    
    def _get_header_columns(self, include_operation_type: bool = False) -> dict:
        """Get header column mapping."""
        columns = {
            'invoice_number': 'Számla sorszáma',
            'invoice_issue_date': 'Számla kelte',
            'fulfillment_date': 'Teljesítés dátuma',
            'invoice_currency': 'Számla pénzneme',
            'exchange_rate': 'Alkalmazott árfolyam',
            'seller_tax_number_main': 'Eladó adószáma (törzsszám)',
            'seller_tax_number_vat': 'Eladó adószáma (ÁFA-kód)',
            'seller_tax_number_county': 'Eladó adószáma (megyekód)',
            'seller_name': 'Eladó neve',
            'seller_country_code': 'Eladó országkódja',
            'seller_postal_code': 'Eladó irányítószáma',
            'seller_city': 'Eladó települése',
            'seller_address_detail': 'Eladó többi címadata',
            'buyer_tax_number_main': 'Vevő adószáma (törzsszám)',
            'buyer_tax_number_vat': 'Vevő adószáma (ÁFA-kód)',
            'buyer_tax_number_county': 'Vevő adószáma (megyekód)',
            'buyer_name': 'Vevő neve',
            'buyer_vat_status': 'Vevő státusza',
            'buyer_community_vat_number': 'Vevő közösségi adószáma',
            'buyer_third_country_tax_number': 'Vevő harmadik országbeli adószáma',
            'buyer_country_code': 'Vevő országkódja',
            'buyer_postal_code': 'Vevő irányítószáma',
            'buyer_city': 'Vevő települése',
            'buyer_address_detail': 'Vevő többi címadata',
            'original_invoice_number': 'Eredeti számla száma',
            'modification_date': 'Módosító okirat kelte',
            'modification_index': 'Módosítás sorszáma',
            'net_amount_original': 'Számla nettó összege (a számla pénznemében)',
            'net_amount_huf': 'Számla nettó összege (forintban)',
            'vat_amount_original': 'Számla ÁFA összege (a számla pénznemében)',
            'vat_amount_huf': 'Számla ÁFA összege (forintban)',
            'gross_amount_original': 'Számla bruttó összege (a számla pénznemében)',
            'gross_amount_huf': 'Számla bruttó összege (forintban)',
            'payment_due_date': 'Fizetési határidő',
            'payment_method': 'Fizetési mód',
            'small_business_indicator': 'Kisadózó jelölése',
            'cash_accounting_indicator': 'Pénzforgalmi elszámolás jelölése',
            'invoice_category': 'Számla típusa',
            'completeness_indicator': 'Az adatszolgáltatás maga a számla',
        }
        
        if include_operation_type:
            columns['operation_type'] = 'Művelet típusa'
        
        return columns
    
    def _get_lines_columns(self, include_operation_type: bool = False) -> dict:
        """Get lines column mapping."""
        columns = {
            'invoice_number': 'Számla sorszáma',
            'buyer_tax_number_main': 'Vevő adószáma (törzsszám)',
            'buyer_name': 'Vevő neve',
            'seller_tax_number_main': 'Eladó adószáma (törzsszám)',
            'seller_name': 'Eladó neve',
            'line_number': 'Tétel sorszáma',
            'modified_line_number': 'Módosítással érintett tétel sorszáma',
            'line_modification_type': 'Módosítás jellege',
            'description': 'Megnevezés',
            'quantity': 'Mennyiség',
            'unit_of_measure': 'Mennyiségi egység',
            'unit_price': 'Egységár',
            'net_amount_original': 'Nettó összeg (a számla pénznemében)',
            'net_amount_huf': 'Nettó összeg (forintban)',
            'vat_rate': 'Adó mértéke',
            'vat_exemption_indicator': 'Áfamentesség jelölés',
            'vat_exemption_case': 'Áfamentesség esete',
            'vat_exemption_reason': 'Áfamentesség leírása',
            'out_of_scope_indicator': 'ÁFA törvény hatályán kívüli jelölés',
            'out_of_scope_case': 'ÁFA törvény hatályon kívüliségének esete',
            'out_of_scope_reason': 'ÁFA törvény hatályon kívüliségének leírása',
            'tax_base_deviation_case': 'Adóalap és felszámított adó eltérésének esete',
            'different_tax_rate_content': 'Eltérő adóalap és felszámított adó adómérték, adótartalom',
            'domestic_reverse_charge_indicator': 'Belföldi fordított adózás jelölés',
            'margin_scheme_with_vat': 'Áthárított adót tartalmazó különbözet szerinti adózás',
            'margin_scheme_without_vat': 'Áthárított adót nem tartalmazó különbözet szerinti adózás',
            'margin_scheme_indicator': 'Különbözet szerinti adózás',
            'vat_amount_original': 'ÁFA összeg (a számla pénznemében)',
            'vat_amount_huf': 'ÁFA összeg (forintban)',
            'gross_amount_original': 'Bruttó összeg (a számla pénznemében)',
            'gross_amount_huf': 'Bruttó összeg (forintban)',
            'vat_content': 'ÁFA tartalom',
            'advance_payment_indicator': 'Előleg jelleg jelölése',
            'line_exchange_rate': 'Tétel árfolyam',
            'line_fulfillment_date': 'Tétel teljesítés dátuma',
            'no_vat_charge_indicator': 'Nincs felszámított áfa az áfa törvény 17. § alapján',
        }
        
        if include_operation_type:
            columns['operation_type'] = 'Művelet típusa'
        
        return columns
    
    def _write_sheet_headers(self, worksheet, headers: list) -> None:
        """Write column headers to worksheet."""
        for col_idx, header in enumerate(headers):
            worksheet.write(0, col_idx, header)
    
    def _write_header_row(
        self, 
        worksheet, 
        row_idx: int, 
        header_row: InvoiceHeaderRow,
        columns: dict,
        include_operation_type: bool
    ) -> None:
        """Write a single header row to worksheet."""
        row_dict = {
            'invoice_number': header_row.invoice_number,
            'invoice_issue_date': header_row.invoice_issue_date,
            'fulfillment_date': header_row.fulfillment_date,
            'invoice_currency': header_row.invoice_currency,
            'exchange_rate': header_row.exchange_rate,
            'seller_tax_number_main': header_row.seller_tax_number_main,
            'seller_tax_number_vat': header_row.seller_tax_number_vat,
            'seller_tax_number_county': header_row.seller_tax_number_county,
            'seller_name': header_row.seller_name,
            'seller_country_code': header_row.seller_country_code,
            'seller_postal_code': header_row.seller_postal_code,
            'seller_city': header_row.seller_city,
            'seller_address_detail': header_row.seller_address_detail,
            'buyer_tax_number_main': header_row.buyer_tax_number_main,
            'buyer_tax_number_vat': header_row.buyer_tax_number_vat,
            'buyer_tax_number_county': header_row.buyer_tax_number_county,
            'buyer_name': header_row.buyer_name,
            'buyer_vat_status': header_row.buyer_vat_status,
            'buyer_community_vat_number': header_row.buyer_community_vat_number,
            'buyer_third_country_tax_number': header_row.buyer_third_country_tax_number,
            'buyer_country_code': header_row.buyer_country_code,
            'buyer_postal_code': header_row.buyer_postal_code,
            'buyer_city': header_row.buyer_city,
            'buyer_address_detail': header_row.buyer_address_detail,
            'original_invoice_number': header_row.original_invoice_number,
            'modification_date': header_row.modification_date,
            'modification_index': header_row.modification_index,
            'net_amount_original': header_row.net_amount_original,
            'net_amount_huf': header_row.net_amount_huf,
            'vat_amount_original': header_row.vat_amount_original,
            'vat_amount_huf': header_row.vat_amount_huf,
            'gross_amount_original': header_row.gross_amount_original,
            'gross_amount_huf': header_row.gross_amount_huf,
            'payment_due_date': header_row.payment_due_date,
            'payment_method': header_row.payment_method,
            'small_business_indicator': header_row.small_business_indicator,
            'cash_accounting_indicator': header_row.cash_accounting_indicator,
            'invoice_category': header_row.invoice_category,
            'completeness_indicator': header_row.completeness_indicator,
        }
        
        # Write values in column order
        for col_idx, field_name in enumerate(columns.keys()):
            value = row_dict.get(field_name, 'n/a')
            if value is None:
                value = 'n/a'
            worksheet.write(row_idx, col_idx, value)
    
    def _write_line_row(
        self,
        worksheet,
        row_idx: int,
        line_row: InvoiceLineRow,
        columns: dict,
        include_operation_type: bool
    ) -> None:
        """Write a single line row to worksheet."""
        row_dict = {
            'invoice_number': line_row.invoice_number,
            'buyer_tax_number_main': line_row.buyer_tax_number_main,
            'buyer_name': line_row.buyer_name,
            'seller_tax_number_main': line_row.seller_tax_number_main,
            'seller_name': line_row.seller_name,
            'line_number': line_row.line_number,
            'modified_line_number': line_row.modified_line_number,
            'line_modification_type': line_row.line_modification_type,
            'description': line_row.description,
            'quantity': line_row.quantity,
            'unit_of_measure': line_row.unit_of_measure,
            'unit_price': line_row.unit_price,
            'net_amount_original': line_row.net_amount_original,
            'net_amount_huf': line_row.net_amount_huf,
            'vat_rate': line_row.vat_rate,
            'vat_exemption_indicator': line_row.vat_exemption_indicator,
            'vat_exemption_case': line_row.vat_exemption_case,
            'vat_exemption_reason': line_row.vat_exemption_reason,
            'out_of_scope_indicator': line_row.out_of_scope_indicator,
            'out_of_scope_case': line_row.out_of_scope_case,
            'out_of_scope_reason': line_row.out_of_scope_reason,
            'tax_base_deviation_case': line_row.tax_base_deviation_case,
            'different_tax_rate_content': line_row.different_tax_rate_content,
            'domestic_reverse_charge_indicator': line_row.domestic_reverse_charge_indicator,
            'margin_scheme_with_vat': line_row.margin_scheme_with_vat,
            'margin_scheme_without_vat': line_row.margin_scheme_without_vat,
            'margin_scheme_indicator': line_row.margin_scheme_indicator,
            'vat_amount_original': line_row.vat_amount_original,
            'vat_amount_huf': line_row.vat_amount_huf,
            'gross_amount_original': line_row.gross_amount_original,
            'gross_amount_huf': line_row.gross_amount_huf,
            'vat_content': line_row.vat_content,
            'advance_payment_indicator': line_row.advance_payment_indicator,
            'line_exchange_rate': line_row.line_exchange_rate,
            'line_fulfillment_date': line_row.line_fulfillment_date,
            'no_vat_charge_indicator': line_row.no_vat_charge_indicator,
        }
        
        # Write values in column order
        for col_idx, field_name in enumerate(columns.keys()):
            value = row_dict.get(field_name, 'n/a')
            if value is None:
                value = 'n/a'
            worksheet.write(row_idx, col_idx, value)

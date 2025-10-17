"""
Excel importer for NAV invoice data.

This module provides functionality to import invoice data from Excel files
and convert them back to InvoiceData objects that can be submitted to NAV.
"""

import logging
import re
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal

import pandas as pd

from ..models import InvoiceData, ManageInvoiceOperationType
from .mapper import ExcelFieldMapper
from .models import InvoiceHeaderRow, InvoiceLineRow
from .exceptions import ExcelProcessingException, ExcelValidationException, ExcelStructureException, ExcelImportException

logger = logging.getLogger(__name__)


class InvoiceExcelImporter:
    """
    Imports NAV invoice data from Excel files and converts them to InvoiceData objects.
    
    Reads two sheets:
    - 'Fejléc adatok' (Header Data): One row per invoice
    - 'Tétel adatok' (Line Item Data): Multiple rows per invoice (one per line item)
    """

    def __init__(self):
        """Initialize the importer."""
        self.mapper = ExcelFieldMapper()

    def import_from_excel(self, file_path: str) -> List[Tuple[InvoiceData, ManageInvoiceOperationType]]:
        """
        Import invoice data from Excel file.

        Args:
            file_path: Path to the Excel file to import

        Returns:
            List[Tuple[InvoiceData, ManageInvoiceOperationType]]: Converted invoice data

        Raises:
            ExcelProcessingException: If import fails
            ExcelStructureException: If Excel structure is invalid
            ExcelValidationException: If data validation fails
        """
        try:
            # Validate file extension
            path = Path(file_path)
            if path.suffix.lower() not in ['.xlsx']:
                raise ExcelProcessingException("File must have .xlsx extension")
                
            # Check file exists
            if not path.exists():
                raise ExcelProcessingException(f"File does not exist: {file_path}")
                
            logger.info(f"Starting Excel import from {file_path}")

            # Read Excel file
            excel_data = self._read_excel_file(file_path)            # Convert to row structures
            header_rows = self._parse_header_sheet(excel_data.get('Fejléc adatok'))
            line_rows = self._parse_line_sheet(excel_data.get('Tétel adatok'))
            
            # Group line rows by invoice number
            lines_by_invoice = self._group_lines_by_invoice(line_rows)
            
            # Convert to InvoiceData objects
            invoice_data_list = []
            for header_row in header_rows:
                try:
                    # Get associated line items
                    invoice_lines = lines_by_invoice.get(header_row.invoice_number, [])
                    
                    # Convert to InvoiceData
                    invoice_data, operation_type = self._convert_to_invoice_data(header_row, invoice_lines)
                    invoice_data_list.append((invoice_data, operation_type))
                    
                except Exception as e:
                    logger.error(f"Failed to convert invoice {header_row.invoice_number}: {e}")
                    # Optionally continue with other invoices instead of failing completely
                    continue
            
            logger.info(f"Successfully imported {len(invoice_data_list)} invoices from Excel")
            return invoice_data_list
            
        except Exception as e:
            if isinstance(e, (ExcelStructureException, ExcelValidationException)):
                raise  # Let structure and validation exceptions pass through
            logger.error(f"Excel import failed: {e}")
            raise ExcelProcessingException(f"Failed to import from Excel: {e}")

    def _read_excel_file(self, file_path: str) -> Dict[str, pd.DataFrame]:
        """
        Read Excel file and return DataFrames for each sheet.
        
        Args:
            file_path: Path to Excel file
            
        Returns:
            Dict[str, pd.DataFrame]: Dictionary mapping sheet names to DataFrames
            
        Raises:
            ExcelStructureException: If required sheets are missing
        """
        try:
            # Read all sheets
            excel_data = pd.read_excel(file_path, sheet_name=None, engine='openpyxl')
            
            # Check required sheets exist
            required_sheets = ['Fejléc adatok', 'Tétel adatok']
            missing_sheets = [sheet for sheet in required_sheets if sheet not in excel_data]
            
            if missing_sheets:
                raise ExcelStructureException(
                    f"Missing required sheets: {', '.join(missing_sheets)}. "
                    f"Available sheets: {', '.join(excel_data.keys())}"
                )
            
            return excel_data
            
        except Exception as e:
            if isinstance(e, ExcelStructureException):
                raise  # Let structure exceptions pass through
            
            # Handle pandas-specific sheet not found errors
            if "Worksheet named" in str(e) and "not found" in str(e):
                # Extract sheet name from error message
                match = re.search(r"Worksheet named '([^']+)' not found", str(e))
                if match:
                    sheet_name = match.group(1)
                    raise ExcelStructureException(f"Required sheet '{sheet_name}' not found")
                    
            raise ExcelProcessingException(f"Failed to read Excel file {file_path}: {e}")

    def _parse_header_sheet(self, df: Optional[pd.DataFrame]) -> List[InvoiceHeaderRow]:
        """
        Parse header data sheet into InvoiceHeaderRow objects.
        
        Args:
            df: DataFrame containing header data
            
        Returns:
            List[InvoiceHeaderRow]: Parsed header rows
            
        Raises:
            ExcelValidationException: If validation fails
        """
        if df is None or df.empty:
            return []
        
        header_rows = []
        
        # Map column names to field names
        column_mapping = {}
        for excel_col, field_name in ExcelFieldMapper.HEADER_COLUMNS.items():
            if excel_col in df.columns:
                column_mapping[excel_col] = field_name
        
        # Process each row
        for idx, row in df.iterrows():
            try:
                header_row = InvoiceHeaderRow()
                
                for excel_col, field_name in column_mapping.items():
                    value = row[excel_col]
                    if pd.isna(value):
                        value = None
                    else:
                        # Convert value to appropriate type
                        value = self._convert_value_for_header_field(field_name, value)
                    
                    setattr(header_row, field_name, value)
                
                # Basic validation
                if not header_row.invoice_number:
                    logger.warning(f"Row {idx + 1}: Missing invoice number, skipping")
                    continue
                
                header_rows.append(header_row)
                
            except Exception as e:
                logger.error(f"Error parsing header row {idx + 1}: {e}")
                # Continue with next row or raise validation exception
                raise ExcelValidationException(f"Invalid data in header row {idx + 1}: {e}")
        
        return header_rows

    def _parse_line_sheet(self, df: Optional[pd.DataFrame]) -> List[InvoiceLineRow]:
        """
        Parse line item data sheet into InvoiceLineRow objects.
        
        Args:
            df: DataFrame containing line item data
            
        Returns:
            List[InvoiceLineRow]: Parsed line rows
        """
        if df is None or df.empty:
            return []
        
        line_rows = []
        
        # Map column names to field names
        column_mapping = {}
        for excel_col, field_name in ExcelFieldMapper.LINE_COLUMNS.items():
            if excel_col in df.columns:
                column_mapping[excel_col] = field_name
        
        # Process each row
        for idx, row in df.iterrows():
            try:
                line_row = InvoiceLineRow()
                
                for excel_col, field_name in column_mapping.items():
                    value = row[excel_col]
                    if pd.isna(value):
                        value = None
                    else:
                        # Convert value to appropriate type
                        value = self._convert_value_for_line_field(field_name, value)
                    
                    setattr(line_row, field_name, value)
                
                # Basic validation
                if not line_row.invoice_number:
                    logger.warning(f"Line row {idx + 1}: Missing invoice number, skipping")
                    continue
                
                line_rows.append(line_row)
                
            except Exception as e:
                logger.error(f"Error parsing line row {idx + 1}: {e}")
                raise ExcelValidationException(f"Invalid data in line row {idx + 1}: {e}")
        
        return line_rows

    def _group_lines_by_invoice(self, line_rows: List[InvoiceLineRow]) -> Dict[str, List[InvoiceLineRow]]:
        """
        Group line rows by invoice number.
        
        Args:
            line_rows: List of line row objects
            
        Returns:
            Dict[str, List[InvoiceLineRow]]: Lines grouped by invoice number
        """
        lines_by_invoice = {}
        for line_row in line_rows:
            invoice_number = line_row.invoice_number
            if invoice_number not in lines_by_invoice:
                lines_by_invoice[invoice_number] = []
            lines_by_invoice[invoice_number].append(line_row)
        
        return lines_by_invoice

    def _validate_excel_structure(self, header_df: pd.DataFrame, lines_df: pd.DataFrame) -> None:
        """
        Validate the structure of Excel data.
        
        Args:
            header_df: Header data DataFrame
            lines_df: Lines data DataFrame
            
        Raises:
            ExcelValidationException: If validation fails
        """
        # Check required header columns are present
        required_header_columns = ['Számla sorszáma', 'Számla kelte']
        missing_header_cols = [col for col in required_header_columns if col not in header_df.columns]
        if missing_header_cols:
            raise ExcelValidationException(f"Missing required header columns: {', '.join(missing_header_cols)}")

    def _parse_lines_sheet(self, df: pd.DataFrame) -> Dict[str, List[InvoiceLineRow]]:
        """
        Parse lines sheet and return grouped by invoice number.
        
        Args:
            df: DataFrame containing line data
            
        Returns:
            Dict[str, List[InvoiceLineRow]]: Lines grouped by invoice number
        """
        line_rows = self._parse_line_sheet(df)
        return self._group_lines_by_invoice(line_rows)

    def _is_date_field(self, field_name: str) -> bool:
        """
        Check if a field is a date field.
        
        Args:
            field_name: Name of the field
            
        Returns:
            bool: True if field is a date field
        """
        date_fields = ['invoice_issue_date', 'fulfillment_date', 'payment_due_date', 'modification_date']
        return field_name in date_fields

    def _is_decimal_field(self, field_name: str) -> bool:
        """
        Check if a field is a decimal field.
        
        Args:
            field_name: Name of the field
            
        Returns:
            bool: True if field is a decimal field
        """
        decimal_fields = [
            'net_amount_original', 'net_amount_huf', 'vat_amount_original', 'vat_amount_huf',
            'gross_amount_original', 'gross_amount_huf', 'exchange_rate', 'unit_price',
            'vat_rate', 'quantity'
        ]
        return field_name in decimal_fields

    def _is_boolean_field(self, field_name: str) -> bool:
        """
        Check if a field is a boolean field.
        
        Args:
            field_name: Name of the field
            
        Returns:
            bool: True if field is a boolean field
        """
        boolean_fields = [
            'completeness_indicator', 'small_business_indicator', 
            'cash_accounting_indicator'
        ]
        return field_name in boolean_fields

    def _is_integer_field(self, field_name: str) -> bool:
        """
        Check if a field is an integer field.
        
        Args:
            field_name: Name of the field
            
        Returns:
            bool: True if field is an integer field
        """
        integer_fields = ['line_number', 'modification_index']
        return field_name in integer_fields

    def _create_header_row_from_dict(self, data: Dict[str, Any]) -> InvoiceHeaderRow:
        """
        Create header row from dictionary data.
        
        Args:
            data: Dictionary containing header data
            
        Returns:
            InvoiceHeaderRow: Created header row
            
        Raises:
            ExcelValidationException: If required fields are missing
        """
        if not data.get('invoice_number'):
            raise ExcelValidationException("Missing required field: invoice_number")
            
        header_row = InvoiceHeaderRow()
        for field_name, value in data.items():
            if hasattr(header_row, field_name):
                setattr(header_row, field_name, value)
                
        return header_row

    def _create_line_row_from_dict(self, data: Dict[str, Any]) -> InvoiceLineRow:
        """
        Create line row from dictionary data.
        
        Args:
            data: Dictionary containing line data
            
        Returns:
            InvoiceLineRow: Created line row
            
        Raises:
            ExcelValidationException: If required fields are missing
        """
        if not data.get('invoice_number'):
            raise ExcelValidationException("Missing required field: invoice_number")
        if not data.get('line_number'):
            raise ExcelValidationException("Missing required field: line_number")
            
        line_row = InvoiceLineRow()
        for field_name, value in data.items():
            if hasattr(line_row, field_name):
                setattr(line_row, field_name, value)
                
        return line_row

    def _convert_to_invoice_data(
        self, 
        header_row: InvoiceHeaderRow, 
        line_rows: List[InvoiceLineRow]
    ) -> Tuple[InvoiceData, ManageInvoiceOperationType]:
        """
        Convert header and line rows back to InvoiceData object.
        
        This is the complex reverse mapping that reconstructs the nested structure.
        
        Args:
            header_row: Invoice header data
            line_rows: Associated line item data
            
        Returns:
            Tuple[InvoiceData, ManageInvoiceOperationType]: Reconstructed invoice data
        """
        try:
            # Use the mapper to convert header data with line data for proper VAT rate aggregation
            invoice_data, operation_type = ExcelFieldMapper.header_row_to_invoice_data(header_row, line_rows)
            
            # Convert line data if present
            if line_rows:
                # Check if this is a modification invoice to pass proper context
                is_modification = (operation_type == ManageInvoiceOperationType.MODIFY)
                lines_type = ExcelFieldMapper.line_rows_to_invoice_lines(
                    line_rows, 
                    is_modification=is_modification,
                    invoice_category=header_row.invoice_category
                )
                if invoice_data.invoice_main and invoice_data.invoice_main.invoice:
                    invoice_data.invoice_main.invoice.invoice_lines = lines_type
                    
                    # For simplified invoices, update the summary with the correct VAT content from lines
                    if (header_row.invoice_category and 
                        ('egyszerűsített' in header_row.invoice_category.lower() or 
                         'simplified' in header_row.invoice_category.lower()) and
                        lines_type and lines_type.line and len(lines_type.line) > 0):
                        
                        # Get VAT content from the first line (all lines should have the same VAT in simplified invoices)
                        first_line = lines_type.line[0]
                        if (hasattr(first_line, 'line_amounts_simplified') and 
                            first_line.line_amounts_simplified and 
                            first_line.line_amounts_simplified.line_vat_rate and
                            hasattr(first_line.line_amounts_simplified.line_vat_rate, 'vat_content')):
                            
                            line_vat_content = first_line.line_amounts_simplified.line_vat_rate.vat_content
                            
                            # Update the summary with the correct VAT content
                            if (invoice_data.invoice_main.invoice.invoice_summary and
                                invoice_data.invoice_main.invoice.invoice_summary.summary_simplified and
                                len(invoice_data.invoice_main.invoice.invoice_summary.summary_simplified) > 0):
                                
                                # Update the VAT rate in the summary
                                summary = invoice_data.invoice_main.invoice.invoice_summary.summary_simplified[0]
                                if summary.vat_rate:
                                    summary.vat_rate.vat_content = line_vat_content
                                    logger.debug(f"Updated summary VAT content to: {line_vat_content}")
            
            
            logger.debug(f"Successfully converted invoice data for: {header_row.invoice_number}")
            return invoice_data, operation_type
            
        except Exception as e:
            logger.error(f"Failed to convert Excel data to InvoiceData: {e}")
            raise ExcelImportException(f"Invoice data conversion failed: {e}")

    def _convert_value_for_header_field(self, field_name: str, value: Any) -> Any:
        """
        Convert Excel value to appropriate Python type for header field.
        
        Args:
            field_name: Name of the field
            value: Raw value from Excel
            
        Returns:
            Any: Converted value
        """
        if value is None or pd.isna(value):
            return None
        
        # Date fields
        if field_name in ['invoice_issue_date', 'fulfillment_date', 'modification_date', 'payment_due_date']:
            return self._parse_date_value(value)
        
        # Decimal fields
        if field_name in ['exchange_rate', 'net_amount_original', 'net_amount_huf', 
                         'vat_amount_original', 'vat_amount_huf', 'gross_amount_original', 'gross_amount_huf']:
            return self._parse_decimal_value(value)
        
        # Integer fields
        if field_name in ['modification_index']:
            return self._parse_integer_value(value)
        
        # Boolean fields
        if field_name in ['small_business_indicator', 'cash_accounting_indicator', 'completeness_indicator']:
            return self._parse_boolean_value(value)
        
        # String fields (default)
        return str(value).strip() if value else None

    def _convert_value_for_line_field(self, field_name: str, value: Any) -> Any:
        """
        Convert Excel value to appropriate Python type for line field.
        
        Args:
            field_name: Name of the field
            value: Raw value from Excel
            
        Returns:
            Any: Converted value
        """
        if value is None or pd.isna(value):
            return None
        
        # Date fields
        if field_name in ['line_fulfillment_date']:
            return self._parse_date_value(value)
        
        # Decimal fields
        if field_name in ['quantity', 'unit_price', 'net_amount_original', 'net_amount_huf',
                         'vat_rate', 'vat_amount_original', 'vat_amount_huf', 
                         'gross_amount_original', 'gross_amount_huf', 'line_exchange_rate']:
            return self._parse_decimal_value(value)
        
        # Integer fields
        if field_name in ['line_number', 'modified_line_number']:
            return self._parse_integer_value(value)
        
        # Boolean fields
        if field_name in ['vat_exemption_indicator', 'out_of_scope_indicator', 
                         'domestic_reverse_charge_indicator', 'margin_scheme_with_vat',
                         'margin_scheme_without_vat', 'advance_payment_indicator', 'no_vat_charge_indicator']:
            return self._parse_boolean_value(value)
        
        # String fields (default)
        return str(value).strip() if value else None

    def _parse_date_value(self, value: Any) -> Optional[str]:
        """Parse date value from various formats and return as string."""
        if value is None or pd.isna(value):
            return None
        
        if isinstance(value, date):
            return value.strftime('%Y-%m-%d')
        elif isinstance(value, datetime):
            return value.date().strftime('%Y-%m-%d')
        elif isinstance(value, str):
            try:
                parsed_date = datetime.strptime(value.strip(), '%Y-%m-%d').date()
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                try:
                    parsed_date = datetime.strptime(value.strip(), '%d.%m.%Y').date()
                    return parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    logger.warning(f"Could not parse date: {value}")
                    return None
        
        return None

    def _parse_decimal_value(self, value: Any) -> Optional[Decimal]:
        """Parse decimal value from various formats."""
        if value is None or pd.isna(value):
            return None
        
        try:
            return Decimal(str(value))
        except (ValueError, TypeError):
            logger.warning(f"Could not parse decimal: {value}")
            return None

    def _parse_integer_value(self, value: Any) -> Optional[int]:
        """Parse integer value."""
        if value is None or pd.isna(value):
            return None
        
        try:
            return int(float(value))  # Handle Excel numbers that come as floats
        except (ValueError, TypeError):
            logger.warning(f"Could not parse integer: {value}")
            return None

    def _parse_boolean_value(self, value: Any) -> Optional[bool]:
        """Parse boolean value from various formats."""
        if value is None or pd.isna(value):
            return None
        
        if isinstance(value, bool):
            return value
        elif isinstance(value, str):
            value_lower = value.strip().lower()
            if value_lower in ['true', 'igen', 'yes', '1', 'x']:
                return True
            elif value_lower in ['false', 'nem', 'no', '0', '']:
                return False
        elif isinstance(value, (int, float)):
            return bool(value)
        
        logger.warning(f"Could not parse boolean: {value}")
        return None
"""
Custom exceptions for Excel processing operations.
"""


class ExcelProcessingException(Exception):
    """
    Base exception for Excel processing operations.
    """
    pass


class ExcelValidationException(ExcelProcessingException):
    """
    Exception raised when Excel data validation fails.
    """
    pass


class ExcelStructureException(ExcelProcessingException):
    """
    Exception raised when Excel file structure is invalid.
    """
    pass


class ExcelMappingException(ExcelProcessingException):
    """
    Exception raised when field mapping fails.
    """
    pass


class ExcelImportException(ExcelProcessingException):
    """
    Exception raised when import conversion fails.
    """
    pass
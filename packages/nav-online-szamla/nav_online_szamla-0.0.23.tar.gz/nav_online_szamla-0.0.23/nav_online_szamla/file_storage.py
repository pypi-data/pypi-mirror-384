"""
Thread-safe file storage for temporary invoice data.

This module provides functionality to store and retrieve invoice data
using the filesystem with thread-safe operations and automatic cleanup.
"""

import logging
import pickle
import shutil
import threading
from pathlib import Path
from typing import List, Tuple, Optional, Iterator
from datetime import datetime
import uuid

from .models import InvoiceData, ManageInvoiceOperationType

logger = logging.getLogger(__name__)


class InvoiceFileStorage:
    """
    Thread-safe file storage for invoice data.
    
    This class provides methods to store invoice data to disk as individual files,
    read them back sequentially, and clean up temporary files after processing.
    Each invoice is stored as a separate pickle file with a unique identifier.
    """
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize the file storage.
        
        Args:
            base_dir: Base directory for storage. If None, creates a temp directory
                     in the system temp location.
        """
        if base_dir is None:
            # Create a unique temporary directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_id = str(uuid.uuid4())[:8]
            base_dir = Path.home() / ".nav_invoice_temp" / f"session_{timestamp}_{session_id}"
        
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Thread-safe counter for file naming
        self._file_counter = 0
        self._counter_lock = threading.Lock()
        
        # Track all files created
        self._files_created = []
        self._files_lock = threading.Lock()
        
        logger.info(f"Initialized InvoiceFileStorage at: {self.base_dir}")
    
    def save_invoice(
        self, 
        invoice_data: InvoiceData, 
        operation_type: ManageInvoiceOperationType
    ) -> str:
        """
        Save a single invoice to disk in a thread-safe manner.
        
        Args:
            invoice_data: Invoice data to save
            operation_type: Operation type for the invoice
            
        Returns:
            str: Path to the saved file
            
        Raises:
            Exception: If file writing fails
        """
        # Get unique file index
        with self._counter_lock:
            file_index = self._file_counter
            self._file_counter += 1
        
        # Create filename with invoice number for easier debugging
        invoice_number = getattr(invoice_data, 'invoice_number', 'unknown')
        # Sanitize invoice number for filename
        safe_invoice_number = "".join(c if c.isalnum() or c in ('-', '_') else '_' 
                                      for c in str(invoice_number))
        
        filename = f"invoice_{file_index:06d}_{safe_invoice_number}.pkl"
        file_path = self.base_dir / filename
        
        try:
            # Pickle the invoice data tuple
            data_tuple = (invoice_data, operation_type)
            
            with open(file_path, 'wb') as f:
                pickle.dump(data_tuple, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            # Track created file
            with self._files_lock:
                self._files_created.append(file_path)
            
            logger.debug(f"Saved invoice {invoice_number} to {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to save invoice {invoice_number}: {e}")
            raise
    
    def save_invoices_batch(
        self,
        invoice_list: List[Tuple[InvoiceData, ManageInvoiceOperationType]]
    ) -> int:
        """
        Save multiple invoices in a batch.
        
        Args:
            invoice_list: List of tuples (invoice_data, operation_type)
            
        Returns:
            int: Number of invoices saved
        """
        saved_count = 0
        for invoice_data, operation_type in invoice_list:
            try:
                self.save_invoice(invoice_data, operation_type)
                saved_count += 1
            except Exception as e:
                invoice_number = getattr(invoice_data, 'invoice_number', 'unknown')
                logger.warning(f"Failed to save invoice {invoice_number}: {e}")
        
        return saved_count
    
    def iterate_invoices(self) -> Iterator[Tuple[InvoiceData, ManageInvoiceOperationType]]:
        """
        Iterate through all stored invoices sequentially.
        
        This is a memory-efficient generator that loads one invoice at a time.
        
        Yields:
            Tuple[InvoiceData, ManageInvoiceOperationType]: Invoice data and operation type
            
        Raises:
            Exception: If file reading fails
        """
        with self._files_lock:
            files_to_read = sorted(self._files_created.copy())
        
        logger.info(f"Starting iteration over {len(files_to_read)} invoice files")
        
        for file_path in files_to_read:
            try:
                with open(file_path, 'rb') as f:
                    data_tuple = pickle.load(f)
                    yield data_tuple
            except Exception as e:
                logger.error(f"Failed to read invoice file {file_path}: {e}")
                # Continue with next file instead of failing completely
                continue
    
    def get_invoice_count(self) -> int:
        """
        Get the total number of invoices stored.
        
        Returns:
            int: Number of stored invoices
        """
        with self._files_lock:
            return len(self._files_created)
    
    def get_storage_size(self) -> int:
        """
        Get the total size of stored data in bytes.
        
        Returns:
            int: Total storage size in bytes
        """
        total_size = 0
        with self._files_lock:
            for file_path in self._files_created:
                if file_path.exists():
                    total_size += file_path.stat().st_size
        return total_size
    
    def cleanup(self, force: bool = False) -> None:
        """
        Clean up temporary files and directories.
        
        Args:
            force: If True, removes all files even if there are errors.
                  If False, stops on first error.
        """
        logger.info(f"Cleaning up invoice storage at: {self.base_dir}")
        
        try:
            if self.base_dir.exists():
                shutil.rmtree(self.base_dir)
                logger.info(f"Successfully removed storage directory: {self.base_dir}")
        except Exception as e:
            logger.error(f"Failed to cleanup storage directory: {e}")
            if not force:
                raise
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with automatic cleanup."""
        self.cleanup(force=True)
    
    def __len__(self) -> int:
        """Return the number of stored invoices."""
        return self.get_invoice_count()

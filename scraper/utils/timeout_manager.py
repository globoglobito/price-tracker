"""
Timeout management utilities for scraper operations.
"""
import time
import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


class TimeoutManager:
    """Manages timeouts for various scraper operations."""
    
    def __init__(self, extraction_timeout_seconds: int = 240):
        """
        Initialize timeout manager.
        
        Args:
            extraction_timeout_seconds: Maximum time allowed for data extraction (default 4 minutes)
        """
        self.extraction_timeout_seconds = extraction_timeout_seconds
        self.extraction_start_time: float = 0
    
    def start_extraction_timer(self) -> None:
        """Start the extraction timeout timer."""
        self.extraction_start_time = time.monotonic()
        logger.info(f"Started extraction timer (timeout: {self.extraction_timeout_seconds}s)")
    
    def check_extraction_timeout(self, operation_name: str = "operation") -> bool:
        """
        Check if extraction has timed out.
        
        Args:
            operation_name: Name of the operation being checked (for logging)
            
        Returns:
            True if timed out, False otherwise
        """
        if self.extraction_start_time == 0:
            return False
            
        elapsed = time.monotonic() - self.extraction_start_time
        if elapsed > self.extraction_timeout_seconds:
            logger.warning(f"Extraction timeout ({self.extraction_timeout_seconds}s) during {operation_name}")
            return True
        return False
    
    def get_extraction_elapsed(self) -> float:
        """Get elapsed time since extraction started."""
        if self.extraction_start_time == 0:
            return 0
        return time.monotonic() - self.extraction_start_time
    
    def reset_extraction_timer(self) -> None:
        """Reset the extraction timer."""
        self.extraction_start_time = 0


def with_timeout_check(timeout_manager: TimeoutManager, operation_name: str):
    """
    Decorator to check timeout before executing a function.
    
    Args:
        timeout_manager: TimeoutManager instance
        operation_name: Name of the operation for logging
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            if timeout_manager.check_extraction_timeout(operation_name):
                logger.warning(f"Skipping {operation_name} due to timeout")
                return None
            return func(*args, **kwargs)
        return wrapper
    return decorator


def should_skip_due_to_timeout(timeout_manager: TimeoutManager, 
                              operation_name: str, 
                              listing_idx: int, 
                              total_listings: int) -> bool:
    """
    Check if operation should be skipped due to timeout.
    
    Args:
        timeout_manager: TimeoutManager instance
        operation_name: Name of the operation
        listing_idx: Current listing index
        total_listings: Total number of listings
        
    Returns:
        True if should skip, False otherwise
    """
    if timeout_manager.check_extraction_timeout(operation_name):
        logger.warning(f"Data extraction timeout ({timeout_manager.extraction_timeout_seconds}s) "
                      f"during {operation_name} - skipping listing {listing_idx}/{total_listings}")
        return True
    return False

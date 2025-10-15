"""
Retry handler with exponential backoff
"""
import asyncio
from typing import Callable, TypeVar, Optional, Set
from functools import wraps
import httpx
from .exceptions import RetryExhaustedError, NetworkError
from .logger import StructuredLogger

T = TypeVar('T')


class RetryHandler:
    """
    Implements retry logic with exponential backoff
    
    Automatically retries transient errors while failing fast on permanent errors
    """
    
    # HTTP status codes that should be retried
    RETRYABLE_STATUS_CODES: Set[int] = {
        408,  # Request Timeout
        429,  # Too Many Requests
        500,  # Internal Server Error
        502,  # Bad Gateway
        503,  # Service Unavailable
        504,  # Gateway Timeout
    }
    
    # HTTP status codes that should NOT be retried (permanent errors)
    PERMANENT_ERROR_CODES: Set[int] = {
        400,  # Bad Request
        401,  # Unauthorized
        403,  # Forbidden
        404,  # Not Found
        405,  # Method Not Allowed
        422,  # Unprocessable Entity
    }
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        multiplier: float = 2.0,
        logger: Optional[StructuredLogger] = None
    ):
        """
        Initialize retry handler
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            multiplier: Backoff multiplier
            logger: Optional logger instance
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
        self.logger = logger
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt using exponential backoff"""
        delay = self.base_delay * (self.multiplier ** attempt)
        return min(delay, self.max_delay)
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """Determine if an error should be retried"""
        # Network errors are retryable
        if isinstance(error, (httpx.NetworkError, httpx.TimeoutException)):
            return True
        
        # Check HTTP status codes
        if isinstance(error, httpx.HTTPStatusError):
            return error.response.status_code in self.RETRYABLE_STATUS_CODES
        
        # Custom network errors
        if isinstance(error, NetworkError):
            return True
        
        return False
    
    def _is_permanent_error(self, error: Exception) -> bool:
        """Determine if an error is permanent (should not retry)"""
        if isinstance(error, httpx.HTTPStatusError):
            return error.response.status_code in self.PERMANENT_ERROR_CODES
        
        return False
    
    async def execute(
        self,
        func: Callable[..., T],
        *args,
        operation: str = "operation",
        **kwargs
    ) -> T:
        """
        Execute function with retry logic
        
        Args:
            func: Async function to execute
            *args: Positional arguments for func
            operation: Operation name for logging
            **kwargs: Keyword arguments for func
        
        Returns:
            Result from func
        
        Raises:
            RetryExhaustedError: If all retries are exhausted
            Exception: If permanent error occurs
        """
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                result = await func(*args, **kwargs)
                
                # Log successful retry
                if attempt > 0 and self.logger:
                    self.logger.info(
                        f"Retry successful for {operation}",
                        attempt=attempt,
                        operation=operation
                    )
                
                return result
                
            except Exception as e:
                last_error = e
                
                # Check if error is permanent (don't retry)
                if self._is_permanent_error(e):
                    if self.logger:
                        self.logger.error(
                            f"Permanent error for {operation}, not retrying",
                            error=e,
                            operation=operation
                        )
                    raise
                
                # Check if error is retryable
                if not self._is_retryable_error(e):
                    if self.logger:
                        self.logger.error(
                            f"Non-retryable error for {operation}",
                            error=e,
                            operation=operation
                        )
                    raise
                
                # Check if we have retries left
                if attempt >= self.max_retries:
                    if self.logger:
                        self.logger.error(
                            f"All retries exhausted for {operation}",
                            error=e,
                            attempts=attempt + 1,
                            operation=operation
                        )
                    raise RetryExhaustedError(
                        f"All {self.max_retries} retries exhausted for {operation}"
                    ) from e
                
                # Calculate delay and wait
                delay = self._calculate_delay(attempt)
                
                if self.logger:
                    self.logger.warning(
                        f"Retrying {operation} after error",
                        error=str(e),
                        attempt=attempt + 1,
                        max_attempts=self.max_retries + 1,
                        delay_seconds=delay,
                        operation=operation
                    )
                
                await asyncio.sleep(delay)
        
        # Should never reach here, but just in case
        raise RetryExhaustedError(
            f"Failed to execute {operation} after {self.max_retries} retries"
        ) from last_error


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    multiplier: float = 2.0
):
    """
    Decorator for adding retry logic to async functions
    
    Usage:
        @with_retry(max_retries=3)
        async def my_function():
            # function code
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            handler = RetryHandler(
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay,
                multiplier=multiplier
            )
            return await handler.execute(
                func,
                *args,
                operation=func.__name__,
                **kwargs
            )
        return wrapper
    return decorator
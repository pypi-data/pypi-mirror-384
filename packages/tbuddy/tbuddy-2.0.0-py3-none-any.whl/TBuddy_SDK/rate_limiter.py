"""
Rate limiter implementation using token bucket algorithm
"""
import asyncio
import time
from typing import Optional
from .exceptions import RateLimitError


class RateLimiter:
    """
    Token bucket rate limiter with burst support
    
    Implements thread-safe rate limiting for API requests
    """
    
    def __init__(
        self,
        queries_per_second: float = 10.0,
        burst_size: int = 20
    ):
        """
        Initialize rate limiter
        
        Args:
            queries_per_second: Maximum sustained rate (QPS)
            burst_size: Maximum burst size (tokens in bucket)
        """
        self.rate = queries_per_second
        self.burst_size = burst_size
        self.tokens = float(burst_size)
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()
    
    async def acquire(self, timeout: Optional[float] = None) -> None:
        """
        Acquire permission to make a request
        
        Args:
            timeout: Maximum time to wait for token (seconds)
        
        Raises:
            RateLimitError: If token cannot be acquired within timeout
        """
        start_time = time.monotonic()
        
        while True:
            async with self._lock:
                now = time.monotonic()
                
                # Refill tokens based on time elapsed
                elapsed = now - self.last_update
                self.tokens = min(
                    self.burst_size,
                    self.tokens + elapsed * self.rate
                )
                self.last_update = now
                
                # Check if we have a token available
                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return
                
                # Calculate wait time for next token
                wait_time = (1.0 - self.tokens) / self.rate
            
            # Check timeout
            if timeout is not None:
                elapsed_total = time.monotonic() - start_time
                if elapsed_total + wait_time > timeout:
                    raise RateLimitError(
                        f"Rate limit exceeded. Try again in {wait_time:.2f}s",
                        retry_after=wait_time
                    )
            
            # Wait for next token
            await asyncio.sleep(wait_time)
    
    def try_acquire(self) -> bool:
        """
        Try to acquire a token without blocking
        
        Returns:
            True if token acquired, False otherwise
        """
        now = time.monotonic()
        
        # Refill tokens
        elapsed = now - self.last_update
        self.tokens = min(
            self.burst_size,
            self.tokens + elapsed * self.rate
        )
        self.last_update = now
        
        # Try to consume token
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        
        return False
    
    async def wait_if_needed(self) -> float:
        """
        Wait if rate limit would be exceeded
        
        Returns:
            Time waited in seconds
        """
        start = time.monotonic()
        await self.acquire()
        return time.monotonic() - start
    
    def get_status(self) -> dict:
        """
        Get current rate limiter status
        
        Returns:
            Dictionary with status information
        """
        now = time.monotonic()
        elapsed = now - self.last_update
        current_tokens = min(
            self.burst_size,
            self.tokens + elapsed * self.rate
        )
        
        return {
            "rate_qps": self.rate,
            "burst_size": self.burst_size,
            "available_tokens": current_tokens,
            "utilization_pct": (1 - current_tokens / self.burst_size) * 100
        }
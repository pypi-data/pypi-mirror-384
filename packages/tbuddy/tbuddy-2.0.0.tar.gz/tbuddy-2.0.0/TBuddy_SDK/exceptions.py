"""
Custom exceptions for TBuddy SDK
"""

class TBuddyError(Exception):
    """Base exception for all TBuddy SDK errors"""
    pass


class AuthenticationError(TBuddyError):
    """Raised when authentication fails"""
    pass


class RateLimitError(TBuddyError):
    """Raised when rate limit is exceeded"""
    def __init__(self, message: str, retry_after: float = None):
        super().__init__(message)
        self.retry_after = retry_after


class SessionNotFoundError(TBuddyError):
    """Raised when session is not found"""
    pass


class SessionNotCompletedError(TBuddyError):
    """Raised when trying to get results for incomplete session"""
    pass


class ValidationError(TBuddyError):
    """Raised when request validation fails"""
    pass


class NetworkError(TBuddyError):
    """Raised on network-related failures"""
    pass


class TimeoutError(TBuddyError):
    """Raised when operation times out"""
    pass


class WebSocketError(TBuddyError):
    """Raised on WebSocket-related errors"""
    pass


class RetryExhaustedError(TBuddyError):
    """Raised when all retry attempts are exhausted"""
    pass

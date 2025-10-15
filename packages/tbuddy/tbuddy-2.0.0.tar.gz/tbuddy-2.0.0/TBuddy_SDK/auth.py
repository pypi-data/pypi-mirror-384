"""
Authentication manager for TBuddy SDK
"""
from typing import Dict
from .exceptions import AuthenticationError


class AuthManager:
    """
    Manages authentication for API requests
    
    Supports API key authentication via headers
    """
    
    def __init__(self, api_key: str):
        """
        Initialize authentication manager
        
        Args:
            api_key: API key for authentication
        
        Raises:
            AuthenticationError: If API key is invalid
        """
        if not api_key or not isinstance(api_key, str) or len(api_key) < 10:
            raise AuthenticationError("Invalid API key provided")
        
        self._api_key = api_key
    
    def get_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for HTTP requests
        
        Returns:
            Dictionary of headers including authentication
        """
        return {
            "X-API-Key": self._api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def get_websocket_params(self) -> Dict[str, str]:
        """
        Get authentication parameters for WebSocket connections
        
        Returns:
            Dictionary of query parameters for WebSocket auth
        """
        return {
            "api_key": self._api_key
        }
    
    def validate_response(self, status_code: int, response_body: Dict) -> None:
        """
        Validate API response for authentication errors
        
        Args:
            status_code: HTTP status code
            response_body: Response body as dictionary
        
        Raises:
            AuthenticationError: If authentication failed
        """
        if status_code == 401:
            raise AuthenticationError(
                f"Authentication failed: {response_body.get('error', 'Unauthorized')}"
            )
        elif status_code == 403:
            raise AuthenticationError(
                f"Access forbidden: {response_body.get('error', 'Forbidden')}"
            )
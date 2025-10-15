"""
REST API client for TBuddy SDK (Orchestrator v2 Compatible)
"""
import httpx
from typing import Optional, Dict, Any
from .models import TravelPlanResult, SessionStatus, HealthStatus
from .auth import AuthManager
from .retry import RetryHandler
from .rate_limiter import RateLimiter
from .logger import StructuredLogger
from .exceptions import (
    SessionNotFoundError,
    SessionNotCompletedError,
    ValidationError,
    NetworkError
)


class RestClient:
    """
    REST API client for TBuddy orchestrator v2
    
    Handles all HTTP operations with retry logic and rate limiting
    """
    
    def __init__(
        self,
        base_url: str,
        auth_manager: AuthManager,
        retry_handler: RetryHandler,
        rate_limiter: RateLimiter,
        logger: StructuredLogger,
        timeout: float = 30.0,
        api_version: str = "v2"  # NEW: Support API versioning
    ):
        """
        Initialize REST client
        
        Args:
            base_url: Base URL of the API (e.g., "http://localhost:8000")
            auth_manager: Authentication manager
            retry_handler: Retry handler
            rate_limiter: Rate limiter
            logger: Structured logger
            timeout: Request timeout in seconds
            api_version: API version (v1 or v2)
        """
        self.base_url = base_url.rstrip('/')
        self.api_version = api_version
        self.auth = auth_manager
        self.retry = retry_handler
        self.rate_limiter = rate_limiter
        self.logger = logger
        self.timeout = timeout
        
        # Build API base path
        self.api_base = f"/api/{api_version}/orchestrator"
        
        # Create HTTP client
        self.client = httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True
        )
        
        self.logger.info(
            "REST client initialized",
            base_url=base_url,
            api_version=api_version,
            api_base=self.api_base
        )
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint"""
        # Remove leading slash if present
        endpoint = endpoint.lstrip('/')
        return f"{self.base_url}{self.api_base}/{endpoint}"
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry and rate limiting
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (relative to api_base)
            json: Request body data
            params: Query parameters
        
        Returns:
            Response data as dictionary
        
        Raises:
            NetworkError: On network failures
            ValidationError: On validation errors
        """
        # Apply rate limiting
        await self.rate_limiter.acquire()
        
        # Build full URL
        url = self._build_url(endpoint)
        headers = self.auth.get_headers()
        
        self.logger.debug(
            f"Making {method} request",
            method=method,
            endpoint=endpoint,
            has_data=json is not None
        )
        
        async def make_request():
            try:
                response = await self.client.request(
                    method=method,
                    url=url,
                    json=json,
                    params=params,
                    headers=headers
                )
                
                # Check for authentication errors
                self.auth.validate_response(response.status_code, {})
                
                # Raise for HTTP errors
                response.raise_for_status()
                
                response_data = response.json()
                
                self.logger.debug(
                    f"{method} request successful",
                    method=method,
                    endpoint=endpoint,
                    status_code=response.status_code
                )
                
                return response_data
                
            except httpx.HTTPStatusError as e:
                # Try to get error details from response
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('error') or error_data.get('detail', str(e))
                except:
                    error_msg = str(e)
                
                self.logger.error(
                    f"{method} request failed",
                    error=error_msg,
                    method=method,
                    endpoint=endpoint,
                    status_code=e.response.status_code
                )
                
                # Handle specific status codes
                if e.response.status_code == 404:
                    raise SessionNotFoundError(error_msg) from e
                elif e.response.status_code == 400:
                    raise ValidationError(error_msg) from e
                
                raise
                
            except httpx.NetworkError as e:
                self.logger.error(
                    f"Network error during {method} request",
                    error=e,
                    method=method,
                    endpoint=endpoint
                )
                raise NetworkError(f"Network error: {str(e)}") from e
        
        # Execute with retry logic
        return await self.retry.execute(
            make_request,
            operation=f"{method} {endpoint}"
        )
    
    # Convenience methods for common HTTP verbs
    
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request"""
        return await self._request("GET", endpoint, params=params)
    
    async def post(self, endpoint: str, json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make POST request"""
        return await self._request("POST", endpoint, json=json)
    
    async def put(self, endpoint: str, json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make PUT request"""
        return await self._request("PUT", endpoint, json=json)
    
    async def delete(self, endpoint: str) -> Dict[str, Any]:
        """Make DELETE request"""
        return await self._request("DELETE", endpoint)
    
    # Orchestrator v2 API Methods
    
    async def submit_query(
        self,
        query: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        force_new_session: bool = False
    ) -> Dict[str, Any]:  # Changed return type - v2 returns AsyncPlanResponse
        """
        Submit a travel query to orchestrator v2
        
        NOTE: v2 returns immediately with session info. Use WebSocket to get updates.
        
        Args:
            query: Natural language travel query
            session_id: Optional session ID (for follow-ups)
            user_id: Optional user ID
            force_new_session: Force new session ignoring memory
        
        Returns:
            AsyncPlanResponse with session_id and websocket_url
        """
        self.logger.info(
            "Submitting travel query",
            session_id=session_id,
            query_length=len(query),
            is_follow_up=session_id is not None
        )
        
        payload = {
            "query": query,
            "session_id": session_id,
            "user_id": user_id,
            "force_new_session": force_new_session
        }
        
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}
        
        response_data = await self.post("plan", json=payload)
        
        self.logger.info(
            "Travel query submitted successfully",
            session_id=response_data.get("session_id"),
            status=response_data.get("status"),
            websocket_url=response_data.get("websocket_url")
        )
        
        return response_data
    
    async def get_session_status(self, session_id: str) -> SessionStatus:
        """
        Get the status of a session
        
        Args:
            session_id: Session identifier
        
        Returns:
            Session status
        """
        self.logger.debug(
            "Getting session status",
            session_id=session_id
        )
        
        response_data = await self.get(f"session/{session_id}/status")
        
        status = SessionStatus(**response_data)
        
        self.logger.debug(
            "Session status retrieved",
            session_id=session_id,
            status=status.status,
            progress=status.progress_percent
        )
        
        return status
    
    async def get_plan_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get plan status (v2 specific endpoint)
        
        Args:
            session_id: Session identifier
        
        Returns:
            Plan status data
        """
        self.logger.debug(
            "Getting plan status",
            session_id=session_id
        )
        
        response_data = await self.get(f"plan/{session_id}/status")
        
        self.logger.debug(
            "Plan status retrieved",
            session_id=session_id,
            workflow_status=response_data.get("workflow_status")
        )
        
        return response_data
    
    async def get_session_result(self, session_id: str) -> TravelPlanResult:
        """
        Get the result of a completed session
        
        Args:
            session_id: Session identifier
        
        Returns:
            Travel plan result
        
        Raises:
            SessionNotCompletedError: If session is not completed
        """
        self.logger.debug(
            "Getting session result",
            session_id=session_id
        )
        
        try:
            response_data = await self.get(f"session/{session_id}/result")
            
            result = TravelPlanResult(**response_data)
            
            self.logger.info(
                "Session result retrieved",
                session_id=session_id,
                status=result.status
            )
            
            return result
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('detail', 'Session not completed')
                except:
                    error_msg = 'Session not completed'
                raise SessionNotCompletedError(error_msg) from e
            raise
    
    # NEW: v2 Memory Management Methods
    
    async def get_session_memory(self, session_id: str) -> Dict[str, Any]:
        """
        Get session memory and context
        
        Args:
            session_id: Session identifier
        
        Returns:
            Session memory information
        """
        self.logger.debug(
            "Getting session memory",
            session_id=session_id
        )
        
        response_data = await self.get(f"session/{session_id}/memory")
        
        self.logger.debug(
            "Session memory retrieved",
            session_id=session_id,
            exists=response_data.get("exists", False),
            turns=response_data.get("conversation_turns", 0)
        )
        
        return response_data
    
    async def get_conversation_history(self, session_id: str) -> Dict[str, Any]:
        """
        Get conversation history for a session
        
        Args:
            session_id: Session identifier
        
        Returns:
            Conversation history
        """
        self.logger.debug(
            "Getting conversation history",
            session_id=session_id
        )
        
        response_data = await self.get(f"session/{session_id}/history")
        
        self.logger.debug(
            "Conversation history retrieved",
            session_id=session_id,
            total_turns=response_data.get("total_turns", 0)
        )
        
        return response_data
    
    async def extend_session(self, session_id: str, hours: int = 24) -> Dict[str, Any]:
        """
        Extend session memory TTL
        
        Args:
            session_id: Session identifier
            hours: Hours to extend (1-168)
        
        Returns:
            Extension confirmation
        """
        self.logger.info(
            "Extending session",
            session_id=session_id,
            hours=hours
        )
        
        response_data = await self.put(
            f"session/{session_id}/extend",
            json={"hours": hours}
        )
        
        self.logger.info(
            "Session extended",
            session_id=session_id,
            hours=hours
        )
        
        return response_data
    
    async def delete_session(self, session_id: str) -> Dict[str, Any]:
        """
        Delete a session and its memory
        
        Args:
            session_id: Session identifier
        
        Returns:
            Deletion confirmation
        """
        self.logger.info(
            "Deleting session",
            session_id=session_id
        )
        
        response_data = await self.delete(f"session/{session_id}")
        
        self.logger.info(
            "Session deleted",
            session_id=session_id
        )
        
        return response_data
    
    # Legacy compatibility
    
    async def cancel_session(self, session_id: str) -> Dict[str, str]:
        """
        Cancel an active session (alias for delete_session)
        
        Args:
            session_id: Session identifier
        
        Returns:
            Cancellation confirmation
        """
        return await self.delete_session(session_id)
    
    async def health_check(self) -> HealthStatus:
        """
        Perform health check on the API
        
        Returns:
            Health status
        """
        self.logger.debug("Performing health check")
        
        response_data = await self.get("health")
        
        health = HealthStatus(**response_data)
        
        self.logger.debug(
            "Health check completed",
            status=health.status
        )
        
        return health
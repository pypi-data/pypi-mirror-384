"""
WebSocket client for real-time streaming updates (Fixed for Orchestrator v2)
"""
import asyncio
import json
from typing import Optional, Callable, Awaitable, Any, Dict
import websockets
from websockets.exceptions import WebSocketException
from .models import StreamUpdate
from .auth import AuthManager
from .logger import StructuredLogger
from .exceptions import WebSocketError, NetworkError


StreamCallback = Callable[[StreamUpdate], Awaitable[None]]


class WebSocketClient:
    """
    WebSocket client for receiving real-time updates
    
    Supports automatic reconnection and message handling
    """
    
    def __init__(
        self,
        url: str,
        auth_manager: AuthManager,
        logger: StructuredLogger,
        timeout: float = 300.0,
        ping_interval: float = 20.0,
        ping_timeout: float = 10.0
    ):
        """
        Initialize WebSocket client
        
        Args:
            url: Full WebSocket URL to connect to
            auth_manager: Authentication manager
            logger: Structured logger
            timeout: Connection timeout in seconds
            ping_interval: Interval between pings in seconds
            ping_timeout: Timeout for ping response in seconds
        """
        self.url = url
        self.auth = auth_manager
        self.logger = logger
        self.timeout = timeout
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        
        self._connection: Optional[websockets.WebSocketClientProtocol] = None
        self._callback: Optional[StreamCallback] = None
        self._running = False
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5
        self._reconnect_delay = 2.0
        
        # Extract session_id from URL for logging
        self._session_id = self._extract_session_id(url)
    
    def _extract_session_id(self, url: str) -> Optional[str]:
        """Extract session ID from WebSocket URL"""
        try:
            parts = url.split('/')
            if len(parts) > 0:
                return parts[-1].split('?')[0]  # Remove query params
        except:
            pass
        return None
    
    async def connect(self, callback: StreamCallback) -> None:
        """
        Connect to WebSocket and start listening for updates
        
        Args:
            callback: Async callback function for handling updates
        
        Raises:
            WebSocketError: If connection fails
        """
        self._callback = callback
        self._running = True
        
        # Add authentication parameters to URL
        url = self.url
        auth_params = self.auth.get_websocket_params()
        if auth_params:
            separator = '&' if '?' in url else '?'
            param_str = "&".join(f"{k}={v}" for k, v in auth_params.items())
            url = f"{url}{separator}{param_str}"
        
        self.logger.info(
            "Connecting to WebSocket",
            session_id=self._session_id,
            url=self.url  # Log without auth params
        )
        
        try:
            self._connection = await websockets.connect(
                url,
                ping_interval=self.ping_interval,
                ping_timeout=self.ping_timeout,
                close_timeout=10.0
            )
            
            self.logger.info(
                "WebSocket connected",
                session_id=self._session_id
            )
            
            # Start listening for messages
            await self._listen()
            
        except WebSocketException as e:
            self.logger.error(
                "WebSocket connection failed",
                error=str(e),
                session_id=self._session_id
            )
            raise WebSocketError(f"Failed to connect: {str(e)}") from e
        except Exception as e:
            self.logger.error(
                "Unexpected error during WebSocket connection",
                error=str(e),
                session_id=self._session_id
            )
            raise WebSocketError(f"Connection error: {str(e)}") from e
    
    async def _listen(self) -> None:
        """Listen for incoming messages"""
        if not self._connection or not self._callback:
            return
        
        try:
            async for message in self._connection:
                if not self._running:
                    break
                
                try:
                    # Parse message
                    data = json.loads(message)
                    
                    # Handle different message types from orchestrator
                    msg_type = data.get("type")
                    
                    # LOGGING: Log all received messages for debugging
                    self.logger.debug(
                        "Received WebSocket message",
                        session_id=self._session_id,
                        msg_type=msg_type,
                        agent=data.get("agent"),
                        progress=data.get("progress_percent")
                    )
                    
                    # Handle internal protocol messages
                    if msg_type == "pong":
                        # Response to ping - just log
                        self.logger.debug("Received pong", session_id=self._session_id)
                        continue
                    
                    if msg_type == "connected":
                        # Initial connection message with context
                        self.logger.info(
                            "WebSocket connection confirmed",
                            session_id=self._session_id,
                            is_follow_up=data.get("is_follow_up", False),
                            has_context=data.get("context") is not None
                        )
                        # Still pass to callback so client can handle it
                    
                    if msg_type == "status":
                        # Status response
                        self.logger.info(
                            "Received status update",
                            session_id=self._session_id,
                            workflow_status=data.get("workflow_status")
                        )
                    
                    # Convert to StreamUpdate model
                    update = StreamUpdate(**data)
                    
                    # Call callback with update
                    await self._callback(update)
                    
                    # Check if this is a final update that should close connection
                    if msg_type in ['completed', 'error', 'timeout']:
                        self.logger.info(
                            "Received final update, closing connection",
                            session_id=self._session_id,
                            update_type=msg_type
                        )
                        # Allow a small delay for any final messages
                        await asyncio.sleep(0.5)
                        break
                    
                except json.JSONDecodeError as e:
                    self.logger.warning(
                        "Failed to parse WebSocket message",
                        error=str(e),
                        message=str(message)[:100]
                    )
                except Exception as e:
                    self.logger.error(
                        "Error processing WebSocket message",
                        error=str(e),
                        session_id=self._session_id
                    )
                    # Don't break on processing errors, continue listening
        
        except websockets.exceptions.ConnectionClosed as e:
            self.logger.info(
                "WebSocket connection closed",
                session_id=self._session_id,
                code=e.code,
                reason=e.reason
            )
        except Exception as e:
            self.logger.error(
                "Error in WebSocket listener",
                error=str(e),
                session_id=self._session_id
            )
            raise WebSocketError(f"Listener error: {str(e)}") from e
        finally:
            await self.disconnect()
    
    async def send_ping(self) -> None:
        """Send a ping message to keep connection alive"""
        if self._connection and not self._connection.closed:
            try:
                await self._connection.send(json.dumps({"type": "ping"}))
                self.logger.debug("Sent ping", session_id=self._session_id)
            except Exception as e:
                self.logger.warning("Failed to send ping", error=str(e))
    
    async def send_message(self, message: Dict[str, Any]) -> None:
        """
        Send a message to the server
        
        Args:
            message: Message dictionary to send
        """
        if self._connection and not self._connection.closed:
            try:
                await self._connection.send(json.dumps(message))
                self.logger.debug(
                    "Sent message",
                    session_id=self._session_id,
                    message_type=message.get("type")
                )
            except Exception as e:
                self.logger.warning("Failed to send message", error=str(e))
                raise WebSocketError(f"Failed to send message: {str(e)}") from e
        else:
            raise WebSocketError("WebSocket is not connected")
    
    async def request_status(self) -> None:
        """Request current status from server"""
        await self.send_message({"type": "get_status"})
    
    async def disconnect(self) -> None:
        """Disconnect from WebSocket"""
        self._running = False
        
        if self._connection and not self._connection.close:
            try:
                await self._connection.close()
                self.logger.info(
                    "WebSocket disconnected",
                    session_id=self._session_id
                )
            except Exception as e:
                self.logger.warning(
                    "Error during WebSocket disconnect",
                    error=str(e)
                )
        
        self._connection = None
    
    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is connected"""
        return (
            self._connection is not None and
            not self._connection.closed and
            self._running
        )


class WebSocketManager:
    """
    Manager for multiple WebSocket connections
    
    Supports managing multiple concurrent session streams
    """
    
    def __init__(
        self,
        base_url: str,
        auth_manager: AuthManager,
        logger: StructuredLogger,
        timeout: float = 300.0
    ):
        """
        Initialize WebSocket manager
        
        Args:
            base_url: Base HTTP/HTTPS URL of the API (e.g., "http://localhost:8000")
            auth_manager: Authentication manager
            logger: Structured logger
            timeout: Connection timeout in seconds
        """
        # Store original base URL
        self.base_url = base_url.rstrip('/')
        
        self.auth = auth_manager
        self.logger = logger
        self.timeout = timeout
        
        self._clients: dict[str, WebSocketClient] = {}
        self._tasks: dict[str, asyncio.Task] = {}
    
    def _build_websocket_url(self, session_id: str) -> str:
        """
        Build full WebSocket URL for a session
        
        Args:
            session_id: Session ID
            
        Returns:
            Full WebSocket URL
        """
        # Convert HTTP to WebSocket protocol
        ws_base = self.base_url.replace('http://', 'ws://').replace('https://', 'wss://')
        
        # Remove leading slash if present in session_id
        session_id = session_id.lstrip('/')
        
        # Build full URL with orchestrator v2 path
        return f"{ws_base}/api/v2/orchestrator/ws/{session_id}"
    
    async def subscribe(
        self,
        session_id: str,
        callback: StreamCallback
    ) -> str:
        """
        Subscribe to updates for a session
        
        Args:
            session_id: Session ID to subscribe to (can include leading /)
            callback: Callback function for updates
            
        Returns:
            Subscription ID (normalized session_id)
        """
        # Normalize session_id
        normalized_id = session_id.lstrip('/')
        
        # Close existing connection if any
        if normalized_id in self._clients:
            await self.unsubscribe(normalized_id)
        
        # Build full WebSocket URL
        ws_url = self._build_websocket_url(normalized_id)
        
        self.logger.info(
            "Subscribing to session updates",
            session_id=normalized_id,
            ws_url=ws_url
        )
        
        # Create new client
        client = WebSocketClient(
            url=ws_url,
            auth_manager=self.auth,
            logger=self.logger,
            timeout=self.timeout
        )
        
        self._clients[normalized_id] = client
        
        # Start connection in background task
        task = asyncio.create_task(client.connect(callback))
        self._tasks[normalized_id] = task
        
        self.logger.info(
            "Subscribed to session updates",
            session_id=normalized_id
        )
        
        return normalized_id
    
    async def unsubscribe(self, session_id: str) -> None:
        """
        Unsubscribe from session updates
        
        Args:
            session_id: Session ID to unsubscribe from
        """
        normalized_id = session_id.lstrip('/')
        
        # Cancel task
        if normalized_id in self._tasks:
            task = self._tasks[normalized_id]
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            del self._tasks[normalized_id]
        
        # Disconnect client
        if normalized_id in self._clients:
            client = self._clients[normalized_id]
            await client.disconnect()
            del self._clients[normalized_id]
        
        self.logger.info(
            "Unsubscribed from session updates",
            session_id=normalized_id
        )
    
    async def send_ping(self, session_id: str) -> None:
        """
        Send ping to keep connection alive
        
        Args:
            session_id: Session ID
        """
        normalized_id = session_id.lstrip('/')
        if normalized_id in self._clients:
            await self._clients[normalized_id].send_ping()
        else:
            raise WebSocketError(f"No active connection for session: {normalized_id}")
    
    async def request_status(self, session_id: str) -> None:
        """
        Request current status for a session
        
        Args:
            session_id: Session ID
        """
        normalized_id = session_id.lstrip('/')
        if normalized_id in self._clients:
            await self._clients[normalized_id].request_status()
        else:
            raise WebSocketError(f"No active connection for session: {normalized_id}")
    
    async def close_all(self) -> None:
        """Close all WebSocket connections"""
        session_ids = list(self._clients.keys())
        for session_id in session_ids:
            await self.unsubscribe(session_id)
        
        self.logger.info("All WebSocket connections closed")
    
    def get_active_sessions(self) -> list[str]:
        """Get list of active session IDs"""
        return [
            sid for sid, client in self._clients.items()
            if client.is_connected
        ]
    
    def is_connected(self, session_id: str) -> bool:
        """
        Check if a session has an active connection
        
        Args:
            session_id: Session ID to check
            
        Returns:
            True if connected
        """
        normalized_id = session_id.lstrip('/')
        if normalized_id in self._clients:
            return self._clients[normalized_id].is_connected
        return False
    
    async def wait_for_completion(self, session_id: str, timeout: Optional[float] = None) -> None:
        """
        Wait for a session's WebSocket connection to complete
        
        Args:
            session_id: Session ID to wait for
            timeout: Optional timeout in seconds
            
        Raises:
            WebSocketError: If session not found or timeout occurs
        """
        normalized_id = session_id.lstrip('/')
        
        if normalized_id not in self._tasks:
            raise WebSocketError(f"No active task for session: {normalized_id}")
        
        task = self._tasks[normalized_id]
        
        try:
            if timeout:
                await asyncio.wait_for(task, timeout=timeout)
            else:
                await task
        except asyncio.TimeoutError:
            raise WebSocketError(f"Timeout waiting for session: {normalized_id}")
        except asyncio.CancelledError:
            self.logger.info(f"Task cancelled for session: {normalized_id}")
        except Exception as e:
            raise WebSocketError(f"Error waiting for session: {str(e)}")
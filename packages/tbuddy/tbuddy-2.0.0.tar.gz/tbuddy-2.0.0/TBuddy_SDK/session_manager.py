"""
Session state management for TBuddy SDK (Enhanced for v2)
"""
import asyncio
from typing import Optional, Dict, Any, Callable, Awaitable, List
from datetime import datetime
from .models import TravelPlanResult, SessionStatus, StreamUpdate
from .cache import ResultCache
from .logger import StructuredLogger


SessionUpdateCallback = Callable[[str, StreamUpdate], Awaitable[None]]


class SessionInfo:
    """Enhanced session information with v2 features"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.utcnow()
        self.last_update = datetime.utcnow()
        self.status = "initialized"
        self.progress = 0
        self.updates_received = 0
        
        # NEW: v2 fields
        self.is_follow_up = False
        self.conversation_turns = 0
        self.update_type: Optional[str] = None  # budget_update, itinerary_update, etc.
        self.destination: Optional[str] = None
        self.travel_dates: List[str] = []
        self.has_itinerary = False
        self.has_budget = False
        self.has_weather = False
        self.has_events = False
        self.has_maps = False
        
        # Agent tracking
        self.completed_agents: List[str] = []
        self.pending_agents: List[str] = []
        self.failed_agents: List[str] = []
        
        # Track agent data separately
        self.agent_data: Dict[str, Any] = {}
        
        # Error tracking
        self.error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_update": self.last_update.isoformat(),
            "status": self.status,
            "progress": self.progress,
            "updates_received": self.updates_received,
            "is_follow_up": self.is_follow_up,
            "conversation_turns": self.conversation_turns,
            "update_type": self.update_type,
            "destination": self.destination,
            "travel_dates": self.travel_dates,
            "has_itinerary": self.has_itinerary,
            "has_budget": self.has_budget,
            "has_weather": self.has_weather,
            "has_events": self.has_events,
            "has_maps": self.has_maps,
            "completed_agents": self.completed_agents,
            "pending_agents": self.pending_agents,
            "failed_agents": self.failed_agents,
            "error": self.error
        }


class SessionManager:
    """
    Manages multiple session states and subscriptions (Enhanced for v2)
    
    NEW Features:
    - Tracks follow-up status and conversation turns
    - Monitors update types (budget, itinerary, etc.)
    - Per-agent progress tracking
    - Enhanced statistics with v2 metrics
    """
    
    def __init__(
        self,
        cache: ResultCache,
        logger: StructuredLogger
    ):
        """
        Initialize session manager
        
        Args:
            cache: Result cache instance
            logger: Structured logger
        """
        self.cache = cache
        self.logger = logger
        
        # Track active sessions with enhanced info
        self._sessions: Dict[str, SessionInfo] = {}
        self._session_callbacks: Dict[str, list[SessionUpdateCallback]] = {}
        self._lock = asyncio.Lock()
    
    async def register_session(
        self,
        session_id: str,
        initial_status: Optional[SessionStatus] = None,
        is_follow_up: bool = False
    ) -> None:
        """
        Register a new session
        
        Args:
            session_id: Session identifier
            initial_status: Optional initial status
            is_follow_up: Whether this is a follow-up query
        """
        async with self._lock:
            if session_id not in self._sessions:
                session_info = SessionInfo(session_id)
                session_info.is_follow_up = is_follow_up
                
                if initial_status:
                    session_info.status = initial_status.status
                    session_info.progress = initial_status.progress_percent
                    
                    # Extract agent info
                    if hasattr(initial_status, 'completed_agents'):
                        session_info.completed_agents = initial_status.completed_agents or []
                    if hasattr(initial_status, 'pending_agents'):
                        session_info.pending_agents = initial_status.pending_agents or []
                
                self._sessions[session_id] = session_info
                
                self.logger.info(
                    "Session registered",
                    session_id=session_id,
                    is_follow_up=is_follow_up
                )
    
    async def update_session(
        self,
        session_id: str,
        update: StreamUpdate
    ) -> None:
        """
        Update session with new stream update
        
        Args:
            session_id: Session identifier
            update: Stream update
        """
        async with self._lock:
            if session_id not in self._sessions:
                # Auto-register if not exists
                self._sessions[session_id] = SessionInfo(session_id)
            
            session_info = self._sessions[session_id]
            session_info.last_update = datetime.utcnow()
            session_info.updates_received += 1
            
            # Update progress
            if update.progress_percent is not None:
                session_info.progress = update.progress_percent
            
            # Handle different update types
            msg_type = update.type
            agent_name = update.agent
            
            # Track agent lifecycle
            if msg_type == "agent_start":
                if agent_name and agent_name not in session_info.pending_agents:
                    session_info.pending_agents.append(agent_name)
                    self.logger.debug(
                        f"Agent {agent_name} started",
                        session_id=session_id
                    )
            
            elif msg_type == "agent_update":
                # Agent completed successfully
                if agent_name:
                    # Move from pending to completed
                    if agent_name in session_info.pending_agents:
                        session_info.pending_agents.remove(agent_name)
                    if agent_name not in session_info.completed_agents:
                        session_info.completed_agents.append(agent_name)
                    
                    # Extract and store agent data
                    if update.data:
                        # Check for agent-specific data keys
                        data_key = f"{agent_name}_data"
                        if data_key in update.data:
                            session_info.agent_data[agent_name] = update.data[data_key]
                        
                        # Update has_* flags
                        if f"{agent_name}_complete" in update.data:
                            if agent_name == "weather":
                                session_info.has_weather = True
                            elif agent_name == "events":
                                session_info.has_events = True
                            elif agent_name == "maps":
                                session_info.has_maps = True
                            elif agent_name == "budget":
                                session_info.has_budget = True
                            elif agent_name == "itinerary":
                                session_info.has_itinerary = True
                    
                    self.logger.debug(
                        f"Agent {agent_name} completed",
                        session_id=session_id,
                        has_data=bool(update.data)
                    )
            
            elif msg_type == "progress":
                # General progress update
                if agent_name and "completed" in update.message.lower():
                    # Agent completed based on message
                    if agent_name in session_info.pending_agents:
                        session_info.pending_agents.remove(agent_name)
                    if agent_name not in session_info.completed_agents:
                        session_info.completed_agents.append(agent_name)
            
            elif msg_type == "error":
                # Track failed agents
                if agent_name and agent_name not in session_info.failed_agents:
                    session_info.failed_agents.append(agent_name)
                    if agent_name in session_info.pending_agents:
                        session_info.pending_agents.remove(agent_name)
                
                session_info.status = "failed"
                session_info.error = update.message
                
                self.logger.warning(
                    f"Agent {agent_name} failed" if agent_name else "Session failed",
                    session_id=session_id,
                    error=update.message
                )
            
            # Update status based on update type
            if msg_type == "completed":
                session_info.status = "completed"
                session_info.progress = 100
                self.logger.info(
                    "Session completed",
                    session_id=session_id,
                    completed_agents=len(session_info.completed_agents)
                )
            
            elif msg_type == "timeout":
                session_info.status = "timeout"
                self.logger.warning(
                    "Session timed out",
                    session_id=session_id
                )
            
            # Extract v2 metadata from update data
            if update.data:
                if "is_follow_up" in update.data:
                    session_info.is_follow_up = update.data["is_follow_up"]
                if "update_type" in update.data:
                    session_info.update_type = update.data["update_type"]
                if "destination" in update.data:
                    session_info.destination = update.data["destination"]
                if "travel_dates" in update.data:
                    session_info.travel_dates = update.data["travel_dates"] or []
                
                # Check completion flags
                if "itinerary_complete" in update.data:
                    session_info.has_itinerary = update.data["itinerary_complete"]
                if "budget_complete" in update.data:
                    session_info.has_budget = update.data["budget_complete"]
                if "weather_complete" in update.data:
                    session_info.has_weather = update.data["weather_complete"]
                if "events_complete" in update.data:
                    session_info.has_events = update.data["events_complete"]
                if "maps_complete" in update.data:
                    session_info.has_maps = update.data["maps_complete"]
            
            self.logger.debug(
                "Session updated",
                session_id=session_id,
                update_type=msg_type,
                progress=session_info.progress,
                agent=agent_name,
                status=session_info.status
            )
        
        # Notify callbacks (outside lock)
        await self._notify_callbacks(session_id, update)
    
    async def update_from_result(
        self,
        session_id: str,
        result: TravelPlanResult
    ) -> None:
        """
        Update session from a travel plan result
        
        Args:
            session_id: Session identifier
            result: Travel plan result
        """
        async with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = SessionInfo(session_id)
            
            session_info = self._sessions[session_id]
            session_info.status = result.status
            session_info.last_update = datetime.utcnow()
            
            # Extract v2 fields
            if hasattr(result, 'is_follow_up'):
                session_info.is_follow_up = result.is_follow_up
            if hasattr(result, 'update_type'):
                session_info.update_type = result.update_type
            if hasattr(result, 'conversation_turn'):
                session_info.conversation_turns = result.conversation_turn
            if hasattr(result, 'destination'):
                session_info.destination = result.destination
            if hasattr(result, 'travel_dates'):
                session_info.travel_dates = result.travel_dates or []
            
            # Check what data is available
            if hasattr(result, 'itinerary') and result.itinerary:
                session_info.has_itinerary = True
                session_info.agent_data['itinerary'] = result.itinerary
            if hasattr(result, 'budget') and result.budget:
                session_info.has_budget = True
                session_info.agent_data['budget'] = result.budget
            if hasattr(result, 'weather') and result.weather:
                session_info.has_weather = True
                session_info.agent_data['weather'] = result.weather
            if hasattr(result, 'events') and result.events:
                session_info.has_events = True
                session_info.agent_data['events'] = result.events
            if hasattr(result, 'maps') and result.maps:
                session_info.has_maps = True
                session_info.agent_data['maps'] = result.maps
            
            # Extract agent statuses
            if hasattr(result, 'agent_statuses'):
                for agent, status in result.agent_statuses.items():
                    if status == "completed":
                        if agent not in session_info.completed_agents:
                            session_info.completed_agents.append(agent)
                    elif status == "failed":
                        if agent not in session_info.failed_agents:
                            session_info.failed_agents.append(agent)
    
    async def register_callback(
        self,
        session_id: str,
        callback: SessionUpdateCallback
    ) -> None:
        """
        Register a callback for session updates
        
        Args:
            session_id: Session identifier
            callback: Callback function
        """
        async with self._lock:
            if session_id not in self._session_callbacks:
                self._session_callbacks[session_id] = []
            
            self._session_callbacks[session_id].append(callback)
            
            self.logger.debug(
                "Callback registered",
                session_id=session_id,
                callback_count=len(self._session_callbacks[session_id])
            )
    
    async def _notify_callbacks(
        self,
        session_id: str,
        update: StreamUpdate
    ) -> None:
        """Notify all callbacks for a session"""
        callbacks = self._session_callbacks.get(session_id, [])
        
        for callback in callbacks:
            try:
                await callback(session_id, update)
            except Exception as e:
                self.logger.error(
                    "Error in session callback",
                    error=str(e),
                    session_id=session_id
                )
    
    async def complete_session(
        self,
        session_id: str,
        result: TravelPlanResult
    ) -> None:
        """
        Mark session as completed and cache result
        
        Args:
            session_id: Session identifier
            result: Final travel plan result
        """
        async with self._lock:
            if session_id in self._sessions:
                session_info = self._sessions[session_id]
                session_info.status = "completed"
                session_info.progress = 100
                session_info.last_update = datetime.utcnow()
                
                # Update v2 fields from result
                if hasattr(result, 'is_follow_up'):
                    session_info.is_follow_up = result.is_follow_up
                if hasattr(result, 'conversation_turn'):
                    session_info.conversation_turns = result.conversation_turn
        
        # Cache the result
        self.cache.set_result(session_id, result)
        
        self.logger.info(
            "Session completed",
            session_id=session_id,
            is_follow_up=self._sessions.get(session_id, SessionInfo(session_id)).is_follow_up
        )
    
    async def fail_session(
        self,
        session_id: str,
        error: str
    ) -> None:
        """
        Mark session as failed
        
        Args:
            session_id: Session identifier
            error: Error message
        """
        async with self._lock:
            if session_id in self._sessions:
                session_info = self._sessions[session_id]
                session_info.status = "failed"
                session_info.error = error
                session_info.last_update = datetime.utcnow()
        
        self.logger.error(
            "Session failed",
            session_id=session_id,
            error=error
        )
    
    async def remove_session(self, session_id: str) -> None:
        """
        Remove session from tracking
        
        Args:
            session_id: Session identifier
        """
        async with self._lock:
            self._sessions.pop(session_id, None)
            self._session_callbacks.pop(session_id, None)
        
        self.logger.info(
            "Session removed",
            session_id=session_id
        )
    
    def get_session_info(self, session_id: str) -> Optional[SessionInfo]:
        """
        Get session information
        
        Args:
            session_id: Session identifier
        
        Returns:
            Session information or None
        """
        return self._sessions.get(session_id)
    
    def get_session_agent_data(self, session_id: str, agent: str) -> Optional[Any]:
        """
        Get specific agent data for a session
        
        Args:
            session_id: Session identifier
            agent: Agent name (weather, events, maps, budget, itinerary)
        
        Returns:
            Agent data or None
        """
        session_info = self._sessions.get(session_id)
        if session_info:
            return session_info.agent_data.get(agent)
        return None
    
    def get_active_sessions(self) -> list[str]:
        """Get list of active session IDs"""
        return list(self._sessions.keys())
    
    def get_follow_up_sessions(self) -> list[str]:
        """Get list of follow-up session IDs"""
        return [
            sid for sid, info in self._sessions.items()
            if info.is_follow_up
        ]
    
    def get_completed_sessions(self) -> list[str]:
        """Get list of completed session IDs"""
        return [
            sid for sid, info in self._sessions.items()
            if info.status == "completed"
        ]
    
    def get_failed_sessions(self) -> list[str]:
        """Get list of failed session IDs"""
        return [
            sid for sid, info in self._sessions.items()
            if info.status == "failed"
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get session manager statistics with v2 metrics
        
        Returns:
            Dictionary with statistics
        """
        total_sessions = len(self._sessions)
        completed = sum(1 for s in self._sessions.values() if s.status == "completed")
        failed = sum(1 for s in self._sessions.values() if s.status == "failed")
        timeout = sum(1 for s in self._sessions.values() if s.status == "timeout")
        in_progress = sum(
            1 for s in self._sessions.values()
            if s.status not in ["completed", "failed", "timeout"]
        )
        
        # NEW: v2 statistics
        follow_ups = sum(1 for s in self._sessions.values() if s.is_follow_up)
        with_itinerary = sum(1 for s in self._sessions.values() if s.has_itinerary)
        with_budget = sum(1 for s in self._sessions.values() if s.has_budget)
        with_weather = sum(1 for s in self._sessions.values() if s.has_weather)
        with_events = sum(1 for s in self._sessions.values() if s.has_events)
        with_maps = sum(1 for s in self._sessions.values() if s.has_maps)
        
        # Update type breakdown
        update_types = {}
        for session in self._sessions.values():
            if session.update_type:
                update_types[session.update_type] = update_types.get(session.update_type, 0) + 1
        
        # Average conversation turns
        total_turns = sum(s.conversation_turns for s in self._sessions.values())
        avg_turns = total_turns / total_sessions if total_sessions > 0 else 0
        
        # Agent completion statistics
        total_agent_completions = sum(
            len(s.completed_agents) for s in self._sessions.values()
        )
        total_agent_failures = sum(
            len(s.failed_agents) for s in self._sessions.values()
        )
        
        # Average progress
        total_progress = sum(s.progress for s in self._sessions.values())
        avg_progress = total_progress / total_sessions if total_sessions > 0 else 0
        
        return {
            "total_sessions": total_sessions,
            "completed": completed,
            "failed": failed,
            "timeout": timeout,
            "in_progress": in_progress,
            "active_callbacks": sum(len(cbs) for cbs in self._session_callbacks.values()),
            # NEW: v2 metrics
            "follow_up_sessions": follow_ups,
            "sessions_with_itinerary": with_itinerary,
            "sessions_with_budget": with_budget,
            "sessions_with_weather": with_weather,
            "sessions_with_events": with_events,
            "sessions_with_maps": with_maps,
            "update_types": update_types,
            "average_conversation_turns": round(avg_turns, 2),
            "total_agent_completions": total_agent_completions,
            "total_agent_failures": total_agent_failures,
            "average_progress": round(avg_progress, 2)
        }
    
    def get_session_details(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed session information as dictionary
        
        Args:
            session_id: Session identifier
        
        Returns:
            Session details dictionary or None
        """
        session_info = self._sessions.get(session_id)
        if not session_info:
            return None
        
        details = session_info.to_dict()
        
        # Add agent data summary
        details["agent_data_keys"] = list(session_info.agent_data.keys())
        details["total_callbacks"] = len(self._session_callbacks.get(session_id, []))
        
        return details
    
    async def get_agent_progress(self, session_id: str) -> Dict[str, Any]:
        """
        Get agent-by-agent progress for a session
        
        Args:
            session_id: Session identifier
        
        Returns:
            Agent progress information
        """
        session_info = self._sessions.get(session_id)
        if not session_info:
            return {
                "session_id": session_id,
                "found": False
            }
        
        all_agents = ["weather", "events", "maps", "budget", "itinerary"]
        agent_status = {}
        
        for agent in all_agents:
            if agent in session_info.completed_agents:
                agent_status[agent] = "completed"
            elif agent in session_info.failed_agents:
                agent_status[agent] = "failed"
            elif agent in session_info.pending_agents:
                agent_status[agent] = "processing"
            else:
                agent_status[agent] = "not_started"
        
        return {
            "session_id": session_id,
            "found": True,
            "overall_progress": session_info.progress,
            "overall_status": session_info.status,
            "agent_status": agent_status,
            "completed_agents": session_info.completed_agents,
            "pending_agents": session_info.pending_agents,
            "failed_agents": session_info.failed_agents,
            "has_data": {
                "weather": session_info.has_weather,
                "events": session_info.has_events,
                "maps": session_info.has_maps,
                "budget": session_info.has_budget,
                "itinerary": session_info.has_itinerary
            }
        }
    
    async def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """
        Clean up old sessions that haven't been updated recently
        
        Args:
            max_age_hours: Maximum age in hours
        
        Returns:
            Number of sessions cleaned up
        """
        from datetime import timedelta
        
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        sessions_to_remove = []
        
        async with self._lock:
            for session_id, session_info in self._sessions.items():
                if session_info.last_update < cutoff_time:
                    sessions_to_remove.append(session_id)
        
        # Remove outside lock
        for session_id in sessions_to_remove:
            await self.remove_session(session_id)
        
        if sessions_to_remove:
            self.logger.info(
                "Cleaned up old sessions",
                count=len(sessions_to_remove),
                max_age_hours=max_age_hours
            )
        
        return len(sessions_to_remove)
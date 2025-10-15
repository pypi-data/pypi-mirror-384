"""
Data models for TBuddy SDK using Pydantic
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict




from pydantic import BaseModel
from typing import Optional, List

class SessionMemory(BaseModel):
    session_id: str
    exists: bool = False
    destination: Optional[str] = None
    travel_dates: List[str] = []
    travelers_count: Optional[int] = None
    budget_range: Optional[str] = None
    has_itinerary: bool = False
    has_budget_data: bool = False
    conversation_turns: int = 0
    last_updated: Optional[str] = None
    expires_in_hours: Optional[float] = None

class ConversationHistory:
    """Conversation history for a session"""
    def __init__(self, data: Dict[str, Any]):
        self.session_id = data.get("session_id")
        self.history = data.get("conversation_history", [])
        self.total_turns = data.get("total_turns", 0)

class TravelQuery(BaseModel):
    """Model for travel query request"""
    query: str = Field(..., min_length=10, description="Natural language travel query")
    session_id: Optional[str] = Field(None, description="Optional session ID")
    user_id: Optional[str] = Field(None, description="Optional user ID")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "Plan a 3-day trip to Paris from London in July",
                "session_id": "session_abc123"
            }
        }
    )


class AgentStatus(BaseModel):
    """Model for individual agent status"""
    name: str
    status: str  # pending, processing, completed, timeout, failed
    message: Optional[str] = None


class SessionStatus(BaseModel):
    """Model for session status response"""
    session_id: str
    status: str  # initialized, processing, completed, failed
    progress_percent: int = Field(0, ge=0, le=100)
    current_agent: Optional[str] = None
    completed_agents: List[str] = Field(default_factory=list)
    pending_agents: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TravelPlanResult(BaseModel):
    session_id: str
    status: str
    destination: Optional[str] = None
    travel_dates: List[str] = Field(default_factory=list)
    needs_itinerary: bool = False
    weather: Optional[Dict[str, Any]] = None
    events: Optional[Dict[str, Any]] = None
    maps: Optional[Dict[str, Any]] = None
    budget: Optional[Dict[str, Any]] = None
    itinerary: Optional[Dict[str, Any]] = None
    messages: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    agent_statuses: Dict[str, str] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    is_follow_up: Optional[bool] = False  # ✅ make optional
    update_type: Optional[str] = None     # ✅ make optional



class StreamUpdate(BaseModel):
    """Model for WebSocket stream updates"""
    type: str  # progress, agent_update, completed, error, connected, timeout
    session_id: Optional[str] = None
    agent: Optional[str] = None
    message: str
    progress_percent: Optional[int] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthStatus(BaseModel):
    """Model for health check response"""
    status: str  # healthy, degraded, unhealthy
    orchestrator: str
    redis: str
    timestamp: datetime
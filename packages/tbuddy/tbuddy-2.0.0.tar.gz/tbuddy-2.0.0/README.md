# TBuddy SDK

**Official Python SDK for TBuddy Travel Planning API**

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

TBuddy SDK is a production-ready Python client for the TBuddy Travel Planning API. It provides an intuitive, async-first interface for creating personalized travel itineraries with real-time updates, session memory, and conversation context management.

## 🌟 Features

- **🚀 Async/Await Support** - Built with modern Python async patterns
- **💬 Multi-turn Conversations** - Context-aware follow-up queries
- **📡 Real-time Streaming** - WebSocket support for live updates
- **🧠 Session Memory** - Automatic context retention across conversations
- **🔄 Smart Retry Logic** - Exponential backoff with configurable policies
- **⚡ Rate Limiting** - Token bucket algorithm with burst support
- **💾 Result Caching** - TTL-based caching for improved performance
- **📊 Metrics Collection** - Built-in monitoring and analytics
- **🛡️ Type Safety** - Full type hints and Pydantic models
- **📝 Structured Logging** - JSON and text logging formats

## 📦 Installation

```bash
pip install tbuddy
```

### Development Installation

```bash
git clone https://github.com/ayush-jadaun/TBuddy-client
cd tbuddy-client
pip install -e ".[dev]"
```

## 🚀 Quick Start

### Basic Usage

```python
import asyncio
from TBuddy_SDK import TBuddyClient, TBuddyConfig

async def main():
    # Initialize client
    config = TBuddyConfig(
        api_key="your-api-key-here",
        base_url="http://localhost:8000"
    )
    
    async with TBuddyClient(config) as client:
        # Submit a travel query
        result = await client.submit_query(
            "Plan a 5-day trip to Paris for 2 people with $3000 budget"
        )
        
        print(f"✅ Session: {result.session_id}")
        print(f"📍 Destination: {result.destination}")
        print(f"🗓️ Itinerary: {result.itinerary}")
        print(f"💰 Budget: {result.budget}")

asyncio.run(main())
```

### With Real-time Updates

```python
from TBuddy_SDK.models import StreamUpdate

async def handle_update(update: StreamUpdate):
    if update.type == "agent_update":
        print(f"✨ {update.agent}: {update.message}")
    elif update.type == "progress":
        print(f"📊 Progress: {update.progress_percent}%")

async def main():
    async with TBuddyClient(config) as client:
        result = await client.submit_query(
            query="Plan a week in Tokyo",
            stream_callback=handle_update
        )
```

### Multi-turn Conversations

```python
async def conversation_example():
    async with TBuddyClient(config) as client:
        # Initial query
        result1 = await client.submit_query(
            "Plan a romantic weekend in Venice"
        )
        session_id = result1.session_id
        
        # Follow-up queries use the same session
        result2 = await client.submit_query(
            "Change my budget to $2500",
            session_id=session_id
        )
        
        result3 = await client.submit_query(
            "Add a gondola ride to the itinerary",
            session_id=session_id
        )
```

## 📚 Core Concepts

### Sessions

Every travel planning request creates a **session** that maintains context across multiple interactions:

```python
# Get session memory
memory = await client.get_session_memory(session_id)
print(f"Destination: {memory.destination}")
print(f"Conversation Turns: {memory.conversation_turns}")
print(f"Has Itinerary: {memory.has_itinerary}")

# Get conversation history
history = await client.get_conversation_history(session_id)
for msg in history.history:
    print(f"{msg['role']}: {msg['content']}")
```

### Session Management

```python
# Extend session TTL
await client.extend_session(session_id, hours=48)

# Delete session and its memory
await client.delete_session(session_id)

# Get session status
status = await client.get_status(session_id)
print(f"Status: {status.status}")
print(f"Progress: {status.progress_percent}%")
```

### Streaming Updates

Real-time progress updates via WebSocket:

```python
async def stream_handler(update: StreamUpdate):
    match update.type:
        case "agent_start":
            print(f"🚀 Starting {update.agent}")
        case "agent_update":
            print(f"✨ {update.agent} completed")
        case "progress":
            print(f"📊 {update.progress_percent}%")
        case "completed":
            print("✅ Done!")
        case "error":
            print(f"❌ Error: {update.message}")

result = await client.submit_query(
    query="Plan a trip",
    stream_callback=stream_handler
)
```

## ⚙️ Configuration

### Basic Configuration

```python
from TBuddy_SDK import TBuddyConfig

config = TBuddyConfig(
    api_key="your-api-key",
    base_url="http://localhost:8000"
)
```

### Advanced Configuration

```python
config = TBuddyConfig(
    api_key="your-api-key",
    base_url="http://localhost:8000",
    
    # Rate limiting
    queries_per_second=10.0,
    burst_size=20,
    
    # Retry configuration
    max_retries=3,
    retry_base_delay=1.0,
    retry_max_delay=60.0,
    retry_multiplier=2.0,
    
    # Timeouts
    request_timeout=30.0,
    websocket_timeout=300.0,
    
    # Cache settings
    cache_enabled=True,
    cache_ttl=3600,
    cache_max_size=1000,
    
    # Logging
    log_level="INFO",
    log_format="json",
    
    # Metrics
    metrics_enabled=True
)
```

### Environment Variables

```bash
export TBUDDY_API_KEY="your-api-key"
export TBUDDY_BASE_URL="http://localhost:8000"
export TBUDDY_QPS="10.0"
export TBUDDY_MAX_RETRIES="3"
export TBUDDY_CACHE_ENABLED="true"
export TBUDDY_LOG_LEVEL="INFO"
export TBUDDY_METRICS_ENABLED="true"
```

```python
config = TBuddyConfig.from_env(env_prefix="TBUDDY_")
```

## 🔧 API Reference

### TBuddyClient

#### `submit_query()`

Submit a travel planning query.

```python
result = await client.submit_query(
    query: str,                          # Natural language query
    session_id: Optional[str] = None,    # For follow-ups
    user_id: Optional[str] = None,       # User identifier
    force_new_session: bool = False,     # Ignore memory
    stream_callback: Optional[Callable] = None,
    wait_for_completion: bool = True
) -> TravelPlanResult
```

#### `get_status()`

Get current session status.

```python
status = await client.get_status(session_id: str) -> SessionStatus
```

#### `get_result()`

Get completed travel plan.

```python
result = await client.get_result(session_id: str) -> TravelPlanResult
```

#### `get_session_memory()`

Get session memory and context.

```python
memory = await client.get_session_memory(session_id: str) -> SessionMemory
```

#### `get_conversation_history()`

Get conversation history.

```python
history = await client.get_conversation_history(
    session_id: str
) -> ConversationHistory
```

#### `extend_session()`

Extend session TTL.

```python
await client.extend_session(
    session_id: str,
    hours: int = 24  # 1-168 hours
)
```

#### `delete_session()`

Delete session and memory.

```python
await client.delete_session(session_id: str)
```

#### `get_metrics()`

Get SDK metrics.

```python
metrics = client.get_metrics() -> Dict[str, Any]
```

### Models

#### `TravelPlanResult`

```python
class TravelPlanResult:
    session_id: str
    status: str
    destination: Optional[str]
    travel_dates: List[str]
    itinerary: Optional[Dict[str, Any]]
    budget: Optional[Dict[str, Any]]
    weather: Optional[Dict[str, Any]]
    events: Optional[Dict[str, Any]]
    maps: Optional[Dict[str, Any]]
    messages: List[str]
    errors: List[str]
    is_follow_up: Optional[bool]
    update_type: Optional[str]
```

#### `SessionStatus`

```python
class SessionStatus:
    session_id: str
    status: str  # initialized, processing, completed, failed
    progress_percent: int  # 0-100
    current_agent: Optional[str]
    completed_agents: List[str]
    pending_agents: List[str]
```

#### `SessionMemory`

```python
class SessionMemory:
    session_id: str
    exists: bool
    destination: Optional[str]
    travel_dates: List[str]
    travelers_count: Optional[int]
    budget_range: Optional[str]
    has_itinerary: bool
    has_budget_data: bool
    conversation_turns: int
    expires_in_hours: Optional[float]
```

#### `StreamUpdate`

```python
class StreamUpdate:
    type: str  # progress, agent_update, completed, error, etc.
    session_id: Optional[str]
    agent: Optional[str]
    message: str
    progress_percent: Optional[int]
    data: Optional[Dict[str, Any]]
    timestamp: datetime
```

## 🛡️ Error Handling

```python
from TBuddy_SDK.exceptions import (
    TBuddyError,
    AuthenticationError,
    SessionNotFoundError,
    SessionNotCompletedError,
    ValidationError,
    NetworkError,
    RateLimitError,
    TimeoutError,
    WebSocketError
)

try:
    result = await client.submit_query("Plan a trip")
except AuthenticationError:
    print("Invalid API key")
except SessionNotFoundError:
    print("Session not found")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
except NetworkError:
    print("Network connection failed")
except TBuddyError as e:
    print(f"General error: {e}")
```

## 📊 Metrics and Monitoring

```python
# Enable metrics
config = TBuddyConfig(
    api_key="your-key",
    metrics_enabled=True
)

async with TBuddyClient(config) as client:
    # Perform operations...
    
    # Get metrics
    metrics = client.get_metrics()
    
    print("Requests:")
    print(f"  Total: {metrics['requests']['total']}")
    print(f"  Success Rate: {metrics['requests']['success_rate_percent']}%")
    print(f"  Avg Latency: {metrics['requests']['avg_latency_ms']}ms")
    
    print("Sessions:")
    print(f"  Created: {metrics['sessions']['created']}")
    print(f"  Completed: {metrics['sessions']['completed']}")
    
    print("Cache:")
    print(f"  Hit Rate: {metrics['cache']['hit_rate_percent']}%")
```



## 🔍 Logging

### JSON Logging (Default)

```python
config = TBuddyConfig(
    api_key="your-key",
    log_level="INFO",
    log_format="json"
)
```

Output:
```json
{
  "timestamp": "2025-10-11T10:30:00.000Z",
  "level": "INFO",
  "logger": "TBuddy_SDK",
  "message": "Query submitted successfully",
  "session_id": "abc123",
  "status": "completed"
}
```

### Text Logging

```python
config = TBuddyConfig(
    api_key="your-key",
    log_level="DEBUG",
    log_format="text"
)
```

## 🎯 Best Practices

### 1. Use Context Managers

```python
async with TBuddyClient(config) as client:
    # Automatic cleanup
    result = await client.submit_query("Plan a trip")
```

### 2. Handle Errors Gracefully

```python
try:
    result = await client.submit_query(query)
except TBuddyError as e:
    logger.error(f"Query failed: {e}")
    # Fallback logic
```

### 3. Use Streaming for Long Operations

```python
# For queries that take time, use streaming
result = await client.submit_query(
    query="Complex multi-city itinerary",
    stream_callback=progress_handler
)
```

### 4. Cache Configuration

```python
# Enable caching for better performance
config = TBuddyConfig(
    api_key="your-key",
    cache_enabled=True,
    cache_ttl=3600  # 1 hour
)
```

### 5. Rate Limiting

```python
# Configure rate limits to match your API tier
config = TBuddyConfig(
    api_key="your-key",
    queries_per_second=10.0,
    burst_size=20
)
```

### 6. Conversation Context

```python
# Leverage session memory for better responses
result1 = await client.submit_query("Plan trip to Rome")
session_id = result1.session_id

# Context is preserved
result2 = await client.submit_query(
    "Add Colosseum to day 2",
    session_id=session_id
)
```

## 🔄 Migration Guide

### From v1 to v2

**v1:**
```python
result = await client.plan_trip(
    destination="Paris",
    duration=5,
    budget=3000
)
```

**v2:**
```python
result = await client.submit_query(
    "Plan a 5-day trip to Paris with $3000 budget"
)
```

Key changes:
- Natural language queries instead of structured parameters
- Session-based conversations
- Automatic context management
- Real-time streaming support

## 📖 Examples

### Example 1: Simple Trip Planning

```python
import asyncio
from TBuddy_SDK import TBuddyClient, TBuddyConfig

async def plan_simple_trip():
    config = TBuddyConfig(api_key="your-api-key")
    
    async with TBuddyClient(config) as client:
        result = await client.submit_query(
            "Plan a 3-day beach vacation in Bali for 2 people"
        )
        
        print(f"Destination: {result.destination}")
        print(f"Dates: {result.travel_dates}")
        print(f"Budget: {result.budget}")

asyncio.run(plan_simple_trip())
```

### Example 2: Budget Modification

```python
async def modify_budget():
    config = TBuddyConfig(api_key="your-api-key")
    
    async with TBuddyClient(config) as client:
        # Initial planning
        result1 = await client.submit_query(
            "Plan a week in New York with $2000 budget"
        )
        
        # Modify budget
        result2 = await client.submit_query(
            "Actually, I can spend up to $3500",
            session_id=result1.session_id
        )
        
        print(f"Updated budget: {result2.budget}")

asyncio.run(modify_budget())
```

### Example 3: Activity Additions

```python
async def add_activities():
    config = TBuddyConfig(api_key="your-api-key")
    
    async with TBuddyClient(config) as client:
        result1 = await client.submit_query(
            "Plan a 4-day trip to London"
        )
        
        # Add specific activities
        result2 = await client.submit_query(
            "Add British Museum and Tower of London",
            session_id=result1.session_id
        )
        
        print(f"Itinerary: {result2.itinerary}")

asyncio.run(add_activities())
```

### Example 4: Weather and Events

```python
async def check_weather_events():
    config = TBuddyConfig(api_key="your-api-key")
    
    async with TBuddyClient(config) as client:
        result = await client.submit_query(
            "Plan a trip to Berlin in December"
        )
        
        print(f"Weather: {result.weather}")
        print(f"Local Events: {result.events}")

asyncio.run(check_weather_events())
```

### Example 5: Progress Tracking

```python
async def track_progress():
    config = TBuddyConfig(api_key="your-api-key")
    
    async def progress_callback(update):
        print(f"[{update.type}] {update.message}")
        if update.progress_percent:
            print(f"Progress: {update.progress_percent}%")
    
    async with TBuddyClient(config) as client:
        result = await client.submit_query(
            query="Plan a complex 10-day European tour",
            stream_callback=progress_callback
        )
        
        print(f"Final result: {result.session_id}")

asyncio.run(track_progress())
```

## 🔐 Security

### API Key Management

**✅ Do:**
```python
# Use environment variables
import os
config = TBuddyConfig(api_key=os.getenv("TBUDDY_API_KEY"))

# Or use .env files
from dotenv import load_dotenv
load_dotenv()
config = TBuddyConfig.from_env()
```

**❌ Don't:**
```python
# Never hardcode API keys
config = TBuddyConfig(api_key="sk_live_12345...")  # Bad!
```

### HTTPS in Production

```python
config = TBuddyConfig(
    api_key=os.getenv("TBUDDY_API_KEY"),
    base_url="https://api.tbuddy.com"  # Use HTTPS
)
```

## 🚦 Rate Limiting

The SDK includes built-in rate limiting using a token bucket algorithm:

```python
config = TBuddyConfig(
    api_key="your-key",
    queries_per_second=10.0,  # Sustained rate
    burst_size=20             # Allow bursts
)
```

When rate limit is hit:
```python
from TBuddy_SDK.exceptions import RateLimitError

try:
    result = await client.submit_query(query)
except RateLimitError as e:
    print(f"Rate limited. Wait {e.retry_after}s")
    await asyncio.sleep(e.retry_after)
```

## 🔄 Retry Logic

Automatic retry with exponential backoff:

```python
config = TBuddyConfig(
    api_key="your-key",
    max_retries=3,              # Max attempts
    retry_base_delay=1.0,       # Initial delay
    retry_max_delay=60.0,       # Max delay
    retry_multiplier=2.0        # Backoff multiplier
)
```

Retryable errors:
- Network timeouts
- 5xx server errors
- 429 Too Many Requests
- Connection failures

Non-retryable errors:
- 400 Bad Request
- 401 Unauthorized
- 403 Forbidden
- 404 Not Found

## 🎭 Use Cases

### Personal Travel Planning

```python
result = await client.submit_query(
    "Plan a romantic anniversary trip to Santorini for 5 days"
)
```

### Business Travel

```python
result = await client.submit_query(
    "Plan a 3-day business trip to Singapore with meetings downtown"
)
```

### Group Travel

```python
result = await client.submit_query(
    "Plan a week-long group trip for 6 friends to Costa Rica"
)
```

### Adventure Travel

```python
result = await client.submit_query(
    "Plan an adventure trip to Iceland with hiking and glacier tours"
)
```

### Budget Travel

```python
result = await client.submit_query(
    "Plan a budget-friendly backpacking trip through Southeast Asia"
)
```

## 🧩 Integration Examples

### FastAPI Integration

```python
from fastapi import FastAPI, HTTPException
from TBuddy_SDK import TBuddyClient, TBuddyConfig

app = FastAPI()
config = TBuddyConfig.from_env()
client = TBuddyClient(config)

@app.on_event("startup")
async def startup():
    # Client is already initialized
    pass

@app.on_event("shutdown")
async def shutdown():
    await client.close()

@app.post("/plan-trip")
async def plan_trip(query: str, session_id: str = None):
    try:
        result = await client.submit_query(
            query=query,
            session_id=session_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Flask Integration

```python
from flask import Flask, jsonify, request
from TBuddy_SDK import TBuddyClient, TBuddyConfig
import asyncio

app = Flask(__name__)
config = TBuddyConfig.from_env()
client = TBuddyClient(config)

@app.route('/plan-trip', methods=['POST'])
def plan_trip():
    data = request.json
    query = data.get('query')
    
    # Run async function in sync context
    result = asyncio.run(client.submit_query(query))
    
    return jsonify({
        'session_id': result.session_id,
        'destination': result.destination,
        'itinerary': result.itinerary
    })
```

### Django Integration

```python
# views.py
from django.http import JsonResponse
from asgiref.sync import async_to_sync
from TBuddy_SDK import TBuddyClient, TBuddyConfig

config = TBuddyConfig.from_env()
client = TBuddyClient(config)

def plan_trip_view(request):
    query = request.POST.get('query')
    
    # Convert async to sync
    result = async_to_sync(client.submit_query)(query)
    
    return JsonResponse({
        'session_id': result.session_id,
        'destination': result.destination
    })
```

### Celery Task

```python
from celery import Celery
from TBuddy_SDK import TBuddyClient, TBuddyConfig
import asyncio

app = Celery('tasks')

@app.task
def plan_trip_task(query: str):
    config = TBuddyConfig.from_env()
    client = TBuddyClient(config)
    
    result = asyncio.run(client.submit_query(query))
    
    asyncio.run(client.close())
    
    return {
        'session_id': result.session_id,
        'destination': result.destination
    }
```

## 🧪 Testing Your Integration

```python
import pytest
from TBuddy_SDK import TBuddyClient, TBuddyConfig

@pytest.fixture
async def client():
    config = TBuddyConfig(
        api_key="test-key",
        base_url="http://localhost:8000"
    )
    client = TBuddyClient(config)
    yield client
    await client.close()

@pytest.mark.asyncio
async def test_submit_query(client):
    result = await client.submit_query(
        "Plan a trip to Paris"
    )
    assert result.session_id is not None
    assert result.status == "completed"

@pytest.mark.asyncio
async def test_follow_up_query(client):
    result1 = await client.submit_query("Plan trip to Rome")
    result2 = await client.submit_query(
        "Change budget to $2000",
        session_id=result1.session_id
    )
    assert result2.is_follow_up == True
```

## 📊 Performance Tips

### 1. Connection Pooling
```python
# Reuse client instance
client = TBuddyClient(config)

# Make multiple requests
for query in queries:
    result = await client.submit_query(query)

await client.close()
```

### 2. Enable Caching
```python
config = TBuddyConfig(
    api_key="your-key",
    cache_enabled=True,
    cache_ttl=3600
)
```

### 3. Concurrent Requests
```python
async def process_multiple_queries():
    async with TBuddyClient(config) as client:
        tasks = [
            client.submit_query(q) 
            for q in queries
        ]
        results = await asyncio.gather(*tasks)
```

### 4. Stream for Long Operations
```python
# Don't wait for completion
result = await client.submit_query(
    query="Complex query",
    stream_callback=handler,
    wait_for_completion=False
)
```

## 🐛 Troubleshooting

### Connection Errors

**Problem:** Can't connect to API
```python
NetworkError: Connection refused
```

**Solution:**
1. Check base_url is correct
2. Verify API server is running
3. Check firewall/network settings

### Authentication Errors

**Problem:** 401 Unauthorized
```python
AuthenticationError: Invalid API key
```

**Solution:**
1. Verify API key is correct
2. Check key hasn't expired
3. Ensure key has proper permissions

### Rate Limiting

**Problem:** 429 Too Many Requests
```python
RateLimitError: Rate limit exceeded
```

**Solution:**
1. Reduce queries_per_second
2. Implement backoff logic
3. Use caching
4. Upgrade API tier

### Timeout Issues

**Problem:** Operation times out
```python
TimeoutError: Request timeout
```

**Solution:**
```python
config = TBuddyConfig(
    api_key="your-key",
    request_timeout=60.0,  # Increase timeout
    websocket_timeout=600.0
)
```

### WebSocket Connection Issues

**Problem:** WebSocket won't connect

**Solution:**
1. Check WebSocket URL format
2. Verify firewall allows WebSocket
3. Ensure session_id is valid
4. Check for proxy issues

## 📝 Changelog

### v2.0.0 (2025-10-11)
- ✨ Multi-turn conversation support
- ✨ Session memory management
- ✨ Real-time streaming updates
- ✨ Enhanced metrics collection
- 🔄 Breaking: Changed to natural language queries
- 🔄 Breaking: Session-based architecture

### v1.0.0 (2024-12-01)
- 🎉 Initial release
- ✨ Basic travel planning
- ✨ Async support
- ✨ Rate limiting

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

```bash
# Setup development environment
git clone https://github.com/tbuddy/tbuddy-sdk-python.git
cd tbuddy-sdk-python
pip install -e ".[dev]"

```

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

## 🔗 Links

- **Documentation:** https://docs.tbuddy.com
- **API Reference:** https://api.tbuddy.com/docs
- **GitHub:** https://github.com/ayush-jadaun/TBuddy-client
- **PyPI:** https://pypi.org/project/tbuddy

## 💬 Support

- 📧 Email: ayushjadaun6@gmail.com

- 🐛 Issues: [GitHub Issues](https://github.com/ayush-jadaun/TBuddy-client/issues)
- 📖 Docs: [Official Documentation](https://docs.tbuddy.com)

## 🙏 Acknowledgments

Built with:
- [httpx](https://www.python-httpx.org/) - HTTP client
- [websockets](https://websockets.readthedocs.io/) - WebSocket support
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation
- [cachetools](https://cachetools.readthedocs.io/) - Caching utilities

---

Made with ❤️ by TBuddy Team
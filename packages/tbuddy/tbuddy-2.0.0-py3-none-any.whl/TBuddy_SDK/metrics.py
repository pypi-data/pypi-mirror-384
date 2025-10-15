"""
Optional metrics collection for TBuddy SDK
"""
import time
from typing import Dict, Any, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta
import threading


class MetricsCollector:
    """
    Collects operational metrics for the SDK
    
    Tracks success/failure rates, latencies, and connection health
    """
    
    def __init__(self, enabled: bool = True, window_size: int = 1000):
        """
        Initialize metrics collector
        
        Args:
            enabled: Whether metrics collection is enabled
            window_size: Size of sliding window for rate calculations
        """
        self.enabled = enabled
        self.window_size = window_size
        
        # Counters
        self._requests_total = 0
        self._requests_success = 0
        self._requests_failed = 0
        self._sessions_created = 0
        self._sessions_completed = 0
        self._sessions_failed = 0
        self._websocket_connections = 0
        self._websocket_reconnects = 0
        self._websocket_errors = 0
        self._cache_hits = 0
        self._cache_misses = 0
        self._rate_limit_hits = 0
        self._retries_total = 0
        
        # Latency tracking (sliding window)
        self._request_latencies = deque(maxlen=window_size)
        self._session_durations = deque(maxlen=window_size)
        
        # Error tracking
        self._errors_by_type = defaultdict(int)
        
        # Start time
        self._start_time = datetime.utcnow()
        
        # Thread safety
        self._lock = threading.RLock()
    
    def record_request(
        self,
        success: bool,
        latency_ms: float,
        error_type: Optional[str] = None
    ) -> None:
        """Record an API request"""
        if not self.enabled:
            return
        
        with self._lock:
            self._requests_total += 1
            if success:
                self._requests_success += 1
            else:
                self._requests_failed += 1
                if error_type:
                    self._errors_by_type[error_type] += 1
            
            self._request_latencies.append(latency_ms)
    
    def record_session_created(self) -> None:
        """Record session creation"""
        if not self.enabled:
            return
        
        with self._lock:
            self._sessions_created += 1
    
    def record_session_completed(self, duration_seconds: float) -> None:
        """Record successful session completion"""
        if not self.enabled:
            return
        
        with self._lock:
            self._sessions_completed += 1
            self._session_durations.append(duration_seconds)
    
    def record_session_failed(self) -> None:
        """Record failed session"""
        if not self.enabled:
            return
        
        with self._lock:
            self._sessions_failed += 1
    
    def record_websocket_connection(self) -> None:
        """Record WebSocket connection"""
        if not self.enabled:
            return
        
        with self._lock:
            self._websocket_connections += 1
    
    def record_websocket_reconnect(self) -> None:
        """Record WebSocket reconnection"""
        if not self.enabled:
            return
        
        with self._lock:
            self._websocket_reconnects += 1
    
    def record_websocket_error(self) -> None:
        """Record WebSocket error"""
        if not self.enabled:
            return
        
        with self._lock:
            self._websocket_errors += 1
    
    def record_cache_hit(self) -> None:
        """Record cache hit"""
        if not self.enabled:
            return
        
        with self._lock:
            self._cache_hits += 1
    
    def record_cache_miss(self) -> None:
        """Record cache miss"""
        if not self.enabled:
            return
        
        with self._lock:
            self._cache_misses += 1
    
    def record_rate_limit_hit(self) -> None:
        """Record rate limit hit"""
        if not self.enabled:
            return
        
        with self._lock:
            self._rate_limit_hits += 1
    
    def record_retry(self) -> None:
        """Record retry attempt"""
        if not self.enabled:
            return
        
        with self._lock:
            self._retries_total += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics snapshot
        
        Returns:
            Dictionary with all metrics
        """
        if not self.enabled:
            return {"enabled": False}
        
        with self._lock:
            uptime = (datetime.utcnow() - self._start_time).total_seconds()
            
            # Calculate success rate
            success_rate = 0.0
            if self._requests_total > 0:
                success_rate = (self._requests_success / self._requests_total) * 100
            
            # Calculate average latencies
            avg_request_latency = 0.0
            p95_request_latency = 0.0
            if self._request_latencies:
                sorted_latencies = sorted(self._request_latencies)
                avg_request_latency = sum(sorted_latencies) / len(sorted_latencies)
                p95_index = int(len(sorted_latencies) * 0.95)
                if p95_index < len(sorted_latencies):
                    p95_request_latency = sorted_latencies[p95_index]
            
            # Calculate session metrics
            avg_session_duration = 0.0
            if self._session_durations:
                avg_session_duration = sum(self._session_durations) / len(self._session_durations)
            
            session_success_rate = 0.0
            total_sessions = self._sessions_completed + self._sessions_failed
            if total_sessions > 0:
                session_success_rate = (self._sessions_completed / total_sessions) * 100
            
            # Calculate cache hit rate
            cache_hit_rate = 0.0
            total_cache_requests = self._cache_hits + self._cache_misses
            if total_cache_requests > 0:
                cache_hit_rate = (self._cache_hits / total_cache_requests) * 100
            
            return {
                "enabled": True,
                "uptime_seconds": uptime,
                "requests": {
                    "total": self._requests_total,
                    "success": self._requests_success,
                    "failed": self._requests_failed,
                    "success_rate_percent": round(success_rate, 2),
                    "avg_latency_ms": round(avg_request_latency, 2),
                    "p95_latency_ms": round(p95_request_latency, 2)
                },
                "sessions": {
                    "created": self._sessions_created,
                    "completed": self._sessions_completed,
                    "failed": self._sessions_failed,
                    "success_rate_percent": round(session_success_rate, 2),
                    "avg_duration_seconds": round(avg_session_duration, 2)
                },
                "websocket": {
                    "connections": self._websocket_connections,
                    "reconnects": self._websocket_reconnects,
                    "errors": self._websocket_errors
                },
                "cache": {
                    "hits": self._cache_hits,
                    "misses": self._cache_misses,
                    "hit_rate_percent": round(cache_hit_rate, 2)
                },
                "rate_limiting": {
                    "hits": self._rate_limit_hits
                },
                "retries": {
                    "total": self._retries_total
                },
                "errors_by_type": dict(self._errors_by_type)
            }
    
    def reset(self) -> None:
        """Reset all metrics"""
        with self._lock:
            self._requests_total = 0
            self._requests_success = 0
            self._requests_failed = 0
            self._sessions_created = 0
            self._sessions_completed = 0
            self._sessions_failed = 0
            self._websocket_connections = 0
            self._websocket_reconnects = 0
            self._websocket_errors = 0
            self._cache_hits = 0
            self._cache_misses = 0
            self._rate_limit_hits = 0
            self._retries_total = 0
            self._request_latencies.clear()
            self._session_durations.clear()
            self._errors_by_type.clear()
            self._start_time = datetime.utcnow()
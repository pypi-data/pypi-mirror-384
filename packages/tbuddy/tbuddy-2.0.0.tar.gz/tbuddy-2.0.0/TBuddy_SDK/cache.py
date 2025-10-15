"""
Local result caching for TBuddy SDK
"""
import time
from typing import Optional, Any, Dict
from cachetools import TTLCache
import threading
from .models import TravelPlanResult, SessionStatus


class ResultCache:
    """
    Thread-safe cache for storing session results and status
    
    Uses TTL (Time To Live) based eviction
    """
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        """
        Initialize result cache
        
        Args:
            max_size: Maximum number of cached items
            ttl: Time to live in seconds
        """
        self._results_cache: TTLCache = TTLCache(maxsize=max_size, ttl=ttl)
        self._status_cache: TTLCache = TTLCache(maxsize=max_size, ttl=ttl)
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
    
    def set_result(self, session_id: str, result: TravelPlanResult) -> None:
        """
        Cache a travel plan result
        
        Args:
            session_id: Session identifier
            result: Travel plan result to cache
        """
        with self._lock:
            self._results_cache[session_id] = result
    
    def get_result(self, session_id: str) -> Optional[TravelPlanResult]:
        """
        Retrieve cached travel plan result
        
        Args:
            session_id: Session identifier
        
        Returns:
            Cached result or None if not found
        """
        with self._lock:
            result = self._results_cache.get(session_id)
            if result:
                self._hits += 1
            else:
                self._misses += 1
            return result
    
    def set_status(self, session_id: str, status: SessionStatus) -> None:
        """
        Cache a session status
        
        Args:
            session_id: Session identifier
            status: Session status to cache
        """
        with self._lock:
            self._status_cache[session_id] = status
    
    def get_status(self, session_id: str) -> Optional[SessionStatus]:
        """
        Retrieve cached session status
        
        Args:
            session_id: Session identifier
        
        Returns:
            Cached status or None if not found
        """
        with self._lock:
            status = self._status_cache.get(session_id)
            if status:
                self._hits += 1
            else:
                self._misses += 1
            return status
    
    def invalidate_session(self, session_id: str) -> None:
        """
        Remove session from cache
        
        Args:
            session_id: Session identifier
        """
        with self._lock:
            self._results_cache.pop(session_id, None)
            self._status_cache.pop(session_id, None)
    
    def clear(self) -> None:
        """Clear all cached data"""
        with self._lock:
            self._results_cache.clear()
            self._status_cache.clear()
            self._hits = 0
            self._misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "results_cached": len(self._results_cache),
                "status_cached": len(self._status_cache),
                "cache_hits": self._hits,
                "cache_misses": self._misses,
                "hit_rate_percent": round(hit_rate, 2),
                "total_requests": total_requests
            }
"""
Configuration management for TBuddy SDK
"""
from typing import Optional
from pydantic import BaseModel, Field, field_validator
import os


class TBuddyConfig(BaseModel):
    """Configuration for TBuddy SDK client"""
    
    # API Configuration
    api_key: str = Field(..., description="API key for authentication")
    base_url: str = Field(
        default="http://localhost:8000",
        description="Base URL of the TBuddy API"
    )
    
    # Rate Limiting
    queries_per_second: float = Field(
        default=10.0,
        ge=0.1,
        description="Maximum queries per second"
    )
    burst_size: int = Field(
        default=20,
        ge=1,
        description="Maximum burst size for rate limiting"
    )
    
    # Retry Configuration
    max_retries: int = Field(default=3, ge=0, description="Maximum retry attempts")
    retry_base_delay: float = Field(
        default=1.0,
        ge=0.1,
        description="Base delay in seconds for exponential backoff"
    )
    retry_max_delay: float = Field(
        default=60.0,
        ge=1.0,
        description="Maximum delay in seconds between retries"
    )
    retry_multiplier: float = Field(
        default=2.0,
        ge=1.0,
        description="Multiplier for exponential backoff"
    )
    
    # Timeout Configuration
    request_timeout: float = Field(
        default=30.0,
        ge=1.0,
        description="HTTP request timeout in seconds"
    )
    websocket_timeout: float = Field(
        default=300.0,
        ge=10.0,
        description="WebSocket connection timeout in seconds"
    )
    
    # Cache Configuration
    cache_enabled: bool = Field(default=True, description="Enable result caching")
    cache_ttl: int = Field(
        default=3600,
        ge=60,
        description="Cache TTL in seconds"
    )
    cache_max_size: int = Field(
        default=1000,
        ge=10,
        description="Maximum number of cached items"
    )
    
    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )
    log_format: str = Field(
        default="json",
        description="Log format (json or text)"
    )
    
    # Metrics Configuration
    metrics_enabled: bool = Field(
        default=False,
        description="Enable metrics collection"
    )
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v_upper
    
    @field_validator('log_format')
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        valid_formats = ['json', 'text']
        v_lower = v.lower()
        if v_lower not in valid_formats:
            raise ValueError(f"log_format must be one of {valid_formats}")
        return v_lower
    
    @classmethod
    def from_env(cls, env_prefix: str = "TBUDDY_") -> "TBuddyConfig":
        """Create configuration from environment variables"""
        config_dict = {}
        
        # Map environment variables to config fields
        env_mappings = {
            f"{env_prefix}API_KEY": "api_key",
            f"{env_prefix}BASE_URL": "base_url",
            f"{env_prefix}QPS": "queries_per_second",
            f"{env_prefix}BURST_SIZE": "burst_size",
            f"{env_prefix}MAX_RETRIES": "max_retries",
            f"{env_prefix}REQUEST_TIMEOUT": "request_timeout",
            f"{env_prefix}CACHE_ENABLED": "cache_enabled",
            f"{env_prefix}CACHE_TTL": "cache_ttl",
            f"{env_prefix}LOG_LEVEL": "log_level",
            f"{env_prefix}METRICS_ENABLED": "metrics_enabled",
        }
        
        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert string values to appropriate types
                if config_key in [
                    "queries_per_second", "retry_base_delay",
                    "retry_max_delay", "retry_multiplier",
                    "request_timeout", "websocket_timeout"
                ]:
                    config_dict[config_key] = float(value)
                elif config_key in [
                    "burst_size", "max_retries", "cache_ttl",
                    "cache_max_size"
                ]:
                    config_dict[config_key] = int(value)
                elif config_key in ["cache_enabled", "metrics_enabled"]:
                    config_dict[config_key] = value.lower() in ("true", "1", "yes")
                else:
                    config_dict[config_key] = value
        
        # API key is required
        if "api_key" not in config_dict and f"{env_prefix}API_KEY" not in os.environ:
            raise ValueError(
                f"API key must be provided via {env_prefix}API_KEY environment variable or config"
            )
        
        return cls(**config_dict)

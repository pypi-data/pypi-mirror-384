#!/usr/bin/env python3
"""
DcisionAI MCP Configuration
==========================

Configuration management for the DcisionAI MCP server.
Handles environment variables, API keys, and server settings.
"""

import os
import yaml
from typing import Any, Dict, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Config:
    """Configuration for DcisionAI MCP Server."""
    
    # AgentCore Gateway Configuration
    gateway_url: str = "https://dcisionai-gateway-0de1a655-ja1rhlcqjx.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
    gateway_target: str = "DcisionAI-Optimization-Tools-Fixed"
    access_token: str = ""
    
    # Server Configuration
    host: str = "localhost"
    port: int = 8000
    debug: bool = False
    
    # AWS Configuration
    aws_region: str = "us-east-1"
    aws_profile: Optional[str] = None
    
    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Timeout Configuration
    request_timeout: int = 30
    connection_timeout: int = 10
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600  # 1 hour
    
    def __post_init__(self):
        """Post-initialization setup."""
        # Load from environment variables
        self._load_from_env()
        
        # Validate configuration
        self._validate()
    
    def _load_from_env(self):
        """Load configuration from environment variables."""
        # AgentCore Gateway
        self.gateway_url = os.getenv("DCISIONAI_GATEWAY_URL", self.gateway_url)
        self.gateway_target = os.getenv("DCISIONAI_GATEWAY_TARGET", self.gateway_target)
        self.access_token = os.getenv("DCISIONAI_ACCESS_TOKEN", self.access_token)
        
        # Server settings
        self.host = os.getenv("DCISIONAI_HOST", self.host)
        self.port = int(os.getenv("DCISIONAI_PORT", str(self.port)))
        self.debug = os.getenv("DCISIONAI_DEBUG", "false").lower() == "true"
        
        # AWS settings
        self.aws_region = os.getenv("AWS_REGION", self.aws_region)
        self.aws_profile = os.getenv("AWS_PROFILE", self.aws_profile)
        
        # Logging
        self.log_level = os.getenv("DCISIONAI_LOG_LEVEL", self.log_level)
        
        # Timeouts
        self.request_timeout = int(os.getenv("DCISIONAI_REQUEST_TIMEOUT", str(self.request_timeout)))
        self.connection_timeout = int(os.getenv("DCISIONAI_CONNECTION_TIMEOUT", str(self.connection_timeout)))
        
        # Rate limiting
        self.rate_limit_requests = int(os.getenv("DCISIONAI_RATE_LIMIT_REQUESTS", str(self.rate_limit_requests)))
        self.rate_limit_window = int(os.getenv("DCISIONAI_RATE_LIMIT_WINDOW", str(self.rate_limit_window)))
    
    def _validate(self):
        """Validate configuration values."""
        if not self.gateway_url:
            raise ValueError("Gateway URL is required")
        
        if not self.gateway_target:
            raise ValueError("Gateway target is required")
        
        # Access token is optional for direct Bedrock calls
        # if not self.access_token:
        #     raise ValueError("Access token is required")
        
        if self.port < 1 or self.port > 65535:
            raise ValueError("Port must be between 1 and 65535")
        
        if self.request_timeout < 1:
            raise ValueError("Request timeout must be positive")
        
        if self.connection_timeout < 1:
            raise ValueError("Connection timeout must be positive")
    
    @classmethod
    def from_file(cls, config_path: str) -> "Config":
        """Load configuration from a YAML file."""
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Create config instance with default values
        config = cls()
        
        # Update with file values
        for key, value in config_data.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "gateway_url": self.gateway_url,
            "gateway_target": self.gateway_target,
            "access_token": "***" if self.access_token else "",  # Hide token
            "host": self.host,
            "port": self.port,
            "debug": self.debug,
            "aws_region": self.aws_region,
            "aws_profile": self.aws_profile,
            "log_level": self.log_level,
            "log_format": self.log_format,
            "request_timeout": self.request_timeout,
            "connection_timeout": self.connection_timeout,
            "rate_limit_requests": self.rate_limit_requests,
            "rate_limit_window": self.rate_limit_window,
        }
    
    def save_to_file(self, config_path: str):
        """Save configuration to a YAML file."""
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, indent=2)
    
    def get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for API requests."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}",
            "User-Agent": "DcisionAI-MCP-Server/1.0.0"
        }
    
    def get_client_config(self) -> Dict[str, Any]:
        """Get HTTP client configuration."""
        return {
            "timeout": self.request_timeout,
            "headers": self.get_headers(),
            "follow_redirects": True,
            "verify": True
        }

# Default configuration instance
default_config = Config()

# Environment-specific configurations
def get_config(env: str = "development") -> Config:
    """Get configuration for specific environment."""
    if env == "production":
        return Config(
            debug=False,
            log_level="WARNING",
            rate_limit_requests=1000,
            rate_limit_window=3600
        )
    elif env == "testing":
        return Config(
            debug=True,
            log_level="DEBUG",
            port=8001,
            request_timeout=5
        )
    else:  # development
        return Config(
            debug=True,
            log_level="INFO",
            port=8000
        )

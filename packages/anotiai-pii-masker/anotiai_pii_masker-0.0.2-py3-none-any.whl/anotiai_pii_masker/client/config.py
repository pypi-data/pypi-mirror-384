"""
Configuration management for AnotiAI PII Masker API client.
"""

import os
import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class ClientConfig:
    """Configuration class for API client."""
    
    runpod_api_key: Optional[str] = None
    endpoint_id: Optional[str] = None
    base_url: str = "https://api.runpod.ai/v2"
    timeout: int = 60
    retry_attempts: int = 3
    retry_delay: float = 1.0
    local_fallback: bool = False
    
    @classmethod
    def from_env(cls) -> "ClientConfig":
        """Create configuration from environment variables."""
        return cls(
            runpod_api_key=os.getenv("RUNPOD_API_KEY"),
            endpoint_id=os.getenv("ANOTIAI_ENDPOINT_ID"),
            base_url=os.getenv("ANOTIAI_BASE_URL", "https://api.runpod.ai/v2"),
            timeout=int(os.getenv("ANOTIAI_TIMEOUT", "60")),
            retry_attempts=int(os.getenv("ANOTIAI_RETRY_ATTEMPTS", "3")),
            retry_delay=float(os.getenv("ANOTIAI_RETRY_DELAY", "1.0")),
            local_fallback=os.getenv("ANOTIAI_LOCAL_FALLBACK", "false").lower() == "true"
        )
    
    @classmethod
    def from_file(cls, config_path: Optional[str] = None) -> "ClientConfig":
        """Load configuration from file."""
        if config_path is None:
            config_path = Path.home() / ".anotiai" / "config.json"
        
        if not Path(config_path).exists():
            return cls.from_env()
        
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            return cls(
                runpod_api_key=config_data.get("runpod_api_key"),
                endpoint_id=config_data.get("endpoint_id"),
                base_url=config_data.get("base_url", "https://api.runpod.ai/v2"),
                timeout=config_data.get("timeout", 60),
                retry_attempts=config_data.get("retry_attempts", 3),
                retry_delay=config_data.get("retry_delay", 1.0),
                local_fallback=config_data.get("local_fallback", False)
            )
        except (json.JSONDecodeError, IOError):
            # Fall back to environment variables if file is invalid
            return cls.from_env()
    
    def save_to_file(self, config_path: Optional[str] = None) -> None:
        """Save configuration to file."""
        if config_path is None:
            config_dir = Path.home() / ".anotiai"
            config_dir.mkdir(exist_ok=True)
            config_path = config_dir / "config.json"
        
        config_data = {
            "runpod_api_key": self.runpod_api_key,
            "endpoint_id": self.endpoint_id,
            "base_url": self.base_url,
            "timeout": self.timeout,
            "retry_attempts": self.retry_attempts,
            "retry_delay": self.retry_delay,
            "local_fallback": self.local_fallback
        }
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def is_valid(self) -> bool:
        """Check if the configuration is valid for API usage."""
        return self.runpod_api_key is not None and self.endpoint_id is not None

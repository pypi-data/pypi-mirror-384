"""
Service configuration for Dasein distributed services
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class ServiceConfig:
    """Configuration for Dasein services"""
    
    # Service endpoints
    pre_run_url: str = "https://dasein-pre-run-939340394421.us-central1.run.app"
    post_run_url: str = "https://dasein-post-run-939340394421.us-central1.run.app"
    
    # Authentication
    auth_token: Optional[str] = None
    
    # Timeouts
    request_timeout: int = 30
    
    # Retry configuration
    max_retries: int = 3
    retry_delay: float = 1.0
    
    @classmethod
    def from_env(cls) -> "ServiceConfig":
        """Create config from environment variables"""
        return cls(
            pre_run_url=os.getenv("DASEIN_PRE_RUN_URL", "https://dasein-pre-run-939340394421.us-central1.run.app"),
            post_run_url=os.getenv("DASEIN_POST_RUN_URL", "https://dasein-post-run-939340394421.us-central1.run.app"),
            auth_token=os.getenv("DASEIN_AUTH_TOKEN"),
            request_timeout=int(os.getenv("DASEIN_REQUEST_TIMEOUT", "30")),
            max_retries=int(os.getenv("DASEIN_MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("DASEIN_RETRY_DELAY", "1.0"))
        )
    
    def get_headers(self) -> dict:
        """Get HTTP headers for requests"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "dasein-sdk/0.1.0"
        }
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

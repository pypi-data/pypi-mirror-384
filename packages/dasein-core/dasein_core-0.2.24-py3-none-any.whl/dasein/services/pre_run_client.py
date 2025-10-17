"""
Pre-run service client for rule selection
"""

import json
import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .service_config import ServiceConfig

logger = logging.getLogger(__name__)


@dataclass
class RuleSelectionRequest:
    """Request for rule selection"""
    query: str
    agent_fingerprint: Optional[str] = None
    artifacts: Optional[List[str]] = None
    limits: Optional[Dict[str, int]] = None
    run_id: Optional[str] = None
    max_rules_per_layer: Optional[int] = 5
    performance_tracking_id: Optional[str] = None
    is_baseline: bool = False
    verbose: bool = False


@dataclass
class RuleSelectionResponse:
    """Response from rule selection"""
    rules: List[Dict[str, Any]]
    rationale: str
    version: str
    latency_ms: int
    run_id: str


class PreRunClient:
    """Client for the pre-run rule selection service"""
    
    def __init__(self, config: ServiceConfig):
        self.config = config
        self.session = self._create_session()
        self._last_run_id = None
    
    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry configuration"""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def select_rules(self, request: RuleSelectionRequest) -> RuleSelectionResponse:
        """
        Select rules for an incoming run
        
        Args:
            request: Rule selection request
            
        Returns:
            Rule selection response
            
        Raises:
            requests.RequestException: If the request fails
        """
        url = f"{self.config.pre_run_url}/v1/pre-run/select"
        
        payload = {
            "query": request.query,
            "agent_fingerprint": request.agent_fingerprint,
            "artifacts": request.artifacts or [],
            "limits": request.limits or {},
            "run_id": request.run_id,
            "max_rules_per_layer": request.max_rules_per_layer,
            "performance_tracking_id": request.performance_tracking_id,
            "is_baseline": request.is_baseline,
            "verbose": request.verbose
        }
        
        logger.info(f"Selecting rules for query: {str(request.query)[:50]}...")
        logger.info(f"Request payload: {payload}")
        
        start_time = time.time()
        
        try:
            response = self.session.post(
                url,
                json=payload,
                headers=self.config.get_headers(),
                timeout=self.config.request_timeout
            )
            
            if not response.ok:
                logger.error(f"Pre-run service error {response.status_code}: {response.text}")
            response.raise_for_status()
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            data = response.json()
            
            # Store the run_id for later use
            self._last_run_id = data.get("run_id")
            
            return RuleSelectionResponse(
                rules=data.get("rules", []),
                rationale=data.get("rationale", ""),
                version=data.get("version", "unknown"),
                latency_ms=latency_ms,
                run_id=self._last_run_id
            )
            
        except requests.RequestException as e:
            logger.error(f"Failed to select rules: {e}")
            raise
    
    def health_check(self) -> bool:
        """Check if the pre-run service is healthy"""
        try:
            url = f"{self.config.pre_run_url}/v1/healthz"
            response = self.session.get(
                url,
                headers=self.config.get_headers(),
                timeout=5
            )
            response.raise_for_status()
            return response.json().get("ok", False)
        except requests.RequestException:
            return False

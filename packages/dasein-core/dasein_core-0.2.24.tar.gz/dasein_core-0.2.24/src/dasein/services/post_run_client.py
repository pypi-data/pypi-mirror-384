"""
Post-run service client for rule synthesis
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
class RuleSynthesisRequest:
    """Request for rule synthesis"""
    run_id: str
    trace: List[Dict[str, Any]]
    outcomes: List[Dict[str, Any]]
    artifacts: Optional[List[Dict[str, Any]]] = None
    signals: Optional[Dict[str, Any]] = None
    original_query: Optional[str] = None
    agent_fingerprint: Optional[str] = None
    max_rules: Optional[int] = 5
    performance_tracking_id: Optional[str] = None
    skip_synthesis: bool = False
    wait_for_synthesis: bool = False
    step_id: Optional[str] = None
    tools_metadata: Optional[List[Dict[str, Any]]] = None  # Tool metadata for Stage 3.5 tool grounding
    graph_metadata: Optional[Dict[str, Any]] = None  # Graph metadata for Stage 3.5 node grounding
    rules_applied: Optional[List[str]] = None  # Rule IDs that were selected by pre-run and applied during execution
    context_hash: Optional[str] = None  # Context hash for grouping traces (query + agent fingerprint)


@dataclass
class RuleSynthesisResponse:
    """Response from rule synthesis"""
    new_rules: List[Dict[str, Any]]
    updated_rules: List[Dict[str, Any]]
    rejected: List[Dict[str, Any]]
    notes: str
    # Include KPIs returned by the post-run service
    kpis: Optional[Dict[str, Any]] = None


class PostRunClient:
    """Client for the post-run rule synthesis service"""
    
    def __init__(self, config: ServiceConfig):
        self.config = config
        self.session = self._create_session()
    
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
    
    def synthesize_rules(self, request: RuleSynthesisRequest) -> RuleSynthesisResponse:
        """
        Synthesize rules from run telemetry
        
        Args:
            request: Rule synthesis request
            
        Returns:
            Rule synthesis response
            
        Raises:
            requests.RequestException: If the request fails
        """
        url = f"{self.config.post_run_url}/v1/post-run/synthesize"
        
        payload = {
            "run_id": request.run_id,
            "trace": request.trace,
            "outcomes": request.outcomes,
            "artifacts": request.artifacts or [],
            "signals": request.signals or {},
            "original_query": request.original_query,
            "agent_fingerprint": request.agent_fingerprint,
            "max_rules": request.max_rules,
            "performance_tracking_id": request.performance_tracking_id,
            "skip_synthesis": request.skip_synthesis,
            "wait_for_synthesis": request.wait_for_synthesis,
            "step_id": request.step_id,
            "tools_metadata": request.tools_metadata or [],
            "graph_metadata": request.graph_metadata or {},
            "rules_applied": request.rules_applied or [],
            "context_hash": request.context_hash,
        }
        
        logger.info(f"Synthesizing rules for run: {request.run_id}")
        
        try:
            response = self.session.post(
                url,
                json=payload,
                headers=self.config.get_headers(),
                timeout=600  # 10 minutes for rule synthesis (deep research agents need more time)
            )
            response.raise_for_status()
            
            data = response.json()
            
            return RuleSynthesisResponse(
                new_rules=data.get("new_rules", []),
                updated_rules=data.get("updated_rules", []),
                rejected=data.get("rejected", []),
                notes=data.get("notes", ""),
                kpis=data.get("kpis")
            )
            
        except requests.RequestException as e:
            logger.error(f"Failed to synthesize rules: {e}")
            raise
    
    def health_check(self) -> bool:
        """Check if the post-run service is healthy"""
        try:
            url = f"{self.config.post_run_url}/v1/healthz"
            response = self.session.get(
                url,
                headers=self.config.get_headers(),
                timeout=5
            )
            response.raise_for_status()
            return response.json().get("ok", False)
        except requests.RequestException:
            return False

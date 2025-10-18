"""
Service adapter that replaces in-memory storage with HTTP service calls
"""

import logging
from typing import List, Dict, Any, Optional
from .service_config import ServiceConfig
from .pre_run_client import PreRunClient, RuleSelectionRequest
from .post_run_client import PostRunClient, RuleSynthesisRequest
# Rule schema migrated to post-run service - using dict for now

logger = logging.getLogger(__name__)


class ServiceAdapter:
    """
    Adapter that replaces in-memory storage with HTTP service calls.
    This allows the existing dasein code to work with distributed services.
    """
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        self.config = config or ServiceConfig.from_env()
        self.pre_run_client = PreRunClient(self.config)
        self.post_run_client = PostRunClient(self.config)
        self._last_run_id = None
        
        # Check service health
        self._check_services()
    
    def _check_services(self):
        """Check if services are available"""
        pre_run_healthy = self.pre_run_client.health_check()
        post_run_healthy = self.post_run_client.health_check()
        
        if not pre_run_healthy:
            logger.warning("Pre-run service is not healthy")
        if not post_run_healthy:
            logger.warning("Post-run service is not healthy")
        
        if not (pre_run_healthy and post_run_healthy):
            logger.warning("Some services are not available - falling back to local mode")
    
    def select_rules(self, query: str, agent_fingerprint: Optional[str] = None, 
                    artifacts: Optional[List[str]] = None, limits: Optional[Dict[str, int]] = None,
                    run_id: Optional[str] = None, max_rules_per_layer: Optional[int] = 5,
                    performance_tracking_id: Optional[str] = None, is_baseline: bool = False,
                    verbose: bool = False) -> List[Dict[str, Any]]:
        """
        Select rules for an incoming run (replaces local rule selection)
        
        Args:
            query: User query
            agent_fingerprint: Agent fingerprint
            artifacts: List of artifacts
            limits: Selection limits
            run_id: Run identifier
            max_rules_per_layer: Maximum rules per layer (default: 5)
            performance_tracking_id: Performance tracking session ID for rule isolation
            
        Returns:
            List of selected rules
        """
        try:
            request = RuleSelectionRequest(
                query=query,
                agent_fingerprint=agent_fingerprint,
                artifacts=artifacts,
                limits=limits,
                run_id=run_id,
                max_rules_per_layer=max_rules_per_layer,
                performance_tracking_id=performance_tracking_id,
                is_baseline=is_baseline,
                verbose=verbose
            )
            
            response = self.pre_run_client.select_rules(request)
            
            # Store the run_id for later use in post-run phase
            self._last_run_id = response.run_id
            
            # Return rule data as dicts (Rule schema migrated to post-run service)
            rules = response.rules
            
            logger.info(f"Selected {len(rules)} rules from pre-run service")
            return rules
            
        except Exception as e:
            logger.error(f"Failed to select rules from service: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            # Return empty list as fallback
            return []
    
    def synthesize_rules(self, run_id: str, trace: List[Dict[str, Any]], 
                        outcomes: List[Dict[str, Any]], artifacts: Optional[List[Dict[str, Any]]] = None,
                        signals: Optional[Dict[str, Any]] = None, original_query: Optional[str] = None,
                        max_rules: Optional[int] = 5, performance_tracking_id: Optional[str] = None,
                        skip_synthesis: bool = False, agent_fingerprint: Optional[str] = None,
                        step_id: Optional[str] = None, post_run_mode: str = "full",
                        wait_for_synthesis: bool = False, tools_metadata: Optional[List[Dict[str, Any]]] = None,
                        graph_metadata: Optional[Dict[str, Any]] = None, rules_applied: Optional[List[str]] = None,
                        context_hash: Optional[str] = None) -> Dict[str, Any]:
        """
        Synthesize rules from run telemetry (replaces local rule synthesis)
        
        Args:
            run_id: Run identifier
            trace: Run trace data
            outcomes: Run outcomes
            artifacts: List of artifacts
            signals: Additional signals
            original_query: Original user query for final success determination
            max_rules: Maximum number of rules to synthesize
            performance_tracking_id: Performance tracking session ID for rule isolation
            skip_synthesis: Skip expensive rule synthesis, only return KPIs (deprecated, use post_run_mode)
            step_id: Step identifier for parallel execution tracking
            post_run_mode: "full" (KPIs + rule synthesis) or "kpi_only" (KPIs only, no rule synthesis)
            wait_for_synthesis: Wait for synthesis to complete before returning (for benchmarking)
            
        Returns:
            Synthesis results including KPIs
        """
        try:
            # Use the stored run_id if not provided
            actual_run_id = run_id or self._last_run_id
            if not actual_run_id:
                raise ValueError("No run_id available for synthesis")
            
            # Convert post_run_mode to skip_synthesis for backward compatibility
            # "kpi_only" mode skips rule synthesis
            should_skip_synthesis = (post_run_mode == "kpi_only") or skip_synthesis
            
            request = RuleSynthesisRequest(
                run_id=actual_run_id,
                trace=trace,
                outcomes=outcomes,
                artifacts=artifacts,
                signals=signals,
                original_query=original_query,
                agent_fingerprint=agent_fingerprint,
                max_rules=max_rules,
                performance_tracking_id=performance_tracking_id,
                skip_synthesis=should_skip_synthesis,
                wait_for_synthesis=wait_for_synthesis,
                step_id=step_id,
                tools_metadata=tools_metadata,
                graph_metadata=graph_metadata,
                rules_applied=rules_applied,
                context_hash=context_hash
            )
            
            response = self.post_run_client.synthesize_rules(request)
            
            result = {
                "new_rules": response.new_rules,
                "updated_rules": response.updated_rules,
                "rejected": response.rejected,
                "notes": response.notes,
                "kpis": response.kpis
            }
            
            logger.info(f"Synthesized {len(response.new_rules)} new rules from post-run service")
            return result
            
        except Exception as e:
            logger.error(f"Failed to synthesize rules from service: {e}")
            # Return empty result as fallback
            return {
                "new_rules": [],
                "updated_rules": [],
                "rejected": [],
                "notes": f"Service error: {e}",
                "kpis": None
            }

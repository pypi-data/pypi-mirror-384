"""
Dasein Injector Module - Main orchestrator for advice injection

This module provides the main injection orchestrator that manages guard maps,
dispatches to correct site strategies, and handles logging and graph integration.
"""

from typing import Any, Dict, Union, Optional, Tuple
import logging
from .config import (
    INJECTION_ENABLED_SITES, INJECTION_LOG_PREFIX, ADVICE_MAX_CHARS
)
from .injection_strategies import get_injection_strategy
from .advice_format import render_advice

logger = logging.getLogger(__name__)

# Global guard map to prevent duplicate injections
_guard_map: set = set()


def inject_hint(
    site: str,
    input_obj: Union[str, Dict[str, Any]],
    *,
    run_id: str,
    step_id: str,
    rule: Any,
    selection_meta: Dict[str, Any],
    baseline_source: Optional[str] = None,
    graph_store: Optional[Any] = None
) -> Tuple[Union[str, Dict[str, Any]], Dict[str, Any]]:
    """
    Inject advice hint into input object for the specified site.
    
    Args:
        site: Injection site ("planner", "codegen", "tool")
        input_obj: Input object to modify (string or dict)
        run_id: Run identifier
        step_id: Step identifier
        rule: Rule object containing advice
        selection_meta: Selection metadata from rule selection
        baseline_source: Source of baseline metrics (optional)
        graph_store: Graph store for linking rules to steps (optional)
        
    Returns:
        Tuple of (modified_input, apply_meta)
    """
    # 1) Check if site is enabled
    if site not in INJECTION_ENABLED_SITES:
        logger.debug(f"{INJECTION_LOG_PREFIX} Site {site} not enabled, skipping injection")
        return input_obj, {"skipped": True, "reason": "site_disabled"}
    
    # 2) Check guard map for duplicate injection
    guard_key = (run_id, step_id, site)
    if guard_key in _guard_map:
        logger.debug(f"{INJECTION_LOG_PREFIX} Already injected for {guard_key}, skipping")
        return input_obj, {"skipped": True, "reason": "already_applied"}
    
    try:
        # 3) Get injection strategy
        strategy = get_injection_strategy(site)
        
        # 4) Check if strategy is applicable
        if not strategy.is_applicable(step_id):  # Using step_id as step context
            logger.debug(f"{INJECTION_LOG_PREFIX} Strategy not applicable for {site}")
            return input_obj, {"skipped": True, "reason": "not_applicable"}
        
        # 5) Render preamble
        preamble = strategy.render_preamble(rule, selection_meta)
        
        # 6) Apply injection
        modified_input = strategy.apply(input_obj, preamble)
        
        # 7) Add to guard map
        _guard_map.add(guard_key)
        
        # 8) Build apply_meta
        apply_meta = _build_apply_meta(
            rule, selection_meta, baseline_source, preamble
        )
        
        # 9) Log injection
        _log_injection(site, rule, selection_meta, apply_meta, baseline_source)
        
        # 10) Handle graph integration
        if graph_store:
            _link_rule_to_step(graph_store, rule, run_id, step_id, apply_meta)
        
        return modified_input, apply_meta
        
    except Exception as e:
        logger.warning(f"{INJECTION_LOG_PREFIX} Injection failed for {site}: {e}")
        return input_obj, {"skipped": True, "reason": "error", "error": str(e)}


def _build_apply_meta(
    rule: Any,
    selection_meta: Dict[str, Any],
    baseline_source: Optional[str],
    preamble: str
) -> Dict[str, Any]:
    """
    Build apply metadata dictionary.
    
    Args:
        rule: Rule object
        selection_meta: Selection metadata
        baseline_source: Baseline source
        preamble: Rendered preamble
        
    Returns:
        Apply metadata dictionary
    """
    # Extract rule information
    rule_id = getattr(rule, 'id', 'unknown')
    cluster_id = getattr(rule, 'cluster_id', None)
    if not cluster_id and hasattr(rule, 'meta') and isinstance(rule.meta, dict):
        cluster_id = rule.meta.get('cluster_id')
    
    # Extract selection metrics
    cost = selection_meta.get('cost', 0.0)
    similarity = selection_meta.get('similarity', 0.0)
    
    return {
        "rule_id": rule_id,
        "cluster_id": cluster_id,
        "advice_len": len(preamble),
        "selection_cost": cost,
        "similarity": similarity,
        "baseline_source": baseline_source,
        "applied": True
    }


def _log_injection(
    site: str,
    rule: Any,
    selection_meta: Dict[str, Any],
    apply_meta: Dict[str, Any],
    baseline_source: Optional[str]
) -> None:
    """
    Log injection details.
    
    Args:
        site: Injection site
        rule: Rule object
        selection_meta: Selection metadata
        apply_meta: Apply metadata
        baseline_source: Baseline source
    """
    rule_id = apply_meta.get('rule_id', 'unknown')
    cluster_id = apply_meta.get('cluster_id', '-')
    advice_len = apply_meta.get('advice_len', 0)
    cost = apply_meta.get('selection_cost', 0.0)
    similarity = apply_meta.get('similarity', 0.0)
    baseline = baseline_source or 'unknown'
    
    logger.info(
        f"{INJECTION_LOG_PREFIX} site={site} rule={rule_id} cluster={cluster_id} "
        f"len={advice_len} cost={cost:.2f} sim={similarity:.2f} baseline={baseline}"
    )


def _link_rule_to_step(
    graph_store: Any,
    rule: Any,
    run_id: str,
    step_id: str,
    apply_meta: Dict[str, Any]
) -> None:
    """
    Link rule to step in graph store and stage uplift metrics.
    
    Args:
        graph_store: Graph store instance
        rule: Rule object
        run_id: Run identifier
        step_id: Step identifier
        apply_meta: Apply metadata
    """
    try:
        # Import here to avoid circular imports
        from .graph_hooks import link_rule_supports_step, stage_uplift_metrics_shell
        
        # Link rule to step
        link_rule_supports_step(
            graph_store, rule, run_id, step_id, apply_meta
        )
        
        # Stage uplift metrics shell
        stage_uplift_metrics_shell(
            graph_store, rule, run_id, step_id, apply_meta
        )
        
    except Exception as e:
        logger.warning(f"{INJECTION_LOG_PREFIX} Graph linking failed: {e}")


def clear_guard_map() -> None:
    """
    Clear the guard map (useful for testing).
    """
    global _guard_map
    _guard_map.clear()
    logger.debug(f"{INJECTION_LOG_PREFIX} Guard map cleared")


def get_guard_map() -> set:
    """
    Get current guard map (for debugging).
    
    Returns:
        Current guard map
    """
    return _guard_map.copy()


def is_injection_guarded(run_id: str, step_id: str, site: str) -> bool:
    """
    Check if injection is already guarded for the given parameters.
    
    Args:
        run_id: Run identifier
        step_id: Step identifier
        site: Injection site
        
    Returns:
        True if already guarded, False otherwise
    """
    return (run_id, step_id, site) in _guard_map

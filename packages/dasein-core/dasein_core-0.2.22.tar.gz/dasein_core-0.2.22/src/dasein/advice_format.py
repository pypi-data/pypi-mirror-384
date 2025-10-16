"""
Dasein Advice Format Module - Safe rendering and formatting of advice text

This module provides utilities for safely rendering advice text with proper
headers, footers, and truncation. Handles different injection sites and
provides prepend/attach helpers.
"""

from typing import Dict, Any, Union
import logging
from .config import (
    ADVICE_MAX_CHARS, INJECTION_HEADERS, INJECTION_FOOTER,
    MAX_ADVICE_CHARS
)

logger = logging.getLogger(__name__)


def render_advice(rule: Any, max_len: int = None) -> str:
    """
    Safely render advice text from a rule with proper truncation.
    
    Args:
        rule: Rule object with advice_text attribute
        max_len: Maximum length for advice text (default from config)
        
    Returns:
        Safely truncated advice text
    """
    max_len = max_len or ADVICE_MAX_CHARS
    
    # Extract advice text from rule
    advice_text = ""
    if hasattr(rule, 'advice_text'):
        advice_text = rule.advice_text or ""
    elif hasattr(rule, 'meta') and isinstance(rule.meta, dict):
        advice_text = rule.meta.get('advice_text', '')
    
    # Ensure it's a string
    advice_text = str(advice_text).strip()
    
    # Truncate if too long
    if len(advice_text) > max_len:
        advice_text = advice_text[:max_len-3] + "..."
        logger.debug(f"Truncated advice text to {max_len} characters")
    
    return advice_text


def make_preamble(rule: Any, site: str, meta: Dict[str, Any]) -> str:
    """
    Create a preamble with site-specific header and footer.
    
    Args:
        rule: Rule object
        site: Injection site ("planner", "codegen", "tool")
        meta: Selection metadata
        
    Returns:
        Formatted preamble string
    """
    # Get site-specific header
    header = INJECTION_HEADERS.get(site, "--- DASEIN hint ---")
    
    # Render advice text
    advice_text = render_advice(rule)
    
    # Build preamble
    preamble_parts = [
        header,
        "",
        advice_text,
        "",
        INJECTION_FOOTER
    ]
    
    return "\n".join(preamble_parts)


def prepend_to_string(input_obj: str, preamble: str) -> str:
    """
    Prepend preamble to a string input.
    
    Args:
        input_obj: Original string input
        preamble: Preamble to prepend
        
    Returns:
        Modified string with preamble prepended
    """
    if not input_obj:
        return preamble
    
    return preamble + "\n\n" + input_obj


def prepend_to_dict_field(input_obj: Dict[str, Any], field: str, preamble: str) -> Dict[str, Any]:
    """
    Prepend preamble to a specific field in a dictionary.
    
    Args:
        input_obj: Original dictionary input
        field: Field name to prepend to
        preamble: Preamble to prepend
        
    Returns:
        Modified dictionary with preamble prepended to field
    """
    if not isinstance(input_obj, dict):
        return input_obj
    
    # Create a copy to avoid modifying original
    modified = input_obj.copy()
    
    # Get existing field value
    existing_value = modified.get(field, "")
    if not existing_value:
        modified[field] = preamble
    else:
        modified[field] = preamble + "\n\n" + str(existing_value)
    
    return modified


def attach_to_tool_args(input_obj: Dict[str, Any], preamble: str) -> Dict[str, Any]:
    """
    Attach preamble to tool arguments as dasein_hint.
    
    Args:
        input_obj: Original dictionary input (tool args)
        preamble: Preamble to attach
        
    Returns:
        Modified dictionary with dasein_hint attached
    """
    if not isinstance(input_obj, dict):
        return input_obj
    
    # Create a copy to avoid modifying original
    modified = input_obj.copy()
    
    # Ensure args field exists
    if "args" not in modified:
        modified["args"] = {}
    
    # Attach dasein_hint
    modified["args"]["dasein_hint"] = preamble
    
    return modified


def safe_truncate(text: str, max_len: int) -> str:
    """
    Safely truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_len: Maximum length
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if not text or len(text) <= max_len:
        return text
    
    return text[:max_len-3] + "..."


def validate_advice_content(advice_text: str) -> bool:
    """
    Validate advice content for safety (placeholder for future sanitization).
    
    Args:
        advice_text: Advice text to validate
        
    Returns:
        True if content is safe, False otherwise
    """
    # TODO: Implement content sanitization for codegen/tool sites
    # For now, just check basic safety
    if not advice_text or len(advice_text.strip()) == 0:
        return False
    
    # Basic safety checks
    dangerous_patterns = [
        "rm -rf",
        "sudo",
        "chmod 777",
        "eval(",
        "exec(",
        "__import__",
    ]
    
    advice_lower = advice_text.lower()
    for pattern in dangerous_patterns:
        if pattern in advice_lower:
            logger.warning(f"Potentially dangerous content detected: {pattern}")
            return False
    
    return True

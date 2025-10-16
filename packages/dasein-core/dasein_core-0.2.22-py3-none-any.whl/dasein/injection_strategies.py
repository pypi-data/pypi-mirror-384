"""
Dasein Injection Strategies Module - Site-specific injection strategies

This module implements site-specific injection strategies for different
agent execution sites (planner, codegen, tool). Each strategy handles
the specific format and requirements of its target site.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Union
import logging
from .advice_format import (
    make_preamble, prepend_to_string, prepend_to_dict_field,
    attach_to_tool_args, validate_advice_content
)

logger = logging.getLogger(__name__)


class InjectionStrategy(ABC):
    """
    Base class for injection strategies.
    
    Each strategy handles injection for a specific site type and implements
    the common interface for applicability checking, preamble rendering, and application.
    """
    
    @abstractmethod
    def is_applicable(self, step: Any) -> bool:
        """
        Check if this strategy is applicable to the given step.
        
        Args:
            step: Step object or context
            
        Returns:
            True if strategy can be applied, False otherwise
        """
        pass
    
    @abstractmethod
    def render_preamble(self, rule: Any, meta: Dict[str, Any]) -> str:
        """
        Render the preamble for this strategy.
        
        Args:
            rule: Rule object
            meta: Selection metadata
            
        Returns:
            Formatted preamble string
        """
        pass
    
    @abstractmethod
    def apply(self, input_obj: Union[str, Dict[str, Any]], preamble: str) -> Union[str, Dict[str, Any]]:
        """
        Apply the preamble to the input object.
        
        Args:
            input_obj: Original input object
            preamble: Preamble to apply
            
        Returns:
            Modified input object of the same type
        """
        pass


class PlannerInjection(InjectionStrategy):
    """
    Injection strategy for planner steps.
    
    Handles injection into user input or planner context.
    """
    
    def is_applicable(self, step: Any) -> bool:
        """Planner injection is always applicable."""
        return True
    
    def render_preamble(self, rule: Any, meta: Dict[str, Any]) -> str:
        """Render preamble for planner injection."""
        return make_preamble(rule, "planner", meta)
    
    def apply(self, input_obj: Union[str, Dict[str, Any]], preamble: str) -> Union[str, Dict[str, Any]]:
        """
        Apply preamble to planner input.
        
        Handles both string inputs and dictionary inputs with 'input' field.
        """
        if isinstance(input_obj, str):
            return prepend_to_string(input_obj, preamble)
        elif isinstance(input_obj, dict):
            return prepend_to_dict_field(input_obj, "input", preamble)
        else:
            logger.warning("PlannerInjection: Unsupported input type, returning unchanged")
            return input_obj


class CodegenInjection(InjectionStrategy):
    """
    Injection strategy for codegen steps.
    
    Handles injection into code generation instructions or context.
    """
    
    def is_applicable(self, step: Any) -> bool:
        """Codegen injection is always applicable."""
        return True
    
    def render_preamble(self, rule: Any, meta: Dict[str, Any]) -> str:
        """Render preamble for codegen injection."""
        return make_preamble(rule, "codegen", meta)
    
    def apply(self, input_obj: Union[str, Dict[str, Any]], preamble: str) -> Union[str, Dict[str, Any]]:
        """
        Apply preamble to codegen input.
        
        Handles both string inputs and dictionary inputs with 'instructions' field.
        """
        # Validate advice content for safety
        advice_text = getattr(rule, 'advice_text', '') if hasattr(rule, 'advice_text') else ''
        if not validate_advice_content(advice_text):
            logger.warning("CodegenInjection: Unsafe advice content detected, skipping injection")
            return input_obj
        
        if isinstance(input_obj, str):
            return prepend_to_string(input_obj, preamble)
        elif isinstance(input_obj, dict):
            return prepend_to_dict_field(input_obj, "instructions", preamble)
        else:
            logger.warning("CodegenInjection: Unsupported input type, returning unchanged")
            return input_obj


class ToolInjection(InjectionStrategy):
    """
    Injection strategy for tool steps.
    
    Handles injection into tool arguments or context.
    """
    
    def is_applicable(self, step: Any) -> bool:
        """Tool injection is always applicable."""
        return True
    
    def render_preamble(self, rule: Any, meta: Dict[str, Any]) -> str:
        """Render preamble for tool injection."""
        return make_preamble(rule, "tool", meta)
    
    def apply(self, input_obj: Union[str, Dict[str, Any]], preamble: str) -> Union[str, Dict[str, Any]]:
        """
        Apply preamble to tool input.
        
        For dictionary inputs, attaches as 'dasein_hint' in args.
        For string inputs, prepends the preamble.
        """
        if isinstance(input_obj, dict):
            return attach_to_tool_args(input_obj, preamble)
        elif isinstance(input_obj, str):
            return prepend_to_string(input_obj, preamble)
        else:
            logger.warning("ToolInjection: Unsupported input type, returning unchanged")
            return input_obj


# Registry of injection strategies
INJECTION_STRATEGIES = {
    "planner": PlannerInjection(),
    "codegen": CodegenInjection(),
    "tool": ToolInjection(),
}


def get_injection_strategy(site: str) -> InjectionStrategy:
    """
    Get the injection strategy for a specific site.
    
    Args:
        site: Site name ("planner", "codegen", "tool")
        
    Returns:
        Injection strategy instance
        
    Raises:
        ValueError: If site is not supported
    """
    if site not in INJECTION_STRATEGIES:
        raise ValueError(f"Unsupported injection site: {site}")
    
    return INJECTION_STRATEGIES[site]


def get_supported_sites() -> list:
    """
    Get list of supported injection sites.
    
    Returns:
        List of supported site names
    """
    return list(INJECTION_STRATEGIES.keys())

"""
Dasein - Universal memory for agentic codegen.

Attach a brain to any agent in a single line.

Usage:
    from dasein import cognate
    
    # Basic usage - wrap any agent
    wrapped_agent = cognate(your_agent)
    result = wrapped_agent.run("your query")
    
    # Advanced usage - customize rule selection weights
    wrapped_agent = cognate(your_agent, weights={
        "w1": 2.0,  # Favor successful rules
        "w2": 0.5,  # Less emphasis on turns
        "w3": 1.0,  # Standard uncertainty penalty
        "w4": 3.0,  # Heavily favor token efficiency
        "w5": 0.1   # Minimal time emphasis
    })
"""

# Core API
from .api import cognate, inspect_rules, reset_brain

# Trace tools
from .capture import print_trace, get_trace, clear_trace

# Rule injection
from .injector import inject_hint

# Core types and events
from .types import (
    StepType, CostSource, TokenUsage, TimeWindow, MinimalContext,
    RunId, StepId, RuleId, MessageId, ToolCallId, CodeBlockId, 
    ArtifactId, ObservationId, OutcomeId
)
from .events import (
    Message, ToolCall, CodeBlock, Artifact, Observation, Step, Outcome,
    EventStore, TokenAndTimeMixin
)
from .extractors import (
    detect_fenced_code_blocks, try_parse_json_yaml, extract_symbols_and_uris,
    text_fingerprint, excerpt
)
from .trace_buffer import TraceBuffer

# Distributed services
from .services import ServiceConfig, PreRunClient, PostRunClient, ServiceAdapter

__version__ = "0.1.1"
__all__ = [
    # Core API
    "cognate",
    "inspect_rules", 
    "reset_brain",
    
    # Trace tools
    "print_trace",
    "get_trace",
    "clear_trace",
    
    # Rule injection
    "inject_hint",
    
    # Types
    "StepType", "CostSource", "TokenUsage", "TimeWindow", "MinimalContext",
    "RunId", "StepId", "RuleId", "MessageId", "ToolCallId", "CodeBlockId",
    "ArtifactId", "ObservationId", "OutcomeId",
    
    # Events
    "Message", "ToolCall", "CodeBlock", "Artifact", "Observation", "Step", "Outcome",
    "EventStore", "TokenAndTimeMixin",
    
    # Extractors
    "detect_fenced_code_blocks", "try_parse_json_yaml", "extract_symbols_and_uris",
    "text_fingerprint", "excerpt",
    
    # Trace Buffer
    "TraceBuffer",
    
    # Distributed Services
    "ServiceConfig", "PreRunClient", "PostRunClient", "ServiceAdapter",
]
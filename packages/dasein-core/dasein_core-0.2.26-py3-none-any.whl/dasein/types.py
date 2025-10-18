"""
Dasein Types Module - Core type definitions

This module provides core enums, dataclasses, and type aliases for the dasein library.
Pure typing layer with no business logic.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict, Any

# Type aliases for clarity
RunId = str
StepId = str
RuleId = str
MessageId = str
ToolCallId = str
CodeBlockId = str
ArtifactId = str
ObservationId = str
OutcomeId = str


class StepType(str, Enum):
    """Types of execution steps in the agent workflow."""
    PLANNER = "planner"
    TOOL = "tool"
    CODEGEN = "codegen"
    LLM = "llm"
    CHAIN = "chain"


class CostSource(str, Enum):
    """Source of cost/token information."""
    PROVIDER = "provider"
    ESTIMATED = "estimated"


@dataclass
class TokenUsage:
    """Token usage information with cost source attribution."""
    prompt: int = 0
    output: int = 0
    total: int = 0
    cost_source: Optional[CostSource] = None
    
    def __post_init__(self):
        """Calculate total if not explicitly set."""
        if self.total == 0 and (self.prompt > 0 or self.output > 0):
            self.total = self.prompt + self.output


@dataclass
class TimeWindow:
    """Time window for measuring duration."""
    t_ms_start: Optional[int] = None
    t_ms_end: Optional[int] = None
    
    def duration_ms(self) -> Optional[int]:
        """Calculate duration in milliseconds."""
        if self.t_ms_start is None or self.t_ms_end is None:
            return None
        return self.t_ms_end - self.t_ms_start


@dataclass
class MinimalContext:
    """Minimal context information for events."""
    run_id: RunId
    scope_tags: List[str] = None
    
    def __post_init__(self):
        """Initialize scope_tags if not provided."""
        if self.scope_tags is None:
            self.scope_tags = []


@dataclass
class FormatSignals:
    """Format signals detected in tool inputs."""
    has_backticks: bool = False
    has_fenced_block: bool = False
    fenced_lang: str = ""
    leading_backticks: int = 0
    trailing_backticks: int = 0


@dataclass
class InputEvidence:
    """Safe evidence about input without exposing payload bodies."""
    input_len: int = 0
    prefix_16: str = ""
    suffix_16: str = ""
    sha1: str = ""


@dataclass
class ErrorItem:
    """Error information with optional format detection."""
    type: str
    msg: str
    at: Dict[str, Any]
    fingerprint: Optional[str] = None
    format_signals: Optional[FormatSignals] = None
    input_evidence: Optional[InputEvidence] = None


@dataclass
class StepItem:
    """Step information with optional format signals."""
    step_type: str
    tool: Optional[str] = None
    ms: Optional[int] = None
    in_tokens: Optional[int] = None
    out_tokens: Optional[int] = None
    input_format_signals: Optional[FormatSignals] = None

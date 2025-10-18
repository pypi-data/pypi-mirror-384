"""
Dasein Events Module - Event dataclasses and EventStore

This module provides dataclasses for all traceable entities and an EventStore class
to hold them in memory. No embeddings, no LLM calls, no persistence.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from .types import (
    RunId, StepId, MessageId, ToolCallId, CodeBlockId, ArtifactId, 
    ObservationId, OutcomeId, StepType, TokenUsage, TimeWindow
)

logger = logging.getLogger(__name__)


@dataclass
class TokenAndTimeMixin:
    """Mixin for entities that have token usage and timing information."""
    pass


@dataclass
class Message:
    """Represents a message in the conversation."""
    id: MessageId
    run_id: RunId
    role: str
    text_excerpt: str
    text_hash: str
    modality: str = "text"
    
    def __str__(self) -> str:
        return f"Message({self.id}: {self.role})"


@dataclass
class ToolCall:
    """Represents a tool call with arguments."""
    id: ToolCallId
    run_id: RunId
    name: str
    args_repr: str
    args_hash: str
    
    def __str__(self) -> str:
        return f"ToolCall({self.id}: {self.name})"


@dataclass
class CodeBlock:
    """Represents a code block with language and content."""
    id: CodeBlockId
    run_id: RunId
    language: str
    text_hash: str
    lines: Optional[int] = None
    
    def __str__(self) -> str:
        return f"CodeBlock({self.id}: {self.language})"


@dataclass
class Artifact:
    """Represents an artifact with MIME type and tags."""
    id: ArtifactId
    run_id: RunId
    mime_type: str
    tags: List[str] = field(default_factory=list)
    content_hash: str = ""
    excerpt: Optional[str] = None
    
    def __str__(self) -> str:
        return f"Artifact({self.id}: {self.mime_type})"


@dataclass
class Observation:
    """Represents an observation with optional structured data."""
    id: ObservationId
    run_id: RunId
    text_excerpt: str
    text_hash: str
    structured: bool = False
    
    def __str__(self) -> str:
        return f"Observation({self.id}: structured={self.structured})"


@dataclass
class Step(TokenAndTimeMixin):
    """Represents an execution step with token and timing information."""
    id: StepId
    run_id: RunId
    parent_run_id: Optional[str] = None
    step_type: StepType = StepType.TOOL
    ts: int = 0
    tool_name: Optional[str] = None
    ok: Optional[bool] = None
    tokens: TokenUsage = field(default_factory=TokenUsage)
    time: TimeWindow = field(default_factory=TimeWindow)
    
    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.ts == 0:
            self.ts = int(datetime.now().timestamp() * 1000)  # milliseconds
    
    def __str__(self) -> str:
        return f"Step({self.id}: {self.step_type})"


@dataclass
class Outcome(TokenAndTimeMixin):
    """Represents the outcome of an execution with return values."""
    id: OutcomeId
    run_id: RunId
    return_values_excerpt: Optional[str] = None
    return_values_hash: Optional[str] = None
    success: Optional[bool] = None
    tokens: TokenUsage = field(default_factory=TokenUsage)
    time: TimeWindow = field(default_factory=TimeWindow)
    
    def __str__(self) -> str:
        return f"Outcome({self.id}: success={self.success})"


class EventStore:
    """
    In-memory event store for holding all traceable entities.
    
    Provides add/get methods for each entity type and utility methods
    for aggregating token usage and timing information.
    """
    
    def __init__(self):
        """Initialize empty event store."""
        # Entity storage
        self._messages: Dict[MessageId, Message] = {}
        self._tool_calls: Dict[ToolCallId, ToolCall] = {}
        self._code_blocks: Dict[CodeBlockId, CodeBlock] = {}
        self._artifacts: Dict[ArtifactId, Artifact] = {}
        self._observations: Dict[ObservationId, Observation] = {}
        self._steps: Dict[StepId, Step] = {}
        self._outcomes: Dict[OutcomeId, Outcome] = {}
        
        logger.info("[DASEIN][EVENTS] EventStore initialized")
    
    # Validation helpers
    def _require_nonempty(self, name: str, value: str) -> bool:
        """Validate that a required string value is non-empty."""
        if not value or not value.strip():
            self._safe_log_warning(f"Required field '{name}' is empty")
            return False
        return True
    
    def _safe_log_warning(self, msg: str) -> None:
        """Log warning message safely."""
        # Avoid direct prints; rely on logger
        logger.warning(f"[DASEIN][EVENTS] {msg}")
    
    # Add methods for each entity type
    def add_message(self, message: Message) -> bool:
        """Add a message to the store."""
        if not self._require_nonempty("message.id", message.id):
            return False
        if not self._require_nonempty("message.run_id", message.run_id):
            return False
        
        self._messages[message.id] = message
        logger.debug(f"[DASEIN][EVENTS] Added message: {message.id}")
        return True
    
    def add_tool_call(self, tool_call: ToolCall) -> bool:
        """Add a tool call to the store."""
        if not self._require_nonempty("tool_call.id", tool_call.id):
            return False
        if not self._require_nonempty("tool_call.run_id", tool_call.run_id):
            return False
        
        self._tool_calls[tool_call.id] = tool_call
        logger.debug(f"[DASEIN][EVENTS] Added tool call: {tool_call.id}")
        return True
    
    def add_code_block(self, code_block: CodeBlock) -> bool:
        """Add a code block to the store."""
        if not self._require_nonempty("code_block.id", code_block.id):
            return False
        if not self._require_nonempty("code_block.run_id", code_block.run_id):
            return False
        
        self._code_blocks[code_block.id] = code_block
        logger.debug(f"[DASEIN][EVENTS] Added code block: {code_block.id}")
        return True
    
    def add_artifact(self, artifact: Artifact) -> bool:
        """Add an artifact to the store."""
        if not self._require_nonempty("artifact.id", artifact.id):
            return False
        if not self._require_nonempty("artifact.run_id", artifact.run_id):
            return False
        
        self._artifacts[artifact.id] = artifact
        logger.debug(f"[DASEIN][EVENTS] Added artifact: {artifact.id}")
        return True
    
    def add_observation(self, observation: Observation) -> bool:
        """Add an observation to the store."""
        if not self._require_nonempty("observation.id", observation.id):
            return False
        if not self._require_nonempty("observation.run_id", observation.run_id):
            return False
        
        self._observations[observation.id] = observation
        logger.debug(f"[DASEIN][EVENTS] Added observation: {observation.id}")
        return True
    
    def add_step(self, step: Step) -> bool:
        """Add a step to the store."""
        if not self._require_nonempty("step.id", step.id):
            return False
        if not self._require_nonempty("step.run_id", step.run_id):
            return False
        
        self._steps[step.id] = step
        logger.debug(f"[DASEIN][EVENTS] Added step: {step.id}")
        return True
    
    def add_outcome(self, outcome: Outcome) -> bool:
        """Add an outcome to the store."""
        if not self._require_nonempty("outcome.id", outcome.id):
            return False
        if not self._require_nonempty("outcome.run_id", outcome.run_id):
            return False
        
        self._outcomes[outcome.id] = outcome
        logger.debug(f"[DASEIN][EVENTS] Added outcome: {outcome.id}")
        return True
    
    # Get methods for each entity type
    def get_message(self, message_id: MessageId) -> Optional[Message]:
        """Get a message by ID."""
        return self._messages.get(message_id)
    
    def get_tool_call(self, tool_call_id: ToolCallId) -> Optional[ToolCall]:
        """Get a tool call by ID."""
        return self._tool_calls.get(tool_call_id)
    
    def get_code_block(self, code_block_id: CodeBlockId) -> Optional[CodeBlock]:
        """Get a code block by ID."""
        return self._code_blocks.get(code_block_id)
    
    def get_artifact(self, artifact_id: ArtifactId) -> Optional[Artifact]:
        """Get an artifact by ID."""
        return self._artifacts.get(artifact_id)
    
    def get_observation(self, observation_id: ObservationId) -> Optional[Observation]:
        """Get an observation by ID."""
        return self._observations.get(observation_id)
    
    def get_step(self, step_id: StepId) -> Optional[Step]:
        """Get a step by ID."""
        return self._steps.get(step_id)
    
    def get_outcome(self, outcome_id: OutcomeId) -> Optional[Outcome]:
        """Get an outcome by ID."""
        return self._outcomes.get(outcome_id)
    
    # Iteration methods by run_id
    def get_messages_by_run(self, run_id: RunId) -> List[Message]:
        """Get all messages for a run."""
        return [msg for msg in self._messages.values() if msg.run_id == run_id]
    
    def get_tool_calls_by_run(self, run_id: RunId) -> List[ToolCall]:
        """Get all tool calls for a run."""
        return [tc for tc in self._tool_calls.values() if tc.run_id == run_id]
    
    def get_code_blocks_by_run(self, run_id: RunId) -> List[CodeBlock]:
        """Get all code blocks for a run."""
        return [cb for cb in self._code_blocks.values() if cb.run_id == run_id]
    
    def get_artifacts_by_run(self, run_id: RunId) -> List[Artifact]:
        """Get all artifacts for a run."""
        return [art for art in self._artifacts.values() if art.run_id == run_id]
    
    def get_observations_by_run(self, run_id: RunId) -> List[Observation]:
        """Get all observations for a run."""
        return [obs for obs in self._observations.values() if obs.run_id == run_id]
    
    def get_steps_by_run(self, run_id: RunId) -> List[Step]:
        """Get all steps for a run."""
        return [step for step in self._steps.values() if step.run_id == run_id]
    
    def get_outcomes_by_run(self, run_id: RunId) -> List[Outcome]:
        """Get all outcomes for a run."""
        return [outcome for outcome in self._outcomes.values() if outcome.run_id == run_id]
    
    # Aggregation methods
    def tally_step_tokens(self, run_id: RunId) -> TokenUsage:
        """Tally total token usage for all steps in a run."""
        steps = self.get_steps_by_run(run_id)
        
        total_prompt = sum(step.tokens.prompt for step in steps)
        total_output = sum(step.tokens.output for step in steps)
        total_tokens = sum(step.tokens.total for step in steps)
        
        # Determine cost source (prefer provider over estimated)
        cost_sources = [step.tokens.cost_source for step in steps if step.tokens.cost_source]
        cost_source = None
        if cost_sources:
            cost_source = max(cost_sources, key=lambda x: x.value)  # provider > estimated
        
        return TokenUsage(
            prompt=total_prompt,
            output=total_output,
            total=total_tokens,
            cost_source=cost_source
        )
    
    def tally_step_time_ms(self, run_id: RunId) -> int:
        """Tally total time in milliseconds for all steps in a run."""
        steps = self.get_steps_by_run(run_id)
        
        total_time = 0
        for step in steps:
            duration = step.time.duration_ms()
            if duration is not None:
                total_time += duration
        
        return total_time
    
    def pretty_counts(self) -> Dict[str, int]:
        """Get pretty counts of all stored entities."""
        return {
            'messages': len(self._messages),
            'tool_calls': len(self._tool_calls),
            'code_blocks': len(self._code_blocks),
            'artifacts': len(self._artifacts),
            'observations': len(self._observations),
            'steps': len(self._steps),
            'outcomes': len(self._outcomes)
        }
    
    def clear(self) -> None:
        """Clear all stored entities."""
        self._messages.clear()
        self._tool_calls.clear()
        self._code_blocks.clear()
        self._artifacts.clear()
        self._observations.clear()
        self._steps.clear()
        self._outcomes.clear()
        
        logger.info("[DASEIN][EVENTS] EventStore cleared")

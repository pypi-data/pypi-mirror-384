"""
API functions for Dasein package.
"""

import os
import logging
import time
from typing import Optional, Dict, Any, List
from .capture import DaseinCallbackHandler
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_core.exceptions import OutputParserException
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from .events import EventStore
from .services import ServiceAdapter
from .config import W_COST


# ============================================================================
# CONFIGURATION
# ============================================================================

# Microturn enforcement configuration
USE_LLM_MICROTURN = False  # If True, use LLM to judge which calls to allow
                           # If False, use deterministic duplicate detection only
                           # (Keep False - LLM microturn adds latency, use only for semantic rules)

# ============================================================================
# VERBOSE LOGGING HELPER
# ============================================================================

def _vprint(message: str, verbose: bool = False, force: bool = False):
    """
    Helper function for verbose printing.
    
    Args:
        message: Message to print
        verbose: Whether verbose mode is enabled
        force: If True, always print regardless of verbose setting
    """
    if force or verbose:
        print(message)


class DaseinLLMWrapper(BaseChatModel):
    """Wrapper around any LLM that captures traces for Dasein."""
    
    def __init__(self, llm, callback_handler: DaseinCallbackHandler, verbose: bool = False):
        super().__init__()
        self._llm = llm
        self._callback_handler = callback_handler
        self._trace = []
        self._verbose = verbose
    
    def _vprint(self, message: str, force: bool = False):
        """Helper for verbose printing."""
        _vprint(message, self._verbose, force)
    
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        """Generate response and capture trace."""
        self._vprint(f"[DASEIN][TRACE] LLM wrapper _generate called with {len(messages)} messages")
        
        # Get model name dynamically
        model_name = self._get_model_name()
        
        # Record start time for timing
        start_time = datetime.now()
        
        # Capture the LLM call (tokens will be updated after rule injection)
        step = {
            "step_type": "llm_start",
            "tool_name": model_name,
            "args_excerpt": str(messages)[:240] + "..." if len(str(messages)) > 240 else str(messages),
            "outcome": "",
            "ts": start_time.isoformat(),
            "run_id": None,
            "parent_run_id": None,
            "start_time": start_time,
            "tokens_input": 0,  # Will be updated after rule injection
            "tokens_output": 0,
            "duration_ms": 0,
            "success": False
        }
        self._trace.append(step)
        self._vprint(f"[DASEIN][TRACE] Captured LLM call: {len(self._trace)} total steps")
        
        # Trigger callback events for rule injection BEFORE calling the LLM
        if self._callback_handler:
            # Convert messages to the format expected by callbacks
            prompts = []
            for msg in messages:
                if hasattr(msg, 'content'):
                    prompts.append(msg.content)
                else:
                    prompts.append(str(msg))
            
            # Trigger on_llm_start callback and get modified prompts
            self._callback_handler.on_llm_start(
                serialized={"name": model_name},
                prompts=prompts,
                **kwargs
            )
            
            # Get the modified prompts from the callback handler
            modified_prompts = getattr(self._callback_handler, '_last_modified_prompts', prompts)
            
            # Check if prompts were actually modified by comparing content
            prompts_changed = False
            if len(modified_prompts) != len(prompts):
                prompts_changed = True
            else:
                for i, (orig, mod) in enumerate(zip(prompts, modified_prompts)):
                    if orig != mod:
                        prompts_changed = True
                        break
            
            # Convert modified prompts back to message format if they were changed
            if prompts_changed:
                self._vprint(f"[DASEIN][WRAPPER] Prompts were modified! Original: {len(prompts)}, Modified: {len(modified_prompts)}")
                self._vprint(f"[DASEIN][WRAPPER] Original first prompt: {prompts[0][:100]}...")
                self._vprint(f"[DASEIN][WRAPPER] Modified first prompt: {modified_prompts[0][:100]}...")
                
                # Reconstruct messages from modified prompts
                new_messages = []
                for i, prompt in enumerate(modified_prompts):
                    if i < len(messages):
                        # Update existing message content, preserving the original message type
                        if hasattr(messages[i], 'content'):
                            messages[i].content = prompt
                        else:
                            messages[i] = type(messages[i])(content=prompt)
                        new_messages.append(messages[i])
                    else:
                        # Create new message - preserve the original message type
                        from langchain_core.messages import HumanMessage, SystemMessage
                        if i == 0:  # First message should be system prompt
                            new_messages.append(SystemMessage(content=prompt))
                        else:
                            new_messages.append(HumanMessage(content=prompt))
                messages = new_messages
                self._vprint(f"[DASEIN][WRAPPER] Using modified messages for LLM call")
            else:
                self._vprint(f"[DASEIN][WRAPPER] No prompt modifications applied")
        
        # Update token count with the actual messages that will be sent to LLM
        step["tokens_input"] = self._estimate_input_tokens(messages)
        
        # Call the original LLM with potentially modified messages
        result = self._llm._generate(messages, stop=stop, run_manager=run_manager, **kwargs)
        
        # Record end time and calculate duration
        end_time = datetime.now()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Extract result text and estimate tokens
        result_text = self._extract_result_text(result)
        output_tokens = self._estimate_output_tokens(result_text)
        
        # Determine success based on result quality
        success = self._determine_success(result_text, result)
        
        # Update step with complete metrics
        step["outcome"] = result_text
        step["tokens_output"] = output_tokens
        step["duration_ms"] = duration_ms
        step["success"] = success
        step["end_time"] = end_time
        
        # Enhanced verbose logging
        self._vprint(f"[DASEIN][TRACE] LLM result: {result_text[:100]}...")
        self._vprint(f"[DASEIN][METRICS] Tokens: {step['tokens_input']}->{output_tokens} | Time: {duration_ms}ms | Success: {'OK' if success else 'FAIL'}")
        
        # 🚨 MICROTURN ENFORCEMENT - DISABLED (can interfere with tool execution)
        if False:  # Disabled
            try:
                proposed_func_name = None
                self._vprint(f"[DASEIN][MICROTURN_DEBUG] Checking result for function call...")
                if hasattr(result, 'generations') and result.generations:
                    first_gen = result.generations[0]
                    if isinstance(first_gen, list) and len(first_gen) > 0:
                        generation = first_gen[0]
                    else:
                        generation = first_gen
                    
                    self._vprint(f"[DASEIN][MICROTURN_DEBUG] generation type: {type(generation)}")
                    if hasattr(generation, 'message') and hasattr(generation.message, 'additional_kwargs'):
                        func_call = generation.message.additional_kwargs.get('function_call')
                        self._vprint(f"[DASEIN][MICROTURN_DEBUG] func_call: {func_call}")
                        if func_call and isinstance(func_call, dict) and 'name' in func_call:
                            proposed_func_name = func_call['name']
                else:
                    self._vprint(f"[DASEIN][MICROTURN_DEBUG] No generations in result")
                
                if not proposed_func_name:
                    self._vprint(f"[DASEIN][MICROTURN_DEBUG] No function call in response, skipping microturn")
                else:
                    self._vprint(f"[DASEIN][MICROTURN_DEBUG] Found proposed function: {proposed_func_name}")
                    
                    # Build execution state (BEFORE adding current call)
                    state_lines = []
                    if hasattr(self._callback_handler, '_function_calls_made') and self._callback_handler._function_calls_made:
                        for fname in sorted(self._callback_handler._function_calls_made.keys()):
                            count = len(self._callback_handler._function_calls_made[fname])
                            if count > 0:
                                state_lines.append(f"  • {fname}: called {count}x")
                    
                    state_context = "EXECUTION STATE:\n" + "\n".join(state_lines) if state_lines else "EXECUTION STATE: No calls yet"
                    
                    microturn_prompt = f"""You are a rule enforcement system. Your job is to decide if a proposed action violates the rules.

HARD RULE: You MUST make at maximum a single summary call

{state_context}

PROPOSED ACTION: Call {proposed_func_name}

DECISION:
If this action violates the rule, respond with EXACTLY: BLOCK
If this action is allowed, respond with EXACTLY: PASS

Your response (BLOCK or PASS):"""
                    
                    self._vprint(f"[DASEIN][MICROTURN_DEBUG] Calling microturn LLM...")
                    from langchain_core.messages import HumanMessage
                    messages_for_microturn = [HumanMessage(content=microturn_prompt)]
                    microturn_response = self._llm.invoke(messages_for_microturn)
                    
                    if hasattr(microturn_response, 'content'):
                        decision = microturn_response.content.strip().upper()
                    else:
                        decision = str(microturn_response).strip().upper()
                    
                    node_name = getattr(self._callback_handler, '_current_chain_node', 'agent')
                    self._vprint(f"[DASEIN][MICROTURN] Node: {node_name} | Proposed: {proposed_func_name} | Decision: {decision}")
                    
                    if "BLOCK" in decision:
                        self._vprint(f"[DASEIN][MICROTURN] BLOCKING {proposed_func_name} call!")
                        # Modify the result to clear the function call
                        if hasattr(result, 'generations') and result.generations:
                            first_gen = result.generations[0]
                            if isinstance(first_gen, list) and len(first_gen) > 0:
                                generation = first_gen[0]
                            else:
                                generation = first_gen
                            
                            if hasattr(generation, 'message'):
                                generation.message.additional_kwargs['function_call'] = {}
                                generation.message.content = ""
            except Exception as e:
                self._vprint(f"[DASEIN][MICROTURN] Error in microturn: {e}")
                import traceback
                traceback.print_exc()
        
        # Trigger on_llm_end callback
        if self._callback_handler:
            self._callback_handler.on_llm_end(
                response=result,
                **kwargs
            )
        
        return result
    
    def _get_model_name(self):
        """Get model name dynamically from any LLM type."""
        # Try various common attributes
        for attr in ['model_name', 'model', 'llm_type', '__class__.__name__']:
            try:
                if '.' in attr:
                    # Handle nested attributes like __class__.__name__
                    obj = self._llm
                    for part in attr.split('.'):
                        obj = getattr(obj, part)
                    return str(obj)
                else:
                    value = getattr(self._llm, attr, None)
                    if value:
                        return str(value)
            except:
                continue
        return "unknown_llm"
    
    def _extract_result_text(self, result):
        """Extract text from any LLM result format."""
        try:
            # Try different result formats
            if hasattr(result, 'generations') and result.generations:
                generation = result.generations[0]
                if hasattr(generation, 'text'):
                    text = generation.text
                elif hasattr(generation, 'message') and hasattr(generation.message, 'content'):
                    text = generation.message.content
                else:
                    text = str(generation)
            elif hasattr(result, 'content'):
                text = result.content
            elif hasattr(result, 'text'):
                text = result.text
            else:
                text = str(result)
            
            # Truncate if too long
            if len(text) > 240:
                return text[:240] + "..."
            return text
        except:
            return "No result"
    
    def invoke(self, messages, **kwargs):
        """Override invoke to intercept all LLM calls."""
        self._vprint(f"[DASEIN][WRAPPER] invoke() called with {len(messages) if isinstance(messages, list) else 1} messages")
        
        # Call the parent's invoke which will call our _generate
        result = super().invoke(messages, **kwargs)
        
        return result
    
    def _llm_type(self):
        return "dasein_llm_wrapper"
    
    def get_trace(self):
        """Get the current trace."""
        return self._trace.copy()
    
    def clear_trace(self):
        """Clear the current trace."""
        self._trace.clear()
    
    def _estimate_input_tokens(self, messages):
        """Estimate input tokens from messages."""
        try:
            total_chars = 0
            for msg in messages:
                if hasattr(msg, 'content'):
                    total_chars += len(str(msg.content))
                else:
                    total_chars += len(str(msg))
            # Rough estimation: ~4 characters per token
            return max(1, total_chars // 4)
        except:
            return 50  # Fallback estimate
    
    def _estimate_output_tokens(self, text):
        """Estimate output tokens from text."""
        try:
            # Rough estimation: ~4 characters per token
            return max(1, len(str(text)) // 4)
        except:
            return 50  # Fallback estimate
    
    def _determine_success(self, result_text, result):
        """Determine if the LLM call was successful."""
        try:
            # Check for common failure indicators
            failure_indicators = [
                "I don't know",
                "I cannot",
                "I'm unable",
                "Error:",
                "Exception:",
                "Failed:",
                "syntax error",
                "not found"
            ]
            
            result_lower = result_text.lower()
            for indicator in failure_indicators:
                if indicator in result_lower:
                    return False
            
            # Check if result is too short (likely incomplete)
            if len(result_text.strip()) < 10:
                return False
            
            # Check if result contains actual content (not just error messages)
            if any(word in result_lower for word in ["query", "select", "result", "data", "answer"]):
                return True
            
            # Default to success if no clear failure indicators
            return True
        except:
            return False
    
    def _determine_final_outcome(self, result, query=None):
        """Determine if the agent completed the task or gave up using LLM-based evaluation."""
        try:
            if not result:
                return "failed"  # No result means failure
            
            # Extract the output text from the result
            if isinstance(result, dict):
                output_text = result.get('output', '')
                # Also extract query if available
                if query is None:
                    query = result.get('input', '')
            elif hasattr(result, 'content'):
                output_text = result.content
            else:
                output_text = str(result)
            
            if not output_text:
                return "failed"  # Empty output means failure
            
            # Simple heuristic: check for common failure/error patterns
            output_lower = output_text.lower()
            failure_patterns = ['error', 'failed', 'could not', 'unable to', 'cannot', 'exception']
            
            if any(pattern in output_lower for pattern in failure_patterns):
                return "gave_up"
            
            # If we have output and no obvious failure, assume completed
            return "completed"
                
        except Exception as e:
            logger.debug(f"[DEBUG] Error in _determine_final_outcome: {str(e)}")
            return "failed"
    
    def _fallback_outcome_determination(self, output_text):
        """Fallback outcome determination using simple heuristics."""
        try:
            output_lower = output_text.lower()
            
            # Check for explicit failure indicators
            failure_indicators = [
                "i don't know", "i cannot", "i'm unable", "i am unable",
                "i can't", "i am not able", "unable to", "cannot proceed",
                "cannot complete", "failed to", "error occurred",
                "exception occurred", "syntax error", "not found",
                "no results", "empty result"
            ]
            
            for indicator in failure_indicators:
                if indicator in output_lower:
                    return "gave_up"
            
            # Check if output is substantial (likely a real answer)
            if len(output_text.strip()) > 50:
                return "completed"
            else:
                return "gave_up"
                
        except Exception:
            return "failed"
    
    def _format_final_outcome(self, outcome):
        """Format final outcome for display."""
        if outcome == "completed":
            return "✅ Task Completed"
        elif outcome == "gave_up":
            return "⚠️ Agent Gave Up"
        elif outcome == "failed":
            return "❌ Failed"
        else:
            return f"❓ {outcome}"

# Configure logging
logger = logging.getLogger(__name__)

# Global state management
_event_store: Optional[EventStore] = None
_global_cognate_proxy = None


def _get_event_store() -> EventStore:
    """Get global event store, creating if necessary."""
    global _event_store
    if _event_store is None:
        _event_store = EventStore()
    return _event_store




def cognate(agent, *, weights=None, verbose=False, retry=1, performance_tracking=False, rule_trace=False, post_run="full", performance_tracking_id=None, top_k=5):
    """
    Wrap an agent with Dasein's memory capabilities.
    
    Returns a proxy that exposes .run() and .invoke() exactly like the original,
    but appends our callback via callbacks kwarg if present.
    
    Args:
        agent: The LangChain agent to wrap
        weights: Optional custom weights for rule selection. If None, uses default even weights.
                Format: {"w1": float, "w2": float, "w3": float, "w4": float, "w5": float}
                Where w1=success_prob, w2=turns, w3=uncertainty, w4=tokens, w5=time
        verbose: If True, print full rule details during synthesis
        retry: Number of times to retry the same query (default: 1)
        performance_tracking: If True, enable detailed performance metrics and improvement analysis.
                             If "sequential", enable sequential learning mode for POC demonstrations.
        rule_trace: If True, print raw step LLM calls to help debug rule generation
        post_run: Controls post-run behavior. Options: "full" (KPIs + rule synthesis), "kpi_only" (KPIs only, skip rule synthesis)
        performance_tracking_id: Optional custom performance tracking ID for grouping related runs. 
                                If None, auto-generates a unique ID. Use same ID to share learnings across queries.
        top_k: Maximum number of rules to select per layer (default: 5)
        
    Returns:
        A proxy object with .run() and .invoke() methods
    """
    # CRITICAL: Prevent double-wrapping in Jupyter/Colab when cell is rerun
    # If agent is already a CognateProxy, unwrap it first to avoid nested retry loops
    if isinstance(agent, CognateProxy):
        logger.warning("[DASEIN][WARNING] Agent is already wrapped with cognate(). Unwrapping to prevent nested loops.")
        logger.warning(f"[DASEIN][WARNING] Previous config: retry={agent._retry}, performance_tracking={agent._performance_tracking}")
        logger.warning(f"[DASEIN][WARNING] New config: retry={retry}, performance_tracking={performance_tracking}")
        agent = agent._agent  # Unwrap to get original agent
    
    global _global_cognate_proxy
    _global_cognate_proxy = CognateProxy(agent, weights=weights, verbose=verbose, retry=retry, performance_tracking=performance_tracking, rule_trace=rule_trace, post_run=post_run, performance_tracking_id=performance_tracking_id, top_k=top_k)
    return _global_cognate_proxy


def inspect_rules():
    """
    Inspect current rules from cloud services.
    
    Returns:
        List of rule summaries
    """
    logger.info("[DASEIN] Rule inspection requires cloud service access - not available in SDK")
    return []


def reset_brain():
    """
    Reset brain state - clear event store and proxy.
    """
    global _event_store, _global_cognate_proxy
    
    if _event_store is not None:
        # Clear all events from the store
        _event_store._messages.clear()
        _event_store._tool_calls.clear()
        _event_store._code_blocks.clear()
        _event_store._artifacts.clear()
        _event_store._observations.clear()
        _event_store._steps.clear()
        _event_store._outcomes.clear()
        logger.info("[DASEIN][RESET] Cleared event store")
    
    # Set global variables to None
    _event_store = None
    _global_cognate_proxy = None
    logger.info("[DASEIN][RESET] Brain state reset - local storage cleared")


class DaseinToolWrapper:
    """Wrapper that intercepts tool calls and applies tool_start rules."""
    
    def __init__(self, original_tool, callback_handler, verbose: bool = False):
        self.original_tool = original_tool
        self.callback_handler = callback_handler
        self._verbose = verbose
        
        # Copy all public attributes from original tool, but exclude methods we override
        excluded_methods = {'_run', 'invoke', '__call__', '_arun'}
        for attr in dir(original_tool):
            if not attr.startswith('_') and not hasattr(self, attr) and attr not in excluded_methods:
                try:
                    setattr(self, attr, getattr(original_tool, attr))
                except:
                    pass
    
    def _vprint(self, message: str, force: bool = False):
        """Helper for verbose printing."""
        _vprint(message, self._verbose, force)
    
    def _run(self, *args, **kwargs) -> str:
        """Intercept tool call and apply tool_start rules."""
        self._vprint(f"[DASEIN][TOOL_WRAPPER] _run called for {self.name} - VERSION 2.0")
        self._vprint(f"[DASEIN][TOOL_WRAPPER] Args: {args}")
        self._vprint(f"[DASEIN][TOOL_WRAPPER] Kwargs: {kwargs}")
        
        try:
            # Apply tool_start rules if we have selected rules
            if hasattr(self.callback_handler, '_selected_rules') and self.callback_handler._selected_rules:
                self._vprint(f"[DASEIN][TOOL_WRAPPER] Applying tool_start rules...")
                modified_args = self._apply_tool_rules(args, kwargs)
                args, kwargs = modified_args
            
            self._vprint(f"[DASEIN][TOOL_WRAPPER] About to call original tool _run")
            # Call the original tool
            result = self.original_tool._run(*args, **kwargs)
            self._vprint(f"[DASEIN][TOOL_WRAPPER] Original tool _run completed, result length: {len(str(result))}")
            
            # Capture the tool output in the trace
            self._vprint(f"[DASEIN][TOOL_WRAPPER] About to capture tool output for {self.name}")
            self._capture_tool_output(self.name, args, kwargs, result)
            self._vprint(f"[DASEIN][TOOL_WRAPPER] Finished capturing tool output for {self.name}")
            
            return result
            
        except OutputParserException:
            # Pass through parsing errors so agent's handle_parsing_errors can work
            self._vprint(f"[DASEIN][TOOL_WRAPPER] OutputParserException detected - passing through to agent")
            raise
        except Exception as e:
            self._vprint(f"[DASEIN][TOOL_WRAPPER] Exception in _run: {e}")
            import traceback
            traceback.print_exc()
            # Still try to call the original tool
            result = self.original_tool._run(*args, **kwargs)
            return result
    
    def invoke(self, *args, **kwargs) -> str:
        """Intercept invoke call and apply tool_start rules."""
        self._vprint(f"[DASEIN][TOOL_WRAPPER] invoke called for {self.name}")
        self._vprint(f"[DASEIN][TOOL_WRAPPER] Args: {args}")
        self._vprint(f"[DASEIN][TOOL_WRAPPER] Kwargs: {kwargs}")
        
        try:
            # Apply tool_start rules if we have selected rules
            if hasattr(self.callback_handler, '_selected_rules') and self.callback_handler._selected_rules:
                self._vprint(f"[DASEIN][TOOL_WRAPPER] Applying tool_start rules...")
                modified_args = self._apply_tool_rules(args, kwargs)
                args, kwargs = modified_args
            
            self._vprint(f"[DASEIN][TOOL_WRAPPER] About to call original tool invoke")
            # Call the original tool
            if hasattr(self.original_tool, 'invoke'):
                result = self.original_tool.invoke(*args, **kwargs)
            else:
                result = self.original_tool._run(*args, **kwargs)
            self._vprint(f"[DASEIN][TOOL_WRAPPER] Original tool invoke completed, result length: {len(str(result))}")
            
            # Capture the tool output in the trace
            self._vprint(f"[DASEIN][TOOL_WRAPPER] About to capture tool output for {self.name}")
            self._capture_tool_output(self.name, args, kwargs, result)
            self._vprint(f"[DASEIN][TOOL_WRAPPER] Finished capturing tool output for {self.name}")
            
            return result
            
        except OutputParserException:
            # Pass through parsing errors so agent's handle_parsing_errors can work
            self._vprint(f"[DASEIN][TOOL_WRAPPER] OutputParserException detected - passing through to agent")
            raise
        except Exception as e:
            self._vprint(f"[DASEIN][TOOL_WRAPPER] Exception in invoke: {e}")
            import traceback
            traceback.print_exc()
            # Still try to call the original tool
            if hasattr(self.original_tool, 'invoke'):
                result = self.original_tool.invoke(*args, **kwargs)
            else:
                result = self.original_tool._run(*args, **kwargs)
            return result
    
    def __call__(self, *args, **kwargs) -> str:
        """Intercept direct call and apply tool_start rules."""
        self._vprint(f"[DASEIN][TOOL_WRAPPER] _run called for {self.name}")
        
        try:
            # Apply tool_start rules if we have selected rules
            if hasattr(self.callback_handler, '_selected_rules') and self.callback_handler._selected_rules:
                self._vprint(f"[DASEIN][TOOL_WRAPPER] Applying tool_start rules...")
                modified_args = self._apply_tool_rules(args, kwargs)
                args, kwargs = modified_args
            
            # Call the original tool
            if hasattr(self.original_tool, '__call__'):
                result = self.original_tool(*args, **kwargs)
            elif hasattr(self.original_tool, 'invoke'):
                result = self.original_tool.invoke(*args, **kwargs)
            else:
                result = self.original_tool._run(*args, **kwargs)
            
            # Capture the tool output in the trace
            self._capture_tool_output(self.name, args, kwargs, result)
            
            return result
            
        except OutputParserException:
            # Pass through parsing errors so agent's handle_parsing_errors can work
            self._vprint(f"[DASEIN][TOOL_WRAPPER] OutputParserException detected - passing through to agent")
            raise
    
    async def _arun(self, *args, **kwargs) -> str:
        """Async version."""
        self._vprint(f"[DASEIN][TOOL_WRAPPER] _run called for {self.name}")
        
        try:
            # Apply tool_start rules if we have selected rules
            if hasattr(self.callback_handler, '_selected_rules') and self.callback_handler._selected_rules:
                self._vprint(f"[DASEIN][TOOL_WRAPPER] Applying tool_start rules...")
                modified_args = self._apply_tool_rules(args, kwargs)
                args, kwargs = modified_args
            
            # Call the original tool
            result = await self.original_tool._arun(*args, **kwargs)
            
            # Capture the tool output in the trace
            self._capture_tool_output(self.name, args, kwargs, result)
            
            return result
            
        except OutputParserException:
            # Pass through parsing errors so agent's handle_parsing_errors can work
            self._vprint(f"[DASEIN][TOOL_WRAPPER] OutputParserException detected - passing through to agent")
            raise
    
    def _apply_tool_rules(self, args, kwargs):
        """Apply tool_start rules to modify tool input."""
        try:
            # Get tool_start rules from callback handler
            tool_rules = []
            for rule_meta in self.callback_handler._selected_rules:
                if isinstance(rule_meta, tuple) and len(rule_meta) == 2:
                    rule, metadata = rule_meta
                else:
                    rule = rule_meta
                
                # Only apply rules that target tool_start
                if hasattr(rule, 'target_step_type') and rule.target_step_type == "tool_start":
                    tool_rules.append(rule)
                    self._vprint(f"[DASEIN][TOOL_WRAPPER] Tool rule: {rule.advice_text[:100]}...")
            
            if tool_rules:
                # Apply rules to modify the tool input
                modified_args = list(args)
                modified_kwargs = kwargs.copy()
                
                for rule in tool_rules:
                    if "strip" in rule.advice_text.lower() and "fence" in rule.advice_text.lower():
                        # Strip markdown code fences from the first argument
                        if modified_args and isinstance(modified_args[0], str):
                            import re
                            original = modified_args[0]
                            modified_args[0] = re.sub(r'```(?:sql)?\s*(.*?)\s*```', r'\1', modified_args[0], flags=re.DOTALL)
                            if modified_args[0] != original:
                                self._vprint(f"[DASEIN][TOOL_WRAPPER] Stripped code fences from tool input")
                                self._vprint(f"[DASEIN][TOOL_WRAPPER] Before: {original[:100]}...")
                                self._vprint(f"[DASEIN][TOOL_WRAPPER] After: {modified_args[0][:100]}...")
                    elif "strip" in rule.advice_text.lower() and "quote" in rule.advice_text.lower():
                        # Strip quotes from the first argument
                        if modified_args and isinstance(modified_args[0], str):
                            import re
                            original = modified_args[0]
                            modified_args[0] = re.sub(r'^["\']|["\']$', '', modified_args[0].strip())
                            if modified_args[0] != original:
                                self._vprint(f"[DASEIN][TOOL_WRAPPER] Stripped quotes from tool input")
                                self._vprint(f"[DASEIN][TOOL_WRAPPER] Before: {original[:100]}...")
                                self._vprint(f"[DASEIN][TOOL_WRAPPER] After: {modified_args[0][:100]}...")
                
                return tuple(modified_args), modified_kwargs
            else:
                return args, kwargs
                
        except Exception as e:
            self._vprint(f"[DASEIN][TOOL_WRAPPER] Error applying tool rules: {e}")
            return args, kwargs
    
    def _capture_tool_output(self, tool_name, args, kwargs, result):
        """Capture tool output in the trace."""
        try:
            from datetime import datetime
            from dasein.capture import _TRACE
            
            # Create args excerpt
            args_str = str(args) if args else ""
            if len(args_str) > 1000:
                args_str = args_str[:1000] + "..."
            
            # Create result excerpt (with 10k limit)
            result_str = str(result) if result else ""
            if len(result_str) > 10000:
                result_str = result_str[:10000] + "..."
            
            # Add tool_end step to trace
            step = {
                "step_type": "tool_end",
                "tool_name": tool_name,
                "args_excerpt": args_str,
                "outcome": result_str,
                "ts": datetime.now().isoformat(),
                "run_id": f"tool_{id(self)}_{datetime.now().timestamp()}",
                "parent_run_id": None,
            }
            _TRACE.append(step)
            
            self._vprint(f"[DASEIN][TOOL_WRAPPER] Captured tool output for {tool_name}")
            self._vprint(f"[DASEIN][TOOL_WRAPPER] Output length: {len(result_str)} chars")
            self._vprint(f"[DASEIN][TOOL_WRAPPER] First 200 chars: {result_str[:200]}")
            self._vprint(f"[DASEIN][TOOL_WRAPPER] Trace length after capture: {len(_TRACE)}")
            
        except Exception as e:
            self._vprint(f"[DASEIN][TOOL_WRAPPER] Error capturing tool output: {e}")

class CognateProxy:
    """
    Proxy that wraps a LangChain agent and implements the complete Dasein pipeline.
    """
    
    def __init__(self, agent, weights=None, verbose=False, retry=1, performance_tracking=False, rule_trace=False, post_run="full", performance_tracking_id=None, top_k=5):
        self._agent = agent
        self._weights = weights or W_COST
        self._verbose = verbose
        self._retry = retry
        self._performance_tracking = performance_tracking
        self._rule_trace = rule_trace
        self._post_run = post_run  # "full" or "kpi_only"
        self._top_k = top_k  # Maximum number of rules to select per layer
        # Ensure naive flag exists (legacy code path)
        self._naive = False
        #  CRITICAL: LangGraph Detection & Parameter Extraction
        self._is_langgraph = self._detect_langgraph_agent(agent)
        
        #  Identify coordinator node for targeted injection
        coordinator_node = None
        planning_nodes = set()
        if self._is_langgraph:
            self._vprint(f"[DASEIN][LANGGRAPH] LangGraph agent detected: {type(agent).__name__}")
            coordinator_node = self._identify_coordinator_node(agent)
            if coordinator_node:
                print(f"[DASEIN] Coordinator node: {coordinator_node}")
                planning_nodes = self._identify_planning_nodes(agent, coordinator_node)
        
        self._callback_handler = DaseinCallbackHandler(weights=weights, llm=None, is_langgraph=self._is_langgraph, coordinator_node=coordinator_node, planning_nodes=planning_nodes, verbose=verbose, agent=self._agent, extract_tools_fn=self._extract_tool_metadata)
        self._langgraph_params = None
        self._original_agent = agent  # Keep reference to original
        self._agent_was_recreated = False  # Track if agent recreation succeeded
        
        if self._is_langgraph:
            self._langgraph_params = self._extract_langgraph_params(agent)
            if self._langgraph_params:
                print(f" [DASEIN][LANGGRAPH] Successfully extracted creation parameters")
            else:
                print(f" [DASEIN][LANGGRAPH] FAILED to extract parameters - falling back to callback injection")
        else:
            print(f" [DASEIN][LANGCHAIN] LangChain agent detected: {type(agent).__name__}")
            print(f" [DASEIN][LANGCHAIN] Using callback-based system prompt injection")
        
        # Sequential tracking state
        self._sequential_mode = performance_tracking == "sequential"
        self._sequential_step = 0
        self._sequential_metrics = []
        
        # Performance tracking isolation - use provided ID or auto-generate
        if self._performance_tracking or self._sequential_mode:
            if performance_tracking_id:
                # Use provided tracking ID (for grouping related runs)
                self._performance_tracking_id = performance_tracking_id
                print(f"[DASEIN] Performance tracking session (custom ID): {self._performance_tracking_id}")
            else:
                # Auto-generate unique ID
                import uuid
                self._performance_tracking_id = str(uuid.uuid4())
                print(f"[DASEIN] Performance tracking session (auto-generated): {self._performance_tracking_id}")
        else:
            self._performance_tracking_id = None
        
        # Step tracking for parallel execution
        self._current_step_id = None
        
        # Service-first architecture - only use ServiceAdapter
        self._service_adapter = ServiceAdapter()
        self._event_store = _get_event_store()
        print("[DASEIN] Using distributed services (pre-run/post-run)")
        
        # Initialize KPI tracking
        self._last_run_kpis = None
        
        # Initialize wrapped LLM (will be set by _wrap_agent_llm if applicable)
        self._wrapped_llm = None
        
        # Initialize recreation flag (will be set to True if LangGraph recreation succeeds)
        self._agent_was_recreated = False
        
        # Track which LLM classes have been monkey-patched (to avoid double-patching)
        self._patched_llm_classes = set()
        
        # Generate agent fingerprint ONCE and cache it (must be consistent across pre-run and post-run)
        self._agent_fingerprint = None
        
        # Wrap the agent's LLM with our trace capture wrapper
        self._wrap_agent_llm()
        
        # CRITICAL: Update langgraph_params to use wrapped LLM for recreation
        if self._is_langgraph and self._langgraph_params and self._wrapped_llm:
            print(f" [DASEIN][WRAPPER] Updating langgraph_params to use wrapped LLM")
            self._langgraph_params['model'] = self._wrapped_llm
        
        # Inject universal dead-letter tool
        self._inject_deadletter_tool()
    
    def _vprint(self, message: str, force: bool = False):
        """Helper for verbose printing."""
        _vprint(message, self._verbose, force)
    
    def _format_final_outcome(self, outcome):
        """Format final outcome for display."""
        if outcome == "completed":
            return "✅ Task Completed"
        elif outcome == "gave_up":
            return "⚠️ Agent Gave Up"
        elif outcome == "failed":
            return "❌ Failed"
        else:
            return f"❓ {outcome}"
        
    def _extract_query_from_input(self, input_data):
        """ CRITICAL: Extract query string from various input formats."""
        try:
            # Handle string input (simple case)
            if isinstance(input_data, str):
                return input_data
            
            # Handle dict input
            if isinstance(input_data, dict):
                # LangChain SQL agent format: {"input": "query"}
                if "input" in input_data:
                    return str(input_data["input"])
                # Alternative keys
                if "question" in input_data:
                    return str(input_data["question"])
                if "query" in input_data:
                    return str(input_data["query"])
                
                # Handle LangGraph message format: {"messages": [("user", "query")]}
                if "messages" in input_data:
                    messages = input_data["messages"]
                    if messages and len(messages) > 0:
                        # Get the last human message
                        for message in reversed(messages):
                            if isinstance(message, tuple) and len(message) == 2:
                                role, content = message
                                if role in ["user", "human"]:
                                    return str(content)
                            elif hasattr(message, 'content') and hasattr(message, 'type'):
                                if message.type in ["human", "user"]:
                                    return str(message.content)
            
            # Handle list input
            if isinstance(input_data, list) and input_data:
                return str(input_data[0])
            
            # Fallback to string representation
            return str(input_data)[:200]  # Truncate to avoid huge strings
            
        except Exception as e:
            print(f" [DASEIN][QUERY_EXTRACT] Error extracting query: {e}")
            return str(input_data)[:200] if input_data else ""
    
    def _detect_langgraph_agent(self, agent):
        """ CRITICAL: Detect if agent is a LangGraph agent that needs prompt injection."""
        try:
            agent_class_name = agent.__class__.__name__
            module_name = agent.__class__.__module__
            
            # Check class name and module for LangGraph indicators
            is_langgraph = (
                ('Compiled' in agent_class_name and 'Graph' in agent_class_name) or
                'langgraph' in agent_class_name.lower() or
                'langgraph' in module_name.lower()
            )
            
            self._vprint(f"[DASEIN][DETECTION] Agent: {agent_class_name} from {module_name}")
            self._vprint(f"[DASEIN][DETECTION] LangGraph detected: {is_langgraph}")
            
            return is_langgraph
            
        except Exception as e:
            print(f" [DASEIN][DETECTION] ERROR detecting agent type: {e}")
            return False
    
    def _identify_coordinator_node(self, agent):
        """ Identify coordinator node via structural graph analysis."""
        try:
            if not hasattr(agent, 'get_graph'):
                return None
            
            graph = agent.get_graph()
            nodes = graph.nodes
            edges = graph.edges
            
            if not nodes or not edges:
                return None
            
            print(f"\n[DASEIN][COORDINATOR] Analyzing graph structure:")
            print(f"   Nodes: {list(nodes.keys())}")
            
            # Compute out-degree
            out_degree = {node_id: sum(1 for e in edges if e.source == node_id) for node_id in nodes.keys()}
            
            # Score nodes
            scores = {}
            for node_id in nodes.keys():
                if node_id in ['__start__', '__end__']:
                    continue
                    
                score = 0
                node_obj = nodes[node_id]
                
                # Subgraph dispatch (strongest signal)
                if hasattr(node_obj.data, 'nodes') and 'Compiled' in type(node_obj.data).__name__:
                    score += 50
                    self._vprint(f"[DASEIN][COORDINATOR] {node_id}: +50 (subgraph)")
                
                # High out-degree
                if out_degree.get(node_id, 0) >= 2:
                    score += 10
                    self._vprint(f"[DASEIN][COORDINATOR] {node_id}: +10 (out-degree={out_degree[node_id]})")
                
                scores[node_id] = score
            
            self._vprint(f"[DASEIN][COORDINATOR] Scores: {scores}")
            
            if scores:
                coordinator = max(scores.items(), key=lambda x: x[1])
                if coordinator[1] > 0:
                    self._vprint(f"[DASEIN][COORDINATOR] Selected: {coordinator[0]} (score={coordinator[1]})")
                    return coordinator[0]
            
            return None
            
        except Exception as e:
            self._vprint(f"[DASEIN][COORDINATOR] ERROR: {e}")
            return None
    
    def _identify_planning_nodes(self, agent, coordinator_node):
        """Identify all nodes capable of planning/fan-out (including subgraph children).
        
        Planning nodes are those that can delegate to other nodes (out-degree >= 2).
        For subgraphs, we recursively analyze their internal structure.
        """
        try:
            if not hasattr(agent, 'get_graph') or not coordinator_node:
                return set()
            
            graph = agent.get_graph()
            nodes = graph.nodes
            edges = graph.edges
            
            if not nodes or not edges:
                return set()
            
            print(f"\n[DASEIN][PLANNING_NODES] Analyzing planning-capable nodes:")
            planning_nodes = set()
            
            # Compute out-degree for all nodes
            out_degree = {node_id: sum(1 for e in edges if e.source == node_id) for node_id in nodes.keys()}
            
            # Check each node
            for node_id in nodes.keys():
                if node_id in ['__start__', '__end__']:
                    continue
                
                node_obj = nodes[node_id]
                
                # If this is the coordinator (subgraph), analyze its children
                if node_id == coordinator_node and hasattr(node_obj.data, 'nodes') and 'Compiled' in type(node_obj.data).__name__:
                    self._vprint(f"[DASEIN][PLANNING_NODES] {node_id}: Subgraph coordinator - analyzing children...")
                    planning_nodes.add(node_id)  # Add the subgraph itself
                    
                    # Get subgraph structure
                    try:
                        subgraph = node_obj.data.get_graph()
                        sub_nodes = subgraph.nodes
                        sub_edges = subgraph.edges
                        
                        # Compute out-degree in subgraph
                        sub_out_degree = {nid: sum(1 for e in sub_edges if e.source == nid) for nid in sub_nodes.keys()}
                        
                        # Find planning nodes in subgraph (out-degree >= 2)
                        for sub_node_id in sub_nodes.keys():
                            if sub_node_id in ['__start__', '__end__']:
                                continue
                            if sub_out_degree.get(sub_node_id, 0) >= 2:
                                planning_nodes.add(sub_node_id)
                                self._vprint(f"[DASEIN][PLANNING_NODES]   └─ {sub_node_id}: Planning node (out-degree={sub_out_degree[sub_node_id]})")
                    except Exception as e:
                        self._vprint(f"[DASEIN][PLANNING_NODES]   ERROR analyzing subgraph: {e}")
                
                # Check if this node itself is a planner (out-degree >= 2)
                elif out_degree.get(node_id, 0) >= 2:
                    planning_nodes.add(node_id)
                    self._vprint(f"[DASEIN][PLANNING_NODES] {node_id}: Planning node (out-degree={out_degree[node_id]})")
            
            self._vprint(f"[DASEIN][PLANNING_NODES] Identified planning nodes: {planning_nodes}")
            return planning_nodes
            
        except Exception as e:
            self._vprint(f"[DASEIN][PLANNING_NODES] ERROR: {e}")
            return set()
    
    def _extract_tool_metadata(self, agent):
        """
        Extract tool metadata (name, description, args_schema) from agent.
        
        CRITICAL: Extracts ALL available tools from the agent, not just tools used in trace.
        Why: If agent used wrong tool (e.g., extract_text instead of get_elements), 
        the trace won't show the correct tool. Stage 3.5 needs to see all options
        to suggest better alternatives.
        
        For multi-agent systems, preserves node→tool mapping so Stage 3.5 knows
        which tools are available in which nodes (critical for grounding).
        """
        tools_metadata = []
        tools_to_process = []  # Format: (tool, node_name or None)
        
        # Get ALL tools from agent (LangChain or LangGraph) - not filtered by trace usage
        tools_attr = getattr(agent, 'tools', None)
        if tools_attr:
            try:
                # Top-level tools have no node context
                tools_to_process = [(t, None) for t in list(tools_attr)]
            except Exception:
                pass
        elif getattr(agent, 'toolkit', None):
            tk = getattr(agent, 'toolkit')
            tk_tools = getattr(tk, 'tools', None) or getattr(tk, 'get_tools', None)
            try:
                # Toolkit tools have no node context
                tools_to_process = [(t, None) for t in list(tk_tools() if callable(tk_tools) else tk_tools or [])]
            except Exception:
                pass
        
        # Also try LangGraph tools from compiled graph
        # For multi-agent systems, scan ALL nodes for tools (not just 'tools' node)
        # CRITICAL: Preserve node→tool mapping for proper grounding
        # CRITICAL: Use agent.get_graph().nodes (same as planning node discovery)
        # NOT agent.nodes which returns different objects without .data attribute
        if hasattr(agent, 'get_graph'):
            graph = agent.get_graph()
            nodes = graph.nodes
            for node_name, node_obj in nodes.items():
                if node_name.startswith('__'):  # Skip __start__, __end__
                    continue
                
                # Check if this is a subgraph with child nodes (like research_supervisor)
                # CRITICAL: Use node_obj.data (compiled graph) not node_obj.node (implementation)
                if hasattr(node_obj, 'data') and hasattr(node_obj.data, 'nodes') and 'Compiled' in type(node_obj.data).__name__:
                    try:
                        subgraph = node_obj.data.get_graph()
                        for sub_node_name, sub_node_obj in subgraph.nodes.items():
                            if sub_node_name.startswith('__'):
                                continue
                            if hasattr(sub_node_obj, 'node'):
                                sub_actual = sub_node_obj.node
                                # Use fully qualified node name: parent.child
                                full_node_name = f"{node_name}.{sub_node_name}"
                                
                                # Check all tool patterns in subgraph children
                                if hasattr(sub_actual, 'tools_by_name'):
                                    tools_to_process.extend([(t, full_node_name) for t in sub_actual.tools_by_name.values()])
                                if hasattr(sub_actual, 'runnable') and hasattr(sub_actual.runnable, 'tools'):
                                    sub_tools = sub_actual.runnable.tools
                                    if callable(sub_tools):
                                        try:
                                            sub_tools = sub_tools()
                                        except:
                                            pass
                                    if isinstance(sub_tools, list):
                                        tools_to_process.extend([(t, full_node_name) for t in sub_tools])
                                        print(f" [DASEIN][EXTRACT]     Found {len(sub_tools)} tools in {full_node_name}.runnable.tools")
                                    else:
                                        tools_to_process.append((sub_tools, full_node_name))
                                        print(f" [DASEIN][EXTRACT]     Found 1 tool in {full_node_name}.runnable.tools")
                    except Exception as e:
                        print(f" [DASEIN][EXTRACT]   Failed to analyze subgraph: {e}")
                
                # Check if node has steps with tools
                if hasattr(node_obj, 'node'):
                    actual_node = node_obj.node
                    
                    # Check for tools_by_name (common in agent nodes)
                    if hasattr(actual_node, 'tools_by_name'):
                        node_tools = actual_node.tools_by_name.values()
                        tools_to_process.extend([(t, node_name) for t in node_tools])
                        print(f" [DASEIN][EXTRACT] Found {len(node_tools)} tools in {node_name}.tools_by_name")
                    
                    # Check for runnable.tools (dynamic tools like ConductResearch)
                    if hasattr(actual_node, 'runnable') and hasattr(actual_node.runnable, 'tools'):
                        runnable_tools = actual_node.runnable.tools
                        if callable(runnable_tools):
                            try:
                                runnable_tools = runnable_tools()
                            except:
                                pass
                        if isinstance(runnable_tools, list):
                            tools_to_process.extend([(t, node_name) for t in runnable_tools])
                            print(f" [DASEIN][EXTRACT] Found {len(runnable_tools)} tools in {node_name}.runnable.tools")
                        else:
                            tools_to_process.append((runnable_tools, node_name))
                            print(f" [DASEIN][EXTRACT] Found 1 tool in {node_name}.runnable.tools")
                    
                    # Check for bound.tools (another common pattern)
                    if hasattr(actual_node, 'bound') and hasattr(actual_node.bound, 'tools'):
                        bound_tools = actual_node.bound.tools
                        if isinstance(bound_tools, list):
                            tools_to_process.extend([(t, node_name) for t in bound_tools])
                            print(f" [DASEIN][EXTRACT] Found {len(bound_tools)} tools in {node_name}.bound.tools")
                        else:
                            tools_to_process.append((bound_tools, node_name))
                            print(f" [DASEIN][EXTRACT] Found 1 tool in {node_name}.bound.tools")
                    
                    # Check for steps (legacy pattern)
                    if hasattr(actual_node, 'steps'):
                        for step in actual_node.steps:
                            if hasattr(step, 'tools_by_name'):
                                step_tools = step.tools_by_name.values()
                                tools_to_process.extend([(t, node_name) for t in step_tools])
                                print(f" [DASEIN][EXTRACT] Found {len(step_tools)} tools in {node_name}.steps")
                                break
        
        # Extract metadata from each tool (with node context for multi-agent)
        for tool_tuple in tools_to_process:
            try:
                # Unpack (tool, node_name)
                if isinstance(tool_tuple, tuple) and len(tool_tuple) == 2:
                    tool, node_name = tool_tuple
                else:
                    tool = tool_tuple
                    node_name = None
                
                # Unwrap DaseinToolWrapper to get complete metadata (especially args_schema)
                if hasattr(tool, 'original_tool'):
                    tool = tool.original_tool
                
                tool_meta = {
                    'name': getattr(tool, 'name', str(tool.__class__.__name__)),
                    'description': getattr(tool, 'description', ''),
                }
                
                # CRITICAL: Add node context for multi-agent systems (for grounding)
                if node_name:
                    tool_meta['node'] = node_name
                
                # Extract args_schema if available
                if hasattr(tool, 'args_schema') and tool.args_schema:
                    try:
                        # Try Pydantic v2 method
                        if hasattr(tool.args_schema, 'model_json_schema'):
                            tool_meta['args_schema'] = tool.args_schema.model_json_schema()
                        # Fallback to Pydantic v1 method
                        elif hasattr(tool.args_schema, 'schema'):
                            tool_meta['args_schema'] = tool.args_schema.schema()
                        else:
                            tool_meta['args_schema'] = {}
                    except Exception:
                        tool_meta['args_schema'] = {}
                else:
                    tool_meta['args_schema'] = {}
                
                tools_metadata.append(tool_meta)
            except Exception as e:
                # Skip tools that fail to extract
                pass
        
        return tools_metadata
    
    def _extract_langgraph_params(self, agent):
        """ CRITICAL: Extract LangGraph agent creation parameters for recreation."""
        try:
            params = {}
            
            # Try to extract the LLM/model
            if hasattr(agent, 'llm'):
                params['model'] = agent.llm
                print(f" [DASEIN][EXTRACT] Found LLM: {type(agent.llm).__name__}")
            else:
                print(f" [DASEIN][EXTRACT] No LLM found in agent")
                return None
            
            # Try to extract tools from the compiled graph
            # CRITICAL: For multi-agent, scan ALL nodes (not just 'tools' node)
            tools = []
            # CRITICAL: Use agent.get_graph().nodes (same as planning node discovery)
            # NOT agent.nodes which returns different objects without .data attribute
            if hasattr(agent, 'get_graph'):
                graph = agent.get_graph()
                nodes = graph.nodes
                print(f" [DASEIN][EXTRACT] Scanning {len(nodes)} LangGraph nodes for tools...")
                for node_name, node_obj in nodes.items():
                    if node_name.startswith('__'):  # Skip __start__, __end__
                        continue
                    
                    print(f" [DASEIN][EXTRACT] Checking node: {node_name}")
                    
                    # Check if this is a subgraph with child nodes (like research_supervisor)
                    # CRITICAL: Use node_obj.data (compiled graph) not node_obj.node (implementation)
                    if hasattr(node_obj, 'data') and hasattr(node_obj.data, 'nodes') and 'Compiled' in type(node_obj.data).__name__:
                        try:
                            subgraph = node_obj.data.get_graph()
                            print(f" [DASEIN][EXTRACT]   {node_name} is a subgraph with {len(subgraph.nodes)} child nodes")
                            for sub_node_name, sub_node_obj in subgraph.nodes.items():
                                if sub_node_name.startswith('__'):
                                    continue
                                print(f" [DASEIN][EXTRACT]   Checking subgraph child: {sub_node_name}")
                                if hasattr(sub_node_obj, 'node'):
                                    sub_actual = sub_node_obj.node
                                    
                                    # Debug: print what attributes this node has
                                    attrs = [a for a in dir(sub_actual) if not a.startswith('_')]
                                    print(f" [DASEIN][EXTRACT]     Node attributes: {', '.join(attrs[:10])}...")
                                    
                                    # Check all tool patterns in subgraph children
                                    if hasattr(sub_actual, 'tools_by_name'):
                                        for tool_name, tool in sub_actual.tools_by_name.items():
                                            if hasattr(tool, 'original_tool'):
                                                tools.append(tool.original_tool)
                                            else:
                                                tools.append(tool)
                                        print(f" [DASEIN][EXTRACT]     Found {len(sub_actual.tools_by_name)} tools in {node_name}.{sub_node_name}.tools_by_name")
                                    if hasattr(sub_actual, 'runnable') and hasattr(sub_actual.runnable, 'tools'):
                                        sub_tools = sub_actual.runnable.tools
                                        if callable(sub_tools):
                                            try:
                                                sub_tools = sub_tools()
                                            except:
                                                pass
                                        if isinstance(sub_tools, list):
                                            tools.extend(sub_tools)
                                            print(f" [DASEIN][EXTRACT]     Found {len(sub_tools)} tools in {node_name}.{sub_node_name}.runnable.tools")
                                        else:
                                            tools.append(sub_tools)
                                            print(f" [DASEIN][EXTRACT]     Found 1 tool in {node_name}.{sub_node_name}.runnable.tools")
                                    
                                    # Also check if sub_actual IS a callable with tools (another pattern)
                                    if callable(sub_actual) and hasattr(sub_actual, 'tools'):
                                        direct_tools = sub_actual.tools
                                        if callable(direct_tools):
                                            try:
                                                direct_tools = direct_tools()
                                            except:
                                                pass
                                        if isinstance(direct_tools, list):
                                            tools.extend(direct_tools)
                                            print(f" [DASEIN][EXTRACT]     Found {len(direct_tools)} tools in {node_name}.{sub_node_name} (direct)")
                                        elif direct_tools:
                                            tools.append(direct_tools)
                                            print(f" [DASEIN][EXTRACT]     Found 1 tool in {node_name}.{sub_node_name} (direct)")
                        except Exception as e:
                            print(f" [DASEIN][EXTRACT]   Failed to analyze subgraph: {e}")
                    
                    # Check if node has tools
                    if hasattr(node_obj, 'node'):
                        actual_node = node_obj.node
                        
                        # Check for tools_by_name (common in agent nodes)
                        if hasattr(actual_node, 'tools_by_name'):
                            for tool_name, tool in actual_node.tools_by_name.items():
                                # If it's our wrapped tool, get the original
                                if hasattr(tool, 'original_tool'):
                                    tools.append(tool.original_tool)
                                else:
                                    tools.append(tool)
                            print(f" [DASEIN][EXTRACT] Found {len(actual_node.tools_by_name)} tools in {node_name}.tools_by_name")
                        
                        # Check for runnable.tools (dynamic tools like ConductResearch)
                        if hasattr(actual_node, 'runnable') and hasattr(actual_node.runnable, 'tools'):
                            runnable_tools = actual_node.runnable.tools
                            if callable(runnable_tools):
                                try:
                                    runnable_tools = runnable_tools()
                                except:
                                    pass
                            if isinstance(runnable_tools, list):
                                tools.extend(runnable_tools)
                                print(f" [DASEIN][EXTRACT] Found {len(runnable_tools)} tools in {node_name}.runnable.tools")
                            else:
                                tools.append(runnable_tools)
                                print(f" [DASEIN][EXTRACT] Found 1 tool in {node_name}.runnable.tools")
                        
                        # Check for bound.tools (another common pattern)
                        if hasattr(actual_node, 'bound') and hasattr(actual_node.bound, 'tools'):
                            bound_tools = actual_node.bound.tools
                            if isinstance(bound_tools, list):
                                tools.extend(bound_tools)
                                print(f" [DASEIN][EXTRACT] Found {len(bound_tools)} tools in {node_name}.bound.tools")
                            else:
                                tools.append(bound_tools)
                                print(f" [DASEIN][EXTRACT] Found 1 tool in {node_name}.bound.tools")
                        
                        # Check for steps (legacy pattern)
                        if hasattr(actual_node, 'steps'):
                            for step in actual_node.steps:
                                if hasattr(step, 'tools_by_name'):
                                    for tool_name, tool in step.tools_by_name.items():
                                        if hasattr(tool, 'original_tool'):
                                            tools.append(tool.original_tool)
                                        else:
                                            tools.append(tool)
                                    print(f" [DASEIN][EXTRACT] Found {len(step.tools_by_name)} tools in {node_name}.steps")
                                    break
            
            if tools:
                params['tools'] = tools
                print(f" [DASEIN][EXTRACT] Total: {len(tools)} tools extracted")
            else:
                print(f" [DASEIN][EXTRACT] No tools found in agent")
                return None
            
            # Try to extract any existing system message/prompt
            params['original_prompt'] = None  # We'll detect this later if needed
            
            print(f" [DASEIN][EXTRACT] Successfully extracted all parameters")
            return params
            
        except Exception as e:
            print(f" [DASEIN][EXTRACT] CRITICAL ERROR extracting parameters: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _create_langgraph_system_template(self, selected_rules):
        """ OPTIMIZED: Create system template that merges planning rules with existing client prompts."""
        try:
            # Filter for planning rules (llm_start, chain_start) with DEBUG info
            planning_rules = []
            all_rule_types = []
            
            print(f" [DASEIN][TEMPLATE] Processing {len(selected_rules)} total rules")
            
            for i, rule_meta in enumerate(selected_rules):
                if isinstance(rule_meta, tuple) and len(rule_meta) == 2:
                    rule, metadata = rule_meta
                else:
                    rule = rule_meta
                
                # Handle different rule formats (dict vs object)
                if isinstance(rule, dict):
                    target_step_type = rule.get('target_step_type', 'MISSING')
                    rule_id = rule.get('rule_id', rule.get('id', f'rule_{i}'))
                    advice = rule.get('advice_text', rule.get('advice', ''))
                else:
                    target_step_type = getattr(rule, 'target_step_type', 'MISSING')
                    rule_id = getattr(rule, 'rule_id', getattr(rule, 'id', f'rule_{i}'))
                    advice = getattr(rule, 'advice_text', getattr(rule, 'advice', ''))
                
                all_rule_types.append(f"{rule_id}:{target_step_type}")
                
                # Filter for planning rules (llm_start, chain_start)
                if target_step_type in ['llm_start', 'chain_start']:
                    if advice:
                        planning_rules.append(advice)
                        print(f" [DASEIN][TEMPLATE] Added planning rule: {rule_id}")
                    else:
                        print(f" [DASEIN][TEMPLATE] Skipped rule {rule_id} - no advice text")
                else:
                    print(f" [DASEIN][TEMPLATE] Skipped rule {rule_id} - not a planning rule (target: {target_step_type})")
            
            print(f" [DASEIN][TEMPLATE] All rule types found: {all_rule_types}")
            print(f" [DASEIN][TEMPLATE] Found {len(planning_rules)} planning rules to embed")
            
            if not planning_rules:
                print(f" [DASEIN][TEMPLATE] No planning rules - using original template")
                return None
            
            #  OPTIMIZED: Create static template that merges with existing client prompts
            # This eliminates 600+ tokens per LLM call by embedding rules once in system template
            
            # Get the original LangGraph parameters to access existing prompt
            original_prompt = None
            if hasattr(self, '_langgraph_params') and self._langgraph_params:
                original_prompt = self._langgraph_params.get('prompt')
            
            # Create concise planning rules text (much shorter than dynamic injection)
            rules_text = "; ".join(planning_rules)
            
            # Create enhanced system template that merges with existing client prompts
            from langchain_core.prompts import ChatPromptTemplate
            
            if original_prompt and hasattr(original_prompt, 'messages'):
                # Client has existing prompt - merge with it (transparent wrapper philosophy)
                print(f" [DASEIN][TEMPLATE] Merging with existing client prompt")
                
                # Get the original system message
                original_system = None
                other_messages = []
                
                for msg in original_prompt.messages:
                    if hasattr(msg, 'prompt') and hasattr(msg.prompt, 'template'):
                        if 'system' in str(type(msg)).lower():
                            original_system = msg.prompt.template
                        else:
                            other_messages.append(msg)
                    else:
                        other_messages.append(msg)
                
                # Merge planning rules with original system message
                if original_system:
                    enhanced_system_content = f"""{original_system}

PLANNING RULES: {rules_text}
Follow these rules when planning your actions."""
                else:
                    enhanced_system_content = f"""You are a helpful assistant. Use the available tools to help the user.

PLANNING RULES: {rules_text}
Follow these rules when planning your actions."""
                
                # Create merged template
                messages = [("system", enhanced_system_content)] + [("placeholder", "{messages}")]
                enhanced_template = ChatPromptTemplate.from_messages(messages)
                
            else:
                # No existing prompt - create new one with planning rules
                print(f" [DASEIN][TEMPLATE] Creating new template with planning rules")
                
                enhanced_system_content = f"""You are a helpful assistant. Use the available tools to help the user.

PLANNING RULES: {rules_text}
Follow these rules when planning your actions."""
                
                # Create the template
                enhanced_template = ChatPromptTemplate.from_messages([
                    ("system", enhanced_system_content),
                    ("placeholder", "{messages}"),
                ])
            

            return enhanced_template
            
        except Exception as e:
            print(f" [DASEIN][PROMPT] CRITICAL ERROR creating prompt function: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _recreate_langgraph_agent_with_prompt(self, selected_rules):
        """ CRITICAL: Recreate LangGraph agent with injected prompt."""
        try:
            print(f" [DASEIN][RECREATE] Starting recreation - LangGraph: {self._is_langgraph}, Params: {self._langgraph_params is not None}")
            
            if not self._is_langgraph or not self._langgraph_params:
                print(f" [DASEIN][RECREATE] Cannot recreate - not LangGraph or missing parameters")
                return False
            
            # Create enhanced system template with merged planning rules
            print(f" [DASEIN][RECREATE] Creating enhanced system template...")
            enhanced_template = self._create_langgraph_system_template(selected_rules)
            if not enhanced_template:
                print(f" [DASEIN][RECREATE] No planning rules - keeping original agent")
                return False
            
            print(f" [DASEIN][RECREATE] Recreating LangGraph agent with injected prompt...")
            print(f" [DASEIN][RECREATE] Model: {type(self._langgraph_params['model'])}")
            print(f" [DASEIN][RECREATE] Tools: {len(self._langgraph_params['tools'])}")
            
            # Import create_react_agent
            from langgraph.prebuilt import create_react_agent
            
            # Recreate with enhanced system template - transparent wrapper approach
            print(f" [DASEIN][RECREATE] Calling create_react_agent with enhanced template...")
            new_agent = create_react_agent(
                model=self._langgraph_params['model'],
                tools=self._langgraph_params['tools'],
                prompt=enhanced_template
            )
            print(f" [DASEIN][RECREATE] New agent created: {type(new_agent)}")
            
            # Preserve LLM reference for Dasein
            new_agent.llm = self._langgraph_params['model']
            print(f" [DASEIN][RECREATE] LLM reference preserved")
            
            # Replace the agent
            old_agent_type = type(self._agent)
            self._agent = new_agent
            print(f" [DASEIN][RECREATE] Agent replaced: {old_agent_type} -> {type(new_agent)}")
            
            #  CRITICAL: Update callback handler LLM reference after recreation
            print(f" [DASEIN][RECREATE] Updating callback handler LLM reference...")
            self._set_callback_handler_llm()
            
            print(f" [DASEIN][RECREATE] Successfully recreated LangGraph agent with enhanced system template!")
            print(f" [DASEIN][RECREATE] Planning rules embedded in system template (massive token savings)")
            print(f" [DASEIN][RECREATE] Eliminated ~600 tokens per LLM call vs dynamic injection")
            
            # Mark that agent was successfully recreated so callback knows to skip planning rules
            self._agent_was_recreated = True
            self._callback_handler._agent_was_recreated = True
            
            # CRITICAL: Re-wrap the agent LLM now that we know recreation succeeded
            # This will switch from monkey-patch to wrapper for WebBrowse agents
            print(f" [DASEIN][RECREATE] Re-wrapping agent LLM with correct strategy...")
            self._wrap_agent_llm()
            
            return True
            
        except Exception as e:
            print(f" [DASEIN][RECREATE] CRITICAL FAILURE recreating agent: {e}")
            print(f" [DASEIN][RECREATE] FALLING BACK TO CALLBACK INJECTION")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def _create_deadletter_tool():
        """Create the universal dead-letter tool for blocked calls.
        
        This tool acts as a sink for calls blocked by anti-fanout rules.
        It returns instantly with structured metadata, allowing nodes to complete normally.
        """
        def dasein_deadletter(
            original_tool: str,
            original_args_fingerprint: str,
            reason_code: str,
            policy_trace_id: str,
            tokens_saved_estimate: int = 0,
            cached_result: Any = None
        ) -> Any:
            """Universal dead-letter tool for blocked policy calls.
            
            **INTERNAL USE ONLY - DO NOT CALL DIRECTLY**
            
            This tool is automatically invoked when Dasein blocks a call for policy reasons
            (e.g., anti-fanout rules). Supports transparent deduplication by returning
            cached results from previous identical calls.
            
            Args:
                original_tool: Name of the tool that was blocked
                original_args_fingerprint: Hash/summary of original arguments
                reason_code: Why the call was blocked (e.g., "duplicate_detected")
                policy_trace_id: Trace ID for the rule that caused the block
                tokens_saved_estimate: Estimated tokens saved by blocking this call
                cached_result: If provided, return this (transparent deduplication)
            
            Returns:
                Either cached_result (transparent) or structured error dict (explicit block)
            """
            import time
            
            if cached_result is not None:
                # Transparent deduplication - return the original result seamlessly
                print(f"[DASEIN][DEADLETTER] 🔄 Transparent dedup: {original_tool} (returning cached result, {tokens_saved_estimate} tokens saved)")
                return cached_result
            else:
                # Explicit block - return error structure
                result = {
                    "blocked_by_policy": True,
                    "original_tool": original_tool,
                    "original_args_fingerprint": original_args_fingerprint,
                    "reason_code": reason_code,
                    "policy_trace_id": policy_trace_id,
                    "tokens_saved_estimate": tokens_saved_estimate,
                    "timestamp": time.time(),
                    "message": f"Call to {original_tool} was blocked by Dasein policy: {reason_code}"
                }
                print(f"[DASEIN][DEADLETTER] 🚫 Blocked {original_tool}: {reason_code} (est. {tokens_saved_estimate} tokens saved)")
                return result
        
        return dasein_deadletter
    
    def _inject_deadletter_tool(self):
        """Inject the dead-letter tool into the agent's tool registry.
        
        The tool is added to the executor but hidden from the LLM's view by marking it internal.
        """
        try:
            deadletter_fn = self._create_deadletter_tool()
            
            # Convert to LangChain Tool
            from langchain.tools import Tool
            deadletter_tool = Tool(
                name="dasein_deadletter",
                description="**INTERNAL USE ONLY - DO NOT CALL DIRECTLY**\nThis tool is automatically invoked when Dasein blocks a call for policy reasons.",
                func=deadletter_fn
            )
            
            # For LangGraph agents: Add to tools list in langgraph_params
            if self._is_langgraph and self._langgraph_params and 'tools' in self._langgraph_params:
                self._langgraph_params['tools'].append(deadletter_tool)
                print(f"[DASEIN][DEADLETTER] Injected dead-letter tool into LangGraph params")
            
            # For LangChain agents: Add to agent's tools attribute if accessible
            elif hasattr(self._agent, 'tools'):
                if isinstance(self._agent.tools, list):
                    self._agent.tools.append(deadletter_tool)
                    print(f"[DASEIN][DEADLETTER] Injected dead-letter tool into LangChain agent")
            
            # Store reference for later use
            self._deadletter_tool = deadletter_tool
            self._deadletter_fn = deadletter_fn
            
        except Exception as e:
            print(f"[DASEIN][DEADLETTER] Failed to inject dead-letter tool: {e}")
            import traceback
            traceback.print_exc()
            self._deadletter_tool = None
            self._deadletter_fn = None
    
    def _wrap_agent_llm(self):
        """Conditionally wrap LLM OR monkey-patch based on agent type."""
        try:
            # CRITICAL: Detect agent type to choose the right interception strategy
            # - Deep Research (LangGraph multi-agent with runtime tools) → Monkey-patch ONLY
            # - SQL agent (NOT LangGraph) → Wrapper ONLY
            # - Web Browse (LangGraph single-agent, recreates successfully) → Wrapper ONLY
            
            is_deep_research = False
            if self._is_langgraph:
                # Check if we failed to recreate (means it's deep research multi-agent)
                # Note: _agent_was_recreated is set in _recreate_langgraph_agent_with_prompt (line 1583)
                recreation_failed = not hasattr(self, '_agent_was_recreated') or not self._agent_was_recreated
                if recreation_failed:
                    is_deep_research = True
            
            if is_deep_research:
                # Deep Research: Use monkey-patch ONLY (no wrapper to avoid double interception)
                self._vprint(f"[DASEIN][WRAPPER] Using monkey-patch strategy (Deep Research)")
                self._wrapped_llm = None  # Don't wrap
                self._monkey_patch_llm_classes()  # Monkey-patch for hotpath interception
            else:
                # SQL/Web Browse: Use wrapper ONLY (no monkey-patch to avoid double interception)
                self._vprint(f"[DASEIN][WRAPPER] Using wrapper strategy (SQL/WebBrowse)")
                llm = self._find_llm_recursively(self._agent, max_depth=5)
                if llm:
                    wrapped_llm = DaseinLLMWrapper(llm, self._callback_handler, verbose=self._verbose)
                    self._replace_llm_in_structure(self._agent, llm, wrapped_llm, max_depth=5)
                    self._wrapped_llm = wrapped_llm
                    self._vprint(f"[DASEIN][WRAPPER] Successfully wrapped {type(llm).__name__} LLM")
                else:
                    self._vprint(f"[DASEIN][WRAPPER] Could not find any LLM in agent structure")
                    self._wrapped_llm = None
                # Do NOT monkey-patch (would conflict with wrapper)
            
        except Exception as e:
            self._vprint(f"[DASEIN][WRAPPER] Failed to wrap agent LLM: {e}")
            import traceback
            traceback.print_exc()
            self._wrapped_llm = None
    
    def _replace_llm_in_structure(self, obj, original_llm, wrapped_llm, max_depth=5, path=""):
        """Replace the original LLM with wrapped LLM in the structure."""
        if max_depth <= 0:
            return
        
        # Special handling for RunnableSequence - check steps
        if hasattr(obj, 'steps') and hasattr(obj, '__iter__'):
            for i, step in enumerate(obj.steps):
                if step is original_llm:
                    self._vprint(f"[DASEIN][WRAPPER] Replacing LLM at {path}.steps[{i}]")
                    obj.steps[i] = wrapped_llm
                    return
                # Check if step has bound attribute (RunnableBinding)
                if hasattr(step, 'bound') and step.bound is original_llm:
                    self._vprint(f"[DASEIN][WRAPPER] Replacing LLM at {path}.steps[{i}].bound")
                    step.bound = wrapped_llm
                    return
                # Recursively search in the step
                self._replace_llm_in_structure(step, original_llm, wrapped_llm, max_depth - 1, f"{path}.steps[{i}]")
        
        # Search in attributes
        for attr_name in dir(obj):
            if attr_name.startswith('_'):
                continue
            try:
                attr_value = getattr(obj, attr_name)
                if attr_value is original_llm:
                    self._vprint(f"[DASEIN][WRAPPER] Replacing LLM at {path}.{attr_name}")
                    setattr(obj, attr_name, wrapped_llm)
                    return
                # Recursively search in the attribute
                if hasattr(attr_value, '__dict__') or hasattr(attr_value, '__iter__'):
                    self._replace_llm_in_structure(attr_value, original_llm, wrapped_llm, max_depth - 1, f"{path}.{attr_name}")
            except:
                continue
    
    def _monkey_patch_llm_classes(self):
        """Monkey-patch ALL LLM classes found in agent + tools for Pipecleaner deduplication."""
        try:
            # Find ALL LLMs in agent structure + tools
            print(f"[DASEIN][WRAPPER] Searching for ALL LLMs in agent+tools...")
            all_llms = []
            
            # 1. Search in agent
            agent_llm = self._find_llm_recursively(self._agent, max_depth=5)
            if agent_llm:
                # CRITICAL: If this is a DaseinLLMWrapper, we need to patch the INNER LLM for pipecleaner!
                # But we skip patching the wrapper itself to avoid double callbacks
                if isinstance(agent_llm, DaseinLLMWrapper) and hasattr(agent_llm, '_llm'):
                    print(f"[DASEIN][WRAPPER] Found DaseinLLMWrapper, patching inner LLM: {type(agent_llm._llm).__name__}")
                    all_llms.append(('agent_inner', agent_llm._llm))
                else:
                    all_llms.append(('agent', agent_llm))
            
            # 2. Search in tools (where Summary LLM lives!)
            if hasattr(self._agent, 'tools'):
                for i, tool in enumerate(self._agent.tools or []):
                    tool_llm = self._find_llm_recursively(tool, max_depth=3, path=f"tools[{i}]")
                    if tool_llm:
                        # Skip if it's a DaseinLLMWrapper (already handles callbacks)
                        if isinstance(tool_llm, DaseinLLMWrapper):
                            print(f"[DASEIN][WRAPPER] Found DaseinLLMWrapper in tool - skipping")
                        else:
                            all_llms.append((f'tool_{i}_{getattr(tool, "name", "unknown")}', tool_llm))
            
            print(f"[DASEIN][WRAPPER] Found {len(all_llms)} LLM(s)")
            for location, llm in all_llms:
                print(f"[DASEIN][WRAPPER]   - {location}: {type(llm).__name__}")
            
            # Patch all unique LLM classes (use instance variable to persist across calls)
            for location, llm in all_llms:
                llm_class = type(llm)
                if llm_class in self._patched_llm_classes:
                    print(f"[DASEIN][WRAPPER] {llm_class.__name__} already patched (from previous call), skipping")
                    continue
                    
                print(f"[DASEIN][WRAPPER] Patching {llm_class.__name__} (found in {location})...")
                
                # Check what methods the LLM class has
                # CRITICAL: Only patch LOW-LEVEL methods (_generate, _agenerate) to prevent recursion!
                # High-level methods (invoke, ainvoke) internally call _generate/_agenerate, 
                # so patching both causes double deduplication.
                print(f"[DASEIN][WRAPPER] Checking LLM methods...")
                methods_to_patch = []
                for method in ['_generate', '_agenerate']:  # LOW-LEVEL only to prevent recursion
                    if hasattr(llm_class, method):
                        print(f"[DASEIN][WRAPPER]   - Has {method}")
                        methods_to_patch.append(method)
                
                if not methods_to_patch:
                    print(f"[DASEIN][WRAPPER] No methods to patch found!")
                    return
                
                # Check if we already patched this class
                first_method = getattr(llm_class, methods_to_patch[0])
                if hasattr(first_method, '_dasein_patched'):
                    print(f"[DASEIN][WRAPPER] {llm_class.__name__} already patched, skipping")
                    return
                    
                callback_handler = self._callback_handler
                
                # Thread-local to track depth and max depth reached
                import threading
                _patch_depth = threading.local()
                
                def get_max_depth():
                    return getattr(_patch_depth, 'max_depth', 0)
                
                def set_max_depth(val):
                    _patch_depth.max_depth = val
                
                def is_in_microturn():
                    return getattr(_patch_depth, 'in_microturn', False)
                
                def set_in_microturn(val):
                    _patch_depth.in_microturn = val
                
                # Thread-local state tracking for Summary calls (mirrors callback pattern)
                def get_summary_calls_made():
                    """Get count of Summary calls made in this run."""
                    return getattr(_patch_depth, 'summary_calls_made', 0)
                
                def increment_summary_calls():
                    """Increment Summary call counter."""
                    current = getattr(_patch_depth, 'summary_calls_made', 0)
                    _patch_depth.summary_calls_made = current + 1
                    return _patch_depth.summary_calls_made
                
                # Patch ALL methods (silent)
                for method_name in methods_to_patch:
                    original_method = getattr(llm_class, method_name)
                    is_async = 'a' in method_name and (method_name.startswith('a') or method_name.startswith('_a'))
                    
                    # Use a factory function to properly capture the closure variables
                    def make_patched_method(orig_method, meth_name, is_async_method, depth_tracker, max_depth_getter, max_depth_setter, in_microturn_getter, in_microturn_setter, get_summary_calls, increment_summary):
                        if is_async_method:
                            async def patched_method(self_llm, *args, **kwargs):
                                # Track depth to find the leaf method
                                depth = getattr(depth_tracker, 'value', 0)
                                is_entry_point = (depth == 0)
                                depth_tracker.value = depth + 1
                                current_depth = depth_tracker.value
                                
                                # Track max depth reached (silent)
                                if is_entry_point:
                                    max_depth_setter(current_depth)
                                else:
                                    if current_depth > max_depth_getter():
                                        max_depth_setter(current_depth)
                                
                                # 🔥 PIPECLEANER DEDUPLICATION (only patching top-level methods, always apply)
                                # Skip depth checks - they don't work with async/parallel execution
                                # NO RE-ENTRANCY GUARD: We need all Summary calls to batch together
                                # The embedding model (SentenceTransformer) does NOT use LangChain, so no recursion risk
                                if callback_handler:
                                    try:
                                        # Extract messages from args based on method signature
                                        messages_to_dedupe = None
                                        arg_index = 0
                                        
                                        if meth_name in ['invoke', 'ainvoke']:
                                            # First arg is 'input' (can be string, list, or PromptValue)
                                            messages_to_dedupe = args[0] if args else kwargs.get('input', kwargs.get('messages'))
                                            arg_index = 0
                                        elif meth_name in ['_generate', '_agenerate']:
                                            # First arg is 'messages' (list of BaseMessage)
                                            messages_to_dedupe = args[0] if args else kwargs.get('messages')
                                            arg_index = 0
                                        elif meth_name in ['generate', 'agenerate']:
                                            # First arg is 'prompts' (list of message lists)
                                            messages_to_dedupe = args[0] if args else kwargs.get('prompts')
                                            arg_index = 0
                                        
                                        # Convert to strings for deduplication
                                        if messages_to_dedupe:
                                            prompt_strings = []
                                            for msg in (messages_to_dedupe if isinstance(messages_to_dedupe, list) else [messages_to_dedupe]):
                                                if hasattr(msg, 'content'):
                                                    prompt_strings.append(msg.content)
                                                elif isinstance(msg, str):
                                                    prompt_strings.append(msg)
                                                else:
                                                    prompt_strings.append(str(msg))
                                    # HOTPATH DEBUGGING (commented out for production)
                                    # =============================================================
                                    # print(f"\n{'='*70}")
                                    # print(f"[🔥 HOTPATH] {meth_name}() call")
                                    # print(f"{'='*70}")
                                    # current_node = getattr(callback_handler, '_current_chain_node', None)
                                    # current_tool = getattr(callback_handler, '_current_tool_name', None)
                                    # print(f"[🔥] Current node: {current_node}")
                                    # print(f"[🔥] Current tool: {current_tool}")
                                    # print(f"{'='*70}\n")
                                        
                                    # =============================================================
                                    # Extract tools from LLM call kwargs (for filter_search rules)
                                    # =============================================================
                                        tools_in_this_call = []
                                        
                                    # Extract tool names from kwargs (handles multiple LLM providers' formats)
                                    # Pattern 1: invocation_params (some providers)
                                        if 'invocation_params' in kwargs:
                                            inv_params = kwargs['invocation_params']
                                            tools_param = inv_params.get('tools') or inv_params.get('functions') or []
                                            for t in tools_param:
                                                if isinstance(t, dict):
                                                # Try: t['name'] or t['function']['name']
                                                    name = t.get('name') or (t.get('function', {}).get('name') if isinstance(t.get('function'), dict) else None)
                                                    if name:
                                                        tools_in_this_call.append(name)
                                    # Pattern 2: Direct 'tools' key (common)
                                        elif 'tools' in kwargs:
                                            tools_param = kwargs.get('tools', [])
                                            for t in tools_param:
                                                if isinstance(t, dict):
                                                # Try: t['name'] or t['function']['name']
                                                    name = t.get('name') or (t.get('function', {}).get('name') if isinstance(t.get('function'), dict) else None)
                                                    if name:
                                                        tools_in_this_call.append(name)
                                    # Pattern 3: 'functions' key (OpenAI function calling)
                                        elif 'functions' in kwargs:
                                            funcs_param = kwargs.get('functions', [])
                                            for t in funcs_param:
                                                if isinstance(t, dict):
                                                    name = t.get('name')
                                                    if name:
                                                        tools_in_this_call.append(name)
                                    # Pattern 4: additional_kwargs (Gemini and other providers store tools here)
                                        if not tools_in_this_call and messages_to_dedupe:
                                            msgs_to_check = messages_to_dedupe if isinstance(messages_to_dedupe, list) else [messages_to_dedupe]
                                            # Check ALL messages for additional_kwargs (not just first)
                                            for msg in msgs_to_check:
                                                if hasattr(msg, 'additional_kwargs') and msg.additional_kwargs:
                                                    add_kwargs = msg.additional_kwargs
                                                    tools_param = add_kwargs.get('tools') or add_kwargs.get('functions') or []
                                                    for t in tools_param:
                                                        if isinstance(t, dict):
                                                            # Gemini format: {'function_declarations': [{'name': '...'}]}
                                                            if 'function_declarations' in t:
                                                                for func in t.get('function_declarations', []):
                                                                    name = func.get('name')
                                                                    if name:
                                                                        tools_in_this_call.append(name)
                                                            else:
                                                                name = t.get('name') or (t.get('function', {}).get('name') if isinstance(t.get('function'), dict) else None)
                                                                if name:
                                                                    tools_in_this_call.append(name)
                                                    # Break after first message with tools
                                                    if tools_in_this_call:
                                                        break
                                        
                                    # Check if any filter_search rules match the tools in this LLM call
                                        from .pipecleaner import _find_filter_search_rules
                                        filter_rules = None
                                        should_dedupe = False
                                        
                                        # 🎯 USE EXTRACTED TOOLS from hotpath, not callback state (callback is too late!)
                                        if hasattr(callback_handler, '_selected_rules') and prompt_strings and tools_in_this_call:
                                        # Get all filter_search rules (they specify which tools to target via references.tools)
                                            filter_rules = _find_filter_search_rules('*', callback_handler._selected_rules)
                                            
                                        # Check if any extracted tool matches rule's target tools
                                            if filter_rules:
                                                for rule in filter_rules:
                                                # Handle both dict and object formats
                                                    if isinstance(rule, dict):
                                                        references = rule.get('references', {})
                                                        rule_tools = references.get('tools', []) if isinstance(references, dict) else []
                                                    else:
                                                        references = getattr(rule, 'references', None)
                                                    # references might be a dict or object, handle both
                                                        if isinstance(references, dict):
                                                            rule_tools = references.get('tools', [])
                                                        elif references:
                                                            rule_tools = getattr(references, 'tools', [])
                                                        else:
                                                            rule_tools = []
                                                    
                                                    # Match extracted tools against rule's target tools (case-insensitive)
                                                    for tool_in_call in tools_in_this_call:
                                                        if tool_in_call.lower() in [rt.lower() for rt in rule_tools]:
                                                            should_dedupe = True
                                                            break
                                                    if should_dedupe:
                                                        break
                                        
                                            if should_dedupe:
                                                    # Deduplicate each prompt
                                                    from .pipecleaner import get_or_create_corpus
                                                    import hashlib
                                                    corpus = get_or_create_corpus(callback_handler.run_id, verbose=callback_handler._verbose)
                                                
                                                    deduplicated_strings = []
                                                    for i, prompt_str in enumerate(prompt_strings):
                                                        if len(prompt_str) < 2500:
                                                            deduplicated_strings.append(prompt_str)
                                                            continue
                                                        
                                                        # Split system/content like in callback
                                                        system_part = prompt_str[:2000]
                                                        content_part = prompt_str[2000:]
                                                        prompt_id = f"p{i}_{hashlib.md5(content_part[:100].encode()).hexdigest()[:8]}"
                                                        
                                                        # Deduplicate (ASYNC - allows parallel Summary calls to batch together)
                                                        deduplicated_content = await corpus.enqueue_prompt(prompt_id, content_part)
                                                        deduplicated_str = system_part + deduplicated_content
                                                        deduplicated_strings.append(deduplicated_str)
                                                    
                                                    # Convert back to original format
                                                    if isinstance(messages_to_dedupe, list):
                                                        for i, msg in enumerate(messages_to_dedupe):
                                                            if i < len(deduplicated_strings) and hasattr(msg, 'content'):
                                                                msg.content = deduplicated_strings[i]
                                                    elif isinstance(messages_to_dedupe, str):
                                                        messages_to_dedupe = deduplicated_strings[0] if deduplicated_strings else messages_to_dedupe
                                                    
                                                    # Replace in args/kwargs
                                                    if args and arg_index < len(args):
                                                        args = list(args)
                                                        args[arg_index] = messages_to_dedupe
                                                        args = tuple(args)
                                                    elif 'input' in kwargs:
                                                        kwargs['input'] = messages_to_dedupe
                                                    elif 'messages' in kwargs:
                                                        kwargs['messages'] = messages_to_dedupe
                                                    elif 'prompts' in kwargs:
                                                        kwargs['prompts'] = messages_to_dedupe
                                    except Exception as e:
                                        print(f"[🔥 HOTPATH] ⚠️ Deduplication error: {e}")
                                        import traceback
                                        traceback.print_exc()
                                
                                try:
                                    result = await orig_method(self_llm, *args, **kwargs)
                                    
                                    # 🚨 MICROTURN ENFORCEMENT - DISABLED
                                    # Microturn can interfere with tool execution, so it's disabled
                                    # TODO: Re-enable with proper gating if needed for specific use cases
                                    
                                    return result
                                finally:
                                    # Restore depth on exit
                                    depth_tracker.value = depth
                                    # Clear processed tool calls set when returning to entry point (prevents memory leak)
                                    if depth == 0:
                                        if hasattr(_patch_depth, 'processed_tool_calls'):
                                            _patch_depth.processed_tool_calls.clear()
                                        if hasattr(_patch_depth, 'seen_tool_signatures'):
                                            _patch_depth.seen_tool_signatures.clear()
                                        if hasattr(_patch_depth, 'tool_result_cache'):
                                            _patch_depth.tool_result_cache.clear()
                            
                            return patched_method
                        else:
                            def patched_method(self_llm, *args, **kwargs):
                                # Track depth to find the leaf method
                                depth = getattr(depth_tracker, 'value', 0)
                                is_entry_point = (depth == 0)
                                depth_tracker.value = depth + 1
                                current_depth = depth_tracker.value
                                
                                # Track max depth reached
                                if is_entry_point:
                                    max_depth_setter(current_depth)  # Reset for new entry
                                else:
                                    # Update max if we went deeper
                                    if current_depth > max_depth_getter():
                                        max_depth_setter(current_depth)
                                
                                # 🔥 PIPECLEANER DEDUPLICATION (use thread-local for per-thread re-entrancy guard!)
                                # CRITICAL: depth_tracker is shared, so use thread-local which is per-thread
                                import threading
                                if not hasattr(_patch_depth, '_dedupe_guard_sync'):
                                    _patch_depth._dedupe_guard_sync = threading.local()
                                
                                in_dedupe = getattr(_patch_depth._dedupe_guard_sync, 'value', False)
                                if callback_handler and not in_dedupe:
                                    _patch_depth._dedupe_guard_sync.value = True
                                    try:
                                        # Extract messages from args based on method signature
                                        messages_to_dedupe = None
                                        arg_index = 0
                                        
                                        if meth_name in ['invoke', 'ainvoke']:
                                            messages_to_dedupe = args[0] if args else kwargs.get('input', kwargs.get('messages'))
                                            arg_index = 0
                                        elif meth_name in ['_generate', '_agenerate']:
                                            messages_to_dedupe = args[0] if args else kwargs.get('messages')
                                            arg_index = 0
                                        elif meth_name in ['generate', 'agenerate']:
                                            messages_to_dedupe = args[0] if args else kwargs.get('prompts')
                                            arg_index = 0
                                        
                                        # Convert to strings for deduplication
                                        if messages_to_dedupe:
                                            prompt_strings = []
                                            for msg in (messages_to_dedupe if isinstance(messages_to_dedupe, list) else [messages_to_dedupe]):
                                                if hasattr(msg, 'content'):
                                                    prompt_strings.append(msg.content)
                                                elif isinstance(msg, str):
                                                    prompt_strings.append(msg)
                                                else:
                                                    prompt_strings.append(str(msg))
                                            
                                            # =============================================================
                                            # HOTPATH DEBUGGING (commented out for production)
                                            # =============================================================
                                            # print(f"\n{'='*70}")
                                            # print(f"[🔥 HOTPATH FULL DEBUG] {meth_name}() call")
                                            # print(f"{'='*70}")
                                            # 
                                            # # 1. Callback state
                                            # current_node = getattr(callback_handler, '_current_chain_node', None)
                                            # current_tool = getattr(callback_handler, '_current_tool_name', None)
                                            # print(f"[🔥] Current node: {current_node}")
                                            # print(f"[🔥] Current tool: {current_tool}")
                                            # 
                                            # # 2. Tools in this call
                                            # tools_in_call = []
                                            # if 'invocation_params' in kwargs:
                                            #     tools = kwargs['invocation_params'].get('tools') or kwargs['invocation_params'].get('functions') or []
                                            #     tools_in_call = [t.get('name', t.get('function', {}).get('name', '?')) for t in tools]
                                            # elif 'tools' in kwargs:
                                            #     tools_in_call = [t.get('name', '?') for t in kwargs.get('tools', [])]
                                            # elif 'functions' in kwargs:
                                            #     tools_in_call = [t.get('name', '?') for t in kwargs.get('functions', [])]
                                            # print(f"[🔥] Tools in call: {tools_in_call if tools_in_call else 'NONE'}")
                                            # 
                                            # # 3. Prompt characteristics
                                            # prompt_lens = [len(s) for s in prompt_strings]
                                            # print(f"[🔥] Prompt count: {len(prompt_strings)}")
                                            # print(f"[🔥] Prompt lengths: {prompt_lens}")
                                            # 
                                            # # 4. Kwargs keys (for debugging)
                                            # print(f"[🔥] Kwargs keys: {list(kwargs.keys())}")
                                            # 
                                            # # 5. Messages structure
                                            # if messages_to_dedupe:
                                            #     if isinstance(messages_to_dedupe, list):
                                            #         msg_types = [type(m).__name__ for m in messages_to_dedupe[:3]]
                                            #         print(f"[🔥] Message types (first 3): {msg_types}")
                                            #     else:
                                            #         print(f"[🔥] Messages type: {type(messages_to_dedupe).__name__}")
                                            # 
                                            # print(f"{'='*70}\n")
                                            # 
                                            # # Show first 200 chars to see the fingerprint
                                            # if prompt_strings:
                                            #     first_200 = prompt_strings[0][:200] if len(prompt_strings[0]) > 200 else prompt_strings[0]
                                            #     print(f"[🔥] Prompt start (200 chars): {first_200}")
                                            
                                            # =============================================================
                                            # Extract tools from LLM call kwargs (for filter_search rules)
                                            # =============================================================
                                            tools_in_this_call = []
                                            
                                            # Extract tool names from kwargs (handles multiple LLM providers' formats)
                                            # Pattern 1: invocation_params (some providers)
                                            if 'invocation_params' in kwargs:
                                                inv_params = kwargs['invocation_params']
                                                tools_param = inv_params.get('tools') or inv_params.get('functions') or []
                                                for t in tools_param:
                                                    if isinstance(t, dict):
                                                        # Try: t['name'] or t['function']['name']
                                                        name = t.get('name') or (t.get('function', {}).get('name') if isinstance(t.get('function'), dict) else None)
                                                        if name:
                                                            tools_in_this_call.append(name)
                                            # Pattern 2: Direct 'tools' key (common)
                                            elif 'tools' in kwargs:
                                                tools_param = kwargs.get('tools', [])
                                                for t in tools_param:
                                                    if isinstance(t, dict):
                                                        # Try: t['name'] or t['function']['name']
                                                        name = t.get('name') or (t.get('function', {}).get('name') if isinstance(t.get('function'), dict) else None)
                                                        if name:
                                                            tools_in_this_call.append(name)
                                            # Pattern 3: 'functions' key (OpenAI function calling)
                                            elif 'functions' in kwargs:
                                                funcs_param = kwargs.get('functions', [])
                                                for t in funcs_param:
                                                    if isinstance(t, dict):
                                                        name = t.get('name')
                                                        if name:
                                                            tools_in_this_call.append(name)
                                            
                                            # Check if any filter_search rules match the tools in this LLM call
                                            from .pipecleaner import _find_filter_search_rules
                                            filter_rules = None
                                            should_dedupe = False
                                            
                                            # 🎯 USE EXTRACTED TOOLS from hotpath, not callback state (callback is too late!)
                                            if hasattr(callback_handler, '_selected_rules') and prompt_strings and tools_in_this_call:
                                                # Get all filter_search rules (they specify which tools to target via references.tools)
                                                filter_rules = _find_filter_search_rules('*', callback_handler._selected_rules)
                                                
                                                # Check if any extracted tool matches rule's target tools
                                                if filter_rules:
                                                    for rule in filter_rules:
                                                        # Handle both dict and object formats
                                                        if isinstance(rule, dict):
                                                            references = rule.get('references', {})
                                                            rule_tools = references.get('tools', []) if isinstance(references, dict) else []
                                                        else:
                                                            references = getattr(rule, 'references', None)
                                                            # references might be a dict or object, handle both
                                                            if isinstance(references, dict):
                                                                rule_tools = references.get('tools', [])
                                                            elif references:
                                                                rule_tools = getattr(references, 'tools', [])
                                                            else:
                                                                rule_tools = []
                                                        
                                                        # Match extracted tools against rule's target tools (case-insensitive)
                                                        for tool_in_call in tools_in_this_call:
                                                            if tool_in_call.lower() in [rt.lower() for rt in rule_tools]:
                                                                should_dedupe = True
                                                                break
                                                        if should_dedupe:
                                                            break
                                            
                                            if should_dedupe:
                                                    # Deduplicate each prompt
                                                    from .pipecleaner import get_or_create_corpus
                                                    import hashlib
                                                    corpus = get_or_create_corpus(callback_handler.run_id, verbose=callback_handler._verbose)
                                                    
                                                    deduplicated_strings = []
                                                    for i, prompt_str in enumerate(prompt_strings):
                                                        if len(prompt_str) < 2500:
                                                            deduplicated_strings.append(prompt_str)
                                                            continue
                                                        
                                                        # Split system/content like in callback
                                                        system_part = prompt_str[:2000]
                                                        content_part = prompt_str[2000:]
                                                        prompt_id = f"p{i}_{hashlib.md5(content_part[:100].encode()).hexdigest()[:8]}"
                                                        
                                                        # Deduplicate (wrap async in sync context)
                                                        import asyncio
                                                        try:
                                                            loop = asyncio.get_event_loop()
                                                        except RuntimeError:
                                                            loop = asyncio.new_event_loop()
                                                            asyncio.set_event_loop(loop)
                                                        
                                                        deduplicated_content = loop.run_until_complete(corpus.enqueue_prompt(prompt_id, content_part))
                                                        deduplicated_str = system_part + deduplicated_content
                                                        deduplicated_strings.append(deduplicated_str)
                                                    
                                                    # Convert back to original format
                                                    if isinstance(messages_to_dedupe, list):
                                                        for i, msg in enumerate(messages_to_dedupe):
                                                            if i < len(deduplicated_strings) and hasattr(msg, 'content'):
                                                                msg.content = deduplicated_strings[i]
                                                    elif isinstance(messages_to_dedupe, str):
                                                        messages_to_dedupe = deduplicated_strings[0] if deduplicated_strings else messages_to_dedupe
                                                    
                                                    # Replace in args/kwargs
                                                    if args and arg_index < len(args):
                                                        args = list(args)
                                                        args[arg_index] = messages_to_dedupe
                                                        args = tuple(args)
                                                    elif 'input' in kwargs:
                                                        kwargs['input'] = messages_to_dedupe
                                                    elif 'messages' in kwargs:
                                                        kwargs['messages'] = messages_to_dedupe
                                                    elif 'prompts' in kwargs:
                                                        kwargs['prompts'] = messages_to_dedupe
                                    except Exception as e:
                                        print(f"[🔥 HOTPATH] ⚠️ Deduplication error: {e}")
                                        import traceback
                                        traceback.print_exc()
                                
                                try:
                                    # NOTE: Manual callback injection DISABLED - DaseinLLMWrapper handles callbacks
                                    # The patched methods ONLY do pipecleaner deduplication, not callbacks
                                    result = orig_method(self_llm, *args, **kwargs)
                                    
                                    # 🚨 MICROTURN ENFORCEMENT - DISABLED (can interfere with tool execution)
                                    # TODO: Re-enable with proper gating if needed
                                    
                                    return result
                                finally:
                                    # CRITICAL: Reset re-entrancy guard AFTER LLM call completes
                                    if hasattr(_patch_depth, '_dedupe_guard_sync'):
                                        _patch_depth._dedupe_guard_sync.value = False
                                    
                                    depth_tracker.value = depth  # Restore depth on exit
                                    # Clear processed tool calls set when returning to entry point (prevents memory leak)
                                    if depth == 0:
                                        if hasattr(_patch_depth, 'processed_tool_calls'):
                                            _patch_depth.processed_tool_calls.clear()
                                        if hasattr(_patch_depth, 'seen_tool_signatures'):
                                            _patch_depth.seen_tool_signatures.clear()
                                        if hasattr(_patch_depth, 'tool_result_cache'):
                                            _patch_depth.tool_result_cache.clear()
                        return patched_method
                    
                    patched_method = make_patched_method(original_method, method_name, is_async, _patch_depth, get_max_depth, set_max_depth, is_in_microturn, set_in_microturn, get_summary_calls_made, increment_summary_calls)
                    
                    # Mark and apply the patch
                    patched_method._dasein_patched = True
                    setattr(llm_class, method_name, patched_method)
                    print(f"[DASEIN][WRAPPER] Patched {method_name}")
                
                # Mark this class as patched
                self._patched_llm_classes.add(llm_class)
                self._wrapped_llm = llm
                print(f"[DASEIN][WRAPPER] Successfully patched {len(methods_to_patch)} methods in {llm_class.__name__}")
            
            print(f"[DASEIN][WRAPPER] Finished patching LLM classes (total patched across all calls: {len(self._patched_llm_classes)})")
            return
        except Exception as e:
            print(f"[DASEIN][WRAPPER] Failed to wrap agent LLM: {e}")
            import traceback
            traceback.print_exc()
            self._wrapped_llm = None
    
    def _set_callback_handler_llm(self):
        """Set the LLM reference in the callback handler for micro-turn calls."""
        try:
            # Use the wrapped LLM if available, otherwise find it in the agent
            if self._wrapped_llm:
                self._callback_handler._llm = self._wrapped_llm
                self._vprint(f"[DASEIN][CALLBACK] Set wrapped LLM reference in callback handler")
            elif hasattr(self._agent, 'llm'):
                self._callback_handler._llm = self._agent.llm
                self._vprint(f"[DASEIN][CALLBACK] Set agent LLM reference in callback handler")
            else:
                self._vprint(f"[DASEIN][CALLBACK] No LLM found in agent")
        except Exception as e:
            self._vprint(f"[DASEIN][CALLBACK] Error setting LLM reference: {e}")
    
    def _find_llm_recursively(self, obj, max_depth=5, path=""):
        """Recursively find any LLM-like object in the structure."""
        if max_depth <= 0:
            return None
        
        # Check if this object is an LLM
        if self._is_llm_like(obj):
            self._vprint(f"[DASEIN][WRAPPER] Found LLM at {path}: {type(obj).__name__}")
            return obj
        
        # Special handling for RunnableSequence - check steps
        if hasattr(obj, 'steps') and hasattr(obj, '__iter__'):
            for i, step in enumerate(obj.steps):
                if self._is_llm_like(step):
                    self._vprint(f"[DASEIN][WRAPPER] Found LLM at {path}.steps[{i}]: {type(step).__name__}")
                    return step
                # Check if step has bound attribute (RunnableBinding)
                if hasattr(step, 'bound') and self._is_llm_like(step.bound):
                    self._vprint(f"[DASEIN][WRAPPER] Found LLM at {path}.steps[{i}].bound: {type(step.bound).__name__}")
                    return step.bound
                # Recursively search in the step
                result = self._find_llm_recursively(step, max_depth - 1, f"{path}.steps[{i}]")
                if result:
                    return result
        
        # Search in attributes
        for attr_name in dir(obj):
            if attr_name.startswith('_'):
                continue
            try:
                attr_value = getattr(obj, attr_name)
                if self._is_llm_like(attr_value):
                    self._vprint(f"[DASEIN][WRAPPER] Found LLM at {path}.{attr_name}: {type(attr_value).__name__}")
                    return attr_value
                # Recursively search in the attribute
                if hasattr(attr_value, '__dict__') or hasattr(attr_value, '__iter__'):
                    result = self._find_llm_recursively(attr_value, max_depth - 1, f"{path}.{attr_name}")
                    if result:
                        return result
            except:
                continue
        
        return None
    
    def _is_llm_like(self, obj):
        """Check if an object is a real LLM by looking for specific LangChain model classes."""
        if obj is None:
            return False
        
        # Skip non-LLM objects
        skip_classes = [
            'AgentExecutor', 'RunnableAgent', 'RunnableSequence', 'RunnableBinding',
            'ReActSingleInputOutputParser', 'PromptTemplate', 'RunnableAssign',
            'OutputParser', 'BaseOutputParser', 'Parser', 'Tool', 'BaseTool'
        ]
        if any(skip_class in str(type(obj)) for skip_class in skip_classes):
            return False
        
        # Look for specific LangChain model classes
        model_classes = [
            'ChatGoogleGenerativeAI',
            'ChatOpenAI', 
            'ChatAnthropic',
            'ChatClaude',
            'OpenAI',
            'Anthropic',
            'BaseChatModel',
            'BaseLanguageModel',
            'BaseLLM'
        ]
        
        class_name = type(obj).__name__
        for model_class in model_classes:
            if model_class in class_name:
                self._vprint(f"[DASEIN][WRAPPER] Found LLM: {class_name}")
                return True
        
        # Check class hierarchy for LangChain base classes
        try:
            for base in obj.__class__.__mro__:
                base_name = base.__name__
                if any(model_class in base_name for model_class in ['BaseChatModel', 'BaseLanguageModel', 'BaseLLM']):
                    self._vprint(f"[DASEIN][WRAPPER] Found LLM via inheritance: {class_name} -> {base_name}")
                    return True
        except:
            pass
        
        return False
    
    def _replace_llm_in_structure(self, obj, original_llm, wrapped_llm, max_depth=5, path="", count=[0]):
        """Replace the original LLM with wrapped LLM in the structure."""
        if max_depth <= 0:
            return
        
        # Special handling for RunnableSequence - check steps
        if hasattr(obj, 'steps') and hasattr(obj, '__iter__'):
            for i, step in enumerate(obj.steps):
                if step is original_llm:
                    count[0] += 1
                    print(f"[DASEIN][WRAPPER] Replacing LLM #{count[0]} at {path}.steps[{i}]")
                    obj.steps[i] = wrapped_llm
                # Check if step has bound attribute (RunnableBinding)
                if hasattr(step, 'bound') and step.bound is original_llm:
                    count[0] += 1
                    print(f"[DASEIN][WRAPPER] Replacing LLM #{count[0]} at {path}.steps[{i}].bound")
                    step.bound = wrapped_llm
                # Recursively search in the step
                self._replace_llm_in_structure(step, original_llm, wrapped_llm, max_depth - 1, f"{path}.steps[{i}]", count)
        
        # Search in attributes
        for attr_name in dir(obj):
            if attr_name.startswith('_'):
                continue
            try:
                attr_value = getattr(obj, attr_name)
                if attr_value is original_llm:
                    print(f"[DASEIN][WRAPPER] Replacing LLM at {path}.{attr_name}")
                    setattr(obj, attr_name, wrapped_llm)
                    # Verify replacement
                    new_value = getattr(obj, attr_name)
                    print(f"[DASEIN][WRAPPER] After replacement, {path}.{attr_name} is now: {type(new_value).__name__}")
                    print(f"[DASEIN][WRAPPER] Is it our wrapper? {isinstance(new_value, DaseinLLMWrapper)}")
                    return
                # Recursively search in the attribute
                if hasattr(attr_value, '__dict__') or hasattr(attr_value, '__iter__'):
                    self._replace_llm_in_structure(attr_value, original_llm, wrapped_llm, max_depth - 1, f"{path}.{attr_name}")
            except:
                continue
    
    def _inject_tool_rules_to_system_prompt(self, selected_rules):
        """Inject tool_start rules into the system prompt."""
        try:
            if self._verbose:
                self._vprint(f"[DASEIN][SYSTEM_PROMPT] Starting tool rule injection to system prompt")
                self._vprint(f"[DASEIN][SYSTEM_PROMPT] Selected rules count: {len(selected_rules)}")
                self._vprint(f"[DASEIN][SYSTEM_PROMPT] Selected rules: {[str(rule) for rule in selected_rules]}")
            
            # Get tool_start rules
            tool_rules = []
            for rule_meta in selected_rules:
                if isinstance(rule_meta, tuple) and len(rule_meta) == 2:
                    rule, metadata = rule_meta
                    if self._verbose:
                        self._vprint(f"[DASEIN][SYSTEM_PROMPT] Processing rule tuple: {rule.id} -> {rule.target_step_type}")
                else:
                    rule = rule_meta
                    if self._verbose:
                        self._vprint(f"[DASEIN][SYSTEM_PROMPT] Processing rule: {rule.id} -> {rule.target_step_type}")
                
                if hasattr(rule, 'target_step_type') and rule.target_step_type == "tool_start":
                    tool_rules.append(rule)
                    if self._verbose:
                        self._vprint(f"[DASEIN][SYSTEM_PROMPT] Added tool_start rule: {rule.id}")
                        self._vprint(f"[DASEIN][SYSTEM_PROMPT] Rule advice: {rule.advice_text}")
            
            if not tool_rules:
                if self._verbose:
                    self._vprint(f"[DASEIN][SYSTEM_PROMPT] No tool_start rules found to inject")
                return
            
            self._vprint(f"[DASEIN][SYSTEM_PROMPT] Injecting {len(tool_rules)} tool_start rules to system prompt")
            self._vprint(f"[DASEIN][SYSTEM_PROMPT] Tool rules: {[rule.advice_text[:50] + '...' for rule in tool_rules]}")
            
            # Store the tool rules for system prompt injection
            if not hasattr(self, '_tool_rules_for_system'):
                self._tool_rules_for_system = []
            
            self._tool_rules_for_system = tool_rules
            
            if self._verbose:
                self._vprint(f"[DASEIN][SYSTEM_PROMPT] Stored {len(tool_rules)} tool rules for system prompt injection")
                
        except Exception as e:
            self._vprint(f"[DASEIN][SYSTEM_PROMPT] Failed to inject tool rules to system prompt: {e}")
            import traceback
            traceback.print_exc()
    
    def _build_enhanced_tool_description(self, tool, tool_rules):
        """Build enhanced tool description with injected rules."""
        original_desc = self._original_tool_descriptions.get(tool.name, tool.description)
        
        if self._verbose:
            self._vprint(f"[DASEIN][TOOL_DESC] Building enhanced description for {tool.name}")
            self._vprint(f"[DASEIN][TOOL_DESC] Original description length: {len(original_desc)}")
            self._vprint(f"[DASEIN][TOOL_DESC] Processing {len(tool_rules)} rules")
        
        # Build rule instructions
        rule_instructions = []
        for i, rule in enumerate(tool_rules):
            if self._verbose:
                self._vprint(f"[DASEIN][TOOL_DESC] Processing rule {i}: {rule.id}")
                self._vprint(f"[DASEIN][TOOL_DESC] Rule advice: {rule.advice_text}")
            
            if "strip" in rule.advice_text.lower() and "fence" in rule.advice_text.lower():
                instruction = "IMPORTANT: Strip markdown code fences (```sql...```) from your input before processing."
                rule_instructions.append(instruction)
                if self._verbose:
                    self._vprint(f"[DASEIN][TOOL_DESC] Added fence stripping instruction")
            elif "strip" in rule.advice_text.lower() and "whitespace" in rule.advice_text.lower():
                instruction = "IMPORTANT: Strip leading/trailing whitespace from your input before processing."
                rule_instructions.append(instruction)
                if self._verbose:
                    self._vprint(f"[DASEIN][TOOL_DESC] Added whitespace stripping instruction")
            else:
                # Generic rule instruction
                instruction = f"IMPORTANT: {rule.advice_text}"
                rule_instructions.append(instruction)
                if self._verbose:
                    self._vprint(f"[DASEIN][TOOL_DESC] Added generic instruction: {instruction}")
        
        if rule_instructions:
            enhanced_desc = f"{original_desc}\n\nTOOL RULES:\n" + "\n".join(f"- {instruction}" for instruction in rule_instructions)
            if self._verbose:
                self._vprint(f"[DASEIN][TOOL_DESC] Built enhanced description with {len(rule_instructions)} rules")
                self._vprint(f"[DASEIN][TOOL_DESC] Enhanced description length: {len(enhanced_desc)}")
            return enhanced_desc
        else:
            if self._verbose:
                self._vprint(f"[DASEIN][TOOL_DESC] No rule instructions generated, returning original description")
            return original_desc
    
    def _clear_tool_rules_from_system(self):
        """Clear tool rules from system prompt."""
        try:
            if self._verbose:
                self._vprint(f"[DASEIN][SYSTEM_PROMPT] Clearing tool rules from system prompt")
            
            # Clear the stored tool rules
            if hasattr(self, '_tool_rules_for_system'):
                self._tool_rules_for_system = []
                if self._verbose:
                    self._vprint(f"[DASEIN][SYSTEM_PROMPT] Cleared tool rules from system prompt")
            else:
                if self._verbose:
                    self._vprint(f"[DASEIN][SYSTEM_PROMPT] No tool rules to clear")
                    
        except Exception as e:
            self._vprint(f"[DASEIN][SYSTEM_PROMPT] Failed to clear tool rules from system prompt: {e}")
            import traceback
            traceback.print_exc()
    
    def _wrap_agent_tools(self):
        """Wrap agent tools with Dasein tool wrapper for micro-turn injection."""
        try:
            from .capture import DaseinToolWrapper
            
            agent_class_name = self._agent.__class__.__name__
            
            # Handle LangGraph agents differently - they have tools compiled into the graph
            if ('Compiled' in agent_class_name and 'Graph' in agent_class_name) or 'langgraph' in agent_class_name.lower():
                self._vprint(f"[DASEIN][WRAP] LangGraph agent detected: {agent_class_name}")
                self._wrap_langgraph_tools()
                return
            
            # Store original tools if not already stored
            if not hasattr(self._agent, '_original_tools'):
                self._agent._original_tools = {}
            
            # Wrap tools in the agent
            if hasattr(self._agent, 'tools'):
                for tool in self._agent.tools:
                    if tool.name not in self._agent._original_tools:
                        # Store original tool
                        self._agent._original_tools[tool.name] = tool
                        # Replace with wrapped tool
                        wrapped_tool = DaseinToolWrapper(tool, self._callback_handler)
                        # Find and replace the tool in the tools list
                        for i, t in enumerate(self._agent.tools):
                            if t.name == tool.name:
                                self._agent.tools[i] = wrapped_tool
                                break
                        self._vprint(f"[DASEIN][WRAP] Wrapped tool: {tool.name}")
                        self._vprint(f"[DASEIN][WRAP] Tool type: {type(tool)}")
                        self._vprint(f"[DASEIN][WRAP] Wrapped tool type: {type(wrapped_tool)}")
            
            # Also wrap tools in the agent's toolkit if it exists
            if hasattr(self._agent, 'toolkit') and hasattr(self._agent.toolkit, 'tools'):
                for tool in self._agent.toolkit.tools:
                    if tool.name not in self._agent._original_tools:
                        # Store original tool
                        self._agent._original_tools[tool.name] = tool
                        # Replace with wrapped tool
                        wrapped_tool = DaseinToolWrapper(tool, self._callback_handler)
                        # Find and replace the tool in the toolkit tools list
                        for i, t in enumerate(self._agent.toolkit.tools):
                            if t.name == tool.name:
                                self._agent.toolkit.tools[i] = wrapped_tool
                                break
                        self._vprint(f"[DASEIN][WRAP] Wrapped toolkit tool: {tool.name}")
                        
        except Exception as e:
            self._vprint(f"[DASEIN][WRAP] Error wrapping agent tools: {e}")
    
    def _wrap_langgraph_tools(self):
        """Wrap tools in LangGraph agents by accessing the compiled graph structure."""
        try:
            from .capture import DaseinToolWrapper
            
            # Access the tools node in the LangGraph agent
            tools_node = self._agent.nodes.get('tools')
            if not tools_node:
                print("[DASEIN][WRAP] No tools node found in LangGraph agent")
                return
            
            # Access the ToolNode in the graph steps
            tool_node = None
            if hasattr(tools_node, 'node') and hasattr(tools_node.node, 'steps'):
                for step in tools_node.node.steps:
                    if hasattr(step, 'tools_by_name'):  # This is the ToolNode
                        tool_node = step
                        break
            
            if not tool_node:
                print("[DASEIN][WRAP] No ToolNode found in LangGraph agent steps")
                return
            
            # Store original tools for restoration
            if not hasattr(self._agent, '_original_langgraph_tools'):
                self._agent._original_langgraph_tools = {}
            
            # Wrap each tool in the ToolNode
            wrapped_count = 0
            for tool_name, tool in tool_node.tools_by_name.items():
                if tool_name not in self._agent._original_langgraph_tools:
                    # Store original tool
                    self._agent._original_langgraph_tools[tool_name] = tool
                    
                    # Create wrapped tool
                    wrapped_tool = DaseinToolWrapper(tool, self._callback_handler)
                    
                    # Replace in the ToolNode
                    tool_node.tools_by_name[tool_name] = wrapped_tool
                    wrapped_count += 1
                    
                    self._vprint(f"[DASEIN][WRAP] Wrapped LangGraph tool: {tool_name}")
            
            self._vprint(f"[DASEIN][WRAP] Successfully wrapped {wrapped_count} tools in LangGraph agent")
            
        except Exception as e:
            self._vprint(f"[DASEIN][WRAP] Error wrapping LangGraph tools: {e}")
            import traceback
            traceback.print_exc()
    
    def _restore_agent_tools(self):
        """Restore original agent tools."""
        try:
            # Restore LangGraph tools
            if hasattr(self._agent, '_original_langgraph_tools'):
                # Access the tools node in the LangGraph agent
                tools_node = self._agent.nodes.get('tools')
                if tools_node and hasattr(tools_node, 'node') and hasattr(tools_node.node, 'steps'):
                    for step in tools_node.node.steps:
                        if hasattr(step, 'tools_by_name'):  # This is the ToolNode
                            # Restore original tools
                            for tool_name, original_tool in self._agent._original_langgraph_tools.items():
                                step.tools_by_name[tool_name] = original_tool
                                self._vprint(f"[DASEIN][RESTORE] Restored LangGraph tool: {tool_name}")
                            break
                
                # Clear the stored original tools
                delattr(self._agent, '_original_langgraph_tools')
                self._vprint(f"[DASEIN][RESTORE] Restored original LangGraph tools")
            
            # Restore standard LangChain tools
            if hasattr(self._agent, '_original_tools'):
                # Restore tools in the agent
                if hasattr(self._agent, 'tools'):
                    for i, tool in enumerate(self._agent.tools):
                        if hasattr(tool, 'original_tool'):
                            self._agent.tools[i] = tool.original_tool
                
                # Restore tools in the agent's toolkit
                if hasattr(self._agent, 'toolkit') and hasattr(self._agent.toolkit, 'tools'):
                    for i, tool in enumerate(self._agent.toolkit.tools):
                        if hasattr(tool, 'original_tool'):
                            self._agent.toolkit.tools[i] = tool.original_tool
                
                self._vprint(f"[DASEIN][RESTORE] Restored original LangChain tools")
                
        except Exception as e:
            self._vprint(f"[DASEIN][RESTORE] Error restoring agent tools: {e}")
    
    def run(self, *args, **kwargs):
        """
        Run the agent with complete Dasein pipeline.
        """
        query = args[0] if args else ""
        
        # Pre-run phase: Rule recall and selection
        selected_rules = self._pre_run_phase(query)
        
        # Set selected rules in callback handler for injection
        self._callback_handler.set_selected_rules(selected_rules)
        
        # Use micro-turn injection at tool start (the proper approach)
        # Wrap agent tools to apply micro-turn modifications
        self._wrap_agent_tools()
        
        # Add our callback - LangGraph needs it in config, LangChain in callbacks
        if self._is_langgraph:
            config = kwargs.get('config', {})
            config_callbacks = config.get('callbacks', [])
            if not isinstance(config_callbacks, list):
                config_callbacks = [config_callbacks] if config_callbacks else []
            config_callbacks.append(self._callback_handler)
            config['callbacks'] = config_callbacks
            kwargs['config'] = config
            self._vprint(f"[DASEIN][CALLBACK] Attached callback to LangGraph config with {len(config_callbacks)} callbacks")
        else:
            callbacks = kwargs.get('callbacks', [])
            if not isinstance(callbacks, list):
                callbacks = [callbacks] if callbacks else []
            callbacks.append(self._callback_handler)
            kwargs['callbacks'] = callbacks
            self._vprint(f"[DASEIN][CALLBACK] Attached callback handler to agent with {len(callbacks)} callbacks")
        
        # Run the agent
        result = self._agent.invoke(*args, **kwargs)
        
        # Post-run phase: Rule synthesis and learning
        self._post_run_phase(query, result, selected_rules)
        
        # Restore original agent tools
        self._restore_agent_tools()
        
        # Clear tool rules from system prompt
        self._clear_tool_rules_from_system()
        
        return result
    
    def _create_synthetic_tool_messages(self, selected_rules):
        """
        Convert selected rules into synthetic ToolMessage objects.
        
        Each rule becomes a tool call/response pair from Dasein, making rules
        appear as data already retrieved from the environment rather than instructions.
        
        Args:
            selected_rules: List of rule objects or (rule, metadata) tuples
            
        Returns:
            List of ToolMessage objects
        """
        try:
            from langchain_core.messages import ToolMessage
            import uuid
            
            tool_messages = []
            
            for i, rule_meta in enumerate(selected_rules):
                # Unwrap tuple format if present
                if isinstance(rule_meta, tuple) and len(rule_meta) == 2:
                    rule, metadata = rule_meta
                else:
                    rule = rule_meta
                    metadata = {}
                
                # Extract rule ID and advice text
                if isinstance(rule, dict):
                    rule_id = rule.get('id', rule.get('rule_id', f'rule_{i}'))
                    advice_text = rule.get('advice_text', rule.get('advice', ''))
                else:
                    rule_id = getattr(rule, 'id', getattr(rule, 'rule_id', f'rule_{i}'))
                    advice_text = getattr(rule, 'advice_text', getattr(rule, 'advice', ''))
                
                # Skip if no advice text
                if not advice_text:
                    continue
                
                # Create ToolMessage with rule content
                # Note: tool_call_id is required for ToolMessage
                tool_msg = ToolMessage(
                    content=advice_text,  # Rule advice as tool output
                    tool_call_id=f"dasein_{rule_id}",
                    name="Dasein"
                )
                
                tool_messages.append(tool_msg)
            
            if tool_messages:
                self._vprint(f"[DASEIN][TOOL_MSG] Created {len(tool_messages)} synthetic tool messages from rules")
            
            return tool_messages
            
        except Exception as e:
            print(f"[DASEIN][TOOL_MSG] ERROR creating synthetic tool messages: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _inject_tool_messages_into_input(self, args, tool_messages):
        """
        Inject synthetic tool messages into agent input at step -1.
        
        Handles both LangChain (dict with 'input' field) and LangGraph
        (dict with 'messages' field) input formats.
        
        Args:
            args: Original args tuple passed to agent.invoke()
            tool_messages: List of ToolMessage objects to inject
            
        Returns:
            Modified args tuple with tool messages injected
        """
        if not tool_messages or not args:
            return args
        
        try:
            original_input = args[0]
            
            # LangGraph format: {"messages": [...]}
            if isinstance(original_input, dict) and "messages" in original_input:
                self._vprint(f"[DASEIN][TOOL_MSG] Detected LangGraph input format")
                modified_input = original_input.copy()
                existing_messages = modified_input.get("messages", [])
                
                # Prepend tool messages BEFORE user message
                modified_input["messages"] = tool_messages + list(existing_messages)
                
                self._vprint(f"[DASEIN][TOOL_MSG] Injected {len(tool_messages)} tool messages before {len(existing_messages)} existing messages")
                
                # Return modified args
                modified_args = list(args)
                modified_args[0] = modified_input
                return tuple(modified_args)
            
            # LangChain format: {"input": "query"} or just "query"
            else:
                self._vprint(f"[DASEIN][TOOL_MSG] Detected LangChain input format")
                
                # For LangChain, we need to convert to message format
                # LangChain expects {"input": str}, so we wrap in messages format
                from langchain_core.messages import HumanMessage
                
                if isinstance(original_input, dict) and "input" in original_input:
                    # Dict with input field
                    user_message = HumanMessage(content=original_input["input"])
                elif isinstance(original_input, str):
                    # String input
                    user_message = HumanMessage(content=original_input)
                else:
                    # Unknown format, skip injection
                    self._vprint(f"[DASEIN][TOOL_MSG] Unknown input format, skipping injection")
                    return args
                
                # Create new input with messages
                # CRITICAL: For LangChain SQL agents, we need to preserve the {"input": ...} format
                # but some agents can handle {"messages": [...]} format
                # Let's try both approaches based on agent type
                
                if self._is_langgraph:
                    # LangGraph always uses messages format
                    modified_input = {
                        "messages": tool_messages + [user_message]
                    }
                else:
                    # LangChain: Keep original format but add messages field
                    # Some agents support both input and messages
                    if isinstance(original_input, dict):
                        modified_input = original_input.copy()
                        modified_input["messages"] = tool_messages + [user_message]
                    else:
                        # String input: convert to messages format
                        modified_input = {
                            "input": original_input,
                            "messages": tool_messages + [user_message]
                        }
                
                self._vprint(f"[DASEIN][TOOL_MSG] Injected {len(tool_messages)} tool messages into LangChain input")
                
                # Return modified args
                modified_args = list(args)
                modified_args[0] = modified_input
                return tuple(modified_args)
                
        except Exception as e:
            print(f"[DASEIN][TOOL_MSG] ERROR injecting tool messages: {e}")
            import traceback
            traceback.print_exc()
            return args
    
    def invoke(self, *args, **kwargs):
        """
        Invoke the agent with complete Dasein pipeline.
        """
        query = args[0] if args else ""
        
        if self._sequential_mode:
            return self._invoke_sequential(*args, **kwargs)
        elif self._retry > 1 and self._performance_tracking:
            return self._invoke_with_retry_and_tracking(*args, **kwargs)
        elif self._retry > 1:
            return self._invoke_with_retry(*args, **kwargs)
        else:
            return self._invoke_single(*args, **kwargs)
    
    async def ainvoke(self, *args, **kwargs):
        """
        Async invoke the agent with complete Dasein pipeline.
        """
        query = self._extract_query_from_input(args[0]) if args else ""
        
        if self._sequential_mode:
            return await self._ainvoke_sequential(*args, **kwargs)
        elif self._retry > 1 and self._performance_tracking:
            return await self._ainvoke_with_retry_and_tracking(*args, **kwargs)
        elif self._retry > 1:
            return await self._ainvoke_with_retry(*args, **kwargs)
        else:
            return await self._ainvoke_single(*args, **kwargs)
    
    def _invoke_single(self, *args, **kwargs):
        """Single invocation with Dasein pipeline."""
        # Extract the actual query string from agent input using unified method
        query = self._extract_query_from_input(args[0]) if args else ""
        
        if self._naive:
            # Naive mode: Skip rule gathering and synthesis, just run the agent
            self._vprint(f"[DASEIN][NAIVE] Running in naive mode - no rule gathering or synthesis")
            result = self._agent.invoke(*args, **kwargs)
            return result
        
        # Reset callback handler state for fresh run
        if hasattr(self, '_callback_handler') and hasattr(self._callback_handler, 'reset_run_state'):
            self._callback_handler.reset_run_state()
        
        # Pre-run phase: Rule recall and selection
        selected_rules = self._pre_run_phase(query)
        
        # Set selected rules in callback handler for injection
        self._callback_handler.set_selected_rules(selected_rules)
        
        # Use micro-turn injection at tool start (the proper approach)
        # Wrap agent tools to apply micro-turn modifications
        self._wrap_agent_tools()
        
        # Add our callback - LangGraph needs it in config, LangChain in callbacks
        if self._is_langgraph:
            config = kwargs.get('config', {})
            config_callbacks = config.get('callbacks', [])
            if not isinstance(config_callbacks, list):
                config_callbacks = [config_callbacks] if config_callbacks else []
            config_callbacks.append(self._callback_handler)
            config['callbacks'] = config_callbacks
            kwargs['config'] = config
            self._vprint(f"[DASEIN][CALLBACK] Attached callback to LangGraph config with {len(config_callbacks)} callbacks")
        else:
            callbacks = kwargs.get('callbacks', [])
            if not isinstance(callbacks, list):
                callbacks = [callbacks] if callbacks else []
            callbacks.append(self._callback_handler)
            kwargs['callbacks'] = callbacks
            self._vprint(f"[DASEIN][CALLBACK] Attached callback handler to agent with {len(callbacks)} callbacks")
        
        # STEP -1: Inject synthetic tool messages BEFORE agent execution
        # Convert rules to tool messages so they appear as data already retrieved
        tool_messages = self._create_synthetic_tool_messages(selected_rules)
        if tool_messages:
            args = self._inject_tool_messages_into_input(args, tool_messages)
            print(f"[DASEIN] 💬 Injected {len(tool_messages)} rule(s) as synthetic tool messages (step -1)")
        
        # Run the agent
        result = self._agent.invoke(*args, **kwargs)
        
        # Print tools summary if available
        if hasattr(self._callback_handler, 'get_compiled_tools_summary'):
            summary = self._callback_handler.get_compiled_tools_summary()
            if summary:
                print(f"[DASEIN] {summary}")
        
        #  FIXED: Extract trace for display but never calculate KPIs locally
        # Service-first architecture: All KPI calculation done by distributed services
        self._vprint(f"[DASEIN][SERVICE_FIRST] Extracting trace for display - KPIs handled by post-run API service")
        
        # Extract trace data for display (but no KPI calculation)
        self._extract_trace_for_display(result, args[0] if args else None)
        
        # NOW capture trace from callback handler AFTER extraction
        if hasattr(self, '_callback_handler') and hasattr(self._callback_handler, 'get_trace'):
            self._last_run_trace = self._callback_handler.get_trace()
        else:
            self._last_run_trace = []
        self._vprint(f"[DASEIN][TRACE_CAPTURE] Captured {len(self._last_run_trace)} steps for display")
        
        # Post-run phase: Get KPIs synchronously (rule synthesis happens async on server)
        # Note: Must do this BEFORE cleanup to preserve trace data
        # Server returns KPIs immediately while handling rule synthesis in background
        self._post_run_phase(query, result, selected_rules)
        
        # Restore original agent tools after post-run
        self._restore_agent_tools()
        
        # Clear tool rules from system prompt after post-run
        self._clear_tool_rules_from_system()
        
        # Cleanup run-scoped corpus (print telemetry and free memory)
        if hasattr(self, '_callback_handler') and hasattr(self._callback_handler, 'run_id'):
            from .pipecleaner import cleanup_corpus
            cleanup_corpus(self._callback_handler.run_id)
        
        return result
    
    async def _ainvoke_single(self, *args, **kwargs):
        """Async single invocation with Dasein pipeline."""
        query = self._extract_query_from_input(args[0]) if args else ""
        
        if self._naive:
            # Naive mode: Skip rule gathering and synthesis, just run the agent
            self._vprint(f"[DASEIN][NAIVE] Running in naive mode - no rule gathering or synthesis")
            result = await self._agent.ainvoke(*args, **kwargs)
            return result
        
        # Reset callback handler state for fresh run
        if hasattr(self, '_callback_handler') and hasattr(self._callback_handler, 'reset_run_state'):
            self._callback_handler.reset_run_state()
        
        # Pre-run phase: Rule recall and selection
        selected_rules = self._pre_run_phase(query)
        
        # Set selected rules in callback handler for injection
        self._callback_handler.set_selected_rules(selected_rules)
        
        # Use micro-turn injection at tool start (the proper approach)
        # Wrap agent tools to apply micro-turn modifications
        self._wrap_agent_tools()
        
        # Add our callback - LangGraph needs it in config, LangChain in callbacks
        if self._is_langgraph:
            config = kwargs.get('config', {})
            config_callbacks = config.get('callbacks', [])
            if not isinstance(config_callbacks, list):
                config_callbacks = [config_callbacks] if config_callbacks else []
            config_callbacks.append(self._callback_handler)
            config['callbacks'] = config_callbacks
            kwargs['config'] = config
            self._vprint(f"[DASEIN][CALLBACK] Attached callback to LangGraph config with {len(config_callbacks)} callbacks")
        else:
            callbacks = kwargs.get('callbacks', [])
            if not isinstance(callbacks, list):
                callbacks = [callbacks] if callbacks else []
            callbacks.append(self._callback_handler)
            kwargs['callbacks'] = callbacks
            self._vprint(f"[DASEIN][CALLBACK] Attached callback handler to agent with {len(callbacks)} callbacks")
        
        # STEP -1: Inject synthetic tool messages BEFORE agent execution
        # Convert rules to tool messages so they appear as data already retrieved
        tool_messages = self._create_synthetic_tool_messages(selected_rules)
        if tool_messages:
            args = self._inject_tool_messages_into_input(args, tool_messages)
            print(f"[DASEIN] 💬 Injected {len(tool_messages)} rule(s) as synthetic tool messages (step -1)")
        
        # Run the agent asynchronously
        result = await self._agent.ainvoke(*args, **kwargs)
        
        # Print tools summary if available
        if hasattr(self._callback_handler, 'get_compiled_tools_summary'):
            summary = self._callback_handler.get_compiled_tools_summary()
            if summary:
                print(f"[DASEIN] {summary}")
        
        #  FIXED: Extract trace for display but never calculate KPIs locally
        # Service-first architecture: All KPI calculation done by distributed services
        self._vprint(f"[DASEIN][SERVICE_FIRST] Extracting trace for display - KPIs handled by post-run API service")
        
        # Extract trace data for display (but no KPI calculation)
        self._extract_trace_for_display(result, args[0] if args else None)
        
        # NOW capture trace from callback handler AFTER extraction
        if hasattr(self, '_callback_handler') and hasattr(self._callback_handler, 'get_trace'):
            self._last_run_trace = self._callback_handler.get_trace()
        else:
            self._last_run_trace = []
        self._vprint(f"[DASEIN][TRACE_CAPTURE] Captured {len(self._last_run_trace)} steps for display")
        
        # Post-run phase: Get KPIs synchronously (rule synthesis happens async on server)
        # Note: Must do this BEFORE cleanup to preserve trace data
        # Server returns KPIs immediately while handling rule synthesis in background
        self._post_run_phase(query, result, selected_rules)
        
        # Restore original agent tools after post-run
        self._restore_agent_tools()
        
        # Clear tool rules from system prompt after post-run
        self._clear_tool_rules_from_system()
        
        # Cleanup run-scoped corpus (print telemetry and free memory)
        if hasattr(self, '_callback_handler') and hasattr(self._callback_handler, 'run_id'):
            from .pipecleaner import cleanup_corpus
            cleanup_corpus(self._callback_handler.run_id)
        
        return result
    
    def _invoke_with_retry(self, *args, **kwargs):
        """Multiple invocations without performance tracking."""
        results = []
        for i in range(self._retry):
            print(f"\n=== RUN-{i+1} ===")
            result = self._invoke_single(*args, **kwargs)
            results.append(result)
            
            # Print trace if verbose is enabled
            if self._verbose:
                print(f"\n TRACE FOR RUN-{i+1}:")
                print("-" * 30)
                from .capture import print_trace
                print_trace()
                print("-" * 30)
        return results[-1]  # Return the last result
    
    async def _ainvoke_with_retry(self, *args, **kwargs):
        """Async multiple invocations without performance tracking."""
        results = []
        for i in range(self._retry):
            print(f"\n=== RUN-{i+1} ===")
            result = await self._ainvoke_single(*args, **kwargs)
            results.append(result)
            
            # Print trace if verbose is enabled
            if self._verbose:
                print(f"\n TRACE FOR RUN-{i+1}:")
                print("-" * 30)
                from .capture import print_trace
                print_trace()
                print("-" * 30)
        return results[-1]  # Return the last result
    
    def _invoke_with_retry_and_tracking(self, *args, **kwargs):
        """Multiple invocations with detailed performance tracking."""
        query = args[0] if args else ""
        results = []
        metrics = []
        
        print(f"\n Dasein POC - Performance Tracking Mode")
        print("=" * 50)
        
        for i in range(self._retry):
            print(f"\n=== RUN-{i+1} {'(Baseline)' if i == 0 else '(With Rules)'} ===")
            print(f"Query: {query}")
            print("-" * 50)
            
            # Reset callback handler state before each run (except the first one)
            # Note: reset_run_state() already clears trace, function calls, guards, and timers
            if i > 0:
                if hasattr(self, '_callback_handler') and hasattr(self._callback_handler, 'reset_run_state'):
                    self._callback_handler.reset_run_state()
                
                # CRITICAL: Reset agent state to prevent result contamination between runs
                # LangChain agents may accumulate memory/message history
                if hasattr(self._agent, 'memory') and self._agent.memory:
                    self._agent.memory.clear()
                    print(f"[DASEIN] Cleared agent memory for RUN-{i+1}")
            
            # Capture metrics for this run (first run is baseline)
            run_metrics = self._capture_run_metrics(*args, is_baseline=(i == 0), step_number=(i+1), total_steps=self._retry, **kwargs)
            results.append(run_metrics['result'])
            metrics.append(run_metrics)
            
            # Print metrics for this run
            self._print_run_metrics(run_metrics, f"RUN-{i+1}")
            
            # Print trace if verbose or performance tracking is enabled
            if self._verbose or self._performance_tracking:
                print(f"\n TRACE FOR RUN-{i+1}:")
                print("-" * 30)
                # Get trace from THIS instance's callback handler, not from global
                trace = self._callback_handler.get_trace() if self._callback_handler else []
                from .capture import print_trace
                print_trace(trace=trace)
                print("-" * 30)
        
        # Print improvement analysis if we have multiple runs
        if len(metrics) > 1:
            self._print_improvement_analysis(metrics)
        
        return results[-1]  # Return the last result
    
    async def _ainvoke_with_retry_and_tracking(self, *args, **kwargs):
        """Async multiple invocations with detailed performance tracking."""
        query = self._extract_query_from_input(args[0]) if args else ""
        results = []
        metrics = []
        
        print(f"\n Dasein POC - Performance Tracking Mode")
        print("=" * 50)
        
        for i in range(self._retry):
            print(f"\n=== RUN-{i+1} {'(Baseline)' if i == 0 else '(With Rules)'} ===")
            print(f"Query: {query}")
            print("-" * 50)
            
            # Reset callback handler state before each run (except the first one)
            # Note: reset_run_state() already clears trace, function calls, guards, and timers
            if i > 0:
                if hasattr(self, '_callback_handler') and hasattr(self._callback_handler, 'reset_run_state'):
                    self._callback_handler.reset_run_state()
                
                # CRITICAL: Reset agent state to prevent result contamination between runs
                # LangChain agents may accumulate memory/message history
                if hasattr(self._agent, 'memory') and self._agent.memory:
                    self._agent.memory.clear()
                    print(f"[DASEIN] Cleared agent memory for RUN-{i+1}")
            
            # Capture metrics for this run (first run is baseline)
            run_metrics = await self._acapture_run_metrics(*args, is_baseline=(i == 0), step_number=(i+1), total_steps=self._retry, **kwargs)
            results.append(run_metrics['result'])
            metrics.append(run_metrics)
            
            # Print metrics for this run
            self._print_run_metrics(run_metrics, f"RUN-{i+1}")
            
            # Print trace if verbose or performance tracking is enabled
            if self._verbose or self._performance_tracking:
                print(f"\n TRACE FOR RUN-{i+1}:")
                print("-" * 30)
                # Get trace from THIS instance's callback handler, not from global
                trace = self._callback_handler.get_trace() if self._callback_handler else []
                from .capture import print_trace
                print_trace(trace=trace)
                print("-" * 30)
        
        # Print improvement analysis if we have multiple runs
        if len(metrics) > 1:
            self._print_improvement_analysis(metrics)
        
        return results[-1]  # Return the last result
    
    def _capture_run_metrics(self, *args, is_baseline=False, step_number=None, total_steps=None, **kwargs):
        """Capture detailed metrics for a single run."""
        # Extract the actual query string from agent input using unified method
        query = self._extract_query_from_input(args[0]) if args else ""
        
        # Generate step ID for tracking
        if step_number is not None:
            phase = "baseline" if is_baseline else "learning"
            self._current_step_id = self._generate_step_id(step_number, phase)
            print(f"[DASEIN] Step ID: {self._current_step_id}")
        
        # Pre-run phase: Rule recall and selection
        selected_rules = self._pre_run_phase(query, is_baseline=is_baseline)
        
        # Set selected rules in callback handler for injection
        self._callback_handler.set_selected_rules(selected_rules)
        
        # [TEST RULE] Inject test rule to verify pipecleaner FAISS integration
        # COMMENTED OUT - Use real rules from rule synthesis instead
        # if True:  # Set to False to disable test rule
        #     from types import SimpleNamespace
        #     test_rule = SimpleNamespace(
        #         id="test_faiss_rule_sync",
        #         target_step_type="llm_start",
        #         advice_text="FILTER SEARCH: Apply deduplication to search results using FAISS-accelerated similarity computation",
        #         references=SimpleNamespace(
        #             tools=["tavily_search", "Summary", "summary"]  # tavily_search because Summary is called from within it
        #         )
        #     )
        #     print(f"[TEST RULE SYNC] Injecting test rule AFTER pre-run (should trigger pipecleaner)")
        #     selected_rules.append(test_rule)
        #     self._callback_handler.set_selected_rules(selected_rules)
        #     print(f"[TEST RULE SYNC] Test rule injected, total rules: {len(selected_rules)}")
        
        # Use micro-turn injection at tool start (the proper approach)
        # Wrap agent tools to apply micro-turn modifications
        self._wrap_agent_tools()
        
        # Add our callback - LangGraph needs it in config, LangChain in callbacks
        if self._is_langgraph:
            config = kwargs.get('config', {})
            config_callbacks = config.get('callbacks', [])
            if not isinstance(config_callbacks, list):
                config_callbacks = [config_callbacks] if config_callbacks else []
            config_callbacks.append(self._callback_handler)
            config['callbacks'] = config_callbacks
            kwargs['config'] = config
            self._vprint(f"[DASEIN][CALLBACK] Attached callback to LangGraph config with {len(config_callbacks)} callbacks")
        else:
            callbacks = kwargs.get('callbacks', [])
            if not isinstance(callbacks, list):
                callbacks = [callbacks] if callbacks else []
            callbacks.append(self._callback_handler)
            kwargs['callbacks'] = callbacks
            self._vprint(f"[DASEIN][CALLBACK] Attached callback handler to agent with {len(callbacks)} callbacks")
        
        # STEP -1: Inject synthetic tool messages BEFORE agent execution
        # Convert rules to tool messages so they appear as data already retrieved
        tool_messages = self._create_synthetic_tool_messages(selected_rules)
        if tool_messages:
            args = self._inject_tool_messages_into_input(args, tool_messages)
            print(f"[DASEIN] 💬 Injected {len(tool_messages)} rule(s) as synthetic tool messages (step -1)")
        
        # Run the agent
        result = self._agent.invoke(*args, **kwargs)
        print(f"[DASEIN][DEBUG] Agent returned result for step {self._current_step_id}: {str(result.get('input', 'NO_INPUT'))[:80] if isinstance(result, dict) else 'NOT_A_DICT'}")
        
        # Post-run phase: Rule synthesis and learning
        post_run_kpis = self._post_run_phase(query, result, selected_rules, step_number=step_number, is_baseline=is_baseline, total_steps=total_steps or self._retry)
        
        # Use KPIs from post-run service - no fallbacks
        if not post_run_kpis:
            raise RuntimeError(f"Post-run service failed to return KPIs for step {self._current_step_id}")
        
        metrics = post_run_kpis.copy()
        metrics['result'] = result
        metrics['step_id'] = self._current_step_id
        print(f"[DASEIN][DEBUG] Stored result in metrics for step {self._current_step_id}: {str(metrics['result'].get('input', 'NO_INPUT'))[:80] if isinstance(metrics['result'], dict) else 'NOT_A_DICT'}")
        print(f"[DASEIN] Using KPIs from post-run service for step {self._current_step_id}")
        
        return metrics
    
    async def _acapture_run_metrics(self, *args, is_baseline=False, step_number=None, total_steps=None, **kwargs):
        """Async capture detailed metrics for a single run."""
        # Extract the actual query string from agent input using unified method
        query = self._extract_query_from_input(args[0]) if args else ""
        
        # Generate step ID for tracking
        if step_number is not None:
            phase = "baseline" if is_baseline else "learning"
            self._current_step_id = self._generate_step_id(step_number, phase)
            print(f"[DASEIN] Step ID: {self._current_step_id}")
        
        # Pre-run phase: Rule recall and selection
        selected_rules = self._pre_run_phase(query, is_baseline=is_baseline)
        
        # Set selected rules in callback handler for injection
        self._callback_handler.set_selected_rules(selected_rules)
        
        # [TEST RULE] Inject test rule to verify pipecleaner FAISS integration
        # COMMENTED OUT - Use real rules from rule synthesis instead
        # if True:  # Set to False to disable test rule
        #     from types import SimpleNamespace
        #     test_rule = SimpleNamespace(
        #         id="test_faiss_rule_async",
        #         target_step_type="llm_start",
        #         advice_text="FILTER SEARCH: Apply deduplication to search results using FAISS-accelerated similarity computation",
        #         references=SimpleNamespace(
        #             tools=["Summary", "summary"]  # Only Summary, not tavily_search
        #         )
        #     )
        #     print(f"[TEST RULE ASYNC] Injecting test rule AFTER pre-run (should trigger pipecleaner)")
        #     selected_rules.append(test_rule)
        #     self._callback_handler.set_selected_rules(selected_rules)
        #     print(f"[TEST RULE ASYNC] Test rule injected, total rules: {len(selected_rules)}")
        
        # Use micro-turn injection at tool start (the proper approach)
        # Wrap agent tools to apply micro-turn modifications
        self._wrap_agent_tools()
        
        # Add our callback - LangGraph needs it in config, LangChain in callbacks
        if self._is_langgraph:
            config = kwargs.get('config', {})
            config_callbacks = config.get('callbacks', [])
            if not isinstance(config_callbacks, list):
                config_callbacks = [config_callbacks] if config_callbacks else []
            config_callbacks.append(self._callback_handler)
            config['callbacks'] = config_callbacks
            kwargs['config'] = config
            self._vprint(f"[DASEIN][CALLBACK] Attached callback to LangGraph config with {len(config_callbacks)} callbacks")
        else:
            callbacks = kwargs.get('callbacks', [])
            if not isinstance(callbacks, list):
                callbacks = [callbacks] if callbacks else []
            callbacks.append(self._callback_handler)
            kwargs['callbacks'] = callbacks
            self._vprint(f"[DASEIN][CALLBACK] Attached callback handler to agent with {len(callbacks)} callbacks")
        
        # STEP -1: Inject synthetic tool messages BEFORE agent execution
        # Convert rules to tool messages so they appear as data already retrieved
        tool_messages = self._create_synthetic_tool_messages(selected_rules)
        if tool_messages:
            args = self._inject_tool_messages_into_input(args, tool_messages)
            print(f"[DASEIN] 💬 Injected {len(tool_messages)} rule(s) as synthetic tool messages (step -1)")
        
        # Run the agent asynchronously
        result = await self._agent.ainvoke(*args, **kwargs)
        print(f"[DASEIN][DEBUG] Agent returned result for step {self._current_step_id}: {str(result.get('input', 'NO_INPUT'))[:80] if isinstance(result, dict) else 'NOT_A_DICT'}")
        
        #  FIXED: Performance tracking mode - extract trace for display but no KPI calculation
        # KPIs will come from post-run service below, not local calculation
        self._vprint(f"[DASEIN][PERF_MODE] Extracting trace for display - KPIs from post-run service")
        
        # Extract trace data for display (but no KPI calculation)
        self._extract_trace_for_display(result, query)
        
        # Capture trace from callback handler for display only
        if hasattr(self, '_callback_handler') and hasattr(self._callback_handler, 'get_trace'):
            self._last_run_trace = self._callback_handler.get_trace()
        else:
            self._last_run_trace = []
        self._vprint(f"[DASEIN][TRACE_CAPTURE] Captured {len(self._last_run_trace)} steps for display")
        
        # Post-run phase: Rule synthesis and learning
        post_run_kpis = self._post_run_phase(query, result, selected_rules, step_number=step_number, is_baseline=is_baseline, total_steps=total_steps or self._retry)
        
        # Restore original agent tools after post-run phase
        self._restore_agent_tools()
        
        # Clear tool rules from system prompt after post-run phase
        self._clear_tool_rules_from_system()
        
        # Use KPIs from post-run service - no fallbacks
        if not post_run_kpis:
            raise RuntimeError(f"Post-run service failed to return KPIs for step {self._current_step_id}")
        
        metrics = post_run_kpis.copy()
        metrics['result'] = result
        metrics['step_id'] = self._current_step_id
        print(f"[DASEIN] Using KPIs from post-run service for step {self._current_step_id}")
        
        return metrics
    
    def _extract_trace_for_display(self, result=None, query=None):
        """Extract trace data for display purposes only. No KPI calculation."""
        print(f"[DEBUG] _extract_trace_for_display called - extracting trace for print_trace()")
        
        # Try to get trace from multiple sources
        trace = None
        
        # PRIORITY 1: Callback handler (has ALL intermediate steps)
        if hasattr(self, '_callback_handler'):
            trace = self._callback_handler.get_trace()
            if trace:
                print(f"[DEBUG] Got {len(trace)} steps from callback handler for display")
        
        # PRIORITY 2: Wrapped LLM
        if not trace and hasattr(self, '_wrapped_llm') and self._wrapped_llm:
            trace = self._wrapped_llm.get_trace()
            if trace:
                print(f"[DEBUG] Got {len(trace)} steps from wrapped LLM for display")
        
        # PRIORITY 3: LangGraph message extraction (fallback only - loses intermediate steps)
        if not trace:
            agent_class_name = self._agent.__class__.__name__
            is_langgraph = ('Compiled' in agent_class_name and 'Graph' in agent_class_name) or 'langgraph' in agent_class_name.lower()
            
            if is_langgraph and result and isinstance(result, dict) and 'messages' in result:
                print(f"[DEBUG] LangGraph agent - extracting trace from result for display (FALLBACK)")
                extracted_query = self._extract_query_from_input(query) if query else ""
                trace = self._extract_trace_from_langgraph_result(result, extracted_query)
                if trace:
                    print(f"[DEBUG] Extracted {len(trace)} steps from LangGraph result for display")
        
        # Note: Trace is already captured from callback handler in _invoke_single/_ainvoke_single
        # No need to store in global _TRACE (removed for thread-safety)
    
    def _extract_metrics_from_trace(self, result=None, query=None):
        """DEPRECATED: Extract trace data only. KPI calculation now handled by post-run API service."""
        print(f"[DEBUG] _extract_metrics_from_trace called with result: {result}")
        print(f"[DEBUG] Result type: {type(result)}")
        
        # Try to get trace from multiple sources
        trace = None
        
        # PRIORITY 1: Callback handler (has ALL intermediate steps)
        if hasattr(self, '_callback_handler'):
            trace = self._callback_handler.get_trace()
            if trace:
                print(f"[DEBUG] Got {len(trace)} steps from callback handler for KPIs")
        
        # PRIORITY 2: Wrapped LLM
        if not trace and hasattr(self, '_wrapped_llm') and self._wrapped_llm:
            trace = self._wrapped_llm.get_trace()
            if trace:
                print(f"[DEBUG] Got {len(trace)} steps from wrapped LLM for KPIs")
        
        # PRIORITY 3: LangGraph message extraction (fallback only - loses intermediate steps)
        if not trace:
            agent_class_name = self._agent.__class__.__name__
            is_langgraph = ('Compiled' in agent_class_name and 'Graph' in agent_class_name) or 'langgraph' in agent_class_name.lower()
            
            if is_langgraph and result and isinstance(result, dict) and 'messages' in result:
                print(f"[DEBUG] No callback trace - extracting from LangGraph result as fallback")
                extracted_query = self._extract_query_from_input(query) if query else ""
                trace = self._extract_trace_from_langgraph_result(result, extracted_query)
        
        # Note: Trace is already captured from callback handler in _invoke_single/_ainvoke_single
        # No need to store in global _TRACE (removed for thread-safety)
        
        if not trace:
            print(f"[DEBUG] No trace available for KPI extraction")
            return {
                'llm_calls': 0,
                'tool_calls': 0,
                'total_turns': 0,
                'input_tokens': 0,
                'output_tokens': 0,
                'total_tokens': 0,
                'trace_time_ms': 0,
                'wall_time_ms': 0,
                'success_rate': 0.0,
                'overall_success': False
            }
        
        # Calculate metrics from trace
        llm_calls = len([step for step in trace if step.get('step_type') == 'llm_start'])
        tool_calls = len([step for step in trace if step.get('step_type') == 'tool_start'])
        total_turns = len(trace)
        
        # Sum up tokens and calculate average time
        input_tokens = sum(step.get('tokens_input', 0) for step in trace)
        output_tokens = sum(step.get('tokens_output', 0) for step in trace)
        total_tokens = input_tokens + output_tokens
        
        # Calculate average duration_ms across all steps that have timing data
        durations = [step.get('duration_ms', 0) for step in trace if step.get('duration_ms', 0) > 0]
        trace_time_ms = int(sum(durations) / len(durations)) if durations else 0
        
        # Calculate wall time from timestamps (they are ISO format strings)
        if len(trace) > 1:
            try:
                from datetime import datetime
                start_ts = datetime.fromisoformat(trace[0].get('ts', '').replace('Z', '+00:00'))
                end_ts = datetime.fromisoformat(trace[-1].get('ts', '').replace('Z', '+00:00'))
                wall_time_ms = int((end_ts - start_ts).total_seconds() * 1000)
            except:
                wall_time_ms = trace_time_ms
        else:
            wall_time_ms = trace_time_ms
        
        # Calculate success rate - improved for LangGraph compatibility
        successful_calls = self._calculate_successful_calls(trace)
        success_rate = (successful_calls / total_turns * 100) if total_turns > 0 else 0.0
        
        # Use final outcome from post-run service if available, otherwise fallback to local calculation
        if hasattr(self, '_last_run_kpis') and self._last_run_kpis:
            final_outcome = self._last_run_kpis.get('final_outcome', 'unknown')
            overall_success = self._last_run_kpis.get('overall_success', False)
            print(f"[DEBUG] Using final_outcome from post-run service: {final_outcome}")
        else:
            print(f"[DEBUG] No post-run KPIs available, using local calculation")
            if hasattr(self, '_wrapped_llm') and self._wrapped_llm:
                print(f"[DEBUG] Using LLM-based success evaluation with wrapped LLM: {type(self._wrapped_llm)}")
                final_outcome = self._wrapped_llm._determine_final_outcome(result, query)
                overall_success = success_rate > 50.0 and final_outcome in ['completed', 'success']
            else:
                print(f"[DEBUG] No wrapped LLM available, using fallback")
                final_outcome = "unknown"  # Fallback if no wrapped LLM
                overall_success = False
        
        return {
            'llm_calls': llm_calls,
            'tool_calls': tool_calls,
            'total_turns': total_turns,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': total_tokens,
            'trace_time_ms': trace_time_ms,
            'wall_time_ms': wall_time_ms,
            'success_rate': success_rate,
            'overall_success': overall_success,
            'final_outcome': final_outcome
        }
    
    def _print_run_metrics(self, metrics, run_name):
        """Print metrics for a single run."""
        print(f"[DASEIN][DEBUG] _print_run_metrics called for {run_name}, step_id={metrics.get('step_id', 'NO_STEP_ID')}")
        print(f"[DASEIN][DEBUG] Result in metrics: {str(metrics['result'].get('input', 'NO_INPUT'))[:80] if isinstance(metrics.get('result'), dict) else 'NOT_A_DICT'}")
        print(f"\n {run_name} METRICS:")
        print(f"  LLM Calls: {metrics['llm_calls']}")
        print(f"  Tool Calls: {metrics['tool_calls']}")
        print(f"  Total Turns: {metrics['total_turns']}")
        print(f"  Input Tokens: {metrics['input_tokens']}")
        print(f"  Output Tokens: {metrics['output_tokens']}")
        print(f"  Total Tokens: {metrics['total_tokens']}")
        print(f"  Trace Time (ms): {metrics['trace_time_ms']}")
        print(f"  Wall Time (ms): {metrics['wall_time_ms']}")
        print(f"  Success Rate: {metrics['success_rate']:.1f}% ({metrics['total_turns']}/{metrics['total_turns']})")
        print(f"  Overall Success: {'✅' if metrics['overall_success'] else '❌'}")
        # Format final outcome
        final_outcome_formatted = self._format_final_outcome(metrics.get('final_outcome', 'unknown'))
        print(f"  Final Outcome: {final_outcome_formatted}")
        print(f"  Result: {str(metrics['result'])[:100]}...")
    
    def _print_improvement_analysis(self, metrics_list):
        """Print improvement analysis between runs."""
        print("\n" + "=" * 70)
        print(" IMPROVEMENT ANALYSIS")
        print("=" * 70)
        
        # Agent Information Section
        print("\n AGENT INFORMATION:")
        print("-" * 30)
        
        # Framework Detection (LangGraph vs LangChain)
        framework = "LangGraph" if self._is_langgraph else "LangChain"
        print(f"Framework: {framework}")
        
        # Sync vs Async Detection
        # Check if we have async methods in the call stack or if we're using async patterns
        import inspect
        is_async = False
        try:
            # Check if the current method was called from an async context
            current_frame = inspect.currentframe()
            while current_frame:
                code = current_frame.f_code
                if 'async' in code.co_name or 'ainvoke' in code.co_name or '_acapture' in code.co_name:
                    is_async = True
                    break
                current_frame = current_frame.f_back
        except:
            # Fallback: check if agent has async methods
            is_async = hasattr(self._agent, 'ainvoke') or hasattr(self._agent, 'astream')
        
        mode = "Async" if is_async else "Sync"
        print(f"Execution Mode: {mode}")
        
        # Agent Fingerprint (Pretty Print)
        print(f"Agent Fingerprint:")
        fingerprint = self._get_pretty_agent_fingerprint()
        for line in fingerprint.split('\n'):
            if line.strip():
                print(f"  {line}")
        
        print("\n📊 PERFORMANCE METRICS:")
        print("-" * 30)
        
        def calc_improvement(before, after, metric_name):
            if before == 0:
                return f"{metric_name}: {after} (no baseline)"
            change = before - after
            pct = (change / before * 100) if before > 0 else 0
            direction = "↓" if change > 0 else "↑" if change < 0 else "="
            return f"{metric_name}: {before} → {after} ({direction}{abs(change)}, {pct:+.1f}%)"
        
        # Compare first run with last run
        first_metrics = metrics_list[0]
        last_metrics = metrics_list[-1]
        
        print(calc_improvement(first_metrics['llm_calls'], last_metrics['llm_calls'], "LLM Calls"))
        print(calc_improvement(first_metrics['tool_calls'], last_metrics['tool_calls'], "Tool Calls"))
        print(calc_improvement(first_metrics['total_turns'], last_metrics['total_turns'], "Total Turns"))
        print(calc_improvement(first_metrics['input_tokens'], last_metrics['input_tokens'], "Input Tokens"))
        print(calc_improvement(first_metrics['output_tokens'], last_metrics['output_tokens'], "Output Tokens"))
        print(calc_improvement(first_metrics['total_tokens'], last_metrics['total_tokens'], "Total Tokens"))
        print(calc_improvement(first_metrics['trace_time_ms'], last_metrics['trace_time_ms'], "Trace Time (ms)"))
        print(calc_improvement(first_metrics['wall_time_ms'], last_metrics['wall_time_ms'], "Wall Time (ms)"))
        
        # Success Rate
        success_rate_change = last_metrics['success_rate'] - first_metrics['success_rate']
        print(f"Success Rate: {first_metrics['success_rate']:.1f}% → {last_metrics['success_rate']:.1f}% ({success_rate_change:+.1f}%)")
        
        success_improvement = "✅ → ✅" if first_metrics['overall_success'] and last_metrics['overall_success'] else \
                             "❌ → ✅" if not first_metrics['overall_success'] and last_metrics['overall_success'] else \
                             "✅ → ❌" if first_metrics['overall_success'] and not last_metrics['overall_success'] else "❌ → ❌"
        print(f"Success: {success_improvement}")
        
        # Final outcome comparison
        first_outcome = first_metrics.get('final_outcome', 'unknown')
        last_outcome = last_metrics.get('final_outcome', 'unknown')
        # Format final outcomes using the wrapped LLM's method
        first_formatted = self._format_final_outcome(first_outcome)
        last_formatted = self._format_final_outcome(last_outcome)
        outcome_improvement = f"{first_formatted} → {last_formatted}"
        print(f"🎯 Final Outcome: {outcome_improvement}")
        
        # Overall assessment
        print("\n🎯 OVERALL ASSESSMENT:")
        
        # Check for improvements
        turns_improved = last_metrics['total_turns'] < first_metrics['total_turns']
        tokens_improved = last_metrics['total_tokens'] < first_metrics['total_tokens']
        time_improved = last_metrics['trace_time_ms'] < first_metrics['trace_time_ms']
        success_improved = last_metrics['success_rate'] > first_metrics['success_rate']
        overall_success = last_metrics['overall_success']
        
        # Check final outcome improvement (most important metric)
        first_outcome = first_metrics.get('final_outcome', 'unknown')
        last_outcome = last_metrics.get('final_outcome', 'unknown')
        outcome_improved = (first_outcome == "gave_up" and last_outcome == "completed") or \
                          (first_outcome == "failed" and last_outcome == "completed")
        
        # Prioritize final outcome improvement
        if outcome_improved:
            first_formatted = self._format_final_outcome(first_outcome)
            last_formatted = self._format_final_outcome(last_outcome)
            print(f"🎉 BREAKTHROUGH: Agent went from {first_formatted} to {last_formatted}!")
        elif turns_improved or tokens_improved or time_improved or success_improved:
            improvements = []
            if turns_improved:
                delta = first_metrics['total_turns'] - last_metrics['total_turns']
                improvements.append(f"turns (↓{delta})")
            if tokens_improved:
                delta = first_metrics['total_tokens'] - last_metrics['total_tokens']
                improvements.append(f"tokens (↓{delta})")
            if time_improved:
                delta = first_metrics['trace_time_ms'] - last_metrics['trace_time_ms']
                improvements.append(f"time (↓{delta}ms)")
            if success_improved:
                delta = last_metrics['success_rate'] - first_metrics['success_rate']
                improvements.append(f"success rate (+{delta:.1f}%)")
            
            print(f"✅ SUCCESS: Dasein improved performance! Improvements: {', '.join(improvements)}")
        else:
            print("❌ NO IMPROVEMENT: Performance did not improve between runs")
        
        # Show final outcome status
        if last_outcome == "gave_up":
            print("⚠️  WARNING: Agent gave up - check rules and prompts")
        elif last_outcome == "failed":
            print("⚠️  WARNING: Agent failed - check configuration")
        elif last_outcome == "completed":
            print("✨ EXCELLENT: Agent completed the task successfully!")
        
        if not overall_success:
            print("⚠️  WARNING: Overall success rate is low - check agent configuration")
    
    def _get_pretty_agent_fingerprint(self):
        """Generate a pretty-printed agent fingerprint with detailed information."""
        try:
            lines = []
            
            # Basic agent information
            agent_class = self._agent.__class__
            lines.append(f"Class: {agent_class.__name__}")
            lines.append(f"Module: {agent_class.__module__}")
            
            # Framework-specific details
            if self._is_langgraph:
                lines.append("Type: LangGraph Compiled Graph")
                
                # LangGraph-specific details
                if self._langgraph_params:
                    model = self._langgraph_params.get('model')
                    if model:
                        lines.append(f"Model: {type(model).__name__}")
                        if hasattr(model, 'model'):
                            lines.append(f"Model ID: {getattr(model, 'model', 'unknown')}")
                        if hasattr(model, 'temperature'):
                            lines.append(f"Temperature: {getattr(model, 'temperature', 'unknown')}")
                    
                    tools = self._langgraph_params.get('tools', [])
                    lines.append(f"Tools: {len(tools)} tools")
                    if tools:
                        tool_names = [getattr(tool, 'name', str(tool)[:20]) for tool in tools[:3]]
                        if len(tools) > 3:
                            tool_names.append(f"... +{len(tools)-3} more")
                        lines.append(f"Tool Names: {', '.join(tool_names)}")
                
                # Graph structure info
                if hasattr(self._agent, 'nodes'):
                    nodes = list(self._agent.nodes.keys()) if self._agent.nodes else []
                    lines.append(f"Graph Nodes: {', '.join(nodes)}")
            else:
                lines.append("Type: LangChain Agent")
                
                # LangChain-specific details
                if hasattr(self._agent, 'llm'):
                    llm = self._agent.llm
                    lines.append(f"LLM: {type(llm).__name__}")
                    if hasattr(llm, 'model'):
                        lines.append(f"Model ID: {getattr(llm, 'model', 'unknown')}")
                
                if hasattr(self._agent, 'tools'):
                    tools = self._agent.tools
                    lines.append(f"Tools: {len(tools)} tools")
                    if tools:
                        tool_names = [getattr(tool, 'name', str(tool)[:20]) for tool in tools[:3]]
                        if len(tools) > 3:
                            tool_names.append(f"... +{len(tools)-3} more")
                        lines.append(f"Tool Names: {', '.join(tool_names)}")
            
            # Capabilities
            capabilities = []
            if hasattr(self._agent, 'ainvoke'):
                capabilities.append("async")
            if hasattr(self._agent, 'invoke'):
                capabilities.append("sync")
            if hasattr(self._agent, 'stream'):
                capabilities.append("streaming")
            if capabilities:
                lines.append(f"Capabilities: {', '.join(capabilities)}")
            
            # Memory/State info
            if hasattr(self._agent, 'memory') and self._agent.memory:
                lines.append(f"Memory: {type(self._agent.memory).__name__}")
            
            # Dasein configuration
            lines.append(f"Dasein Config:")
            lines.append(f"  Retry: {self._retry}")
            lines.append(f"  Performance Tracking: {self._performance_tracking}")
            lines.append(f"  Verbose: {self._verbose}")
            lines.append(f"  Naive Mode: {self._naive}")
            
            return '\n'.join(lines)
            
        except Exception as e:
            return f"Error generating fingerprint: {e}"
    
    def _calculate_successful_calls(self, trace):
        """Calculate successful calls from trace - default to success unless clear error."""
        try:
            if not trace:
                return 0
            
            # Method 1: Check for explicit success field (LangChain style)
            explicit_successes = len([step for step in trace if step.get('success', False)])
            explicit_failures = len([step for step in trace if step.get('success') is False])
            
            # If we have explicit success/failure data, use it
            if explicit_successes > 0 or explicit_failures > 0:
                return explicit_successes
            
            # Method 2: Default to success unless clear error (LangGraph and others)
            # Only count as failure if there's a clear technical error
            failed_calls = 0
            
            for step in trace:
                outcome = step.get('outcome', '').lower()
                
                # Only count as failure if there's a clear error indicator
                if outcome and any(error_indicator in outcome for error_indicator in [
                    'error:', 'exception:', 'traceback', 'failed:', 'timeout',
                    'connection error', 'http error', 'invalid response', 
                    'unauthorized', 'forbidden', 'bad request', 'not found'
                ]):
                    failed_calls += 1
            
            # Success = total steps minus clear failures
            successful_calls = len(trace) - failed_calls
            
            print(f"[DEBUG] Calculated {successful_calls} successful calls from {len(trace)} trace steps ({failed_calls} clear failures)")
            return max(0, successful_calls)
            
        except Exception as e:
            print(f"[DEBUG] Error calculating successful calls: {e}")
            # Fallback: assume all steps successful if we have any trace steps
            return len(trace) if trace else 0
    
    def _generate_step_id(self, step_number: int, phase: str) -> str:
        """Generate unique step ID for tracking individual steps."""
        if not self._performance_tracking_id:
            return f"step_{step_number}_{phase}"
        return f"{self._performance_tracking_id}_{step_number}_{phase}"
    
    def _should_skip_rule_synthesis(self, step_number: Optional[int], is_baseline: bool, total_steps: Optional[int] = None) -> bool:
        """
        Determine if rule synthesis should be skipped for performance optimization.
        
        Skip synthesis when:
        1. Sequential mode baseline runs (steps 2+) - no learning needed
        2. Final step in both performance tracking modes - nothing to learn for
        
        Args:
            step_number: Current step number
            is_baseline: Whether this is a baseline run
            
        Returns:
            True if synthesis should be skipped
        """
        if not (self._performance_tracking or self._sequential_mode):
            return False
        
        if step_number is None:
            return False
        
        # Skip synthesis for baseline runs in sequential mode (steps 2+)
        if self._sequential_mode and is_baseline and step_number >= 2:
            return True
        
        # Skip synthesis for final step in both performance tracking modes
        if total_steps and step_number == total_steps:
            return True
        
        return False
    
    def _pre_run_phase(self, query: str, is_baseline: bool = False) -> List[Dict[str, Any]]:
        """
        Pre-run phase: Get rules from distributed pre-run service.
        
        Args:
            query: User query
            is_baseline: If True, skip rule fetching for baseline performance tracking
        """
        try:
            
            # Use distributed pre-run service
            if is_baseline and self._performance_tracking:
                print(f"[DASEIN] BASELINE RUN - Calling pre-run service (no rule selection)")
            else:
                print(f"[DASEIN] Calling pre-run service for query: {str(query)[:50]}...")
            
            # Generate agent fingerprint (stable categorical tag)
            def _minimal_agent_fingerprint(agent, original_agent) -> str:
                """Generate fingerprint from ORIGINAL unwrapped agent to avoid wrapper contamination"""
                try:
                    # Use original_agent for fingerprinting, not wrapped agent
                    agent_to_fingerprint = original_agent if original_agent else agent
                    
                    # agent class
                    agent_cls = getattr(agent_to_fingerprint, '__class__', None)
                    agent_name = getattr(agent_cls, '__name__', '') if agent_cls else ''
                    # framework top-level module
                    module = getattr(agent_to_fingerprint, '__module__', '') or ''
                    framework = module.split('.')[0] if module else ''
                    
                    # model id (comprehensive search through agent structure)
                    model_id = ''
                    
                    # Helper to extract model from LLM instance
                    def _extract_model_from_llm(llm_obj):
                        if llm_obj is None:
                            return None
                        type_name = type(llm_obj).__name__
                        if 'Language' in type_name or 'Chat' in type_name or 'LLM' in type_name:
                            return (
                                getattr(llm_obj, 'model', None)
                                or getattr(llm_obj, 'model_name', None)
                                or getattr(llm_obj, 'model_id', None)
                                or getattr(llm_obj, 'model_tag', None)
                            )
                        return None
                    
                    # 1. Direct llm
                    llm = getattr(agent_to_fingerprint, 'llm', None)
                    model_id = _extract_model_from_llm(llm)
                    
                    # 2. Legacy ReAct: agent.llm_chain.llm
                    if not model_id:
                        llm_chain = getattr(agent_to_fingerprint, 'llm_chain', None)
                        if llm_chain:
                            llm = getattr(llm_chain, 'llm', None)
                            model_id = _extract_model_from_llm(llm)
                    
                    # 3. Nested agent.agent
                    if not model_id:
                        inner_agent = getattr(agent_to_fingerprint, 'agent', None)
                        if inner_agent:
                            llm = getattr(inner_agent, 'llm', None)
                            model_id = _extract_model_from_llm(llm)
                            if not model_id:
                                llm_chain = getattr(inner_agent, 'llm_chain', None)
                                if llm_chain:
                                    llm = getattr(llm_chain, 'llm', None)
                                    model_id = _extract_model_from_llm(llm)
                    
                    # 4. LCEL runnable graph
                    if not model_id:
                        runnable = getattr(agent_to_fingerprint, 'runnable', None)
                        if runnable:
                            model_id = _extract_model_from_llm(runnable)
                            if not model_id and hasattr(runnable, 'steps'):
                                for step in runnable.steps:
                                    model_id = _extract_model_from_llm(step)
                                    if model_id:
                                        break
                    
                    # 5. Toolkit
                    if not model_id:
                        toolkit = getattr(agent_to_fingerprint, 'toolkit', None)
                        if toolkit:
                            llm = getattr(toolkit, 'llm', None)
                            model_id = _extract_model_from_llm(llm)
                    
                    # 6. Tools list
                    if not model_id:
                        tools_attr = getattr(agent_to_fingerprint, 'tools', None)
                        if tools_attr:
                            try:
                                for tool in tools_attr:
                                    llm = getattr(tool, 'llm', None)
                                    model_id = _extract_model_from_llm(llm)
                                    if model_id:
                                        break
                            except Exception:
                                pass
                    
                    model_id = str(model_id) if model_id else ''
                    
                    # tools/toolkit (from original agent)
                    tool_names = []
                    tools_attr = getattr(agent_to_fingerprint, 'tools', None)
                    if tools_attr:
                        try:
                            for t in tools_attr:
                                name = getattr(t, 'name', None) or getattr(t, '__name__', None) or getattr(t, '__class__', type('x', (), {'__name__': ''})) .__name__
                                if not name and hasattr(t, '__class__'):
                                    name = getattr(t.__class__, '__name__', '')
                                if name:
                                    tool_names.append(str(name))
                        except Exception:
                            pass
                    elif getattr(agent_to_fingerprint, 'toolkit', None):
                        tk = getattr(agent_to_fingerprint, 'toolkit')
                        tk_tools = getattr(tk, 'tools', None) or getattr(tk, 'get_tools', None)
                        try:
                            iterable = tk_tools() if callable(tk_tools) else tk_tools
                            for t in (iterable or []):
                                name = getattr(t, 'name', None) or getattr(t, '__name__', None) or getattr(t, '__class__', type('x', (), {'__name__': ''})) .__name__
                                if not name and hasattr(t, '__class__'):
                                    name = getattr(t.__class__, '__name__', '')
                                if name:
                                    tool_names.append(str(name))
                        except Exception:
                            pass
                    # normalize
                    norm = lambda s: str(s).strip().lower().replace(' ', '_') if s is not None else ''
                    agent_name = norm(agent_name)
                    framework = norm(framework)
                    model_id = norm(model_id)
                    tool_names = [norm(n) for n in tool_names if n]
                    tools_joined = ','.join(sorted(set(tool_names)))
                    # fixed-order segments (keep keys even if empty to preserve format)
                    return f"agent={agent_name}|framework={framework}|model={model_id}|tools={tools_joined}"
                except Exception:
                    # Fallback to prior behavior on any error
                    return getattr(agent_to_fingerprint, 'agent_id', None) or f"agent_{id(agent_to_fingerprint)}"

            # Generate fingerprint once and cache it for reuse in post-run
            if self._agent_fingerprint is None:
                self._agent_fingerprint = _minimal_agent_fingerprint(self._agent, self._original_agent)
            agent_fingerprint = self._agent_fingerprint
            
            # Call pre-run service (it will handle baseline flag internally)
            selected_rules = self._service_adapter.select_rules(
                query=query,
                agent_fingerprint=agent_fingerprint,
                max_rules_per_layer=self._top_k,  # Configurable via top_k parameter
                performance_tracking_id=self._performance_tracking_id,  # For rule isolation
                is_baseline=is_baseline,  # Skip rule selection for baselines
                verbose=self._verbose  # Pass verbose flag through
            )
            
            print(f"[DASEIN] Pre-run service returned {len(selected_rules)} rules")
            
            # Pre-load embedding model if we have filter_search rules (avoid timeout on first batch)
            if selected_rules:
                # Check for any llm_start rules with "filter search" keywords
                has_filter_search_rules = False
                for rule_meta in selected_rules:
                    # Unwrap tuple if needed
                    rule_obj = rule_meta[0] if isinstance(rule_meta, tuple) and len(rule_meta) == 2 else rule_meta
                    
                    # Check if this is an llm_start rule with filter/search keywords
                    # Handle both dict and object formats
                    if isinstance(rule_obj, dict):
                        target_step_type = rule_obj.get('target_step_type')
                        advice = rule_obj.get('advice_text') or rule_obj.get('advice', '')
                    else:
                        target_step_type = getattr(rule_obj, 'target_step_type', None)
                        advice = getattr(rule_obj, 'advice_text', None) or getattr(rule_obj, 'advice', None) or ''
                    
                    advice_lower = advice.lower() if advice else ''
                    
                    if target_step_type == 'llm_start' and 'filter' in advice_lower and 'search' in advice_lower:
                        has_filter_search_rules = True
                        break
                
                if has_filter_search_rules:
                    print(f"[DASEIN] 🔧 Pre-loading embedding model for pipecleaner (found filter search rules)...")
                    from .pipecleaner import _get_embedding_model
                    try:
                        # Suppress protobuf warnings from sentence-transformers
                        import warnings
                        with warnings.catch_warnings():
                            warnings.filterwarnings('ignore', category=Warning)
                            _get_embedding_model()  # Warm up the model
                        print(f"[DASEIN] ✅ Embedding model pre-loaded successfully")
                    except Exception as e:
                        print(f"[DASEIN] ⚠️  Failed to pre-load embedding model: {e}")
            
            #  CRITICAL: For LangGraph agents, recreate with injected prompt
            if self._is_langgraph and selected_rules:
                print(f" [DASEIN][PRERUN] LangGraph agent detected with {len(selected_rules)} rules")
                recreation_success = self._recreate_langgraph_agent_with_prompt(selected_rules)
                if recreation_success:
                    print(f" [DASEIN][PRERUN] LangGraph agent successfully recreated with prompt injection")
                    print(f" [DASEIN][PRERUN] Planning rules will be applied via system prompt")
                    print(f" [DASEIN][PRERUN] Tool rules will still be applied via micro-turn injection")
                else:
                    print(f" [DASEIN][PRERUN] FAILED to recreate LangGraph agent")
                    print(f" [DASEIN][PRERUN] FALLING BACK to callback-based injection")
                    print(f" [DASEIN][PRERUN] This may result in reduced rule compliance!")
            elif self._is_langgraph and not selected_rules:
                print(f" [DASEIN][PRERUN] LangGraph agent detected but no rules - keeping original agent")
            
            return selected_rules
            
        except Exception as e:
            print(f"[DASEIN] Error in pre-run phase: {e}")
            return []
    
    def _post_run_phase(self, query: str, result: Any, selected_rules: List[Dict[str, Any]], 
                       step_number: Optional[int] = None, is_baseline: bool = False, 
                       total_steps: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Post-run phase: Send trace to distributed post-run service for synthesis.
        
        Args:
            query: User query
            result: Agent result
            selected_rules: Rules that were used
            step_number: Current step number for optimization decisions
            is_baseline: Whether this is a baseline run
        
        Returns:
            KPIs from post-run service if available, None otherwise
        """
        try:
            if not self._service_adapter:
                print(f"[DASEIN] Post-run phase skipped - distributed services not available")
                return None
            
            # Determine if we should skip rule synthesis for performance optimization
            skip_synthesis = self._should_skip_rule_synthesis(step_number, is_baseline, total_steps)
            if skip_synthesis:
                print(f"[DASEIN] Skipping rule synthesis for performance optimization (step {step_number}, baseline={is_baseline})")
                # Still need to call post-run for KPIs, but skip expensive synthesis
            
            # 1) Get current trace for synthesis
            trace = None
            
            # PRIORITY 1: Callback handler (has ALL intermediate steps)
            if self._callback_handler:
                trace = self._callback_handler.get_trace()
                if trace:
                    print(f"[DASEIN] Got {len(trace)} steps from callback handler for post-run")
            
            # PRIORITY 2: Wrapped LLM
            if not trace and self._wrapped_llm:
                trace = self._wrapped_llm.get_trace()
                if trace:
                    print(f"[DASEIN] Got {len(trace)} steps from wrapped LLM for post-run")
            
            # PRIORITY 3: LangGraph message extraction (fallback only - loses intermediate steps)
            if not trace:
                agent_class_name = self._agent.__class__.__name__
                is_langgraph = ('Compiled' in agent_class_name and 'Graph' in agent_class_name) or 'langgraph' in agent_class_name.lower()
                
                if is_langgraph and result and isinstance(result, dict) and 'messages' in result:
                    print(f"[DASEIN] No callback trace - extracting from LangGraph result as fallback")
                    extracted_query = self._extract_query_from_input(query) if query else ""
                    trace = self._extract_trace_from_langgraph_result(result, extracted_query)
            
            if not trace:
                # Do not bail out – continue with empty trace so KPIs can still be recorded by the service
                print(f"[DASEIN] No trace available for synthesis - continuing with empty trace for KPIs")
                trace = []
            
            print(f"[DASEIN] Sending trace with {len(trace)} steps to post-run service")
            
            # 2) Prepare outcomes and artifacts from the run
            outcomes = []
            artifacts = []
            signals = {}
            
            # Extract outcomes from trace
            for step in trace:
                if step.get("step_type") == "tool_end":
                    # Convert datetime to string if needed
                    timestamp = step.get("ts", "")
                    if hasattr(timestamp, 'isoformat'):
                        timestamp = timestamp.isoformat()
                    elif timestamp and not isinstance(timestamp, str):
                        timestamp = str(timestamp)
                    
                    outcomes.append({
                        "tool_name": step.get("tool_name", ""),
                        "success": True,  # Assume success for now
                        "result": step.get("outcome", ""),
                        "timestamp": timestamp
                    })
            
            # Clean trace for JSON serialization
            def clean_for_json(obj):
                """Recursively clean an object for JSON serialization."""
                import uuid
                if isinstance(obj, uuid.UUID):
                    return str(obj)
                elif hasattr(obj, 'isoformat'):  # datetime object
                    return obj.isoformat()
                elif isinstance(obj, dict):
                    return {k: clean_for_json(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [clean_for_json(item) for item in obj]
                elif hasattr(obj, '__dict__'):  # Custom object
                    return str(obj)
                else:
                    return obj
            
            cleaned_trace = clean_for_json(trace)
            
            # 3) Call post-run service for synthesis
            # For retry > 1, wait for synthesis on all runs except the last one
            wait_for_synthesis = False
            if total_steps and step_number and step_number < total_steps:
                wait_for_synthesis = True
                print(f"[DASEIN] Will WAIT for rule synthesis (step {step_number}/{total_steps})")
            
            if self._post_run == "kpi_only":
                print(f"[DASEIN] Calling post-run service (KPI-only mode, no rule synthesis)")
            else:
                mode_str = "BLOCKING" if wait_for_synthesis else "ASYNC"
                print(f"[DASEIN] Calling post-run service for rule synthesis ({mode_str} mode)")
            
            # Compute agent fingerprint for post-run (mirror pre-run minimal fingerprint)
            def _minimal_agent_fingerprint(agent, original_agent) -> str:
                """Generate fingerprint from ORIGINAL unwrapped agent to avoid wrapper contamination"""
                try:
                    # Use original_agent for fingerprinting, not wrapped agent
                    agent_to_fingerprint = original_agent if original_agent else agent
                    
                    agent_cls = getattr(agent_to_fingerprint, '__class__', None)
                    agent_name = getattr(agent_cls, '__name__', '') if agent_cls else ''
                    module = getattr(agent_to_fingerprint, '__module__', '') or ''
                    framework = module.split('.')[0] if module else ''
                    
                    # model id (comprehensive search through agent structure)
                    model_id = ''
                    
                    # Helper to extract model from LLM instance
                    def _extract_model_from_llm(llm_obj):
                        if llm_obj is None:
                            return None
                        type_name = type(llm_obj).__name__
                        if 'Language' in type_name or 'Chat' in type_name or 'LLM' in type_name:
                            return (
                                getattr(llm_obj, 'model', None)
                                or getattr(llm_obj, 'model_name', None)
                                or getattr(llm_obj, 'model_id', None)
                                or getattr(llm_obj, 'model_tag', None)
                            )
                        return None
                    
                    # 1. Direct llm
                    llm = getattr(agent_to_fingerprint, 'llm', None)
                    model_id = _extract_model_from_llm(llm)
                    
                    # 2. Legacy ReAct: agent.llm_chain.llm
                    if not model_id:
                        llm_chain = getattr(agent_to_fingerprint, 'llm_chain', None)
                        if llm_chain:
                            llm = getattr(llm_chain, 'llm', None)
                            model_id = _extract_model_from_llm(llm)
                    
                    # 3. Nested agent.agent
                    if not model_id:
                        inner_agent = getattr(agent_to_fingerprint, 'agent', None)
                        if inner_agent:
                            llm = getattr(inner_agent, 'llm', None)
                            model_id = _extract_model_from_llm(llm)
                            if not model_id:
                                llm_chain = getattr(inner_agent, 'llm_chain', None)
                                if llm_chain:
                                    llm = getattr(llm_chain, 'llm', None)
                                    model_id = _extract_model_from_llm(llm)
                    
                    # 4. LCEL runnable graph
                    if not model_id:
                        runnable = getattr(agent_to_fingerprint, 'runnable', None)
                        if runnable:
                            model_id = _extract_model_from_llm(runnable)
                            if not model_id and hasattr(runnable, 'steps'):
                                for step in runnable.steps:
                                    model_id = _extract_model_from_llm(step)
                                    if model_id:
                                        break
                    
                    # 5. Toolkit
                    if not model_id:
                        toolkit = getattr(agent_to_fingerprint, 'toolkit', None)
                        if toolkit:
                            llm = getattr(toolkit, 'llm', None)
                            model_id = _extract_model_from_llm(llm)
                    
                    # 6. Tools list
                    if not model_id:
                        tools_attr = getattr(agent_to_fingerprint, 'tools', None)
                        if tools_attr:
                            try:
                                for tool in tools_attr:
                                    llm = getattr(tool, 'llm', None)
                                    model_id = _extract_model_from_llm(llm)
                                    if model_id:
                                        break
                            except Exception:
                                pass
                    
                    model_id = str(model_id) if model_id else ''
                    
                    tool_names = []
                    tools_attr = getattr(agent_to_fingerprint, 'tools', None)
                    if tools_attr:
                        try:
                            for t in tools_attr:
                                name = getattr(t, 'name', None) or getattr(t, '__name__', None) or getattr(t.__class__, '__name__', '')
                                if name:
                                    tool_names.append(str(name))
                        except Exception:
                            pass
                    elif getattr(agent_to_fingerprint, 'toolkit', None):
                        tk = getattr(agent_to_fingerprint, 'toolkit')
                        tk_tools = getattr(tk, 'tools', None) or getattr(tk, 'get_tools', None)
                        try:
                            iterable = tk_tools() if callable(tk_tools) else tk_tools
                            for t in (iterable or []):
                                name = getattr(t, 'name', None) or getattr(t, '__name__', None) or getattr(t.__class__, '__name__', '')
                                if name:
                                    tool_names.append(str(name))
                        except Exception:
                            pass
                    norm = lambda s: str(s).strip().lower().replace(' ', '_') if s is not None else ''
                    agent_name = norm(agent_name)
                    framework = norm(framework)
                    model_id = norm(model_id)
                    tool_names = [norm(n) for n in tool_names if n]
                    tools_joined = ','.join(sorted(set(tool_names)))
                    return f"agent={agent_name}|framework={framework}|model={model_id}|tools={tools_joined}"
                except Exception:
                    return getattr(agent_to_fingerprint, 'agent_id', None) or f"agent_{id(agent_to_fingerprint)}"

            # Reuse cached fingerprint from pre-run (guaranteed to be identical)
            agent_fingerprint = self._agent_fingerprint
            
            # Get tool metadata from callback handler (extracted during runtime)
            tools_metadata = []
            if hasattr(self._callback_handler, '_compiled_tools_metadata'):
                tools_metadata = self._callback_handler._compiled_tools_metadata
            # Fallback: try extracting now (may not work if tools unbound)
            if not tools_metadata:
                tools_metadata = self._extract_tool_metadata(self._agent)
            
            # Reuse existing graph analysis (already extracted in __init__)
            graph_metadata = None
            if self._is_langgraph and hasattr(self._agent, 'get_graph'):
                try:
                    graph = self._agent.get_graph()
                    graph_metadata = {
                        'nodes': list(graph.nodes.keys()),
                        'edges': [{'source': e.source, 'target': e.target} for e in graph.edges],
                        'is_multi_agent': len(graph.nodes) > 1
                    }
                    print(f"[DASEIN] Extracted graph metadata: {len(graph_metadata['nodes'])} nodes, {len(graph_metadata['edges'])} edges")
                except Exception:
                    pass
            
            print(f"[DASEIN] Extracted metadata for {len(tools_metadata)} tools")
            
            if tools_metadata:
                print(f"[DASEIN] Sample tool: {tools_metadata[0].get('name', 'unknown')}")
            else:
                print(f"[DASEIN] WARNING: No tools extracted! Agent type: {type(self._agent)}")

            # Extract rules_applied from selected_rules (rule IDs that were actually selected by pre-run)
            rules_applied = []
            for rule in selected_rules:
                if isinstance(rule, dict):
                    rule_id = rule.get('id', '')
                    if rule_id:
                        rules_applied.append(rule_id)
                elif hasattr(rule, 'id'):
                    rules_applied.append(rule.id)
            print(f"[DASEIN] Passing {len(rules_applied)} rule IDs to post-run: {rules_applied}")
            
            # Compute context_hash: represents query + agent fingerprint (what context node contains)
            import hashlib
            combined_context = f"{query}:{agent_fingerprint}"
            context_hash = f"ctx_{hashlib.sha256(combined_context.encode()).hexdigest()[:9]}"
            print(f"[DASEIN] Computed context_hash: {context_hash}")

            response = self._service_adapter.synthesize_rules(
                run_id=None,  # Will use stored run_id from pre-run phase
                trace=cleaned_trace,
                outcomes=outcomes,
                artifacts=artifacts,
                signals=signals,
                original_query=query,  # Pass original query for final success determination
                max_rules=self._top_k,  # Configurable via top_k parameter
                performance_tracking_id=self._performance_tracking_id,  # For rule isolation
                skip_synthesis=skip_synthesis,  # Skip expensive synthesis when not needed
                agent_fingerprint=agent_fingerprint,  # Reuse fingerprint from pre-run (line 2613)
                step_id=self._current_step_id,  # Pass step_id for parallel execution tracking
                post_run_mode=self._post_run,  # Pass post_run mode ("full" or "kpi_only")
                wait_for_synthesis=wait_for_synthesis,  # Wait for synthesis on retry runs (except last)
                tools_metadata=tools_metadata,  # Tool metadata for Stage 3.5 tool grounding
                graph_metadata=graph_metadata,  # Graph metadata for Stage 3.5 node grounding
                rules_applied=rules_applied,  # Rule IDs selected by pre-run
                context_hash=context_hash  # Context hash for graph grouping
            )

            # response is a dict from ServiceAdapter; handle accordingly
            new_rules = response.get('new_rules', []) if isinstance(response, dict) else []
            notes = response.get('notes', '') if isinstance(response, dict) else ''
            kpis = response.get('kpis') if isinstance(response, dict) else None

            print(f"[DASEIN] Post-run service returned {len(new_rules)} new rules")
            if notes:
                print(f"[DASEIN] Post-run notes: {notes}")

            # Return KPI data for performance tracking
            if kpis:
                print(f"[DASEIN] Run KPIs:")
                print(f"  Total Turns: {kpis.get('total_turns', 0)}")
                print(f"  Total Tokens: {kpis.get('total_tokens', 0)}")
                print(f"  Trace Time: {kpis.get('trace_time_ms', 0)}ms")
                print(f"  Failures: {kpis.get('failures', 0)}")
                print(f"  Success Rate: {kpis.get('success_rate', 0):.1f}%")
                print(f"  Overall Success: {'' if kpis.get('overall_success', False) else ''}")
                print(f"  Final Outcome: {kpis.get('final_outcome', 'unknown')}")

                # Store and return KPIs
                self._last_run_kpis = kpis
                return kpis
            
            return None
            
        except Exception as e:
            print(f"[DASEIN] Post-run phase failed: {e}")
            return None
    
    
    
    
    
    def _invoke_sequential(self, *args, **kwargs):
        """
        Sequential invocation mode for POC demonstrations.
        
        Process:
        1. Run n sequential queries to build up learning (checkpoint each step's stats)
        2. Reset brain
        3. Run all queries again as baselines (fresh, no rules) - store stats and reset brain each time
        4. Run all queries again with learned rules - store stats and reset brain each time
        5. Provide stepwise and overall comparisons
        """
        query = args[0] if args else ""
        self._sequential_step += 1
        
        print(f"\n SEQUENTIAL STEP {self._sequential_step}")
        print(f"Query: {query}")
        print("-" * 50)
        
        # For now, just run the single invocation and let the overall sequential logic handle the rest
        result = self._invoke_single(*args, **kwargs)
        
        # Store basic info for this step - KPIs will come from post-run service
        self._vprint(f"[DASEIN][SEQUENTIAL] Step {self._sequential_step} completed - KPIs handled by post-run service")
        metrics = {
            'step': self._sequential_step,
            'query': query,
            'result': result,
            'note': 'KPIs calculated by post-run API service'
        }
        self._sequential_metrics.append(metrics)
        
        # Print step summary
        self._print_step_summary(metrics, f"STEP {self._sequential_step}")
        
        return result
    
    async def _ainvoke_sequential(self, *args, **kwargs):
        """
        Async sequential invocation mode for POC demonstrations.
        
        Process:
        1. Run n sequential queries to build up learning (checkpoint each step's stats)
        2. Reset brain
        3. Run all queries again as baselines (fresh, no rules) - store stats and reset brain each time
        4. Run all queries again with learned rules - store stats and reset brain each time
        5. Provide stepwise and overall comparisons
        """
        query = args[0] if args else ""
        self._sequential_step += 1
        
        print(f"\n SEQUENTIAL STEP {self._sequential_step}")
        print(f"Query: {query}")
        print("-" * 50)
        
        # For now, just run the single invocation and let the overall sequential logic handle the rest
        result = await self._ainvoke_single(*args, **kwargs)
        
        # Store basic info for this step - KPIs will come from post-run service
        self._vprint(f"[DASEIN][SEQUENTIAL] Step {self._sequential_step} completed - KPIs handled by post-run service")
        metrics = {
            'step': self._sequential_step,
            'query': query,
            'result': result,
            'note': 'KPIs calculated by post-run API service'
        }
        self._sequential_metrics.append(metrics)
        
        # Print step summary
        self._print_step_summary(metrics, f"STEP {self._sequential_step}")
        
        return result
    
    def _extract_trace_from_langgraph_result(self, result, query):
        """Extract trace from LangGraph agent result when callbacks don't work."""
        try:
            if not isinstance(result, dict) or 'messages' not in result:
                return []
            
            messages = result['messages']
            trace = []
            
            print(f"[DASEIN] Extracting trace from {len(messages)} LangGraph messages")
            
            for i, message in enumerate(messages):
                # Skip the initial human message
                if i == 0:
                    continue
                    
                if hasattr(message, 'type'):
                    if message.type == 'ai':
                        # AI message - this is an LLM call
                        content = getattr(message, 'content', '')
                        tool_calls = getattr(message, 'tool_calls', [])
                        usage_metadata = getattr(message, 'usage_metadata', {})
                        
                        # Extract token counts from usage metadata
                        input_tokens = usage_metadata.get('input_tokens', 0)
                        output_tokens = usage_metadata.get('output_tokens', 0)
                        total_tokens = usage_metadata.get('total_tokens', input_tokens + output_tokens)
                        
                        # Add LLM start step with token info
                        step = {
                            "step_type": "llm_start",
                            "tool_name": "ChatGoogleGenerativeAI",
                            "args_excerpt": str(query)[:200] if query else "",
                            "outcome": "",
                            "ts": datetime.now().isoformat(),
                            "run_id": f"langgraph_{i}",
                            "parent_run_id": None,
                            "tokens_input": input_tokens,
                            "tokens_output": 0,  # Set on end step
                            "duration_ms": 100,  # Estimated duration
                        }
                        trace.append(step)
                        
                        # Add LLM end step with token info
                        step = {
                            "step_type": "llm_end", 
                            "tool_name": "ChatGoogleGenerativeAI",
                            "args_excerpt": "",
                            "outcome": str(content)[:200] if content else "",
                            "ts": datetime.now().isoformat(),
                            "run_id": f"langgraph_{i}",
                            "parent_run_id": None,
                            "tokens_input": 0,  # Already counted in start
                            "tokens_output": output_tokens,
                            "duration_ms": 100,  # Estimated duration
                        }
                        trace.append(step)
                        
                        # Add tool calls if any
                        for j, tool_call in enumerate(tool_calls):
                            tool_name = tool_call.get('name', 'unknown_tool')
                            tool_args = str(tool_call.get('args', {}))[:200]
                            
                            step = {
                                "step_type": "tool_start",
                                "tool_name": tool_name,
                                "args_excerpt": tool_args,
                                "outcome": "",
                                "ts": datetime.now().isoformat(),
                                "run_id": f"langgraph_{i}_tool_{j}",
                                "parent_run_id": f"langgraph_{i}",
                            }
                            trace.append(step)
                    
                    elif message.type == 'tool':
                        # Tool message - this is a tool response
                        content = getattr(message, 'content', '')
                        name = getattr(message, 'name', 'unknown_tool')
                        
                        step = {
                            "step_type": "tool_end",
                            "tool_name": name,
                            "args_excerpt": "",
                            "outcome": str(content)[:200] if content else "",
                            "ts": datetime.now().isoformat(),
                            "run_id": f"langgraph_{i}_tool_end",
                            "parent_run_id": None,
                        }
                        trace.append(step)
            
            print(f"[DASEIN] Extracted {len(trace)} steps from LangGraph result")
            return trace
            
        except Exception as e:
            print(f"[DASEIN] Error extracting trace from LangGraph result: {e}")
            return []
    
    def run_sequential_queries(self, queries):
        """
        Run the complete sequential learning process with the given queries.
        
        Process:
        1. PHASE 1: Run n sequential queries to build up learning (rules accumulate)
        2. PHASE 2: Reset brain, then run baselines vs enhanced for each query
        3. PHASE 3: Provide stepwise and overall comparisons
        """
        print(f"\n{'='*60}")
        print(" SEQUENTIAL PERFORMANCE TRACKING")
        print(f"{'='*60}")
        print(f"Queries: {len(queries)} sequential queries")
        print(f"Process: Learn sequentially, then test baselines vs enhanced")
        print(f"Expected: Stepwise token reductions and overall improvements")
        
        # Store all metrics for analysis
        all_metrics = []
        
        # PHASE 1: Sequential Learning Runs (Rules Accumulate)
        print(f"\n{'='*60}")
        print(" PHASE 1: SEQUENTIAL LEARNING RUNS")
        print(f"{'='*60}")
        print(" Starting sequential learning (rules accumulate in services)...")
        from .capture import clear_trace
        clear_trace()
        
        # Run each query sequentially to build up learning
        learning_metrics = []
        for i, query in enumerate(queries, 1):
            print(f"\n LEARNING RUN {i}/{len(queries)}")
            print(f"Query: {query}")
            print("-" * 50)
            
            # Run with learning enabled (rules from previous steps available)
            run_data = self._capture_run_metrics(query, is_baseline=False, step_number=i, total_steps=len(queries))
            
            # Update metrics with step info
            run_data['step'] = i
            run_data['query'] = query
            run_data['phase'] = 'learning'
            learning_metrics.append(run_data)
            all_metrics.append(run_data)
            
            # Print step summary
            self._print_step_summary(run_data, f"LEARNING-{i}")
            
            # Clear trace for next run (but keep brain state for rule accumulation)
            clear_trace()
        
        # PHASE 2: Baseline Collection (Naive Runs)
        print(f"\n{'='*60}")
        print(" PHASE 2: BASELINE COLLECTION")
        print(f"{'='*60}")
        print(" Running baselines (no rule fetching for comparison)...")
        
        # Run baselines in parallel for steps 2N (Step 1 is always baseline)
        # Note: Step 1 is always naive, so we only need baselines for steps 2N
        baseline_metrics = []
        
        if len(queries) > 1:  # Only if we have steps 2N
            print(f" Running {len(queries)-1} baseline runs in PARALLEL...")
            baseline_metrics = self._run_baselines_parallel(queries[1:], start_step=2)
            all_metrics.extend(baseline_metrics)
        else:
            print(" Only one query - no additional baselines needed")
        
        # PHASE 3: Analysis (Learning vs Baseline Comparison)
        print(f"\n{'='*60}")
        print(" PHASE 3: ANALYSIS")
        print(f"{'='*60}")
        self._print_learning_vs_baseline_analysis(learning_metrics, baseline_metrics)
        
        return all_metrics
    
    def run_sequential(self, queries):
        """
        Run sequential performance tracking with the given queries.
        This is the main entry point for sequential mode.
        """
        if not self._sequential_mode:
            raise ValueError("Sequential mode not enabled. Use performance_tracking='sequential' when creating the cognate proxy.")
        
        return self.run_sequential_queries(queries)
    
    def _run_baselines_parallel(self, queries: List[str], start_step: int = 2) -> List[Dict[str, Any]]:
        """
        Run baseline queries in parallel to cut wall time in half.
        
        Args:
            queries: List of queries to run as baselines
            start_step: Starting step number (usually 2)
            
        Returns:
            List of baseline metrics
        """
        import concurrent.futures
        import threading
        import time
        from .capture import clear_trace
        
        def run_single_baseline(query_info):
            """Run a single baseline in a thread."""
            step_num, query = query_info
            thread_id = threading.current_thread().ident
            
            print(f"[Thread-{thread_id}]  BASELINE RUN {step_num}: {query[:50]}...")
            
            try:
                # Each thread needs its own trace clearing
                clear_trace()
                
                # Run baseline (no rules fetched)  
                # For baselines, total_steps doesn't matter since we skip synthesis anyway
                baseline_data = self._capture_run_metrics(query, is_baseline=True, step_number=step_num)
                
                # Update with step info
                baseline_data['step'] = step_num
                baseline_data['query'] = query
                baseline_data['phase'] = 'baseline'
                
                print(f"[Thread-{thread_id}]  BASELINE {step_num} completed")
                return baseline_data
                
            except Exception as e:
                print(f"[Thread-{thread_id}]  BASELINE {step_num} failed: {e}")
                return {
                    'step': step_num,
                    'query': query,
                    'phase': 'baseline',
                    'error': str(e),
                    'result': None
                }
        
        # Prepare query info tuples (step_number, query)
        query_info_list = [(start_step + i, query) for i, query in enumerate(queries)]
        
        print(f" Starting {len(query_info_list)} parallel baseline threads...")
        start_time = time.time()
        
        # Run baselines in parallel using ThreadPoolExecutor
        baseline_results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(query_info_list)) as executor:
            # Submit all baseline runs
            future_to_step = {executor.submit(run_single_baseline, info): info[0] for info in query_info_list}
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_step):
                step_num = future_to_step[future]
                try:
                    baseline_data = future.result()
                    baseline_results.append(baseline_data)
                    
                    # Print summary for completed baseline
                    if 'error' not in baseline_data:
                        self._print_step_summary(baseline_data, f"BASELINE-{step_num}")
                    
                except Exception as e:
                    print(f" Baseline step {step_num} generated an exception: {e}")
        
        # Sort results by step number
        baseline_results.sort(key=lambda x: x['step'])
        
        wall_time = time.time() - start_time
        print(f" Parallel baselines completed in {wall_time:.2f}s")
        print(f" Processed {len(baseline_results)} baseline runs")
        
        return baseline_results
    
    def _run_naive_baseline(self, *args, **kwargs):
        """Run agent without any Dasein rules (naive baseline)."""
        # Temporarily disable rule injection
        original_rules = self._callback_handler._selected_rules
        self._callback_handler._selected_rules = []
        
        # Clear trace
        from .capture import clear_trace
        clear_trace()
        
        # Run without Dasein pipeline
        callbacks = kwargs.get('callbacks', [])
        if not isinstance(callbacks, list):
            callbacks = [callbacks] if callbacks else []
        
        # Remove our callback handler for naive baseline
        callbacks = [cb for cb in callbacks if not isinstance(cb, DaseinCallbackHandler)]
        kwargs['callbacks'] = callbacks
        
        result = self._agent.invoke(*args, **kwargs)
        
        # Restore original rules
        self._callback_handler._selected_rules = original_rules
        
        return result
    
    def _print_step_summary(self, metrics, step_name):
        """Print summary for a single step."""
        query = metrics.get('query', 'Unknown query')
        print(f"\n {step_name} METRICS:")
        print(f"  Query: {query}")
        print(f"  LLM Calls: {metrics['llm_calls']}")
        print(f"  Tool Calls: {metrics['tool_calls']}")
        print(f"  Total Turns: {metrics['total_turns']}")
        print(f"  Input Tokens: {metrics['input_tokens']}")
        print(f"  Output Tokens: {metrics['output_tokens']}")
        print(f"  Total Tokens: {metrics['total_tokens']}")
        print(f"  Trace Time (ms): {metrics['trace_time_ms']}")
        print(f"  Wall Time (ms): {metrics['wall_time_ms']}")
        print(f"  Success Rate: {metrics['success_rate']:.1f}%")
        print(f"  Overall Success: {'✅' if metrics['overall_success'] else '❌'}")
    
    def _print_step_comparison(self, naive_metrics, enhanced_metrics, step_name):
        """Print comparison between naive and enhanced runs."""
        print(f"\n {step_name} COMPARISON:")
        print("-" * 40)
        
        def calc_improvement(naive, enhanced, metric_name):
            if naive == 0:
                return f"{metric_name}: {enhanced} (no baseline)"
            change = naive - enhanced
            pct = (change / naive * 100) if naive > 0 else 0
            direction = "" if change > 0 else "" if change < 0 else "="
            return f"{metric_name}: {naive}  {enhanced} ({direction}{abs(change)}, {pct:+.1f}%)"
        
        print(calc_improvement(naive_metrics['llm_calls'], enhanced_metrics['llm_calls'], "LLM Calls"))
        print(calc_improvement(naive_metrics['tool_calls'], enhanced_metrics['tool_calls'], "Tool Calls"))
        print(calc_improvement(naive_metrics['total_turns'], enhanced_metrics['total_turns'], "Total Turns"))
        print(calc_improvement(naive_metrics['input_tokens'], enhanced_metrics['input_tokens'], "Input Tokens"))
        print(calc_improvement(naive_metrics['output_tokens'], enhanced_metrics['output_tokens'], "Output Tokens"))
        print(calc_improvement(naive_metrics['total_tokens'], enhanced_metrics['total_tokens'], "Total Tokens"))
        print(calc_improvement(naive_metrics['trace_time_ms'], enhanced_metrics['trace_time_ms'], "Trace Time (ms)"))
        print(calc_improvement(naive_metrics['wall_time_ms'], enhanced_metrics['wall_time_ms'], "Wall Time (ms)"))
        
        success_improvement = "  " if naive_metrics['overall_success'] and enhanced_metrics['overall_success'] else \
                             "  " if not naive_metrics['overall_success'] and enhanced_metrics['overall_success'] else \
                             "  " if naive_metrics['overall_success'] and not enhanced_metrics['overall_success'] else "  "
        print(f"Success: {success_improvement}")
    
    def _print_sequential_summary(self, comparison_metrics):
        """Print overall sequential learning summary."""
        print(f"\n SEQUENTIAL LEARNING SUMMARY")
        print("=" * 60)
        
        if not comparison_metrics:
            print("No comparison metrics available.")
            return
        
        # Calculate overall improvements
        total_baseline_tokens = sum(m['baseline']['total_tokens'] for m in comparison_metrics)
        total_enhanced_tokens = sum(m['enhanced']['total_tokens'] for m in comparison_metrics)
        total_token_improvement = total_baseline_tokens - total_enhanced_tokens
        total_token_pct = (total_token_improvement / total_baseline_tokens * 100) if total_baseline_tokens > 0 else 0
        
        total_baseline_turns = sum(m['baseline']['total_turns'] for m in comparison_metrics)
        total_enhanced_turns = sum(m['enhanced']['total_turns'] for m in comparison_metrics)
        total_turns_improvement = total_baseline_turns - total_enhanced_turns
        total_turns_pct = (total_turns_improvement / total_baseline_turns * 100) if total_baseline_turns > 0 else 0
        
        total_baseline_time = sum(m['baseline']['trace_time_ms'] for m in comparison_metrics)
        total_enhanced_time = sum(m['enhanced']['trace_time_ms'] for m in comparison_metrics)
        total_time_improvement = total_baseline_time - total_enhanced_time
        total_time_pct = (total_time_improvement / total_baseline_time * 100) if total_baseline_time > 0 else 0
        
        print(f" OVERALL PERFORMANCE IMPROVEMENTS:")
        print(f"  Total Tokens: {total_baseline_tokens}  {total_enhanced_tokens} ({total_token_improvement:+d}, {total_token_pct:+.1f}%)")
        print(f"  Total Turns: {total_baseline_turns}  {total_enhanced_turns} ({total_turns_improvement:+d}, {total_turns_pct:+.1f}%)")
        print(f"  Total Time: {total_baseline_time}  {total_enhanced_time}ms ({total_time_improvement:+d}, {total_time_pct:+.1f}%)")
        
        if total_token_improvement > 0 or total_turns_improvement > 0 or total_time_improvement > 0:
            print(f"\n SUCCESS: Sequential learning demonstrated measurable improvements!")
            print(f" COGNITIVE INSIGHT: Rules learned from sequential queries generalized across different query types")
            print(f" KEY DIFFERENTIATOR: True cognitive generalization with cumulative learning benefits")
        else:
            print(f"\n  NOTE: No overall performance improvement detected")
            print(f"   This may indicate that the queries were too different for effective rule generalization")
        
        # Show rule learning progression
        print(f"\n RULE LEARNING PROGRESSION:")
        print(f"  Step 1: Generated planning rules (skip discovery)")
        print(f"  Step 2: Applied planning rules + generated codegen rules")
        print(f"  Step 3: Applied both rule types + demonstrated cognition")
        
        print(f"\n Sequential POC Complete!")

    def _print_learning_vs_baseline_analysis(self, learning_metrics, baseline_metrics):
        """Print learning vs baseline analysis."""
        print(f"\n LEARNING vs BASELINE ANALYSIS")
        print("=" * 60)
        
        if not learning_metrics or not baseline_metrics:
            print("No metrics available for analysis.")
            return
        
        print(f"[DEBUG] Learning metrics: {len(learning_metrics)} items")
        print(f"[DEBUG] Baseline metrics: {len(baseline_metrics)} items")
        if baseline_metrics:
            print(f"[DEBUG] First baseline: {baseline_metrics[0].get('total_tokens', 'NO_TOKENS')} tokens")
        
        # Print model name and step-by-step query summary
        model_name = learning_metrics[0].get('model_name', 'Unknown Model')
        if model_name == 'Unknown Model':
            # Try to get model name from the LLM wrapper
            if hasattr(self, '_llm_wrapper') and hasattr(self._llm_wrapper, '_llm'):
                if hasattr(self._llm_wrapper._llm, 'model_name'):
                    model_name = self._llm_wrapper._llm.model_name
                elif hasattr(self._llm_wrapper._llm, 'model'):
                    model_name = self._llm_wrapper._llm.model
        print(f"\n Model Name: {model_name}")
        print(f"\n STEP-BY-STEP QUERY SUMMARY:")
        print("-" * 60)
        for i, learn_metric in enumerate(learning_metrics, 1):
            query = learn_metric.get('query', f'Query {i}')
            print(f"Step {i}: {query}")
        print("-" * 60)
        
        # Calculate overall improvements (only for steps that have both learning and baseline)
        # Always skip step 1 (which is always naive), compare remaining steps
        # Both learning and baseline should skip step 1 for overall comparison
        total_learning_tokens = sum(m['total_tokens'] for m in learning_metrics[1:])
        total_baseline_tokens = sum(m['total_tokens'] for m in baseline_metrics)
        total_token_improvement = total_baseline_tokens - total_learning_tokens
        total_token_pct = (total_token_improvement / total_baseline_tokens * 100) if total_baseline_tokens > 0 else 0
        
        # Always skip step 1 (which is always naive), compare remaining steps
        # Both learning and baseline should skip step 1 for overall comparison
        total_learning_turns = sum(m['total_turns'] for m in learning_metrics[1:])
        total_baseline_turns = sum(m['total_turns'] for m in baseline_metrics)
        total_learning_time = sum(m['trace_time_ms'] for m in learning_metrics[1:])
        total_baseline_time = sum(m['trace_time_ms'] for m in baseline_metrics)
        
        total_turns_improvement = total_baseline_turns - total_learning_turns
        total_turns_pct = (total_turns_improvement / total_baseline_turns * 100) if total_baseline_turns > 0 else 0
        total_time_improvement = total_baseline_time - total_learning_time
        total_time_pct = (total_time_improvement / total_baseline_time * 100) if total_baseline_time > 0 else 0
        
        # Calculate success rates and failure counts - always skip step 1 for learning, baseline starts from step 2
        learning_success_rate = sum(m['success_rate'] for m in learning_metrics[1:]) / len(learning_metrics[1:]) if learning_metrics[1:] else 0
        baseline_success_rate = sum(m['success_rate'] for m in baseline_metrics) / len(baseline_metrics) if baseline_metrics else 0
        success_rate_improvement = learning_success_rate - baseline_success_rate
        
        # Calculate failure counts - always skip step 1 for learning, baseline starts from step 2
        learning_failures = sum(1 for m in learning_metrics[1:] if not m.get('overall_success', False))
        baseline_failures = sum(1 for m in baseline_metrics if not m.get('overall_success', False))
        failure_reduction = baseline_failures - learning_failures
        failure_reduction_pct = (failure_reduction / baseline_failures * 100) if baseline_failures > 0 else 0
        
        # Calculate final outcome improvements - always skip step 1 for learning, baseline starts from step 2
        learning_completed = sum(1 for m in learning_metrics[1:] if m.get('final_outcome') == 'completed')
        baseline_completed = sum(1 for m in baseline_metrics if m.get('final_outcome') == 'completed')
        learning_gave_up = sum(1 for m in learning_metrics[1:] if m.get('final_outcome') == 'gave_up')
        baseline_gave_up = sum(1 for m in baseline_metrics if m.get('final_outcome') == 'gave_up')
        completion_improvement = learning_completed - baseline_completed
        gave_up_reduction = baseline_gave_up - learning_gave_up
        
        print(f" OVERALL PERFORMANCE IMPROVEMENTS:")
        token_direction = "" if total_token_improvement > 0 else "" if total_token_improvement < 0 else "="
        turn_direction = "" if total_turns_improvement > 0 else "" if total_turns_improvement < 0 else "="
        time_direction = "" if total_time_improvement > 0 else "" if total_time_improvement < 0 else "="
        success_direction = "" if success_rate_improvement > 0 else "" if success_rate_improvement < 0 else "="
        failure_direction = "" if failure_reduction > 0 else "" if failure_reduction < 0 else "="
        print(f"  Total Tokens: {total_baseline_tokens}  {total_learning_tokens} ({token_direction}{abs(total_token_improvement)}, {total_token_pct:+.1f}%)")
        print(f"  Total Turns: {total_baseline_turns}  {total_learning_turns} ({turn_direction}{abs(total_turns_improvement)}, {total_turns_pct:+.1f}%)")
        print(f"  Total Time: {total_baseline_time}  {total_learning_time}ms ({time_direction}{abs(total_time_improvement)}, {total_time_pct:+.1f}%)")
        print(f"  Success Rate: {baseline_success_rate:.1f}%  {learning_success_rate:.1f}% ({success_direction}{abs(success_rate_improvement):.1f}%)")
        print(f"  Failures: {baseline_failures}  {learning_failures} ({failure_direction}{abs(failure_reduction)}, {failure_reduction_pct:+.1f}%)")
        
        # Final outcome metrics
        completion_direction = "" if completion_improvement > 0 else "" if completion_improvement < 0 else "="
        gave_up_direction = "" if gave_up_reduction > 0 else "" if gave_up_reduction < 0 else "="
        print(f"  Task Completions: {baseline_completed}  {learning_completed} ({completion_direction}{abs(completion_improvement)})")
        print(f"  Agent Gave Up: {baseline_gave_up}  {learning_gave_up} ({gave_up_direction}{abs(gave_up_reduction)})")
        
        # Step-by-step comparison
        print(f"\n STEP-BY-STEP COMPARISON:")
        # Format step 1 outcome
        step1_outcome = self._format_final_outcome(learning_metrics[0].get('final_outcome', 'unknown'))
        print(f"  Step 1: {learning_metrics[0]['total_tokens']} tokens, {learning_metrics[0]['total_turns']} turns, {learning_metrics[0]['trace_time_ms']}ms, {learning_metrics[0]['success_rate']:.1f}%, {step1_outcome} (naive baseline)")
        
        # Compare steps 2N (learning vs baseline)
        for i, (learn, base) in enumerate(zip(learning_metrics[1:], baseline_metrics), 2):
            token_improvement = base['total_tokens'] - learn['total_tokens']
            token_pct = (token_improvement / base['total_tokens'] * 100) if base['total_tokens'] > 0 else 0
            turn_improvement = base['total_turns'] - learn['total_turns']
            turn_pct = (turn_improvement / base['total_turns'] * 100) if base['total_turns'] > 0 else 0
            time_improvement = base['trace_time_ms'] - learn['trace_time_ms']
            time_pct = (time_improvement / base['trace_time_ms'] * 100) if base['trace_time_ms'] > 0 else 0
            success_improvement = learn['success_rate'] - base['success_rate']
            
            # Calculate failure counts for this step
            base_failed = 0 if base.get('overall_success', False) else 1
            learn_failed = 0 if learn.get('overall_success', False) else 1
            failure_change = base_failed - learn_failed
            
            token_direction = "" if token_improvement > 0 else "" if token_improvement < 0 else "="
            turn_direction = "" if turn_improvement > 0 else "" if turn_improvement < 0 else "="
            time_direction = "" if time_improvement > 0 else "" if time_improvement < 0 else "="
            success_direction = "" if success_improvement > 0 else "" if success_improvement < 0 else "="
            failure_direction = "" if failure_change > 0 else "" if failure_change < 0 else "="
            
            # Get final outcomes for this step
            base_outcome = self._format_final_outcome(base.get('final_outcome', 'unknown'))
            learn_outcome = self._format_final_outcome(learn.get('final_outcome', 'unknown'))
            
            print(f"  Step {i}: {base['total_tokens']}  {learn['total_tokens']} tokens ({token_direction}{abs(token_improvement)}, {token_pct:+.1f}%)")
            print(f"         {base['total_turns']}  {learn['total_turns']} turns ({turn_direction}{abs(turn_improvement)}, {turn_pct:+.1f}%)")
            print(f"         {base['trace_time_ms']}  {learn['trace_time_ms']}ms ({time_direction}{abs(time_improvement)}, {time_pct:+.1f}%)")
            print(f"         {base['success_rate']:.1f}%  {learn['success_rate']:.1f}% ({success_direction}{abs(success_improvement):.1f}%)")
            print(f"         {base_failed}  {learn_failed} failures ({failure_direction}{abs(failure_change)})")
            print(f"         {base_outcome}  {learn_outcome}")
        
        # Prioritize final outcome improvements
        if completion_improvement > 0 or gave_up_reduction > 0:
            print(f"\n BREAKTHROUGH: Sequential learning improved task completion!")
            if completion_improvement > 0:
                print(f" TASK COMPLETION: {baseline_completed}  {learning_completed} tasks completed")
            if gave_up_reduction > 0:
                print(f" REDUCED GIVE-UPS: {baseline_gave_up}  {learning_gave_up} agents gave up")
            print(f" COGNITIVE INSIGHT: Rules learned from sequential queries enabled task completion")
            print(f" KEY DIFFERENTIATOR: True cognitive learning with cumulative benefits")
        elif total_token_improvement > 0 or total_turns_improvement > 0 or total_time_improvement > 0:
            print(f"\n SUCCESS: Sequential learning demonstrated measurable improvements!")
            print(f" COGNITIVE INSIGHT: Rules learned from sequential queries improved performance")
            print(f" KEY DIFFERENTIATOR: True cognitive learning with cumulative benefits")
        else:
            print(f"\n  NOTE: No overall performance improvement detected")
            print(f"   This may indicate that the queries were too different for effective rule generalization")
        
        print(f"\n Sequential Analysis Complete!")

    def __getattr__(self, name):
        """
        Delegate all other attributes to the wrapped agent.
        """
        return getattr(self._agent, name)

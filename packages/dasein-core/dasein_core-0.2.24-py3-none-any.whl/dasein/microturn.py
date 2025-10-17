"""
Microturn enforcement system for anti-fanout rules.

This module provides real-time LLM call interception and modification
to enforce fanout prevention policies (e.g., "only 1 Summary per search").
"""

from typing import List, Dict, Tuple, Any, Optional, Set
import json
import hashlib


def has_tool_end_rules(callback_handler: Any) -> bool:
    """
    Check if any tool_end rules exist in the selected rules.
    
    Args:
        callback_handler: Callback handler with _selected_rules
        
    Returns:
        True if at least one tool_end rule exists, False otherwise
    """
    if not callback_handler or not hasattr(callback_handler, '_selected_rules'):
        return False
    
    rules = callback_handler._selected_rules or []
    for rule in rules:
        # Handle tuple format (rule, metadata)
        if isinstance(rule, tuple) and len(rule) >= 1:
            rule = rule[0]
        
        # Check target_step_type
        if isinstance(rule, dict):
            target = rule.get('target_step_type', '')
        else:
            target = getattr(rule, 'target_step_type', '')
        
        if target == 'tool_end':
            return True
    
    return False


def extract_tool_call_signatures(msg: Any) -> Dict[str, str]:
    """
    Extract tool call signatures (name + argument hash) from a message.
    
    Args:
        msg: Message object with tool_calls
        
    Returns:
        Dict mapping tool call index to signature string (e.g., "Summary_abc123")
    """
    signatures = {}
    
    if not msg or not hasattr(msg, 'tool_calls') or not msg.tool_calls:
        return signatures
    
    for idx, tc in enumerate(msg.tool_calls):
        tc_name = tc.name if hasattr(tc, 'name') else tc.get('name', '')
        
        # Extract arguments
        if hasattr(tc, 'args'):
            args = tc.args
        elif isinstance(tc, dict) and 'args' in tc:
            args = tc['args']
        else:
            args = {}
        
        # Create content hash from arguments
        try:
            # Serialize args to stable JSON string
            args_str = json.dumps(args, sort_keys=True, default=str)
            # Create short hash (first 8 chars of SHA256)
            content_hash = hashlib.sha256(args_str.encode()).hexdigest()[:8]
            signature = f"{tc_name}_{content_hash}"
        except:
            # Fallback if serialization fails
            signature = f"{tc_name}_unknown"
        
        signatures[idx] = signature
    
    return signatures


def extract_proposed_function_calls(result: Any) -> Tuple[List[str], Optional[Any]]:
    """
    Extract proposed function calls from LLM response.
    
    Args:
        result: LLM response (AIMessage, ChatResult, or LLMResult)
        
    Returns:
        Tuple of (list of function names, message object)
    """
    proposed_func_names = []
    msg = None
    
    # Case 1: Result is AIMessage directly
    if hasattr(result, 'tool_calls') or hasattr(result, 'additional_kwargs'):
        msg = result
    # Case 2: Result has generations
    elif hasattr(result, 'generations') and result.generations:
        first_gen = result.generations[0]
        # Case 2a: Generation has message
        if hasattr(first_gen, 'message'):
            msg = first_gen.message
        # Case 2b: Generation is a list (contains message)
        elif isinstance(first_gen, list) and len(first_gen) > 0:
            if hasattr(first_gen[0], 'message'):
                msg = first_gen[0].message
    
    # Extract tool calls from message
    if msg:
        # CRITICAL: Extract from tool_calls OR function_call, NOT BOTH (prevents duplicates)
        # Prefer tool_calls (modern) if available
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tc in msg.tool_calls:
                if hasattr(tc, 'name'):
                    proposed_func_names.append(tc.name)
                elif isinstance(tc, dict) and 'name' in tc:
                    proposed_func_names.append(tc['name'])
        elif hasattr(msg, 'additional_kwargs'):
            # Only check function_call if tool_calls is empty (fallback)
            func_call = msg.additional_kwargs.get('function_call')
            if func_call and isinstance(func_call, dict) and 'name' in func_call:
                proposed_func_names.append(func_call['name'])
    
    return proposed_func_names, msg


def build_execution_state_summary(callback_handler: Any) -> str:
    """
    Build a human-readable summary of all function calls made so far.
    
    Args:
        callback_handler: DaseinCallbackHandler with _function_calls_made
        
    Returns:
        Formatted string of execution state
    """
    state_summary = []
    if hasattr(callback_handler, '_function_calls_made') and callback_handler._function_calls_made:
        for fname in sorted(callback_handler._function_calls_made.keys()):
            count = len(callback_handler._function_calls_made[fname])
            if count > 0:
                state_summary.append(f"  • {fname}: {count}x")
    
    return "EXECUTION STATE (all calls made so far):\n" + "\n".join(state_summary) if state_summary else "EXECUTION STATE: No calls yet"


def create_microturn_prompt(test_rule: str, full_state: str, proposed_func_names: List[str]) -> str:
    """
    Create the prompt for the microturn LLM to decide on compliant calls.
    
    Args:
        test_rule: The rule to enforce (e.g., "max 1 Summary per search")
        full_state: Execution state summary
        proposed_func_names: List of proposed function names
        
    Returns:
        Formatted prompt string
    """
    proposed_calls_str = "\n".join([f"  {i+1}. {name}" for i, name in enumerate(proposed_func_names)])
    
    return f"""You are an anti-fanout rule enforcement system for AI agents.

RULE TO ENFORCE:
{test_rule}

{full_state}

PROPOSED TOOL CALLS (from LLM):
{proposed_calls_str}

TASK: Check if the proposed calls violate the rule.
- The rule is ONLY about Summary calls relative to tavily_search calls
- ALL other tool calls (ResearchQuestion, think_tool, ConductResearch, etc.) should PASS THROUGH unchanged
- Only remove Summary calls if they violate the ratio

EXAMPLES:
- State: tavily_search: 1x | Proposed: [ResearchQuestion] → COMPLIANT, return: ResearchQuestion
- State: tavily_search: 1x | Proposed: [Summary, Summary] → VIOLATION, return: Summary (keep only 1)
- State: tavily_search: 1x, Summary: 1x | Proposed: [Summary] → VIOLATION, return: (empty, already have 1)
- State: No calls yet | Proposed: [ResearchQuestion, think_tool] → COMPLIANT, return: ResearchQuestion, think_tool

OUTPUT FORMAT: List the compliant function names, one per line. If all are compliant, return ALL of them.

Compliant list:"""


def parse_microturn_response(microturn_response: Any) -> List[str]:
    """
    Parse the microturn LLM response to extract compliant function names.
    
    Args:
        microturn_response: LLM response object
        
    Returns:
        List of compliant function names (may be empty for total block)
    """
    compliant_response = ""
    
    if hasattr(microturn_response, 'generations') and microturn_response.generations:
        # LLMResult with generations
        first_gen = microturn_response.generations[0]
        
        # generations[0] can be a list OR a ChatGeneration
        if isinstance(first_gen, list) and len(first_gen) > 0:
            # It's a list - get first item
            msg_resp = first_gen[0].message if hasattr(first_gen[0], 'message') else first_gen[0]
        elif hasattr(first_gen, 'message'):
            # It's a ChatGeneration
            msg_resp = first_gen.message
        else:
            msg_resp = first_gen
        
        compliant_response = msg_resp.content.strip() if hasattr(msg_resp, 'content') else str(msg_resp).strip()
    elif hasattr(microturn_response, 'content'):
        # AIMessage directly
        compliant_response = microturn_response.content.strip()
    else:
        compliant_response = str(microturn_response).strip()
    
    # Parse compliant list - be lenient with parsing
    compliant_names = []
    for line in compliant_response.split('\n'):
        line = line.strip()
        # Skip empty lines, comments, and prompt echoes
        if not line or line.startswith('#') or line.startswith('Your') or line.startswith('Compliant') or line.startswith('-') or line.startswith('OUTPUT'):
            continue
        # Remove markdown backticks if present
        line = line.strip('`').strip()
        # If line looks like a function name, add it
        if any(c.isalnum() or c == '_' for c in line):
            compliant_names.append(line)
    
    return compliant_names


def modify_tool_calls_with_deadletter(
    msg: Any,
    compliant_names: List[str],
    callback_handler: Any,
    tool_result_cache: Optional[Dict[str, Any]] = None,
    tool_sigs: Optional[Dict[int, str]] = None
) -> Tuple[int, List[str]]:
    """
    Modify msg.tool_calls to redirect blocked calls to dasein_deadletter.
    
    Supports transparent deduplication: if tool_result_cache contains a result
    for a blocked call's signature, pass that cached result to dasein_deadletter
    so it can return it seamlessly (agent never knows it was blocked).
    
    Args:
        msg: Message object with tool_calls attribute
        compliant_names: List of function names that should be allowed
        callback_handler: Callback handler for state tracking
        tool_result_cache: Optional dict mapping signatures to cached results
        tool_sigs: Optional dict mapping tool call index to signature
        
    Returns:
        Tuple of (blocked_count, blocked_call_names)
    """
    if not msg or not hasattr(msg, 'tool_calls'):
        return 0, []
    
    original_tool_calls = msg.tool_calls if msg.tool_calls else []
    modified_tool_calls = []
    compliant_names_set = set(compliant_names)
    blocked_calls = []
    blocked_count = 0
    tool_result_cache = tool_result_cache or {}
    tool_sigs = tool_sigs or {}
    
    # Process each tool call: keep compliant, rewrite blocked to dead-letter
    for idx, tc in enumerate(original_tool_calls):
        tc_name = tc.name if hasattr(tc, 'name') else tc.get('name', '')
        
        # Idempotency: Never rewrite dasein_deadletter itself
        if tc_name == 'dasein_deadletter':
            modified_tool_calls.append(tc)
            continue
        
        if tc_name in compliant_names_set:
            # PASS THROUGH: Compliant call
            modified_tool_calls.append(tc)
            compliant_names_set.remove(tc_name)  # Use each name once
        else:
            # REDIRECT: Blocked call → rewrite to dasein_deadletter
            
            # Create fingerprint of original args
            try:
                args_str = json.dumps(tc.get('args', {}) if isinstance(tc, dict) else getattr(tc, 'args', {}), sort_keys=True)
                args_fingerprint = hashlib.sha256(args_str.encode()).hexdigest()[:16]
            except:
                args_fingerprint = "unknown"
            
            # Estimate tokens saved (rough: 100-500 for Summary)
            tokens_saved_est = 300 if 'summary' in tc_name.lower() else 50
            
            # Check if we have a cached result for transparent deduplication
            sig = tool_sigs.get(idx)
            cached_result = tool_result_cache.get(sig) if sig else None
            
            # Create new tool call for dasein_deadletter
            deadletter_args = {
                'original_tool': tc_name,
                'original_args_fingerprint': args_fingerprint,
                'reason_code': 'duplicate_detected' if cached_result else f"{tc_name}_blocked_by_policy",
                'policy_trace_id': getattr(callback_handler, '_run_id', 'unknown'),
                'tokens_saved_estimate': tokens_saved_est
            }
            
            # Add cached result for transparent deduplication
            if cached_result is not None:
                deadletter_args['cached_result'] = cached_result
            
            deadletter_call = {
                'name': 'dasein_deadletter',
                'args': deadletter_args,
                'id': tc.get('id') if isinstance(tc, dict) else getattr(tc, 'id', f"deadletter_{blocked_count}"),
                'type': 'tool_call'
            }
            
            # Convert dict to ToolCall object if needed
            if hasattr(tc, '__class__') and not isinstance(tc, dict):
                # Try to create same type as original
                try:
                    from langchain_core.messages import tool_call
                    deadletter_call = tool_call.ToolCall(**deadletter_call)
                except:
                    pass  # Keep as dict if conversion fails
            
            modified_tool_calls.append(deadletter_call)
            blocked_calls.append(tc_name)
            blocked_count += 1
    
    # Update with modified list (compliant + redirected)
    msg.tool_calls = modified_tool_calls
    
    return blocked_count, blocked_calls


def update_callback_state(callback_handler: Any, blocked_calls: List[str]) -> None:
    """
    Update callback handler state to reflect redirected calls.
    
    Args:
        callback_handler: DaseinCallbackHandler with _function_calls_made
        blocked_calls: List of function names that were blocked/redirected
    """
    if not callback_handler or not hasattr(callback_handler, '_function_calls_made') or not blocked_calls:
        return
    
    if 'dasein_deadletter' not in callback_handler._function_calls_made:
        callback_handler._function_calls_made['dasein_deadletter'] = []
    
    for blocked_name in blocked_calls:
        callback_handler._function_calls_made['dasein_deadletter'].append({
            'original_tool': blocked_name,
            'blocked_by': 'microturn'
        })


async def run_microturn_enforcement(
    result: Any,
    callback_handler: Any,
    self_llm: Any,
    patch_depth: Any,
    use_llm_microturn: bool = False
) -> bool:
    """
    Main microturn enforcement logic - extracted from api.py for cleaner organization.
    
    Args:
        result: LLM result to potentially modify
        callback_handler: DaseinCallbackHandler with state
        self_llm: The LLM instance (for microturn LLM call if needed)
        patch_depth: Thread-local object with seen_tool_signatures, tool_result_cache
        use_llm_microturn: Whether to use LLM-based microturn (default False, uses deterministic only)
        
    Returns:
        True if enforcement was applied, False if skipped
    """
    try:
        # Extract proposed function calls
        proposed_func_names, msg = extract_proposed_function_calls(result)
        
        if not proposed_func_names:
            return False
        
        if all(name == 'dasein_deadletter' for name in proposed_func_names):
            return False  # Already processed
        
        # Extract tool call signatures for duplicate detection
        tool_sigs = {}
        duplicates = []
        if msg:
            tool_sigs = extract_tool_call_signatures(msg)
            
            # Initialize signature tracking and result cache
            if not hasattr(patch_depth, 'seen_tool_signatures'):
                patch_depth.seen_tool_signatures = set()
            if not hasattr(patch_depth, 'tool_result_cache'):
                patch_depth.tool_result_cache = {}
            
            # Detect duplicates (immediate fanout within this response OR across turns)
            seen_in_response = set()
            for idx, sig in tool_sigs.items():
                if sig in seen_in_response or sig in patch_depth.seen_tool_signatures:
                    # Duplicate detected
                    duplicates.append((idx, sig))
            # Debug duplicate detection only if env enables it
            import os
            if os.getenv("DASEIN_DEBUG_MICROTURN", "0") == "1":
                print(f"[DASEIN][MICROTURN] 🔄 Duplicate detected: {sig}")
                else:
                    # First occurrence
                    seen_in_response.add(sig)
        
        # DETERMINISTIC DUPLICATE BLOCKING (always on)
        if duplicates and msg:
            # Keep this high-signal log behind env flag
            import os
            if os.getenv("DASEIN_DEBUG_MICROTURN", "0") == "1":
                print(f"[DASEIN][MICROTURN] Blocking {len(duplicates)} duplicate call(s)")
            blocked_count, blocked_calls = modify_tool_calls_with_deadletter(
                msg,
                [],  # No LLM-based compliant names, just mark duplicates
                duplicates,
                tool_sigs,
                patch_depth.tool_result_cache
            )
            
            if blocked_count > 0:
                update_callback_state(callback_handler, blocked_calls)
                if os.getenv("DASEIN_DEBUG_MICROTURN", "0") == "1":
                    print(f"[DASEIN][MICROTURN] ✅ Blocked {blocked_count} duplicate(s)")
                return True
        
        # LLM-BASED MICROTURN (behind flag)
        if use_llm_microturn:
            # Build prompt for microturn LLM
            full_state = build_execution_state_summary(callback_handler)
            rule = "ANTI-FANOUT RULE: Only allow 1 Summary call per search. Other tools should pass through."
            microturn_prompt = create_microturn_prompt(rule, full_state, proposed_func_names)
            
            # Call microturn LLM (stripped kwargs to force text response)
            from langchain_core.messages import HumanMessage
            if hasattr(self_llm, 'ainvoke'):
                microturn_response = await self_llm.ainvoke([HumanMessage(content=microturn_prompt)])
            else:
                microturn_response = self_llm.invoke([HumanMessage(content=microturn_prompt)])
            
            # Parse response
            compliant_names = parse_microturn_response(microturn_response)
            
            # Modify tool calls if needed
            if msg:
                blocked_count, blocked_calls = modify_tool_calls_with_deadletter(
                    msg,
                    compliant_names,
                    [],  # No duplicates here, handled above
                    tool_sigs,
                    patch_depth.tool_result_cache
                )
                
                if blocked_count > 0:
                    update_callback_state(callback_handler, blocked_calls)
                    if os.getenv("DASEIN_DEBUG_MICROTURN", "0") == "1":
                        print(f"[DASEIN][MICROTURN] ✅ LLM blocked {blocked_count} call(s): {blocked_calls}")
                    return True
        
        # No enforcement applied
        return False
        
    except Exception as e:
        # Only print on debug; otherwise fail silently
        import os
        if os.getenv("DASEIN_DEBUG_MICROTURN", "0") == "1":
            print(f"[DASEIN][MICROTURN] ⚠️ Error during enforcement: {e}")
        import traceback
        if os.getenv("DASEIN_DEBUG_MICROTURN", "0") == "1":
            traceback.print_exc()
        return False


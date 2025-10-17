"""
Trace capture functionality for Dasein.
"""

# Suppress third-party warnings triggered by pipecleaner dependencies
import warnings
warnings.filterwarnings('ignore', category=FutureWarning, message='.*torch.distributed.reduce_op.*')
warnings.filterwarnings('ignore', category=DeprecationWarning, message='.*Importing chat models from langchain.*')

import hashlib
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.callbacks.manager import CallbackManagerForToolRun
from langchain_core.tools import BaseTool


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


# DEPRECATED: Global trace store removed for thread-safety
# Traces are now stored instance-level in DaseinCallbackHandler._trace
# _TRACE: List[Dict[str, Any]] = []

# Hook cache for agent fingerprinting
_HOOK_CACHE: Dict[str, Any] = {}

# Store for modified tool inputs
_MODIFIED_TOOL_INPUTS: Dict[str, str] = {}


class DaseinToolWrapper(BaseTool):
    """Wrapper for tools that applies micro-turn modifications."""
    
    name: str = ""
    description: str = ""
    original_tool: Any = None
    callback_handler: Any = None
    
    def __init__(self, original_tool, callback_handler=None, verbose: bool = False):
        super().__init__(
            name=original_tool.name,
            description=original_tool.description
        )
        self.original_tool = original_tool
        self.callback_handler = callback_handler
        self._verbose = verbose
    
    def _vprint(self, message: str, force: bool = False):
        """Helper for verbose printing."""
        _vprint(message, self._verbose, force)
    
    def _run(self, *args, **kwargs):
        """Run the tool with micro-turn injection at execution level."""
        self._vprint(f"[DASEIN][TOOL_WRAPPER] _run called for {self.name} - VERSION 2.0")
        self._vprint(f"[DASEIN][TOOL_WRAPPER] Args: {args}")
        self._vprint(f"[DASEIN][TOOL_WRAPPER] Kwargs: {kwargs}")
        
        try:
            # Get the original input
            original_input = args[0] if args else ""
            self._vprint(f"[DASEIN][TOOL_WRAPPER] Original input: {original_input[:100]}...")
            
            # Apply micro-turn injection if we have rules
            modified_input = self._apply_micro_turn_injection(str(original_input))
            
            if modified_input != original_input:
                self._vprint(f"[DASEIN][TOOL_WRAPPER] Applied micro-turn injection for {self.name}: {original_input[:50]}... -> {modified_input[:50]}...")
                # Use modified input
                result = self.original_tool._run(modified_input, *args[1:], **kwargs)
            else:
                self._vprint(f"[DASEIN][TOOL_WRAPPER] No micro-turn injection applied for {self.name}")
                # Use original input
                result = self.original_tool._run(*args, **kwargs)
            
            # Capture the tool output in the trace
            self._vprint(f"[DASEIN][TOOL_WRAPPER] About to capture tool output for {self.name}")
            self._capture_tool_output(self.name, args, kwargs, result)
            self._vprint(f"[DASEIN][TOOL_WRAPPER] Finished capturing tool output for {self.name}")
            
            return result
            
        except Exception as e:
            self._vprint(f"[DASEIN][TOOL_WRAPPER] Exception in _run: {e}")
            import traceback
            traceback.print_exc()
            # Still try to call the original tool
            result = self.original_tool._run(*args, **kwargs)
            return result
    
    def invoke(self, input_data, config=None, **kwargs):
        """Invoke the tool with micro-turn injection."""
        # Get the original input
        original_input = str(input_data)
        
        # Apply micro-turn injection if we have rules
        modified_input = self._apply_micro_turn_injection(original_input)
        
        if modified_input != original_input:
            self._vprint(f"[DASEIN][TOOL_WRAPPER] Applied micro-turn injection for {self.name}: {original_input[:50]}... -> {modified_input[:50]}...")
            # Use modified input
            return self.original_tool.invoke(modified_input, config, **kwargs)
        else:
            # Use original input
            return self.original_tool.invoke(input_data, config, **kwargs)
    
    async def _arun(self, *args, **kwargs):
        """Async run the tool with micro-turn injection at execution level."""
        self._vprint(f"[DASEIN][TOOL_WRAPPER] _arun called for {self.name} - ASYNC VERSION")
        self._vprint(f"[DASEIN][TOOL_WRAPPER] Args: {args}")
        self._vprint(f"[DASEIN][TOOL_WRAPPER] Kwargs: {kwargs}")
        
        try:
            # Get the original input
            original_input = args[0] if args else ""
            self._vprint(f"[DASEIN][TOOL_WRAPPER] Original input: {original_input[:100]}...")
            
            # Apply micro-turn injection if we have rules
            modified_input = self._apply_micro_turn_injection(str(original_input))
            
            if modified_input != original_input:
                self._vprint(f"[DASEIN][TOOL_WRAPPER] Applied micro-turn injection for {self.name}: {original_input[:50]}... -> {modified_input[:50]}...")
                # Use modified input
                result = await self.original_tool._arun(modified_input, *args[1:], **kwargs)
            else:
                self._vprint(f"[DASEIN][TOOL_WRAPPER] No micro-turn injection applied for {self.name}")
                # Use original input
                result = await self.original_tool._arun(*args, **kwargs)
            
            # Capture the tool output in the trace
            self._vprint(f"[DASEIN][TOOL_WRAPPER] About to capture tool output for {self.name}")
            self._capture_tool_output(self.name, args, kwargs, result)
            self._vprint(f"[DASEIN][TOOL_WRAPPER] Finished capturing tool output for {self.name}")
            
            return result
            
        except Exception as e:
            self._vprint(f"[DASEIN][TOOL_WRAPPER] Exception in _arun: {e}")
            import traceback
            traceback.print_exc()
            # Still try to call the original tool
            result = await self.original_tool._arun(*args, **kwargs)
            return result
    
    async def ainvoke(self, input_data, config=None, **kwargs):
        """Async invoke the tool with micro-turn injection."""
        self._vprint(f"[DASEIN][TOOL_WRAPPER] ainvoke called for {self.name} - ASYNC VERSION")
        
        # Get the original input
        original_input = str(input_data)
        
        # Apply micro-turn injection if we have rules
        modified_input = self._apply_micro_turn_injection(original_input)
        
        if modified_input != original_input:
            self._vprint(f"[DASEIN][TOOL_WRAPPER] Applied micro-turn injection for {self.name}: {original_input[:50]}... -> {modified_input[:50]}...")
            # Use modified input
            result = await self.original_tool.ainvoke(modified_input, config, **kwargs)
        else:
            # Use original input
            result = await self.original_tool.ainvoke(input_data, config, **kwargs)
        
        return result
    
    def _apply_micro_turn_injection(self, original_input: str) -> str:
        """Apply micro-turn injection to the tool input."""
        try:
            # Check if we have a callback handler with rules and LLM
            if not self.callback_handler:
                return original_input
                
            # Normalize selected rules into Rule objects (handle (rule, metadata) tuples)
            normalized_rules = []
            for rule_meta in getattr(self.callback_handler, "_selected_rules", []) or []:
                if isinstance(rule_meta, tuple) and len(rule_meta) == 2:
                    rule_obj, _metadata = rule_meta
                else:
                    rule_obj = rule_meta
                normalized_rules.append(rule_obj)
                
            # Filter tool_start rules
            tool_rules = [r for r in normalized_rules if getattr(r, 'target_step_type', '') == "tool_start"]
            
            if not tool_rules:
                self._vprint(f"[DASEIN][MICROTURN] No tool rules selected - skipping micro-turn for {self.name}")
                return original_input
                
            # Check if any rule covers this tool
            covered_rules = [rule for rule in tool_rules 
                             if self._rule_covers_tool(rule, self.name, original_input)]
            
            if not covered_rules:
                return original_input
                
            # Fire micro-turn LLM call (use first matching rule)
            rule = covered_rules[0]
            self._vprint(f"[DASEIN][MICROTURN] rule_id={rule.id} tool={self.name}")
            
            # Create micro-turn prompt
            micro_turn_prompt = self._create_micro_turn_prompt(rule, self.name, original_input)
            
            # Execute micro-turn LLM call
            modified_input = self._execute_micro_turn_llm_call(micro_turn_prompt, original_input)
            
            self._vprint(f"[DASEIN][MICROTURN] Applied rule {rule.id}: {str(original_input)[:50]}... -> {str(modified_input)[:50]}...")
            return modified_input
            
        except Exception as e:
            self._vprint(f"[DASEIN][MICROTURN] Error in micro-turn injection: {e}")
            return original_input
    
    def _rule_covers_tool(self, rule, tool_name: str, tool_input: str) -> bool:
        """Check if a rule covers this tool call."""
        if not hasattr(rule, 'references') or not rule.references:
            return False
            
        # Check if the rule references this tool
        tools = rule.references.get('tools', [])
        return tool_name in tools
    
    def _create_micro_turn_prompt(self, rule, tool_name: str, tool_input: str) -> str:
        """Create the prompt for the micro-turn LLM call."""
        return f"""You are applying a rule to fix a tool input.

Rule: {rule.advice_text}

Tool: {tool_name}
Current Input: {tool_input}

Apply the rule to fix the input. Return only the corrected input, nothing else."""

    def _execute_micro_turn_llm_call(self, prompt: str, original_input: str) -> str:
        """Execute the actual micro-turn LLM call."""
        try:
            if not self.callback_handler or not self.callback_handler._llm:
                self._vprint(f"[DASEIN][MICROTURN] No LLM available for micro-turn call")
                return original_input

            self._vprint(f"[DASEIN][MICROTURN] Executing micro-turn LLM call")
            self._vprint(f"[DASEIN][MICROTURN] Prompt: {prompt[:200]}...")

            # Make the micro-turn LLM call
            messages = [{"role": "user", "content": prompt}]
            response = self.callback_handler._llm.invoke(messages)

            # Extract the response content
            if hasattr(response, 'content'):
                modified_input = response.content.strip()
            elif isinstance(response, str):
                modified_input = response.strip()
            else:
                modified_input = str(response).strip()

            self._vprint(f"[DASEIN][MICROTURN] LLM response: {modified_input[:100]}...")

            # 🚨 CRITICAL: Parse JSON responses with markdown fences
            if modified_input.startswith('```json') or modified_input.startswith('```'):
                try:
                    # Extract JSON from markdown fences
                    import re
                    import json
                    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', modified_input, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1)
                        parsed_json = json.loads(json_str)
                        # Convert back to the expected format
                        if isinstance(parsed_json, dict) and 'name' in parsed_json and 'args' in parsed_json:
                            modified_input = parsed_json
                            self._vprint(f"[DASEIN][MICROTURN] Parsed JSON from markdown fences: {parsed_json}")
                        else:
                            self._vprint(f"[DASEIN][MICROTURN] JSON doesn't have expected structure, using as-is")
                    else:
                        self._vprint(f"[DASEIN][MICROTURN] Could not extract JSON from markdown fences")
                except Exception as e:
                    self._vprint(f"[DASEIN][MICROTURN] Error parsing JSON: {e}")

            # Validate the response - only fallback if completely empty
            if not modified_input:
                self._vprint(f"[DASEIN][MICROTURN] LLM response empty, using original input")
                return original_input

            return modified_input

        except Exception as e:
            self._vprint(f"[DASEIN][MICROTURN] Error executing micro-turn LLM call: {e}")
            return original_input
    
    def _capture_tool_output(self, tool_name, args, kwargs, result):
        """Capture tool output in the trace."""
        try:
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
            
            # Add to LLM wrapper's trace if available
            if self.callback_handler and hasattr(self.callback_handler, '_llm') and self.callback_handler._llm:
                if hasattr(self.callback_handler._llm, '_trace'):
                    self.callback_handler._llm._trace.append(step)
                    self._vprint(f"[DASEIN][TOOL_WRAPPER] Added to LLM wrapper trace")
                else:
                    self._vprint(f"[DASEIN][TOOL_WRAPPER] LLM wrapper has no _trace attribute")
            else:
                self._vprint(f"[DASEIN][TOOL_WRAPPER] No LLM wrapper available")
            
            # Also add to callback handler's trace if it has one
            if self.callback_handler and hasattr(self.callback_handler, '_trace'):
                self.callback_handler._trace.append(step)
                self._vprint(f"[DASEIN][TOOL_WRAPPER] Added to callback handler trace")
            
            self._vprint(f"[DASEIN][TOOL_WRAPPER] Captured tool output for {tool_name}")
            self._vprint(f"[DASEIN][TOOL_WRAPPER] Output length: {len(result_str)} chars")
            self._vprint(f"[DASEIN][TOOL_WRAPPER] First 200 chars: {result_str[:200]}")
            if self.callback_handler and hasattr(self.callback_handler, '_trace'):
                self._vprint(f"[DASEIN][TOOL_WRAPPER] Callback handler trace length after capture: {len(self.callback_handler._trace)}")
            
        except Exception as e:
            self._vprint(f"[DASEIN][TOOL_WRAPPER] Error capturing tool output: {e}")


class DaseinCallbackHandler(BaseCallbackHandler):
    """
    Callback handler that captures step-by-step traces and implements rule injection.
    """
    
    def __init__(self, weights=None, llm=None, is_langgraph=False, coordinator_node=None, planning_nodes=None, verbose: bool = False, agent=None, extract_tools_fn=None):
        super().__init__()
        self._weights = weights
        self._selected_rules = []  # Rules selected for this run
        self._injection_guard = set()  # Prevent duplicate injections
        self._last_modified_prompts = []  # Store modified prompts for LLM wrapper
        self._llm = llm  # Store reference to LLM for micro-turn calls
        self._tool_name_by_run_id = {}  # Track tool names by run_id
        self._discovered_tools = set()  # Track tools discovered during execution
        self._wrapped_dynamic_tools = {}  # Cache of wrapped dynamic tools
        self._is_langgraph = is_langgraph  # Flag to skip planning rule injection for LangGraph
        self._run_number = 1  # Track which run this is (for microturn testing)
        self._coordinator_node = coordinator_node  # Coordinator node (for future targeted injection)
        self._planning_nodes = planning_nodes if planning_nodes else set()  # Planning-capable nodes (including subgraph children)
        self._current_chain_node = None  # Track current LangGraph node
        self._agent_was_recreated = False  # Track if agent was successfully recreated
        self._function_calls_made = {}  # Track function calls: {function_name: [{'step': N, 'ts': timestamp}]}
        self._trace = []  # Instance-level trace storage (not global) for thread-safety
        self._verbose = verbose
        self._start_times = {}  # Track start times for duration calculation: {step_index: datetime}
        self._agent = agent  # CRITICAL: Reference to agent for runtime tool extraction
        self._extract_tools_fn = extract_tools_fn  # Function to extract tools
        self._runtime_tools_extracted = False  # Flag to extract tools only once during execution
        self._compiled_tools_metadata = []  # Store extracted tools
        self._pipecleaner_embedding_model = None  # Cache embedding model for this run
        self._current_tool_name = None  # Track currently executing tool for hotpath deduplication
        self._last_reset_ts = None  # Debounce guard for reset_run_state()
        
        # Generate stable run_id for corpus deduplication
        import uuid
        self.run_id = str(uuid.uuid4())
        
        self._vprint(f"[DASEIN][CALLBACK] Initialized callback handler (LangGraph: {is_langgraph}, run_id: {self.run_id[:8]})")
        if coordinator_node:
            self._vprint(f"[DASEIN][CALLBACK] Coordinator: {coordinator_node}")
        if planning_nodes:
            self._vprint(f"[DASEIN][CALLBACK] Planning nodes: {planning_nodes}")
        self._vprint(f"[DASEIN][CALLBACK] Dynamic tool detection enabled (tools discovered at runtime)")
    
    def _vprint(self, message: str, force: bool = False):
        """Helper for verbose printing."""
        _vprint(message, self._verbose, force)
    
    def reset_run_state(self):
        """Reset state that should be cleared between runs."""
        # Debounce: suppress duplicate rapid invocations (e.g., from multiple callers in same tick)
        try:
            from time import monotonic
            now = monotonic()
            if getattr(self, '_last_reset_ts', None) is not None and (now - self._last_reset_ts) < 0.05:
                # Too soon since last reset; skip
                return
            self._last_reset_ts = now
        except Exception:
            pass
        # Optional debug: print caller stack to trace root cause of unexpected resets
        try:
            import os, traceback
            if os.getenv("DASEIN_DEBUG_RESET", "0") == "1":
                stack_excerpt = ''.join(traceback.format_stack(limit=8))
                self._vprint("[DASEIN][CALLBACK] reset_run_state() caller stack (set DASEIN_DEBUG_RESET=0 to disable):\n" + stack_excerpt, True)
        except Exception:
            pass
        self._function_calls_made = {}
        self._injection_guard = set()
        self._trace = []  # Clear instance trace
        self._start_times = {}  # Clear start times
        self._run_number = getattr(self, '_run_number', 1) + 1  # Increment run number
        self._vprint(f"[DASEIN][CALLBACK] Reset run state (trace, function calls, injection guard, and start times cleared) - now on RUN {self._run_number}")
    
    def get_compiled_tools_summary(self):
        """Return 1-line summary of extracted tools."""
        if not self._compiled_tools_metadata:
            return None
        # Group by node
        by_node = {}
        for tool in self._compiled_tools_metadata:
            node = tool.get('node', 'unknown')
            if node not in by_node:
                by_node[node] = []
            by_node[node].append(tool['name'])
        # Format as: node1:[tool1,tool2] node2:[tool3]
        parts = [f"{node}:[{','.join(tools)}]" for node, tools in sorted(by_node.items())]
        return f"{len(self._compiled_tools_metadata)} tools extracted: {' '.join(parts)}"
    
    def _patch_tools_for_node(self, node_name: str):
        """
        Patch tool objects for a specific node when they're discovered at runtime.
        
        Called from on_llm_start when tools are detected for a node.
        """
        try:
            self._vprint(f"\n{'='*70}")
            self._vprint(f"[DASEIN][TOOL_PATCH] 🔧 Patching tools for node: {node_name}")
            self._vprint(f"{'='*70}")
            
            from .wrappers import patch_tool_instance
            
            # Track patched tools to avoid double-patching
            if not hasattr(self, '_patched_tools'):
                self._patched_tools = set()
                self._vprint(f"[DASEIN][TOOL_PATCH] Initialized patched tools tracker")
            
            # Find the actual tool objects for this node in the agent graph
            self._vprint(f"[DASEIN][TOOL_PATCH] Searching for tool objects in node '{node_name}'...")
            tool_objects = self._find_tool_objects_for_node(node_name)
            
            if not tool_objects:
                self._vprint(f"[DASEIN][TOOL_PATCH] ⚠️  No tool objects found for node '{node_name}'")
                self._vprint(f"{'='*70}\n")
                return
            
            self._vprint(f"[DASEIN][TOOL_PATCH] ✓ Found {len(tool_objects)} tool object(s)")
            
            # Patch each tool
            patched_count = 0
            for i, tool_obj in enumerate(tool_objects, 1):
                tool_name = getattr(tool_obj, 'name', 'unknown')
                tool_type = type(tool_obj).__name__
                tool_id = f"{node_name}:{tool_name}"
                
                self._vprint(f"[DASEIN][TOOL_PATCH] [{i}/{len(tool_objects)}] Tool: '{tool_name}' (type: {tool_type})")
                
                if tool_id in self._patched_tools:
                    self._vprint(f"[DASEIN][TOOL_PATCH]   ⏭️  Already patched, skipping")
                else:
                    self._vprint(f"[DASEIN][TOOL_PATCH]   🔨 Patching...")
                    if patch_tool_instance(tool_obj, self):
                        self._patched_tools.add(tool_id)
                        patched_count += 1
                        self._vprint(f"[DASEIN][TOOL_PATCH]   ✅ Successfully patched '{tool_name}'")
                    else:
                        self._vprint(f"[DASEIN][TOOL_PATCH]   ❌ Failed to patch '{tool_name}'")
            
            self._vprint(f"[DASEIN][TOOL_PATCH] Summary: Patched {patched_count}/{len(tool_objects)} tools")
            self._vprint(f"[DASEIN][TOOL_PATCH] Total tools patched so far: {len(self._patched_tools)}")
            self._vprint(f"{'='*70}\n")
        
        except Exception as e:
            self._vprint(f"[DASEIN][TOOL_PATCH] ❌ ERROR patching tools for node {node_name}: {e}")
            import traceback
            traceback.print_exc()
            self._vprint(f"{'='*70}\n")
    
    def _search_node_recursively(self, node_name: str, nodes: dict, depth: int = 0) -> list:
        """Recursively search for a node by name in graphs and subgraphs."""
        indent = "  " * depth
        tool_objects = []
        
        for parent_name, parent_node in nodes.items():
            if parent_name.startswith('__'):
                continue
            
            print(f"[DASEIN][TOOL_PATCH]{indent}   Checking node: {parent_name}")
            print(f"[DASEIN][TOOL_PATCH]{indent}     Node type: {type(parent_node).__name__}")
            print(f"[DASEIN][TOOL_PATCH]{indent}     Has .data: {hasattr(parent_node, 'data')}")
            if hasattr(parent_node, 'data'):
                print(f"[DASEIN][TOOL_PATCH]{indent}     .data type: {type(parent_node.data).__name__}")
                print(f"[DASEIN][TOOL_PATCH]{indent}     .data has .nodes: {hasattr(parent_node.data, 'nodes')}")
            
            # Check if this parent has a subgraph
            if hasattr(parent_node, 'data') and hasattr(parent_node.data, 'nodes'):
                print(f"[DASEIN][TOOL_PATCH]{indent}     Has subgraph!")
                try:
                    subgraph = parent_node.data.get_graph()
                    sub_nodes = subgraph.nodes
                    print(f"[DASEIN][TOOL_PATCH]{indent}     Subgraph nodes: {list(sub_nodes.keys())}")
                    
                    # Check if target node is in this subgraph
                    if node_name in sub_nodes:
                        print(f"[DASEIN][TOOL_PATCH]{indent}     ✓ Found '{node_name}' in subgraph!")
                        target_node = sub_nodes[node_name]
                        if hasattr(target_node, 'node'):
                            actual_node = target_node.node
                            tool_objects = self._extract_tools_from_node_object(actual_node)
                            if tool_objects:
                                return tool_objects
                    
                    # Not found here, recurse deeper into this subgraph
                    print(f"[DASEIN][TOOL_PATCH]{indent}     Recursing into subgraph nodes...")
                    tool_objects = self._search_node_recursively(node_name, sub_nodes, depth + 1)
                    if tool_objects:
                        return tool_objects
                        
                except Exception as e:
                    print(f"[DASEIN][TOOL_PATCH]{indent}     Error: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"[DASEIN][TOOL_PATCH]{indent}     No subgraph")
        
        return tool_objects
    
    def _find_tool_objects_for_node(self, node_name: str):
        """Find actual Python tool objects for a given node."""
        tool_objects = []
        
        try:
            if not hasattr(self._agent, 'get_graph'):
                print(f"[DASEIN][TOOL_PATCH]   Agent has no get_graph method")
                return tool_objects
            
            graph = self._agent.get_graph()
            nodes = graph.nodes
            node_names = list(nodes.keys())
            print(f"[DASEIN][TOOL_PATCH]   Graph has {len(nodes)} nodes: {node_names}")
            
            # Check if node_name contains a dot (subgraph notation like "research_supervisor.ConductResearch")
            if '.' in node_name:
                print(f"[DASEIN][TOOL_PATCH]   Node is subgraph: {node_name}")
                parent_name, sub_name = node_name.split('.', 1)
                parent_node = nodes.get(parent_name)
                
                if parent_node and hasattr(parent_node, 'data'):
                    print(f"[DASEIN][TOOL_PATCH]   Found parent node, getting subgraph...")
                    subgraph = parent_node.data.get_graph()
                    sub_nodes = subgraph.nodes
                    print(f"[DASEIN][TOOL_PATCH]   Subgraph has {len(sub_nodes)} nodes")
                    target_node = sub_nodes.get(sub_name)
                    
                    if target_node and hasattr(target_node, 'node'):
                        print(f"[DASEIN][TOOL_PATCH]   Found target subnode, extracting tools...")
                        actual_node = target_node.node
                        tool_objects = self._extract_tools_from_node_object(actual_node)
                    else:
                        print(f"[DASEIN][TOOL_PATCH]   ⚠️  Subnode not found or has no .node attribute")
                else:
                    print(f"[DASEIN][TOOL_PATCH]   ⚠️  Parent node not found or has no .data attribute")
            else:
                # Top-level node
                print(f"[DASEIN][TOOL_PATCH]   Node is top-level: {node_name}")
                target_node = nodes.get(node_name)
                
                if target_node:
                    print(f"[DASEIN][TOOL_PATCH]   Found node, checking for .node attribute...")
                    if hasattr(target_node, 'node'):
                        print(f"[DASEIN][TOOL_PATCH]   Has .node attribute, extracting tools...")
                        actual_node = target_node.node
                        tool_objects = self._extract_tools_from_node_object(actual_node)
                    else:
                        print(f"[DASEIN][TOOL_PATCH]   ⚠️  Node has no .node attribute")
                else:
                    # Not found as top-level, search in subgraphs
                    print(f"[DASEIN][TOOL_PATCH]   ⚠️  Node '{node_name}' not found in top-level graph")
                    print(f"[DASEIN][TOOL_PATCH]   Searching in subgraphs...")
                    
                    # Recursively search all subgraphs
                    tool_objects = self._search_node_recursively(node_name, nodes)
                    
                    if not tool_objects:
                        print(f"[DASEIN][TOOL_PATCH]   ⚠️  Node '{node_name}' not found in any subgraph")
        
        except Exception as e:
            print(f"[DASEIN][TOOL_PATCH]   ❌ Exception while finding tools: {e}")
            import traceback
            traceback.print_exc()
        
        return tool_objects
    
    def _extract_tools_from_node_object(self, node_obj):
        """Extract tool objects from a node object."""
        tools = []
        
        print(f"[DASEIN][TOOL_PATCH]     Checking node_obj type: {type(node_obj).__name__}")
        
        # Check tools_by_name
        if hasattr(node_obj, 'tools_by_name'):
            print(f"[DASEIN][TOOL_PATCH]     ✓ Has tools_by_name with {len(node_obj.tools_by_name)} tools")
            tools.extend(node_obj.tools_by_name.values())
        else:
            print(f"[DASEIN][TOOL_PATCH]     ✗ No tools_by_name")
        
        # Check runnable.tools
        if hasattr(node_obj, 'runnable'):
            print(f"[DASEIN][TOOL_PATCH]     ✓ Has runnable")
            if hasattr(node_obj.runnable, 'tools'):
                print(f"[DASEIN][TOOL_PATCH]       ✓ runnable.tools exists")
                runnable_tools = node_obj.runnable.tools
                if callable(runnable_tools):
                    print(f"[DASEIN][TOOL_PATCH]       runnable.tools is callable, calling...")
                    try:
                        runnable_tools = runnable_tools()
                        print(f"[DASEIN][TOOL_PATCH]       Got {len(runnable_tools) if isinstance(runnable_tools, list) else 1} tool(s)")
                    except Exception as e:
                        print(f"[DASEIN][TOOL_PATCH]       ❌ Failed to call: {e}")
                if isinstance(runnable_tools, list):
                    tools.extend(runnable_tools)
                elif runnable_tools:
                    tools.append(runnable_tools)
            else:
                print(f"[DASEIN][TOOL_PATCH]       ✗ No runnable.tools")
        else:
            print(f"[DASEIN][TOOL_PATCH]     ✗ No runnable")
        
        # Check bound.tools
        if hasattr(node_obj, 'bound'):
            print(f"[DASEIN][TOOL_PATCH]     ✓ Has bound")
            if hasattr(node_obj.bound, 'tools'):
                print(f"[DASEIN][TOOL_PATCH]       ✓ bound.tools exists")
                bound_tools = node_obj.bound.tools
                if isinstance(bound_tools, list):
                    print(f"[DASEIN][TOOL_PATCH]       Got {len(bound_tools)} tool(s)")
                    tools.extend(bound_tools)
                elif bound_tools:
                    print(f"[DASEIN][TOOL_PATCH]       Got 1 tool")
                    tools.append(bound_tools)
            else:
                print(f"[DASEIN][TOOL_PATCH]       ✗ No bound.tools")
        else:
            print(f"[DASEIN][TOOL_PATCH]     ✗ No bound")
        
        # Check steps
        if hasattr(node_obj, 'steps'):
            print(f"[DASEIN][TOOL_PATCH]     ✓ Has steps ({len(node_obj.steps)})")
            for i, step in enumerate(node_obj.steps):
                if hasattr(step, 'tools_by_name'):
                    print(f"[DASEIN][TOOL_PATCH]       ✓ Step {i} has tools_by_name with {len(step.tools_by_name)} tools")
                    tools.extend(step.tools_by_name.values())
                    break
        else:
            print(f"[DASEIN][TOOL_PATCH]     ✗ No steps")
        
        print(f"[DASEIN][TOOL_PATCH]     Total tools extracted: {len(tools)}")
        
        return tools
    
    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        *,
        run_id: str = None,
        parent_run_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Called when an LLM starts running."""
        model_name = serialized.get("name", "unknown") if serialized else "unknown"
        
        # PIPECLEANER: Intercept Summary LLM calls
        tools_in_call = None
        if 'invocation_params' in kwargs:
            tools_in_call = kwargs['invocation_params'].get('tools') or kwargs['invocation_params'].get('functions')
        
        if tools_in_call:
            tool_names = [t.get('name') or t.get('function', {}).get('name', 'unknown') for t in tools_in_call]
            
            if 'Summary' in tool_names:
                # NOTE: Deduplication now happens in the HOT PATH (monkey-patched LLM methods)
                # This callback is just for tracking, not deduplication
                pass
                
            if False and 'Summary' in tool_names:  # DISABLED: Deduplication moved to hotpath
                # Check if run-scoped corpus is enabled (has filter search rules)
                has_filter_rules = False
                if hasattr(self, '_selected_rules'):
                    from .pipecleaner import _find_filter_search_rules
                    filter_rules = _find_filter_search_rules('summary', self._selected_rules)
                    has_filter_rules = len(filter_rules) > 0
                
                if not has_filter_rules:
                    # Silent fail - no corpus deduplication if no rules
                    pass
                else:
                    # Only print when we actually have rules and will deduplicate
                    print(f"[CORPUS] 📥 Summary LLM detected with {len(prompts)} prompts")
                    # Re-entrancy guard: prevent nested calls from corrupting state
                    from contextvars import ContextVar
                    if not hasattr(DaseinCallbackHandler, '_in_corpus_processing'):
                        DaseinCallbackHandler._in_corpus_processing = ContextVar('in_corpus', default=False)
                        DaseinCallbackHandler._reentrancy_count = 0
                    
                    if DaseinCallbackHandler._in_corpus_processing.get():
                        # Already processing corpus in this call stack, fail-open
                        DaseinCallbackHandler._reentrancy_count += 1
                        print(f"[CORPUS] ⚠️  Re-entrancy detected #{DaseinCallbackHandler._reentrancy_count}, skipping nested call")
                        return
                    
                    # Set re-entrancy guard
                    token = DaseinCallbackHandler._in_corpus_processing.set(True)
                    
                    try:
                        # Get or create run-scoped corpus
                        from .pipecleaner import get_or_create_corpus
                        import threading
                        corpus = get_or_create_corpus(self.run_id, verbose=self._verbose)
                        
                        # Module-level lock for atomic snapshot/swap (shared across all instances)
                        if not hasattr(DaseinCallbackHandler, '_prompts_lock'):
                            DaseinCallbackHandler._prompts_lock = threading.Lock()
                        
                        # STEP 1: Snapshot under lock (atomic read, NEVER iterate live dict)
                        with DaseinCallbackHandler._prompts_lock:
                            try:
                                snapshot = tuple(prompts)  # Immutable snapshot, safe to iterate
                            except RuntimeError:
                                print(f"[CORPUS] ⚠️  Skipping (prompts being iterated)")
                                return
                    
                        # STEP 2: Process outside lock (no contention)
                        cleaned_prompts = []
                        total_original_chars = 0
                        total_cleaned_chars = 0
                        total_original_tokens_est = 0
                        total_cleaned_tokens_est = 0
                        
                        for i, prompt in enumerate(snapshot):
                            prompt_str = str(prompt)
                            
                            # Skip if too short
                            if len(prompt_str) < 2500:
                                cleaned_prompts.append(prompt_str)
                                continue
                            
                            # Track original
                            original_chars = len(prompt_str)
                            original_tokens_est = original_chars // 4  # Rough estimate: 4 chars/token
                            total_original_chars += original_chars
                            total_original_tokens_est += original_tokens_est
                            
                            # Split: first 2000 chars (system prompt) + rest (content to dedupe)
                            system_part = prompt_str[:2000]
                            content_part = prompt_str[2000:]
                            
                            # Generate unique prompt_id
                            import hashlib
                            prompt_id = f"p{i}_{hashlib.md5(content_part[:100].encode()).hexdigest()[:8]}"
                            
                            # Enqueue into corpus (barrier will handle batching, blocks until ready)
                            # Call synchronous enqueue (will block until batch is processed, then released sequentially)
                            deduplicated_content = corpus.enqueue_prompt(prompt_id, content_part)
                            
                            # Reassemble
                            cleaned_prompt = system_part + deduplicated_content
                            
                            # Track cleaned
                            cleaned_chars = len(cleaned_prompt)
                            cleaned_tokens_est = cleaned_chars // 4
                            total_cleaned_chars += cleaned_chars
                            total_cleaned_tokens_est += cleaned_tokens_est
                            
                            reduction_pct = 100*(original_chars-cleaned_chars)//original_chars if original_chars > 0 else 0
                            # Always show reduction results (key metric)
                            print(f"[🧹 CORPUS] Prompt {prompt_id}: {original_chars} → {cleaned_chars} chars ({reduction_pct}% saved)")
                            cleaned_prompts.append(cleaned_prompt)
                        
                        # Store token delta for later adjustment in on_llm_end
                        if total_original_tokens_est > 0:
                            tokens_saved = total_original_tokens_est - total_cleaned_tokens_est
                            if not hasattr(self, '_corpus_token_savings'):
                                self._corpus_token_savings = {}
                            self._corpus_token_savings[run_id] = tokens_saved
                            print(f"[🔬 TOKEN TRACKING] Pre-prune: {total_original_chars} chars (~{total_original_tokens_est} tokens)")
                            print(f"[🔬 TOKEN TRACKING] Post-prune: {total_cleaned_chars} chars (~{total_cleaned_tokens_est} tokens)")
                            print(f"[🔬 TOKEN TRACKING] Estimated savings: ~{tokens_saved} tokens ({100*tokens_saved//total_original_tokens_est if total_original_tokens_est > 0 else 0}%)")
                            print(f"[🔬 TOKEN TRACKING] Stored savings for run_id={str(run_id)[:8]} to adjust on_llm_end")
                        
                        # STEP 3: Atomic swap under lock (copy-on-write, no in-place mutation)
                        print(f"[🔬 CORPUS DEBUG] About to swap prompts - have {len(cleaned_prompts)} cleaned prompts")
                        with DaseinCallbackHandler._prompts_lock:
                            try:
                                print(f"[🔬 CORPUS DEBUG] Inside lock, swapping...")
                                # Atomic slice assignment (replaces entire contents in one operation)
                                prompts[:] = cleaned_prompts
                                # CRITICAL: Update _last_modified_prompts so DaseinLLMWrapper sees deduplicated prompts
                                self._last_modified_prompts = cleaned_prompts
                                print(f"[🔬 CORPUS] ✅ Updated _last_modified_prompts with {len(cleaned_prompts)} deduplicated prompts")
                            except RuntimeError as e:
                                print(f"[CORPUS] ⚠️  Could not swap prompts (framework collision): {e}")
                            except Exception as e:
                                print(f"[CORPUS] ⚠️  Unexpected error swapping: {e}")
                                import traceback
                                traceback.print_exc()
                    finally:
                        # Always reset re-entrancy guard
                        DaseinCallbackHandler._in_corpus_processing.reset(token)
        
        # DEBUG: Print run context
        # print(f"🔧 [LLM_START DEBUG] run_id: {run_id}, parent: {parent_run_id}")
        
        # 🎯 CRITICAL: Track current node from kwargs metadata FIRST (needed for tool extraction)
        if self._is_langgraph and 'metadata' in kwargs and isinstance(kwargs['metadata'], dict):
            if 'langgraph_node' in kwargs['metadata']:
                node_name = kwargs['metadata']['langgraph_node']
                self._current_chain_node = node_name
        
        # CRITICAL: Extract tools incrementally from each tool-bearing call
        # Tools are bound node-by-node as they're invoked
        if self._is_langgraph and self._agent:
            # Check if THIS call has tools (signal that THIS node's tools are now bound)
            tools_in_call = None
            if 'invocation_params' in kwargs:
                tools_in_call = kwargs['invocation_params'].get('tools') or kwargs['invocation_params'].get('functions')
            elif 'tools' in kwargs:
                tools_in_call = kwargs['tools']
            elif 'functions' in kwargs:
                tools_in_call = kwargs['functions']
            
            if tools_in_call:
                node_name = self._current_chain_node or 'unknown'
                
                # Extract tool names from the schemas
                tool_names = []
                for tool in tools_in_call:
                    name = tool.get('name') or tool.get('function', {}).get('name', 'unknown')
                    tool_names.append(name)
                
                # print(f"🔧 [TOOLS DETECTED] Node '{node_name}' has {len(tool_names)} tools: {tool_names}")  # Commented out - too noisy
                
                # Check if we've already extracted tools for this node
                existing_nodes = {t.get('node') for t in self._compiled_tools_metadata}
                if node_name not in existing_nodes:
                    try:
                        # Extract tools from this specific call (provider-resolved schemas)
                        for tool in tools_in_call:
                            tool_meta = {
                                'name': tool.get('name') or tool.get('function', {}).get('name', 'unknown'),
                                'description': tool.get('description') or tool.get('function', {}).get('description', ''),
                                'node': node_name
                            }
                            
                            # Get args schema
                            if 'parameters' in tool:
                                tool_meta['args_schema'] = tool['parameters']
                            elif 'function' in tool and 'parameters' in tool['function']:
                                tool_meta['args_schema'] = tool['function']['parameters']
                            else:
                                tool_meta['args_schema'] = {}
                            
                            self._compiled_tools_metadata.append(tool_meta)
                        
                        # print(f"🔧 [TOOLS METADATA] Extracted metadata for {len(tool_names)} tools from node '{node_name}'")  # Commented out - too noisy
                    except Exception as e:
                        print(f"🔧 [TOOLS ERROR] Failed to extract metadata: {e}")
                        pass  # Silently fail
                # else:
                    # print(f"🔧 [TOOLS SKIP] Already extracted tools for node '{node_name}'")  # Commented out - too noisy
        
        # Inject rules if applicable
        modified_prompts = self._inject_rule_if_applicable("llm_start", model_name, prompts)
        
        # Store the modified prompts for the LLM wrapper to use
        self._last_modified_prompts = modified_prompts
        
        # Note: Pipecleaner deduplication now happens at ToolExecutor level (see wrappers.py)
        
        # 🚨 OPTIMIZED: For LangGraph, check if kwargs contains 'invocation_params' with messages
        # Extract the most recent message instead of full history
        # Use from_end=True to capture the END of system prompts (where user's actual query is)
        if 'invocation_params' in kwargs and 'messages' in kwargs['invocation_params']:
            args_excerpt = self._extract_recent_message({'messages': kwargs['invocation_params']['messages']})
        else:
            args_excerpt = self._excerpt(" | ".join(modified_prompts), from_end=True)
        
        # GNN-related fields
        step_index = len(self._trace)
        
        # Track which rules triggered at this step (llm_start rules)
        rule_triggered_here = []
        if hasattr(self, '_selected_rules') and self._selected_rules:
            for rule_meta in self._selected_rules:
                if isinstance(rule_meta, tuple) and len(rule_meta) == 2:
                    rule_obj, _metadata = rule_meta
                else:
                    rule_obj = rule_meta
                target_step_type = getattr(rule_obj, 'target_step_type', '')
                if target_step_type in ['llm_start', 'chain_start']:
                    rule_triggered_here.append(getattr(rule_obj, 'id', 'unknown'))
        
        # Record start time for duration calculation
        start_time = datetime.now()
        self._start_times[step_index] = start_time
        
        step = {
            "step_type": "llm_start",
            "tool_name": model_name,
            "args_excerpt": args_excerpt,
            "outcome": "",
            "ts": start_time.isoformat(),
            "run_id": None,
            "parent_run_id": None,
            "node": self._current_chain_node,  # LangGraph node name (if available)
            # GNN step-level fields
            "step_index": step_index,
            "rule_triggered_here": rule_triggered_here,
        }
        self._trace.append(step)
        # self._vprint(f"[DASEIN][CALLBACK] Captured llm_start: {len(_TRACE)} total steps")  # Commented out - too noisy
    
    def on_llm_end(
        self,
        response: Any,
        **kwargs: Any,
    ) -> None:
        """Called when an LLM ends running."""
        outcome = ""
        try:
            # Debug: Print ALL available data to see what we're getting
            # print(f"[DEBUG] on_llm_end called")
            # print(f"  response type: {type(response)}")
            # print(f"  kwargs keys: {kwargs.keys()}")
            
            # Try multiple extraction strategies
            # Strategy 1: Standard LangChain LLMResult structure
            if hasattr(response, 'generations') and response.generations:
                if len(response.generations) > 0:
                    first_gen = response.generations[0]
                    if isinstance(first_gen, list) and len(first_gen) > 0:
                        generation = first_gen[0]
                    else:
                        generation = first_gen
                    
                    # Try multiple content fields
                    if hasattr(generation, 'text') and generation.text:
                        outcome = self._excerpt(generation.text)
                    elif hasattr(generation, 'message'):
                        if hasattr(generation.message, 'content'):
                            outcome = self._excerpt(generation.message.content)
                        elif hasattr(generation.message, 'text'):
                            outcome = self._excerpt(generation.message.text)
                    elif hasattr(generation, 'content'):
                        outcome = self._excerpt(generation.content)
                    else:
                        outcome = self._excerpt(str(generation))
            
            # Strategy 2: Check if response itself has content
            elif hasattr(response, 'content'):
                outcome = self._excerpt(response.content)
            
            # Strategy 3: Check kwargs for output/response
            elif 'output' in kwargs:
                outcome = self._excerpt(str(kwargs['output']))
            elif 'result' in kwargs:
                outcome = self._excerpt(str(kwargs['result']))
            
            # Fallback
            if not outcome:
                outcome = self._excerpt(str(response))
            
            # Debug: Warn if still empty
            if not outcome or len(outcome) == 0:
                self._vprint(f"[DASEIN][CALLBACK] WARNING: on_llm_end got empty outcome!")
                print(f"  Response: {str(response)[:1000]}")
                print(f"  kwargs keys: {list(kwargs.keys())}")
                
        except (AttributeError, IndexError, TypeError) as e:
            self._vprint(f"[DASEIN][CALLBACK] Error in on_llm_end: {e}")
            outcome = self._excerpt(str(response))
        
        # # 🎯 PRINT FULL LLM OUTPUT (RAW, UNTRUNCATED) - COMMENTED OUT FOR TESTING
        # node_name = getattr(self, '_current_chain_node', 'agent')
        # run_number = getattr(self, '_run_number', 1)
        # print(f"\n{'='*80}")
        # print(f"[DASEIN][LLM_END] RUN {run_number} | Node: {node_name}")
        # print(f"{'='*80}")
        # print(f"FULL OUTPUT:\n{str(response)}")
        # print(f"{'='*80}\n")
        
        # 🎯 CRITICAL: Extract function calls for state tracking (agent-agnostic)
        try:
            if hasattr(response, 'generations') and response.generations:
                first_gen = response.generations[0]
                if isinstance(first_gen, list) and len(first_gen) > 0:
                    generation = first_gen[0]
                else:
                    generation = first_gen
                
                # Check for function_call in message additional_kwargs
                if hasattr(generation, 'message') and hasattr(generation.message, 'additional_kwargs'):
                    func_call = generation.message.additional_kwargs.get('function_call')
                    if func_call and isinstance(func_call, dict) and 'name' in func_call:
                        func_name = func_call['name']
                        step_num = len(self._trace)
                        
                        # Extract arguments and create preview
                        args_str = func_call.get('arguments', '')
                        preview = ''
                        if args_str and len(args_str) > 0:
                            # Take first 100 chars as preview
                            preview = args_str[:100].replace('\n', ' ').replace('\r', '')
                            if len(args_str) > 100:
                                preview += '...'
                        
                        call_info = {
                            'step': step_num,
                            'ts': datetime.now().isoformat(),
                            'preview': preview
                        }
                        
                        if func_name not in self._function_calls_made:
                            self._function_calls_made[func_name] = []
                        self._function_calls_made[func_name].append(call_info)
                        
                        # 🔥 HOTPATH: Set current tool name for next LLM call (which will be inside the tool)
                        self._current_tool_name = func_name
                        
                        self._vprint(f"[DASEIN][STATE] Tracked function call: {func_name} (count: {len(self._function_calls_made[func_name])})")
        except Exception as e:
            pass  # Silently skip if function call extraction fails
        
        # Extract token usage from response metadata
        input_tokens = 0
        output_tokens = 0
        try:
            # Try LangChain's standard llm_output field
            if hasattr(response, 'llm_output') and response.llm_output:
                llm_output = response.llm_output
                # Different providers use different field names
                if 'token_usage' in llm_output:
                    usage = llm_output['token_usage']
                    input_tokens = usage.get('prompt_tokens', 0) or usage.get('input_tokens', 0)
                    output_tokens = usage.get('completion_tokens', 0) or usage.get('output_tokens', 0)
                elif 'usage_metadata' in llm_output:
                    usage = llm_output['usage_metadata']
                    input_tokens = usage.get('input_tokens', 0) or usage.get('prompt_tokens', 0)
                    output_tokens = usage.get('output_tokens', 0) or usage.get('completion_tokens', 0)
            
            if (input_tokens == 0 and output_tokens == 0) and hasattr(response, 'generations') and response.generations:
                first_gen = response.generations[0]
                if isinstance(first_gen, list) and len(first_gen) > 0:
                    gen = first_gen[0]
                else:
                    gen = first_gen
                
                # Check message.usage_metadata (Google GenAI stores it here!)
                if hasattr(gen, 'message') and hasattr(gen.message, 'usage_metadata'):
                    usage = gen.message.usage_metadata
                    input_tokens = usage.get('input_tokens', 0)
                    output_tokens = usage.get('output_tokens', 0)
                
                # Fallback: Check generation_info
                elif hasattr(gen, 'generation_info') and gen.generation_info:
                    gen_info = gen.generation_info
                    if 'usage_metadata' in gen_info:
                        usage = gen_info['usage_metadata']
                        input_tokens = usage.get('prompt_token_count', 0) or usage.get('input_tokens', 0)
                        output_tokens = usage.get('candidates_token_count', 0) or usage.get('output_tokens', 0)
            
            # Check if we have stored savings from corpus deduplication and adjust tokens
            current_run_id = kwargs.get('run_id', None)
            if current_run_id and hasattr(self, '_corpus_token_savings') and current_run_id in self._corpus_token_savings:
                tokens_saved = self._corpus_token_savings[current_run_id]
                # Adjust input tokens to reflect deduplication savings
                if input_tokens > 0:
                    # If provider count is much larger than saved estimate, LLM saw original prompts
                    if abs(input_tokens - tokens_saved) >= input_tokens * 0.3:
                        input_tokens = max(0, input_tokens - tokens_saved)
                # Clean up
                del self._corpus_token_savings[current_run_id]
            
            # Log if we got tokens
            # if input_tokens > 0 or output_tokens > 0:
            #     self._vprint(f"[DASEIN][TOKENS] Captured: {input_tokens} in, {output_tokens} out")
                    
        except Exception as e:
            # Print error for debugging
            self._vprint(f"[DASEIN][CALLBACK] Error extracting tokens: {e}")
            import traceback
            traceback.print_exc()
        
        # GNN-related fields: compute tokens_delta
        step_index = len(self._trace)
        tokens_delta = 0
        # Find previous step with tokens_output to compute delta
        for prev_step in reversed(self._trace):
            if 'tokens_output' in prev_step and prev_step['tokens_output'] > 0:
                tokens_delta = output_tokens - prev_step['tokens_output']
                break
        
        # Calculate duration_ms by matching with corresponding llm_start
        duration_ms = 0
        for i in range(len(self._trace) - 1, -1, -1):
            if self._trace[i].get('step_type') == 'llm_start':
                # Found the matching llm_start
                if i in self._start_times:
                    start_time = self._start_times[i]
                    end_time = datetime.now()
                    duration_ms = int((end_time - start_time).total_seconds() * 1000)
                    # Update the llm_start step with duration_ms
                    self._trace[i]['duration_ms'] = duration_ms
                break
        
        step = {
            "step_type": "llm_end",
            "tool_name": "",
            "args_excerpt": "",
            "outcome": self._excerpt(outcome, max_len=1000),  # Truncate to 1000 chars
            "ts": datetime.now().isoformat(),
            "run_id": None,
            "parent_run_id": None,
            "tokens_input": input_tokens,
            "tokens_output": output_tokens,
            "node": self._current_chain_node,  # LangGraph node name (if available)
            # GNN step-level fields
            "step_index": step_index,
            "tokens_delta": tokens_delta,
            "duration_ms": duration_ms,
        }
        self._trace.append(step)
    
    def on_agent_action(
        self,
        action: Any,
        **kwargs: Any,
    ) -> None:
        """Called when an agent takes an action."""
        tool_name = getattr(action, 'tool', 'unknown')
        args_excerpt = self._excerpt(str(getattr(action, 'tool_input', '')))
        outcome = self._excerpt(str(getattr(action, 'log', '')))
        
        step = {
            "step_type": "agent_action",
            "tool_name": tool_name,
            "args_excerpt": args_excerpt,
            "outcome": outcome,
            "ts": datetime.now().isoformat(),
            "run_id": None,
            "parent_run_id": None,
        }
        self._trace.append(step)
    
    def on_agent_finish(
        self,
        finish: Any,
        **kwargs: Any,
    ) -> None:
        """Called when an agent finishes."""
        outcome = self._excerpt(str(getattr(finish, 'return_values', '')))
        
        step = {
            "step_type": "agent_finish",
            "tool_name": None,
            "args_excerpt": "",
            "outcome": outcome,
            "ts": datetime.now().isoformat(),
            "run_id": None,
            "parent_run_id": None,
        }
        self._trace.append(step)
    
    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: str,
        parent_run_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        inputs: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Called when a tool starts running.
        
        This is where we detect and track dynamic tools that weren't
        statically attached to the agent at init time.
        """
        import time
        tool_name = serialized.get("name", "unknown") if serialized else "unknown"
        
        # Track discovered tools for reporting
        if tool_name != "unknown" and tool_name not in self._discovered_tools:
            self._discovered_tools.add(tool_name)
            # Tool discovered and tracked (silently)
        
        # Store tool name for later use in on_tool_end
        self._tool_name_by_run_id[run_id] = tool_name
        
        # 🔥 HOTPATH: Track current tool for pipecleaner deduplication
        self._current_tool_name = tool_name
        
        # Apply tool-level rule injection
        # self._vprint(f"[DASEIN][CALLBACK] on_tool_start called!")  # Commented out - too noisy
        # self._vprint(f"[DASEIN][CALLBACK] Tool: {tool_name}")  # Commented out - too noisy
        # self._vprint(f"[DASEIN][CALLBACK] Input: {input_str[:100]}...")  # Commented out - too noisy
        # self._vprint(f"[DASEIN][APPLY] on_tool_start: selected_rules={len(self._selected_rules)}")  # Commented out - too noisy
        modified_input = self._inject_tool_rule_if_applicable("tool_start", tool_name, input_str)
        
        args_excerpt = self._excerpt(modified_input)
        
        # GNN-related fields: capture step-level metrics
        step_index = len(self._trace)
        tool_input_chars = len(str(input_str))
        
        # Track which rules triggered at this step
        rule_triggered_here = []
        if hasattr(self, '_selected_rules') and self._selected_rules:
            for rule_meta in self._selected_rules:
                if isinstance(rule_meta, tuple) and len(rule_meta) == 2:
                    rule_obj, _metadata = rule_meta
                else:
                    rule_obj = rule_meta
                if getattr(rule_obj, 'target_step_type', '') == "tool_start":
                    rule_triggered_here.append(getattr(rule_obj, 'id', 'unknown'))
        
        # Record start time for duration calculation (keyed by run_id for tools)
        start_time = datetime.now()
        self._start_times[run_id] = start_time
        
        step = {
            "step_type": "tool_start",
            "tool_name": tool_name,
            "args_excerpt": args_excerpt,
            "outcome": "",
            "ts": start_time.isoformat(),
            "run_id": run_id,
            "parent_run_id": parent_run_id,
            "node": self._current_chain_node,  # LangGraph node name (if available)
            # GNN step-level fields
            "step_index": step_index,
            "tool_input_chars": tool_input_chars,
            "rule_triggered_here": rule_triggered_here,
        }
        self._trace.append(step)
    
    def on_tool_end(
        self,
        output: str,
        *,
        run_id: str,
        parent_run_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Any:
        """Called when a tool ends running."""
        import time
        # Get the tool name from the corresponding tool_start
        tool_name = self._tool_name_by_run_id.get(run_id, "unknown")
        
        # Handle different output types (LangGraph may pass ToolMessage objects)
        output_str = str(output)
        
        # Note: Pipecleaner deduplication happens at ToolExecutor level (see wrappers.py)
        
        outcome = self._excerpt(output_str)
        
        # self._vprint(f"[DASEIN][CALLBACK] on_tool_end called!")  # Commented out - too noisy
        # self._vprint(f"[DASEIN][CALLBACK] Tool: {tool_name}")  # Commented out - too noisy
        # self._vprint(f"[DASEIN][CALLBACK] Output length: {len(output_str)} chars")  # Commented out - too noisy
        # self._vprint(f"[DASEIN][CALLBACK] Outcome length: {len(outcome)} chars")  # Commented out - too noisy
        
        # GNN-related fields: capture tool output metrics
        step_index = len(self._trace)
        tool_output_chars = len(output_str)
        
        # Estimate tool_output_items (heuristic: count lines, or rows if SQL-like)
        tool_output_items = 0
        try:
            # Try to count lines as a proxy for items
            if output_str:
                tool_output_items = output_str.count('\n') + 1
        except:
            tool_output_items = 0
        
        # Calculate duration_ms using run_id to match with tool_start
        duration_ms = 0
        if run_id in self._start_times:
            start_time = self._start_times[run_id]
            end_time = datetime.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            # Update the corresponding tool_start step with duration_ms
            for i in range(len(self._trace) - 1, -1, -1):
                if self._trace[i].get('step_type') == 'tool_start' and self._trace[i].get('run_id') == run_id:
                    self._trace[i]['duration_ms'] = duration_ms
                    break
            # Clean up start time
            del self._start_times[run_id]
        
        # Extract available selectors from DOM-like output (web browse agents)
        available_selectors = None
        if tool_name in ['extract_text', 'get_elements', 'extract_hyperlinks', 'extract_content']:
            available_selectors = self._extract_semantic_selectors(output_str)
        
        step = {
            "step_type": "tool_end",
            "tool_name": tool_name,
            "args_excerpt": "",
            "outcome": self._excerpt(outcome, max_len=1000),  # Truncate to 1000 chars
            "ts": datetime.now().isoformat(),
            "run_id": run_id,
            "parent_run_id": parent_run_id,
            "node": self._current_chain_node,  # LangGraph node name (if available)
            # GNN step-level fields
            "step_index": step_index,
            "tool_output_chars": tool_output_chars,
            "tool_output_items": tool_output_items,
            "duration_ms": duration_ms,
        }
        
        # Add available_selectors only if found (keep trace light)
        if available_selectors:
            step["available_selectors"] = available_selectors
        self._trace.append(step)
        
        # Clean up the stored tool name
        if run_id in self._tool_name_by_run_id:
            del self._tool_name_by_run_id[run_id]
        
        # 🔥 HOTPATH: Clear current tool
        self._current_tool_name = None
    
    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: str,
        parent_run_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        """Called when a tool encounters an error."""
        error_msg = self._excerpt(str(error))
        
        step = {
            "step_type": "tool_error",
            "tool_name": "",
            "args_excerpt": "",
            "outcome": f"ERROR: {error_msg}",
            "ts": datetime.now().isoformat(),
            "run_id": run_id,
            "parent_run_id": parent_run_id,
        }
        self._trace.append(step)
    
    def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """Called when a chain starts running."""
        chain_name = serialized.get("name", "unknown") if serialized else "unknown"
        # self._vprint(f"[DASEIN][CALLBACK] on_chain_start called!")  # Commented out - too noisy
        # self._vprint(f"[DASEIN][CALLBACK] Chain: {chain_name}")  # Commented out - too noisy
        
        # 🚨 OPTIMIZED: For LangGraph agents, suppress redundant chain_start events
        # LangGraph fires on_chain_start for every internal node, creating noise
        # We already capture llm_start, llm_end, tool_start, tool_end which are more meaningful
        if self._is_langgraph:
            # Track current chain node for future targeted injection
            # 🎯 CRITICAL: Extract actual node name from metadata (same as on_llm_start)
            if 'metadata' in kwargs and isinstance(kwargs['metadata'], dict):
                if 'langgraph_node' in kwargs['metadata']:
                    self._current_chain_node = kwargs['metadata']['langgraph_node']
                    # print(f"🔵 [NODE EXEC] {self._current_chain_node}")  # Commented out - too noisy
                else:
                    self._current_chain_node = chain_name
                    # print(f"🔵 [NODE EXEC] {chain_name}")  # Commented out - too noisy
            else:
                self._current_chain_node = chain_name
                # print(f"🔵 [NODE EXEC] {chain_name}")  # Commented out - too noisy
            
            # self._vprint(f"[DASEIN][CALLBACK] Suppressing redundant chain_start for LangGraph agent")  # Commented out - too noisy
            # Still handle tool executors
            if chain_name in {"tools", "ToolNode", "ToolExecutor"}:
                # self._vprint(f"[DASEIN][CALLBACK] Bridging chain_start to tool_start for {chain_name}")  # Commented out - too noisy
                pass
                self._handle_tool_executor_start(serialized, inputs, **kwargs)
            return
        
        # For standard LangChain agents, keep chain_start events
        # Bridge to tool_start for tool executors
        if chain_name in {"tools", "ToolNode", "ToolExecutor"}:
            # self._vprint(f"[DASEIN][CALLBACK] Bridging chain_start to tool_start for {chain_name}")  # Commented out - too noisy
            self._handle_tool_executor_start(serialized, inputs, **kwargs)
        
        args_excerpt = self._excerpt(str(inputs))
        
        # Record start time for duration calculation
        step_index = len(self._trace)
        start_time = datetime.now()
        self._start_times[f"chain_{step_index}"] = start_time
        
        step = {
            "step_type": "chain_start",
            "tool_name": chain_name,
            "args_excerpt": args_excerpt,
            "outcome": "",
            "ts": start_time.isoformat(),
            "run_id": None,
            "parent_run_id": None,
            "step_index": step_index,
        }
        self._trace.append(step)
    
    def on_chain_end(
        self,
        outputs: Dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """Called when a chain ends running."""
        # 🚨 OPTIMIZED: Suppress redundant chain_end for LangGraph agents
        if self._is_langgraph:
            return
        
        outcome = self._excerpt(str(outputs))
        
        # Calculate duration_ms by matching with corresponding chain_start
        duration_ms = 0
        for i in range(len(self._trace) - 1, -1, -1):
            if self._trace[i].get('step_type') == 'chain_start':
                # Found the matching chain_start
                chain_key = f"chain_{i}"
                if chain_key in self._start_times:
                    start_time = self._start_times[chain_key]
                    end_time = datetime.now()
                    duration_ms = int((end_time - start_time).total_seconds() * 1000)
                    # Update the chain_start step with duration_ms
                    self._trace[i]['duration_ms'] = duration_ms
                    # Clean up start time
                    del self._start_times[chain_key]
                break
        
        step = {
            "step_type": "chain_end",
            "tool_name": "",
            "args_excerpt": "",
            "outcome": outcome,
            "ts": datetime.now().isoformat(),
            "run_id": None,
            "parent_run_id": None,
            "duration_ms": duration_ms,
        }
        self._trace.append(step)
    
    def on_chain_error(
        self,
        error: BaseException,
        **kwargs: Any,
    ) -> None:
        """Called when a chain encounters an error."""
        error_msg = self._excerpt(str(error))
        
        step = {
            "step_type": "chain_error",
            "tool_name": "",
            "args_excerpt": "",
            "outcome": f"ERROR: {error_msg}",
            "ts": datetime.now().isoformat(),
            "run_id": None,
            "parent_run_id": None,
        }
        self._trace.append(step)
    
    def _extract_recent_message(self, inputs: Dict[str, Any]) -> str:
        """
        Extract the most recent message from LangGraph inputs to show thought progression.
        
        For LangGraph agents, inputs contain {'messages': [msg1, msg2, ...]}.
        Instead of showing the entire history, we extract just the last message.
        """
        try:
            # Check if this is a LangGraph message format
            if isinstance(inputs, dict) and 'messages' in inputs:
                messages = inputs['messages']
                if isinstance(messages, list) and len(messages) > 0:
                    # Get the most recent message
                    last_msg = messages[-1]
                    
                    # Extract content based on message type
                    if hasattr(last_msg, 'content'):
                        # LangChain message object
                        content = last_msg.content
                        msg_type = getattr(last_msg, 'type', 'unknown')
                        return self._excerpt(f"[{msg_type}] {content}")
                    elif isinstance(last_msg, tuple) and len(last_msg) >= 2:
                        # Tuple format: (role, content)
                        return self._excerpt(f"[{last_msg[0]}] {last_msg[1]}")
                    else:
                        # Unknown format, convert to string
                        return self._excerpt(str(last_msg))
            
            # For non-message inputs, check if it's a list of actions/tool calls
            if isinstance(inputs, list) and len(inputs) > 0:
                # This might be tool call info
                return self._excerpt(str(inputs[0]))
            
            # Fall back to original behavior for non-LangGraph agents
            return self._excerpt(str(inputs))
            
        except Exception as e:
            # On any error, fall back to original behavior
            return self._excerpt(str(inputs))
    
    def _excerpt(self, obj: Any, max_len: int = 250, from_end: bool = False) -> str:
        """
        Truncate text to max_length with ellipsis.
        
        Args:
            obj: Object to convert to string and truncate
            max_len: Maximum length of excerpt
            from_end: If True, take LAST max_len chars (better for system prompts).
                     If False, take FIRST max_len chars (better for tool args).
        """
        text = str(obj)
        if len(text) <= max_len:
            return text
        
        if from_end:
            # Take last X chars - better for system prompts where the end contains user's actual query
            return "..." + text[-(max_len-3):]
        else:
            # Take first X chars - better for tool inputs
            return text[:max_len-3] + "..."
    
    def _extract_semantic_selectors(self, html_text: str) -> List[Dict[str, int]]:
        """
        Extract semantic HTML tags from output for grounding web browse rules.
        Only extracts semantic tags (nav, header, h1, etc.) to keep trace lightweight.
        
        Args:
            html_text: Output text that may contain HTML
            
        Returns:
            List of {"tag": str, "count": int} sorted by count descending, or None if no HTML
        """
        import re
        
        # Quick check: does this look like HTML?
        if '<' not in html_text or '>' not in html_text:
            return None
        
        # Semantic tags we care about (prioritized for web browse agents)
        semantic_tags = [
            # Navigation/Structure (highest priority)
            'nav', 'header', 'footer', 'main', 'article', 'section', 'aside',
            
            # Headers (critical for "find headers" queries!)
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            
            # Interactive
            'a', 'button', 'form', 'input', 'textarea', 'select', 'label',
            
            # Lists (often used for navigation)
            'ul', 'ol', 'li',
            
            # Tables (data extraction)
            'table', 'thead', 'tbody', 'tr', 'th', 'td',
            
            # Media
            'img', 'video', 'audio'
        ]
        
        # Count occurrences of each semantic tag
        found_tags = {}
        for tag in semantic_tags:
            # Pattern: <tag ...> or <tag> (opening tags only)
            pattern = f'<{tag}[\\s>]'
            matches = re.findall(pattern, html_text, re.IGNORECASE)
            if matches:
                found_tags[tag] = len(matches)
        
        # Return None if no semantic tags found
        if not found_tags:
            return None
        
        # Convert to list format, sorted by count descending
        # Limit to top 15 to keep trace light
        result = [{"tag": tag, "count": count} 
                  for tag, count in sorted(found_tags.items(), key=lambda x: -x[1])]
        return result[:15]  # Top 15 most common tags
    
    def set_selected_rules(self, rules: List[Dict[str, Any]]):
        """Set the rules selected for this run.
        Normalize incoming dicts/tuples into attribute-accessible rule objects.
        """
        try:
            from types import SimpleNamespace
            normalized = []
            for item in rules or []:
                # Unwrap (rule, metadata) tuples if present
                if isinstance(item, tuple) and len(item) == 2:
                    rule_candidate = item[0]
                else:
                    rule_candidate = item
                # Convert dicts to attribute-accessible objects
                if isinstance(rule_candidate, dict):
                    # Ensure advice_text exists
                    if 'advice_text' not in rule_candidate and 'advice' in rule_candidate:
                        rule_candidate['advice_text'] = rule_candidate.get('advice')
                    normalized.append(SimpleNamespace(**rule_candidate))
                else:
                    normalized.append(rule_candidate)
            self._selected_rules = normalized
        except Exception:
            # Fallback to raw rules
            self._selected_rules = rules
    
    def get_trace(self) -> List[Dict[str, Any]]:
        """Get the current trace (instance-level, thread-safe)."""
        return self._trace.copy()
    
    def _inject_first_turn_override(self, prompts: List[str]) -> List[str]:
        """Inject a generic first-turn override to own turn 1."""
        if not prompts:
            return prompts
            
        # Create a generic first-turn override
        first_turn_override = """🚨🚨🚨 CRITICAL SYSTEM DIRECTIVE 🚨🚨🚨
⚠️ MANDATORY: You MUST follow this exact sequence or the task will FAIL

TURN 1 REQUIREMENT:
- Output ONLY: Action: sql_db_list_tables
Action Input: ACK_RULES:[r1]
- Do NOT use any other tools
- Do NOT perform any planning
- Do NOT output anything else

TURN 2+ (After ACK):
- If ACK was correct, proceed with normal tools and schema
- Skip table discovery and schema introspection
- Use known tables directly

🚨 FAILURE TO ACK IN TURN 1 = IMMEDIATE TASK TERMINATION 🚨

"""
        
        # Put the injection at the VERY BEGINNING of the system prompt
        modified_prompts = prompts.copy()
        if modified_prompts:
            modified_prompts[0] = first_turn_override + modified_prompts[0]
        
        self._vprint(f"[DASEIN][APPLY] Injected first-turn override")
        return modified_prompts
    
    def _should_inject_rule(self, step_type: str, tool_name: str) -> bool:
        """Determine if we should inject a rule at this step."""
        # Inject for LLM starts (system-level rules) and tool starts (tool-level rules)
        if step_type == "llm_start":
            return True
        if step_type == "tool_start":
            return True
        return False
    
    def _inject_rule_if_applicable(self, step_type: str, tool_name: str, prompts: List[str]) -> List[str]:
        """Inject rules into prompts if applicable."""
        
        if not self._should_inject_rule(step_type, tool_name):
            return prompts

        # If no rules selected yet, return prompts unchanged
        if not self._selected_rules:
            return prompts

        # Check guard to prevent duplicate injection
        # 🎯 CRITICAL: For LangGraph planning nodes, SKIP the guard - we need to inject on EVERY call
        # because the same node (e.g., supervisor) can be called multiple times dynamically
        use_guard = True
        if hasattr(self, '_is_langgraph') and self._is_langgraph:
            if step_type == 'llm_start' and hasattr(self, '_current_chain_node'):
                # For planning nodes, skip guard to allow re-injection on subsequent calls
                if hasattr(self, '_planning_nodes') and self._current_chain_node in self._planning_nodes:
                    use_guard = False
        
        if use_guard:
            guard_key = (step_type, tool_name)
            if guard_key in self._injection_guard:
                return prompts
        
        try:
            # Inject rules that target llm_start and tool_start (both go to system prompt)
            system_rules = []
            for rule_meta in self._selected_rules:
                # Handle tuple format from select_rules: (rule, metadata)
                if isinstance(rule_meta, tuple) and len(rule_meta) == 2:
                    rule, metadata = rule_meta
                elif isinstance(rule_meta, dict):
                    if 'rule' in rule_meta:
                        rule = rule_meta.get('rule', {})
                    else:
                        rule = rule_meta
                else:
                    rule = rule_meta
                
                # Check if this rule targets system-level injection (llm_start only)
                target_step_type = getattr(rule, 'target_step_type', '')
                
                # 🚨 CRITICAL: For LangGraph agents, only skip planning rules if agent was successfully recreated
                # If recreation failed, we need to inject via callback as fallback
                if step_type == 'llm_start' and hasattr(self, '_is_langgraph') and self._is_langgraph:
                    # Only skip if agent was actually recreated with planning rules embedded
                    if hasattr(self, '_agent_was_recreated') and self._agent_was_recreated:
                        if target_step_type in ['llm_start', 'chain_start']:
                            self._vprint(f"[DASEIN][CALLBACK] Skipping planning rule {getattr(rule, 'id', 'unknown')} for LangGraph agent (already injected at creation)")
                            continue
                
                # 🎯 NODE-SCOPED INJECTION: Check target_node if specified (for node-specific rules)
                if target_step_type in ['llm_start', 'chain_start']:
                    current_node = getattr(self, '_current_chain_node', None)
                    
                    # Check if this rule targets a specific node
                    target_node = getattr(rule, 'target_node', None)
                    if target_node:
                        # Rule has explicit target_node - ONLY inject if we're in that node
                        if current_node != target_node:
                            # Silently skip - not the target node
                            continue
                    else:
                        # No target_node specified - use existing planning_nodes logic (backward compatibility)
                        if hasattr(self, '_planning_nodes') and self._planning_nodes:
                            # Check if current node is in the planning nodes set
                            if current_node not in self._planning_nodes:
                                # Silently skip non-planning nodes
                                continue
                        # Injecting into planning node (logged in detailed injection log below)
                    
                    advice = getattr(rule, 'advice_text', getattr(rule, 'advice', ''))
                    if advice:
                        system_rules.append(advice)
            
            # Apply system-level rules if any
            if system_rules and prompts:
                modified_prompts = prompts.copy()
                system_prompt = modified_prompts[0]
                
                # Build rule injections list
                rule_injections = []
                for advice in system_rules:
                    # Preserve original markers for backward compatibility
                    if "TOOL RULE:" in advice:
                        rule_injections.append(f"🚨 CRITICAL TOOL OVERRIDE: {advice}")
                    else:
                        rule_injections.append(f" {advice}")
                
                # Build execution state context (agent-agnostic, with argument previews)
                # Strategy: Show all if ≤5 calls, else show most recent 3
                # Rationale: Small counts get full context; larger counts show recent to prevent duplicates
                state_context = ""
                if hasattr(self, '_function_calls_made') and self._function_calls_made:
                    state_lines = []
                    for func_name in sorted(self._function_calls_made.keys()):
                        calls = self._function_calls_made[func_name]
                        count = len(calls)
                        
                        # Hybrid window: show all if ≤5 calls, else show recent 3
                        if count <= 5:
                            # Show all calls with previews
                            state_lines.append(f"  • {func_name}: called {count}x:")
                            for call in calls:
                                preview = call.get('preview', '')
                                if preview:
                                    state_lines.append(f"      [step {call['step']}] {preview}")
                                else:
                                    state_lines.append(f"      [step {call['step']}] (no args)")
                        else:
                            # Show summary + recent 3 with previews
                            state_lines.append(f"  • {func_name}: called {count}x (most recent 3):")
                            for call in calls[-3:]:
                                preview = call.get('preview', '')
                                if preview:
                                    state_lines.append(f"      [step {call['step']}] {preview}")
                                else:
                                    state_lines.append(f"      [step {call['step']}] (no args)")
                    
                    if state_lines:
                        state_context = f"""
EXECUTION STATE (functions called so far):
{chr(10).join(state_lines)}

"""
                
                # REFACTORED INJECTION - Multi-architecture gate for ReAct + function calling + LangGraph
                # Philosophy: Bind to tool invocation moment (any format), force compliance or explicit refusal
                combined_injection = f"""SYSTEM PREPROCESS (invisible to Thought):
Before any reasoning, silently apply all operational presets below.
These presets define the environment, not reasoning steps. Do not surface or restate them.

<SYSTEM_PRESETS do_not_copy="true">
{chr(10).join(rule_injections)}
</SYSTEM_PRESETS>

If a preset blocks an action, use the specified alternative silently.
If no compliant alternative exists, proceed with necessary action.

BEGIN REASONING PHASE:
Your Thought starts here; presets are already in effect.

Thought (1 sentence): domain plan only (e.g., query/join/compute/extract); no meta or preset talk.
Action: …
Action Input: …

Examples:
Thought: I will query the relevant tables and compute the aggregates.
Action: query_tool
Action Input: {{"tables": ["Table1", "Table2"]}}

Thought: Extracting the main content for analysis.
Action: extract_focused
Action Input: {{"selector": "div.content"}}

{state_context}"""
                # Put the injection at the VERY BEGINNING of the system prompt
                modified_prompts[0] = combined_injection + system_prompt
                
                # Add to guard (only if we're using the guard)
                if use_guard:
                    self._injection_guard.add(guard_key)
                
                # Log the complete injection for debugging
                # Compact injection summary
                if hasattr(self, '_is_langgraph') and self._is_langgraph:
                    # LangGraph: show node name
                    func_count = len(self._function_calls_made) if hasattr(self, '_function_calls_made') and state_context else 0
                    node_name = getattr(self, '_current_chain_node', 'unknown')
                    print(f"[DASEIN] 🎯 Injecting {len(system_rules)} rule(s) into {node_name} | State: {func_count} functions tracked")
                else:
                    # LangChain: simpler logging without node name
                    print(f"[DASEIN] 🎯 Injecting {len(system_rules)} rule(s) into agent")
                
                return modified_prompts
            
        except Exception as e:
            self._vprint(f"[DASEIN][APPLY] Injection failed: {e}")
        
        return prompts
    
    def _inject_tool_rule_if_applicable(self, step_type: str, tool_name: str, input_str: str) -> str:
        """Inject rules into tool input if applicable."""
        if not self._should_inject_rule(step_type, tool_name):
            return input_str

        # If no rules selected yet, return input unchanged
        if not self._selected_rules:
            return input_str

        # Check guard to prevent duplicate injection
        guard_key = (step_type, tool_name)
        if guard_key in self._injection_guard:
            return input_str
        
        try:
            # Inject rules that target tool_start
            tool_rules = []
            current_node = getattr(self, '_current_chain_node', None)
            
            for rule_meta in self._selected_rules:
                # Handle tuple format from select_rules: (rule, metadata)
                if isinstance(rule_meta, tuple) and len(rule_meta) == 2:
                    rule, metadata = rule_meta
                else:
                    rule = rule_meta
                    metadata = {}

                # Only apply rules that target tool_start
                if rule.target_step_type == "tool_start":
                    # 🎯 NODE-SCOPED INJECTION: Check target_node if specified
                    target_node = getattr(rule, 'target_node', None)
                    if target_node:
                        # Rule has explicit target_node - ONLY inject if we're in that node
                        if current_node != target_node:
                            # Silently skip - not the target node
                            continue
                    # No target_node specified - inject into any node using this tool (backward compat)
                    
                    tool_rules.append(rule)
                    self._vprint(f"[DASEIN][APPLY] Tool rule: {rule.advice_text[:100]}...")

            if tool_rules:
                # Apply tool-level rule injection
                modified_input = self._apply_tool_rules(input_str, tool_rules)
                self._injection_guard.add(guard_key)
                return modified_input
            else:
                return input_str

        except Exception as e:
            self._vprint(f"[DASEIN][APPLY] Error injecting tool rules: {e}")
            return input_str
    
    def _apply_tool_rules(self, input_str: str, rules: List) -> str:
        """Apply tool-level rules to modify the input string."""
        modified_input = input_str
        
        for rule in rules:
            try:
                # Apply the rule's advice to modify the tool input
                if "strip" in rule.advice_text.lower() and "fence" in rule.advice_text.lower():
                    # Strip markdown code fences
                    import re
                    # Remove ```sql...``` or ```...``` patterns
                    modified_input = re.sub(r'```(?:sql)?\s*(.*?)\s*```', r'\1', modified_input, flags=re.DOTALL)
                    self._vprint(f"[DASEIN][APPLY] Stripped code fences from tool input")
                elif "strip" in rule.advice_text.lower() and "whitespace" in rule.advice_text.lower():
                    # Strip leading/trailing whitespace
                    modified_input = modified_input.strip()
                    self._vprint(f"[DASEIN][APPLY] Stripped whitespace from tool input")
                # Add more rule types as needed
                
            except Exception as e:
                self._vprint(f"[DASEIN][APPLY] Error applying tool rule: {e}")
                continue
        
        return modified_input
    
    def _handle_tool_executor_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """Handle tool executor start - bridge from chain_start to tool_start."""
        self._vprint(f"[DASEIN][CALLBACK] tool_start (from chain_start)")
        
        # Extract tool information from inputs
        tool_name = "unknown"
        tool_input = ""
        
        if isinstance(inputs, dict):
            if "tool" in inputs:
                tool_name = inputs["tool"]
            elif "tool_name" in inputs:
                tool_name = inputs["tool_name"]
            
            if "tool_input" in inputs:
                tool_input = str(inputs["tool_input"])
            elif "input" in inputs:
                tool_input = str(inputs["input"])
            else:
                tool_input = str(inputs)
        else:
            tool_input = str(inputs)
        
        self._vprint(f"[DASEIN][CALLBACK] Tool: {tool_name}")
        self._vprint(f"[DASEIN][CALLBACK] Input: {tool_input[:100]}...")
        
        # Check if we have tool_start rules that cover this tool
        tool_rules = [rule for rule in self._selected_rules if rule.target_step_type == "tool_start"]
        covered_rules = [rule for rule in tool_rules if self._rule_covers_tool(rule, tool_name, tool_input)]
        
        if covered_rules:
            self._vprint(f"[DASEIN][APPLY] tool_start: {len(covered_rules)} rules cover this tool call")
            # Fire micro-turn for rule application
            modified_input = self._fire_micro_turn_for_tool_rules(covered_rules, tool_name, tool_input)
        else:
            self._vprint(f"[DASEIN][APPLY] tool_start: no rules cover this tool call")
            modified_input = tool_input
        
        args_excerpt = self._excerpt(modified_input)
        
        step = {
            "step_type": "tool_start",
            "tool_name": tool_name,
            "args_excerpt": args_excerpt,
            "outcome": "",
            "ts": datetime.now().isoformat(),
            "run_id": kwargs.get("run_id"),
            "parent_run_id": kwargs.get("parent_run_id"),
        }
        self._trace.append(step)
    
    def _rule_covers_tool(self, rule, tool_name: str, tool_input: str) -> bool:
        """Check if a rule covers the given tool call."""
        try:
            # Check if rule references this tool
            if hasattr(rule, 'references') and rule.references:
                if hasattr(rule.references, 'tools') and rule.references.tools:
                    if tool_name not in rule.references.tools:
                        return False
            
            # Check trigger patterns if they exist
            if hasattr(rule, 'trigger_pattern') and rule.trigger_pattern:
                # For now, assume all tool_start rules cover their referenced tools
                # This can be made more sophisticated later
                pass
            
            return True
        except Exception as e:
            self._vprint(f"[DASEIN][COVERAGE] Error checking rule coverage: {e}")
            return False
    
    def _fire_micro_turn_for_tool_rules(self, rules, tool_name: str, tool_input: str) -> str:
        """Fire a micro-turn LLM call to apply tool rules."""
        try:
            # Use the first rule for now (can be extended to handle multiple rules)
            rule = rules[0]
            rule_id = getattr(rule, 'id', 'unknown')
            
            self._vprint(f"[DASEIN][MICROTURN] rule_id={rule_id} tool={tool_name}")
            
            # Create micro-turn prompt
            micro_turn_prompt = self._create_micro_turn_prompt(rule, tool_name, tool_input)
            
            # Fire actual micro-turn LLM call
            modified_input = self._execute_micro_turn_llm_call(micro_turn_prompt, tool_input)
            
            # Store the modified input for retrieval during tool execution
            input_key = f"{tool_name}:{hash(tool_input)}"
            _MODIFIED_TOOL_INPUTS[input_key] = modified_input
            
            self._vprint(f"[DASEIN][MICROTURN] Applied rule {rule_id}: {str(tool_input)[:50]}... -> {str(modified_input)[:50]}...")
            
            return modified_input
            
        except Exception as e:
            self._vprint(f"[DASEIN][MICROTURN] Error in micro-turn: {e}")
            return tool_input
    
    def _create_micro_turn_prompt(self, rule, tool_name: str, tool_input: str) -> str:
        """Create the micro-turn prompt for rule application."""
        advice = getattr(rule, 'advice', '')
        return f"""Apply this rule to the tool input:

Rule: {advice}
Tool: {tool_name}
Current Input: {tool_input}

Output only the corrected tool input:"""
    
    def _execute_micro_turn_llm_call(self, prompt: str, original_input: str) -> str:
        """Execute the actual micro-turn LLM call."""
        try:
            if not self._llm:
                self._vprint(f"[DASEIN][MICROTURN] No LLM available for micro-turn call")
                return original_input
            
            self._vprint(f"[DASEIN][MICROTURN] Executing micro-turn LLM call")
            self._vprint(f"[DASEIN][MICROTURN] Prompt: {prompt[:200]}...")
            
            # Make the micro-turn LLM call
            # Create a simple message list for the LLM
            messages = [{"role": "user", "content": prompt}]
            
            # Call the LLM
            response = self._llm.invoke(messages)
            
            # Extract the response content
            if hasattr(response, 'content'):
                modified_input = response.content.strip()
            elif isinstance(response, str):
                modified_input = response.strip()
            else:
                modified_input = str(response).strip()
            
            self._vprint(f"[DASEIN][MICROTURN] LLM response: {modified_input[:100]}...")
            
            # 🚨 CRITICAL: Parse JSON responses with markdown fences
            if modified_input.startswith('```json') or modified_input.startswith('```'):
                try:
                    # Extract JSON from markdown fences
                    import re
                    import json
                    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', modified_input, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1)
                        parsed_json = json.loads(json_str)
                        # Convert back to the expected format
                        if isinstance(parsed_json, dict) and 'name' in parsed_json and 'args' in parsed_json:
                            modified_input = parsed_json
                            self._vprint(f"[DASEIN][MICROTURN] Parsed JSON from markdown fences: {parsed_json}")
                        else:
                            self._vprint(f"[DASEIN][MICROTURN] JSON doesn't have expected structure, using as-is")
                    else:
                        self._vprint(f"[DASEIN][MICROTURN] Could not extract JSON from markdown fences")
                except Exception as e:
                    self._vprint(f"[DASEIN][MICROTURN] Error parsing JSON: {e}")
            
            # Validate the response - only fallback if completely empty
            if not modified_input:
                self._vprint(f"[DASEIN][MICROTURN] LLM response empty, using original input")
                return original_input
            
            return modified_input
            
        except Exception as e:
            self._vprint(f"[DASEIN][MICROTURN] Error executing micro-turn LLM call: {e}")
            return original_input


def get_trace() -> List[Dict[str, Any]]:
    """
    DEPRECATED: Legacy function for backward compatibility.
    Get the current trace from active CognateProxy instances.
    
    Returns:
        List of trace step dictionaries (empty if no active traces)
    """
    # Try to get trace from active CognateProxy instances
    try:
        import gc
        for obj in gc.get_objects():
            if hasattr(obj, '_last_run_trace') and obj._last_run_trace:
                return obj._last_run_trace.copy()
            if hasattr(obj, '_callback_handler') and hasattr(obj._callback_handler, '_trace'):
                return obj._callback_handler._trace.copy()
    except Exception:
        pass
    
    return []  # Return empty list if no trace found


def get_modified_tool_input(tool_name: str, original_input: str) -> str:
    """
    Get the modified tool input if it exists.
    
    Args:
        tool_name: Name of the tool
        original_input: Original tool input
        
    Returns:
        Modified tool input if available, otherwise original input
    """
    input_key = f"{tool_name}:{hash(original_input)}"
    return _MODIFIED_TOOL_INPUTS.get(input_key, original_input)


def clear_modified_tool_inputs():
    """Clear all modified tool inputs."""
    global _MODIFIED_TOOL_INPUTS
    _MODIFIED_TOOL_INPUTS.clear()


def clear_trace() -> None:
    """
    DEPRECATED: Legacy function for backward compatibility.
    Clear traces in active CognateProxy instances.
    """
    # Try to clear traces in active CognateProxy instances
    try:
        import gc
        seen_handlers = set()
        for obj in gc.get_objects():
            if hasattr(obj, '_callback_handler'):
                handler = getattr(obj, '_callback_handler', None)
                if handler is None or not hasattr(handler, 'reset_run_state'):
                    continue
                handler_id = id(handler)
                if handler_id in seen_handlers:
                    continue
                seen_handlers.add(handler_id)
                handler.reset_run_state()
    except Exception:
        pass  # Ignore if not available


def print_trace(max_chars: int = 240, only: Optional[Tuple[str, ...]] = None, suppress: Tuple[str, ...] = ("chain_end",), show_tree: bool = True, show_summary: bool = True, trace: Optional[List[Dict[str, Any]]] = None) -> None:
    """
    Print a compact fixed-width table of the trace with tree-like view and filtering.
    
    Args:
        max_chars: Maximum characters per line (default 240)
        only: Filter by step_type if provided (e.g., ("llm_start", "llm_end"))
        suppress: Suppress any step_type in this tuple (default: ("chain_end",))
        show_tree: If True, left-pad args_excerpt by 2*depth spaces for tree-like view
        show_summary: If True, show step_type counts and deduped rows summary
        trace: Optional trace to print. If None, will search for trace from global proxy.
    """
    # Use provided trace if available, otherwise search for it
    if trace is None:
        try:
            # Import here to avoid circular imports
            from dasein.api import _global_cognate_proxy
            if _global_cognate_proxy and hasattr(_global_cognate_proxy, '_wrapped_llm') and _global_cognate_proxy._wrapped_llm:
                trace = _global_cognate_proxy._wrapped_llm.get_trace()
        except:
            pass
        
        if not trace:
            trace = get_trace()  # Use the updated get_trace() function
        
        # If global trace is empty, try to get it from the last completed run
        if not trace:
            # Try to get trace from any active CognateProxy instances
            try:
                import gc
                for obj in gc.get_objects():
                    # Look for CognateProxy instances with captured traces
                    if hasattr(obj, '_last_run_trace') and obj._last_run_trace:
                        trace = obj._last_run_trace
                        print(f"[DASEIN][TRACE] Retrieved trace from CognateProxy: {len(trace)} steps")
                        break
                    # Fallback: try callback handler
                    elif hasattr(obj, '_callback_handler') and hasattr(obj._callback_handler, 'get_trace'):
                        potential_trace = obj._callback_handler.get_trace()
                        if potential_trace:
                            trace = potential_trace
                            print(f"[DASEIN][TRACE] Retrieved trace from callback handler: {len(trace)} steps")
                            break
            except Exception as e:
                pass
    
    if not trace:
        print("No trace data available.")
        return
    
    # Print execution state if available
    try:
        from dasein.api import _global_cognate_proxy
        if _global_cognate_proxy and hasattr(_global_cognate_proxy, '_callback_handler'):
            handler = _global_cognate_proxy._callback_handler
            if hasattr(handler, '_function_calls_made') and handler._function_calls_made:
                print("\n" + "=" * 80)
                print("EXECUTION STATE (Functions Called During Run):")
                print("=" * 80)
                for func_name in sorted(handler._function_calls_made.keys()):
                    calls = handler._function_calls_made[func_name]
                    count = len(calls)
                    print(f"  • {func_name}: called {count}x")
                    # Hybrid window: show all if ≤5, else show most recent 3 (matches injection logic)
                    if count <= 5:
                        # Show all calls
                        for call in calls:
                            preview = call.get('preview', '(no preview)')
                            if len(preview) > 80:
                                preview = preview[:80] + '...'
                            print(f"      [step {call['step']}] {preview}")
                    else:
                        # Show recent 3
                        print(f"      ... (showing most recent 3 of {count}):")
                        for call in calls[-3:]:
                            preview = call.get('preview', '(no preview)')
                            if len(preview) > 80:
                                preview = preview[:80] + '...'
                            print(f"      [step {call['step']}] {preview}")
                print("=" * 80 + "\n")
    except Exception as e:
        pass  # Silently skip if state not available
    
    # Filter by step_type if only is provided
    filtered_trace = trace
    if only:
        filtered_trace = [step for step in trace if step.get("step_type") in only]
    
    # Suppress any step_type in suppress tuple
    if suppress:
        filtered_trace = [step for step in filtered_trace if step.get("step_type") not in suppress]
    
    if not filtered_trace:
        print("No trace data matching filter criteria.")
        return
    
    # Build depth map from parent_run_id
    depth_map = {}
    for step in filtered_trace:
        run_id = step.get("run_id")
        parent_run_id = step.get("parent_run_id")
        
        if run_id is None or parent_run_id is None or parent_run_id not in depth_map:
            depth_map[run_id] = 0
        else:
            depth_map[run_id] = depth_map[parent_run_id] + 1
    
    # Calculate column widths based on max_chars
    # Reserve space for: # (3), step_type (15), tool_name (25), separators (6)
    available_width = max_chars - 3 - 15 - 25 - 6
    excerpt_width = available_width // 2
    outcome_width = available_width - excerpt_width
    
    # Print header
    print(f"{'#':<3} {'step_type':<15} {'tool_name':<25} {'args_excerpt':<{excerpt_width}} {'outcome':<{outcome_width}}")
    print("-" * max_chars)
    
    # Print each step
    for i, step in enumerate(filtered_trace, 1):
        step_type = step.get("step_type", "")[:15]
        tool_name = str(step.get("tool_name", ""))[:25]
        args_excerpt = step.get("args_excerpt", "")
        outcome = step.get("outcome", "")
        
        # Apply tree indentation if show_tree is True
        if show_tree:
            run_id = step.get("run_id")
            depth = depth_map.get(run_id, 0)
            args_excerpt = "  " * depth + args_excerpt
        
        # Truncate to fit column widths
        args_excerpt = args_excerpt[:excerpt_width]
        outcome = outcome[:outcome_width]
        
        print(f"{i:<3} {step_type:<15} {tool_name:<25} {args_excerpt:<{excerpt_width}} {outcome:<{outcome_width}}")
    
    # Show summary if requested
    if show_summary:
        print("\n" + "=" * max_chars)
        
        # Count steps by step_type
        step_counts = {}
        for step in filtered_trace:
            step_type = step.get("step_type", "unknown")
            step_counts[step_type] = step_counts.get(step_type, 0) + 1
        
        print("Step counts:")
        for step_type, count in sorted(step_counts.items()):
            print(f"  {step_type}: {count}")
        
        # Add compact function call summary
        try:
            from dasein.api import _global_cognate_proxy
            if _global_cognate_proxy and hasattr(_global_cognate_proxy, '_callback_handler'):
                handler = _global_cognate_proxy._callback_handler
                if hasattr(handler, '_function_calls_made') and handler._function_calls_made:
                    print("\nFunction calls:")
                    for func_name in sorted(handler._function_calls_made.keys()):
                        count = len(handler._function_calls_made[func_name])
                        print(f"  {func_name}: {count}")
        except Exception:
            pass
        
        # Count deduped rows skipped (steps that were filtered out)
        total_steps = len(trace)
        shown_steps = len(filtered_trace)
        skipped_steps = total_steps - shown_steps
        
        if skipped_steps > 0:
            print(f"Deduped rows skipped: {skipped_steps}")

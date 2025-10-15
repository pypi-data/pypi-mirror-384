"""
Monkey-patching wrappers for LLMs and Tools.

This module contains the monkey-patch logic for intercepting:
1. LLM calls (for microturn enforcement)
2. Tool calls (for pipecleaner deduplication)
"""

import threading
import time
from typing import Any, Optional

# Thread-local storage for callback handler (injected at runtime)
_tool_context = threading.local()


def set_pipecleaner_context(callback_handler: Any):
    """
    Inject callback handler into thread-local storage.
    Called from CognateProxy.__init__ after handler is created.
    """
    _tool_context.callback_handler = callback_handler


def get_pipecleaner_context():
    """Get callback handler from thread-local storage."""
    return getattr(_tool_context, 'callback_handler', None)


def wrap_tools_for_pipecleaner(agent: Any, callback_handler: Any, verbose: bool = False) -> bool:
    """
    DISABLED: This function has been disabled to avoid interfering with tool execution.
    """
    # Keep this message silent unless verbose is explicitly enabled
    if verbose:
        print(f"[WRAPPERS DISABLED] wrap_tools_for_pipecleaner called but DISABLED - no patching will occur")
    return False  # Return False to indicate nothing was done
    
    # ORIGINAL CODE BELOW - COMPLETELY DISABLED
    if False:
        pass
    try:
        import importlib
        
        if verbose:
            print(f"[DASEIN][TOOL_WRAPPER] 🔍 Instrumenting tool wrappers...")
        
        patched_count = 0
        
        # ===== [HP2] ToolNode._run_one/_arun_one =====
        try:
            from langgraph.prebuilt.tool_node import ToolNode
            
            if hasattr(ToolNode, '_arun_one'):
                original_arun_one = ToolNode._arun_one
                
                async def patched_arun_one(self, call, config):
                    tool_name = call.get('name', 'unknown') if isinstance(call, dict) else getattr(call, 'name', 'unknown')
                    result = await original_arun_one(self, call, config)
                    # Apply pipecleaner
                    result = _apply_pipecleaner_to_result(tool_name, result, callback_handler)
                    return result
                
                ToolNode._arun_one = patched_arun_one
                if verbose:
                    print(f"[DASEIN][TOOL_WRAPPER] ✅ Patched ToolNode._arun_one")
                patched_count += 1
            
            if hasattr(ToolNode, '_run_one'):
                original_run_one = ToolNode._run_one
                
                def patched_run_one(self, call, config):
                    tool_name = call.get('name', 'unknown') if isinstance(call, dict) else getattr(call, 'name', 'unknown')
                    result = original_run_one(self, call, config)
                    result = _apply_pipecleaner_to_result(tool_name, result, callback_handler)
                    return result
                
                ToolNode._run_one = patched_run_one
                if verbose:
                    print(f"[DASEIN][TOOL_WRAPPER] ✅ Patched ToolNode._run_one")
                patched_count += 1
        except ImportError:
            if verbose:
                print(f"[DASEIN][TOOL_WRAPPER] ⚠️  ToolNode not available")
        
        # ===== BaseTool._run/_arun (ACTUAL EXECUTION, not wrapper) =====
        try:
            from langchain_core.tools.base import BaseTool
            
            # Patch _arun (the actual async execution method)
            if hasattr(BaseTool, '_arun'):
                original_arun = BaseTool._arun
                
                async def patched_arun(self, *args, **kwargs):
                    tool_name = getattr(self, 'name', 'unknown')
                    result = await original_arun(self, *args, **kwargs)
                    handler = get_pipecleaner_context()
                    cleaned_result = _apply_pipecleaner_to_result(tool_name, result, handler)
                    return cleaned_result
                
                BaseTool._arun = patched_arun
                if verbose:
                    print(f"[DASEIN][TOOL_WRAPPER] ✅ Patched BaseTool._arun")
                patched_count += 1
            
            # Patch _run (sync version)
            if hasattr(BaseTool, '_run'):
                original_run = BaseTool._run
                
                def patched_run(self, *args, **kwargs):
                    tool_name = getattr(self, 'name', 'unknown')
                    result = original_run(self, *args, **kwargs)
                    handler = get_pipecleaner_context()
                    cleaned_result = _apply_pipecleaner_to_result(tool_name, result, handler)
                    return cleaned_result
                
                BaseTool._run = patched_run
                if verbose:
                    print(f"[DASEIN][TOOL_WRAPPER] ✅ Patched BaseTool._run")
                patched_count += 1
            
            # ALSO patch ainvoke/invoke as backup
            if hasattr(BaseTool, 'ainvoke'):
                original_ainvoke = BaseTool.ainvoke
                
                async def patched_ainvoke(self, *args, **kwargs):
                    tool_name = getattr(self, 'name', 'unknown')
                    result = await original_ainvoke(self, *args, **kwargs)
                    handler = get_pipecleaner_context()
                    cleaned_result = _apply_pipecleaner_to_result(tool_name, result, handler)
                    
                    if cleaned_result != result:
                        print(f"[🧹 CLEANED] Tool '{tool_name}' | {len(str(result))} → {len(str(cleaned_result))} chars")
                    
                    return cleaned_result
                
                BaseTool.ainvoke = patched_ainvoke
                if verbose:
                    print(f"[DASEIN][TOOL_WRAPPER] ✅ Patched BaseTool.ainvoke")
                patched_count += 1
            
            if hasattr(BaseTool, 'invoke'):
                original_invoke = BaseTool.invoke
                
                def patched_invoke(self, *args, **kwargs):
                    tool_name = getattr(self, 'name', 'unknown')
                    result = original_invoke(self, *args, **kwargs)
                    handler = get_pipecleaner_context()
                    cleaned_result = _apply_pipecleaner_to_result(tool_name, result, handler)
                    
                    if cleaned_result != result:
                        print(f"[🧹 CLEANED] Tool '{tool_name}' | {len(str(result))} → {len(str(cleaned_result))} chars")
                    
                    return cleaned_result
                
                BaseTool.invoke = patched_invoke
                if verbose:
                    print(f"[DASEIN][TOOL_WRAPPER] ✅ Patched BaseTool.invoke")
                patched_count += 1
        except ImportError:
            if verbose:
                print(f"[DASEIN][TOOL_WRAPPER] ⚠️  BaseTool not available")
        
        # ===== ToolMessage creation (catches streaming results) =====
        try:
            from langchain_core.messages import ToolMessage
            
            if hasattr(ToolMessage, '__init__'):
                original_init = ToolMessage.__init__
                
                def patched_init(self, content, **kwargs):
                    # Get tool name from kwargs if available
                    name = kwargs.get('name', 'unknown')
                    
                    # Apply pipecleaner to content before message is created
                    handler = get_pipecleaner_context()
                    if handler and isinstance(content, str):
                        cleaned_content = _apply_pipecleaner_to_result(name, content, handler)
                        if cleaned_content != content:
                            print(f"[🧹 CLEANED] ToolMessage '{name}' | {len(str(content))} → {len(str(cleaned_content))} chars")
                            content = cleaned_content
                    
                    # Call original with potentially cleaned content
                    original_init(self, content, **kwargs)
                
                ToolMessage.__init__ = patched_init
                if verbose:
                    print(f"[DASEIN][TOOL_WRAPPER] ✅ Patched ToolMessage.__init__")
                patched_count += 1
        except ImportError:
            if verbose:
                print(f"[DASEIN][TOOL_WRAPPER] ⚠️  ToolMessage not available")
        
        if verbose:
            print(f"[DASEIN][TOOL_WRAPPER] ✅ Instrumentation complete: {patched_count} seams wrapped")
        return patched_count > 0
            
    except Exception as e:
        print(f"[DASEIN][TOOL_WRAPPER] Error patching: {e}")
        import traceback
        traceback.print_exc()
        return False


def _extract_text_from_search_result(result: Any, tool_name: str) -> str:
    """
    Extract full text content from structured search results.
    
    Handles multiple search tool formats:
    - Tavily: list of dicts with 'content', 'url', 'title'
    - Serper: dict with 'organic' results
    - DuckDuckGo: list of dicts with 'body', 'title'
    - Raw strings: pass through
    """
    # If already a string, return as-is
    if isinstance(result, str):
        return result
    
    extracted_parts = []
    
    # Tavily format: list of result dicts
    if isinstance(result, list):
        # Keep extraction log quiet unless user opts in via env
        import os
        if os.getenv("DASEIN_DEBUG_PIPECLEANER", "0") == "1":
            print(f"[PIPECLEANER] Extracting from list of {len(result)} search results")
        for i, item in enumerate(result, 1):
            if isinstance(item, dict):
                # Extract all text fields
                title = item.get('title', '')
                url = item.get('url', '')
                content = item.get('content', '') or item.get('body', '') or item.get('snippet', '')
                
                if title or content:
                    extracted_parts.append(f"--- SOURCE {i}: {title} ---")
                    if url:
                        extracted_parts.append(f"URL: {url}")
                    if content:
                        extracted_parts.append(content)
                    extracted_parts.append("")  # Blank line separator
    
    # Serper/dict format with 'organic' or 'results'
    elif isinstance(result, dict):
        organic = result.get('organic', []) or result.get('results', [])
        if organic:
            import os
            if os.getenv("DASEIN_DEBUG_PIPECLEANER", "0") == "1":
                print(f"[PIPECLEANER] Extracting from dict with {len(organic)} organic results")
            for i, item in enumerate(organic, 1):
                title = item.get('title', '')
                url = item.get('link', '') or item.get('url', '')
                snippet = item.get('snippet', '') or item.get('content', '')
                
                if title or snippet:
                    extracted_parts.append(f"--- SOURCE {i}: {title} ---")
                    if url:
                        extracted_parts.append(f"URL: {url}")
                    if snippet:
                        extracted_parts.append(snippet)
                    extracted_parts.append("")
        else:
            # Dict without known structure, try to extract any text
            for key, value in result.items():
                if isinstance(value, str) and len(value) > 20:
                    extracted_parts.append(f"{key}: {value}")
    
    # Fallback: convert to string (but log warning)
    if not extracted_parts:
        result_str = str(result)
        import os
        if os.getenv("DASEIN_DEBUG_PIPECLEANER", "0") == "1":
            print(f"[PIPECLEANER] ⚠️  Unknown result format, using str() - may be truncated")
            print(f"[PIPECLEANER] Result type: {type(result).__name__}")
        return result_str
    
    full_text = "\n".join(extracted_parts)
    import os
    if os.getenv("DASEIN_DEBUG_PIPECLEANER", "0") == "1":
        print(f"[PIPECLEANER] ✅ Extracted {len(full_text)} chars from {len(extracted_parts)} parts")
    return full_text


def _apply_pipecleaner_to_result(tool_name: str, result: Any, callback_handler: Any) -> Any:
    """
    Apply pipecleaner deduplication to a tool result.
    
    Called from patched tool execution methods.
    """
    try:
        # Check if we have filter rules
        if not callback_handler or not hasattr(callback_handler, '_selected_rules'):
            return result
        
        # Extract text from structured result (handles Tavily, Serper, etc.)
        result_str = _extract_text_from_search_result(result, tool_name)
        
        # Apply pipecleaner
        from .pipecleaner import apply_pipecleaner_if_applicable
        
        # Get cached model
        cached_model = getattr(callback_handler, '_pipecleaner_embedding_model', None)
        
        # Apply deduplication
        deduplicated_str, model = apply_pipecleaner_if_applicable(
            tool_name=tool_name,
            output_str=result_str,
            selected_rules=callback_handler._selected_rules,
            cached_model=cached_model
        )
        
        # Cache model
        if model is not None:
            callback_handler._pipecleaner_embedding_model = model
        
        # Return deduplicated result (as same type as original if possible)
        if deduplicated_str != result_str:
            import os
            if os.getenv("DASEIN_DEBUG_PIPECLEANER", "0") == "1":
                print(f"[PIPECLEANER] ✅ Deduplicated: {len(result_str)} → {len(deduplicated_str)} chars")
            return deduplicated_str
        
        return result
        
    except Exception as e:
        import os
        if os.getenv("DASEIN_DEBUG_PIPECLEANER", "0") == "1":
            print(f"[PIPECLEANER] Error applying pipecleaner: {e}")
        import traceback
        if os.getenv("DASEIN_DEBUG_PIPECLEANER", "0") == "1":
            traceback.print_exc()
        return result

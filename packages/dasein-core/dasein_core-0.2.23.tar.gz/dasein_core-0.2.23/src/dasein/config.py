"""
Dasein Configuration Module - Central place for model IDs, caps, and thresholds

This module provides configuration constants for the dasein library.
No business logic, just configuration values.
"""

# LLM Model Configuration - SYNTHESIS MIGRATED TO POST-RUN SERVICE
# Note: Compactor and trace processing configuration handled by cloud services

# Text Truncation Limits
MAX_EXCERPT_LENGTH = 240
MAX_ADVICE_LINES = 2
MAX_MEMO_LINES = 6
MAX_ADVICE_CHARS = 200
MAX_MEMO_CHARS = 500

# Validation Limits
MIN_CONFIDENCE = 0.0
MAX_CONFIDENCE = 1.0
MAX_SCOPE_ITEMS = 10

# Note: Rule repository, embedding, and learning configuration handled by cloud services

# Trace View Configuration
TRACE_VIEW_MAX_STEPS = 16      # cap for compact printing
TRACE_VIEW_MAX_MESSAGES = 8
TRACE_VIEW_EXCERPT_CHARS = 160

# Cost function weights: C = w1·−log(p_success+ε) + w2·E[turns] + w3·uncertainty + w4·E[tokens] + w5·E[time_ms]
# Clients can override these weights in select_rules() call for custom optimization preferences
W_COST = {
    "w1": 1.0,  # weight for -log(p_success) - higher = favor more successful rules
    "w2": 1.0,  # weight for E_turns - higher = favor fewer turns
    "w3": 1.0,  # weight for uncertainty - higher = penalize uncertain rules
    "w4": 1.0,  # weight for E_tokens - higher = favor fewer tokens
    "w5": 1.0   # weight for E_time_ms - higher = favor faster execution
}
EPSILON_P = 1e-6  # epsilon for log(p_success) to avoid log(0)

# Injection Configuration
ADVICE_MAX_CHARS = 200
INJECTION_ENABLED_SITES = {"planner"}  # Demo gate: only planner enabled
INJECTION_HEADERS = {
    "planner": "--- DASEIN planner hint ---",
    "codegen": "--- DASEIN codegen hint ---",
    "tool": "--- DASEIN tool hint ---"
}
INJECTION_FOOTER = "--------------------------------"
INJECTION_LOG_PREFIX = "[DASEIN][APPLY]"

# Note: Learning algorithm configuration handled by cloud services
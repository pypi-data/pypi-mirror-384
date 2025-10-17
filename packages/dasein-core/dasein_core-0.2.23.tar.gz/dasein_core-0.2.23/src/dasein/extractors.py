"""
Dasein Extractors Module - Pure text processing helpers

This module provides pure functions for detecting fenced code blocks, parsing JSON/YAML,
extracting URIs/symbols, generating hashes and excerpts. Uses only stdlib.
"""

import re
import json
import hashlib
from typing import List, Tuple, Dict, Any, Optional, Union


def detect_fenced_code_blocks(text: str) -> List[Tuple[str, str]]:
    """
    Detect fenced code blocks in text and return (language, content) tuples.
    
    Args:
        text: Input text to scan for code blocks
        
    Returns:
        List of (language, content) tuples for each code block found
    """
    # Pattern to match fenced code blocks (```lang ... ```)
    pattern = r'```(\w*)\n(.*?)\n```'
    matches = re.findall(pattern, text, re.DOTALL)
    
    # Also handle blocks without language specification
    pattern_no_lang = r'```\n(.*?)\n```'
    matches_no_lang = re.findall(pattern_no_lang, text, re.DOTALL)
    
    # Combine results, using empty string for language when not specified
    all_matches = [(lang, content) for lang, content in matches]
    all_matches.extend([('', content) for content in matches_no_lang])
    
    return all_matches


def try_parse_json_yaml(text: str) -> Optional[Union[Dict, List]]:
    """
    Try to parse text as JSON or YAML (JSON only for now).
    
    Args:
        text: Text to parse
        
    Returns:
        Parsed object if successful, None otherwise
    """
    # Try JSON first
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass
    
    # TODO: Add YAML parsing when yaml library is available
    # For now, return None if JSON parsing fails
    return None


def extract_symbols_and_uris(text: str) -> Dict[str, List[str]]:
    """
    Extract symbols and URIs from text.
    
    Args:
        text: Input text to analyze
        
    Returns:
        Dictionary with 'symbols' and 'uris' keys containing lists of found items
    """
    symbols = []
    uris = []
    
    # Extract function/class names (basic pattern)
    symbol_pattern = r'\b[A-Za-z_][A-Za-z0-9_]*\s*\([^)]*\)'  # function calls
    symbols.extend(re.findall(symbol_pattern, text))
    
    # Extract class definitions
    class_pattern = r'class\s+([A-Za-z_][A-Za-z0-9_]*)'
    symbols.extend(re.findall(class_pattern, text))
    
    # Extract function definitions
    func_pattern = r'def\s+([A-Za-z_][A-Za-z0-9_]*)'
    symbols.extend(re.findall(func_pattern, text))
    
    # Extract URIs (http/https)
    uri_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    uris.extend(re.findall(uri_pattern, text))
    
    # Extract file paths (basic pattern)
    file_pattern = r'[A-Za-z]:\\[^\s<>"{}|\\^`\[\]]+|\/[^\s<>"{}|\\^`\[\]]+'
    file_paths = re.findall(file_pattern, text)
    uris.extend(file_paths)
    
    return {
        'symbols': list(set(symbols)),  # Remove duplicates
        'uris': list(set(uris))
    }


def text_fingerprint(text: str) -> str:
    """
    Generate a deterministic hash fingerprint for text.
    
    Args:
        text: Text to fingerprint
        
    Returns:
        SHA-256 hash as hex string
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def excerpt(text: str, max_len: int = 240) -> str:
    """
    Create a truncated excerpt of text with ellipsis.
    
    Args:
        text: Text to excerpt
        max_len: Maximum length of excerpt
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_len:
        return text
    
    # Try to break at word boundary
    truncated = text[:max_len-3]
    last_space = truncated.rfind(' ')
    
    if last_space > max_len * 0.8:  # If we can break at a reasonable word boundary
        return truncated[:last_space] + '...'
    else:
        return truncated + '...'

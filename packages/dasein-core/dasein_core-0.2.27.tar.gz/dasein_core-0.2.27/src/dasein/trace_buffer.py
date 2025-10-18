"""
Dasein Trace Buffer Module - In-memory cache for text and binary data

This module provides an in-memory cache for storing full text and binary blobs
keyed by hash. No disk I/O, no eviction policy.
"""

from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class TraceBuffer:
    """
    In-memory cache for storing text and binary data by hash.
    
    Provides put/get APIs for text and binary data with no persistence.
    """
    
    def __init__(self):
        """Initialize empty trace buffer."""
        self._text_cache: Dict[str, str] = {}
        self._bytes_cache: Dict[str, bytes] = {}
        
        logger.info("[DASEIN][TRACE_BUFFER] Initialized empty trace buffer")
    
    def put_text(self, text: str) -> str:
        """
        Store text and return its hash.
        
        Args:
            text: Text content to store
            
        Returns:
            Hash key for the stored text
        """
        # Generate hash for the text
        import hashlib
        text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
        
        # Store in cache
        self._text_cache[text_hash] = text
        
        logger.debug(f"[DASEIN][TRACE_BUFFER] Stored text with hash: {text_hash[:8]}...")
        return text_hash
    
    def get_text(self, text_hash: str) -> Optional[str]:
        """
        Retrieve text by hash.
        
        Args:
            text_hash: Hash key to look up
            
        Returns:
            Stored text if found, None otherwise
        """
        text = self._text_cache.get(text_hash)
        if text is not None:
            logger.debug(f"[DASEIN][TRACE_BUFFER] Retrieved text for hash: {text_hash[:8]}...")
        else:
            logger.debug(f"[DASEIN][TRACE_BUFFER] Text not found for hash: {text_hash[:8]}...")
        return text
    
    def put_bytes(self, data: bytes) -> str:
        """
        Store binary data and return its hash.
        
        Args:
            data: Binary data to store
            
        Returns:
            Hash key for the stored data
        """
        # Generate hash for the binary data
        import hashlib
        data_hash = hashlib.sha256(data).hexdigest()
        
        # Store in cache
        self._bytes_cache[data_hash] = data
        
        logger.debug(f"[DASEIN][TRACE_BUFFER] Stored bytes with hash: {data_hash[:8]}...")
        return data_hash
    
    def get_bytes(self, data_hash: str) -> Optional[bytes]:
        """
        Retrieve binary data by hash.
        
        Args:
            data_hash: Hash key to look up
            
        Returns:
            Stored binary data if found, None otherwise
        """
        data = self._bytes_cache.get(data_hash)
        if data is not None:
            logger.debug(f"[DASEIN][TRACE_BUFFER] Retrieved bytes for hash: {data_hash[:8]}...")
        else:
            logger.debug(f"[DASEIN][TRACE_BUFFER] Bytes not found for hash: {data_hash[:8]}...")
        return data
    
    def size(self) -> int:
        """
        Get total number of items stored in the buffer.
        
        Returns:
            Total count of stored items
        """
        total_size = len(self._text_cache) + len(self._bytes_cache)
        logger.debug(f"[DASEIN][TRACE_BUFFER] Buffer size: {total_size} items")
        return total_size
    
    def clear(self) -> None:
        """Clear all stored data from the buffer."""
        self._text_cache.clear()
        self._bytes_cache.clear()
        logger.info("[DASEIN][TRACE_BUFFER] Buffer cleared")
    
    def stats(self) -> Dict[str, int]:
        """
        Get statistics about the buffer contents.
        
        Returns:
            Dictionary with text and bytes counts
        """
        return {
            'text_items': len(self._text_cache),
            'bytes_items': len(self._bytes_cache),
            'total_items': len(self._text_cache) + len(self._bytes_cache)
        }

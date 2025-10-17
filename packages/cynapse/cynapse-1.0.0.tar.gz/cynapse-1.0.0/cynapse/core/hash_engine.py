"""Hash engine with caching for efficient integrity verification."""

import hashlib
from functools import lru_cache
from types import CodeType
from typing import List, Optional

from ..models import MemoryRegion


class HashEngine:
    """Efficient hashing engine with optional accelerators and LRU caching."""
    
    def __init__(self, algorithm: str = "sha256", cache_size: int = 1024):
        """
        Initialize hash engine with specified algorithm.
        
        Args:
            algorithm: Hash algorithm to use ("sha256" or "blake3")
            cache_size: Maximum number of cached hash results
        """
        self.algorithm = algorithm
        self.cache_size = cache_size
        self._blake3_available = False
        
        # Try to import blake3 if requested
        if algorithm == "blake3":
            try:
                import blake3
                self._blake3_available = True
                self._blake3 = blake3
            except ImportError:
                # Graceful fallback to SHA-256
                self.algorithm = "sha256"
        
        # Create LRU cached version of hash computation
        self._hash_bytes_cached = lru_cache(maxsize=cache_size)(self._hash_bytes_impl)
    
    def hash_bytes(self, data: bytes) -> str:
        """
        Hash arbitrary bytes with LRU caching.
        
        Args:
            data: Bytes to hash
            
        Returns:
            Hexadecimal hash string
        """
        return self._hash_bytes_cached(data)
    
    def _hash_bytes_impl(self, data: bytes) -> str:
        """
        Internal implementation of hash_bytes without caching decorator.
        
        Args:
            data: Bytes to hash
            
        Returns:
            Hexadecimal hash string
        """
        if self.algorithm == "blake3" and self._blake3_available:
            return self._blake3.blake3(data).hexdigest()
        else:
            # Default to SHA-256
            return hashlib.sha256(data).hexdigest()
    
    def hash_bytecode(self, code_obj: CodeType) -> str:
        """
        Hash function bytecode including constants and names for completeness.
        
        This hashes the complete code object to detect any modifications to:
        - Bytecode instructions (co_code)
        - Constants used in the code (co_consts)
        - Names referenced in the code (co_names)
        
        Args:
            code_obj: Python code object to hash
            
        Returns:
            Hexadecimal hash string
        """
        # Combine multiple code object attributes for comprehensive hashing
        data = code_obj.co_code
        
        # Add constants (converted to string representation)
        data += str(code_obj.co_consts).encode('utf-8')
        
        # Add names (converted to string representation)
        data += str(code_obj.co_names).encode('utf-8')
        
        return self.hash_bytes(data)
    
    def hash_memory_region(
        self, 
        region: MemoryRegion, 
        chunk_size: int = 4096
    ) -> List[str]:
        """
        Hash memory region in chunks for efficient verification.
        
        This allows for incremental verification where only changed chunks
        need to be re-hashed rather than the entire region.
        
        Args:
            region: Memory region to hash
            chunk_size: Size of each chunk in bytes (default 4KB)
            
        Returns:
            List of hexadecimal hash strings, one per chunk
        """
        hashes = []
        
        for offset in range(0, region.size, chunk_size):
            # Calculate chunk size (handle last chunk which may be smaller)
            current_chunk_size = min(chunk_size, region.size - offset)
            
            try:
                # Read chunk from memory region
                chunk = region.read(offset, current_chunk_size)
                
                # Hash the chunk
                chunk_hash = self.hash_bytes(chunk)
                hashes.append(chunk_hash)
                
            except Exception:
                # If we can't read a chunk, append a placeholder
                # This allows graceful degradation for protected memory
                hashes.append("")
        
        return hashes
    
    def clear_cache(self) -> None:
        """Clear the LRU cache to free memory."""
        self._hash_bytes_cached.cache_clear()
    
    def get_cache_info(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache hits, misses, size, and maxsize
        """
        info = self._hash_bytes_cached.cache_info()
        return {
            'hits': info.hits,
            'misses': info.misses,
            'size': info.currsize,
            'maxsize': info.maxsize,
        }

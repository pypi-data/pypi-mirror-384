"""Baseline storage for integrity checking."""

import json
import pickle
import zlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..models import MemoryRegion
from ..exceptions import BaselineError


class Baseline:
    """Stores and manages baseline integrity data."""
    
    def __init__(self, compress: bool = True):
        """
        Initialize baseline storage.
        
        Args:
            compress: Whether to compress baseline data to save memory
        """
        self.compress = compress
        self.created_at = None
        
        # different types of baseline data
        self._function_hashes: Dict[str, str] = {}  # func_id -> hash
        self._module_hashes: Dict[str, str] = {}    # module_name -> hash
        self._memory_hashes: Dict[str, List[str]] = {}  # region_id -> chunk hashes
        self._import_hooks: List[str] = []  # list of registered import hooks
        
        # metadata
        self._metadata: Dict[str, Any] = {}
    
    def create(self, timestamp: Optional[datetime] = None) -> None:
        """
        Mark baseline as created.
        
        Args:
            timestamp: Creation timestamp (defaults to now)
        """
        self.created_at = timestamp or datetime.now()
        self._metadata['created_at'] = self.created_at.isoformat()
        self._metadata['compressed'] = self.compress
    
    def add_function(self, func_id: str, code_hash: str) -> None:
        """
        Add function to baseline.
        
        Args:
            func_id: Unique function identifier
            code_hash: Hash of function bytecode
        """
        self._function_hashes[func_id] = code_hash
    
    def add_module(self, module_name: str, module_hash: str) -> None:
        """
        Add module to baseline.
        
        Args:
            module_name: Module name
            module_hash: Hash of module contents
        """
        self._module_hashes[module_name] = module_hash
    
    def add_memory_region(self, region_id: str, chunk_hashes: List[str]) -> None:
        """
        Add memory region to baseline.
        
        Args:
            region_id: Unique region identifier
            chunk_hashes: List of hashes for memory chunks
        """
        self._memory_hashes[region_id] = chunk_hashes
    
    def add_import_hook(self, hook_id: str) -> None:
        """
        Record an import hook.
        
        Args:
            hook_id: Identifier for the import hook
        """
        if hook_id not in self._import_hooks:
            self._import_hooks.append(hook_id)
    
    def get_function_hash(self, func_id: str) -> Optional[str]:
        """
        Get baseline hash for a function.
        
        Args:
            func_id: Function identifier
            
        Returns:
            Baseline hash or None if not found
        """
        return self._function_hashes.get(func_id)
    
    def get_module_hash(self, module_name: str) -> Optional[str]:
        """
        Get baseline hash for a module.
        
        Args:
            module_name: Module name
            
        Returns:
            Baseline hash or None if not found
        """
        return self._module_hashes.get(module_name)
    
    def get_memory_hashes(self, region_id: str) -> Optional[List[str]]:
        """
        Get baseline hashes for a memory region.
        
        Args:
            region_id: Region identifier
            
        Returns:
            List of chunk hashes or None if not found
        """
        return self._memory_hashes.get(region_id)
    
    def has_function(self, func_id: str) -> bool:
        """Check if function is in baseline."""
        return func_id in self._function_hashes
    
    def has_module(self, module_name: str) -> bool:
        """Check if module is in baseline."""
        return module_name in self._module_hashes
    
    def get_import_hooks(self) -> List[str]:
        """Get list of registered import hooks."""
        return self._import_hooks.copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get baseline statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'function_count': len(self._function_hashes),
            'module_count': len(self._module_hashes),
            'memory_region_count': len(self._memory_hashes),
            'import_hook_count': len(self._import_hooks),
            'compressed': self.compress,
            'memory_usage_bytes': self._estimate_memory_usage(),
        }
    
    def _estimate_memory_usage(self) -> int:
        """
        Estimate memory usage of baseline data.
        
        Returns:
            Approximate bytes used
        """
        # rough estimate based on data structures
        size = 0
        
        # function hashes (string -> string)
        for k, v in self._function_hashes.items():
            size += len(k) + len(v) + 100  # overhead
        
        # module hashes
        for k, v in self._module_hashes.items():
            size += len(k) + len(v) + 100
        
        # memory region hashes
        for k, v in self._memory_hashes.items():
            size += len(k) + 100
            size += sum(len(h) for h in v)
        
        # import hooks
        size += sum(len(h) for h in self._import_hooks)
        
        return size
    
    def save(self, filepath: str) -> None:
        """
        Save baseline to disk.
        
        Args:
            filepath: Path to save baseline
            
        Raises:
            BaselineError: If save fails
        """
        try:
            data = {
                'metadata': self._metadata,
                'function_hashes': self._function_hashes,
                'module_hashes': self._module_hashes,
                'memory_hashes': self._memory_hashes,
                'import_hooks': self._import_hooks,
            }
            
            # serialize to bytes
            serialized = pickle.dumps(data)
            
            # compress if enabled
            if self.compress:
                serialized = zlib.compress(serialized)
            
            # write to file
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'wb') as f:
                f.write(serialized)
                
        except Exception as e:
            raise BaselineError(f"Failed to save baseline: {e}")
    
    def load(self, filepath: str) -> None:
        """
        Load baseline from disk.
        
        Args:
            filepath: Path to load baseline from
            
        Raises:
            BaselineError: If load fails
        """
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
            
            # decompress if needed
            if self.compress:
                try:
                    data = zlib.decompress(data)
                except zlib.error:
                    # maybe it wasn't compressed
                    pass
            
            # deserialize
            loaded = pickle.loads(data)
            
            # restore data
            self._metadata = loaded.get('metadata', {})
            self._function_hashes = loaded.get('function_hashes', {})
            self._module_hashes = loaded.get('module_hashes', {})
            self._memory_hashes = loaded.get('memory_hashes', {})
            self._import_hooks = loaded.get('import_hooks', [])
            
            # restore created_at
            if 'created_at' in self._metadata:
                self.created_at = datetime.fromisoformat(self._metadata['created_at'])
            
        except Exception as e:
            raise BaselineError(f"Failed to load baseline: {e}")
    
    def export_json(self, filepath: str) -> None:
        """
        Export baseline as human-readable JSON.
        
        Args:
            filepath: Path to save JSON
            
        Raises:
            BaselineError: If export fails
        """
        try:
            data = {
                'metadata': self._metadata,
                'function_hashes': self._function_hashes,
                'module_hashes': self._module_hashes,
                'memory_hashes': self._memory_hashes,
                'import_hooks': self._import_hooks,
            }
            
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            raise BaselineError(f"Failed to export baseline: {e}")
    
    def clear(self) -> None:
        """Clear all baseline data."""
        self._function_hashes.clear()
        self._module_hashes.clear()
        self._memory_hashes.clear()
        self._import_hooks.clear()
        self._metadata.clear()
        self.created_at = None

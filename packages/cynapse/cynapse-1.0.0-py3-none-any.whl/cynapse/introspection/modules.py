"""Module tracking and verification."""

import sys
from typing import Dict, List, Set, Optional
from datetime import datetime

from ..models import TamperEvent, TamperType


class ModuleTracker:
    """Tracks loaded Python modules and detects changes."""
    
    def __init__(self, hash_engine):
        """
        Initialize module tracker.
        
        Args:
            hash_engine: HashEngine instance for hashing
        """
        self.hash_engine = hash_engine
        self._baseline_modules: Set[str] = set()
        self._module_hashes: Dict[str, str] = {}
    
    def create_baseline(self, whitelist: List[str] = None) -> None:
        """
        Create baseline of currently loaded modules.
        
        Args:
            whitelist: Module patterns to skip
        """
        whitelist = whitelist or []
        
        self._baseline_modules = set(sys.modules.keys())
        
        # hash each module
        for module_name in self._baseline_modules:
            if self._should_skip(module_name, whitelist):
                continue
            
            try:
                module_hash = self._hash_module(module_name)
                if module_hash:
                    self._module_hashes[module_name] = module_hash
            except Exception:
                # couldn't hash module, skip it
                pass
    
    def check_for_changes(self, whitelist: List[str] = None) -> List[TamperEvent]:
        """
        Check for module changes since baseline.
        
        Args:
            whitelist: Module patterns to skip
            
        Returns:
            List of tamper events
        """
        events = []
        whitelist = whitelist or []
        
        current_modules = set(sys.modules.keys())
        
        # check for new modules
        new_modules = current_modules - self._baseline_modules
        for module_name in new_modules:
            if self._should_skip(module_name, whitelist):
                continue
            
            events.append(TamperEvent(
                type=TamperType.MODULE_INJECTION,
                target=module_name,
                timestamp=datetime.now(),
                details=f"New module '{module_name}' loaded after baseline"
            ))
        
        # check for removed modules
        removed_modules = self._baseline_modules - current_modules
        for module_name in removed_modules:
            if self._should_skip(module_name, whitelist):
                continue
            
            events.append(TamperEvent(
                type=TamperType.MODULE_REMOVAL,
                target=module_name,
                timestamp=datetime.now(),
                details=f"Module '{module_name}' was removed"
            ))
        
        # check for modified modules
        for module_name in current_modules & self._baseline_modules:
            if self._should_skip(module_name, whitelist):
                continue
            
            if module_name not in self._module_hashes:
                continue
            
            try:
                current_hash = self._hash_module(module_name)
                baseline_hash = self._module_hashes[module_name]
                
                if current_hash and current_hash != baseline_hash:
                    events.append(TamperEvent(
                        type=TamperType.MODULE_MODIFICATION,
                        target=module_name,
                        timestamp=datetime.now(),
                        baseline_hash=baseline_hash,
                        current_hash=current_hash,
                        details=f"Module '{module_name}' was modified"
                    ))
            except Exception:
                # couldn't verify module
                pass
        
        return events
    
    def _hash_module(self, module_name: str) -> Optional[str]:
        """
        Compute hash of a module's contents.
        
        Args:
            module_name: Name of module to hash
            
        Returns:
            Hash string or None if failed
        """
        module = sys.modules.get(module_name)
        if module is None:
            return None
        
        # collect hashable attributes
        data_parts = []
        
        # hash module-level functions
        for attr_name in dir(module):
            if attr_name.startswith('_'):
                continue
            
            try:
                attr = getattr(module, attr_name)
                
                # for functions, hash their bytecode
                if callable(attr) and hasattr(attr, '__code__'):
                    code_hash = self.hash_engine.hash_bytecode(attr.__code__)
                    data_parts.append(f"{attr_name}:{code_hash}")
                
            except Exception:
                pass
        
        # combine and hash
        if not data_parts:
            return None
        
        combined = "|".join(sorted(data_parts))
        return self.hash_engine.hash_bytes(combined.encode())
    
    def _should_skip(self, module_name: str, whitelist: List[str]) -> bool:
        """
        Check if module should be skipped.
        
        Args:
            module_name: Module name to check
            whitelist: List of patterns to skip
            
        Returns:
            True if should skip
        """
        import fnmatch
        
        for pattern in whitelist:
            if fnmatch.fnmatch(module_name, pattern):
                return True
        
        return False
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get module tracking statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            'baseline_modules': len(self._baseline_modules),
            'current_modules': len(sys.modules),
            'tracked_modules': len(self._module_hashes),
        }

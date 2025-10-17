"""Integrity verifier orchestrates checking across different components."""

import sys
import gc
from types import FunctionType, ModuleType
from typing import List, Optional, Dict, Set
from datetime import datetime

from ..models import TamperEvent, TamperType
from ..exceptions import VerificationError


class IntegrityVerifier:
    """Orchestrates integrity verification across multiple components."""
    
    def __init__(self, baseline, bytecode_analyzer, hash_engine):
        """
        Initialize verifier.
        
        Args:
            baseline: Baseline storage instance
            bytecode_analyzer: BytecodeAnalyzer instance
            hash_engine: HashEngine instance
        """
        self.baseline = baseline
        self.bytecode_analyzer = bytecode_analyzer
        self.hash_engine = hash_engine
        
        # track what we've seen to detect new items
        self._seen_modules: Set[str] = set()
        self._seen_functions: Set[str] = set()
    
    def verify_all(self, whitelist_modules: List[str] = None) -> List[TamperEvent]:
        """
        Run comprehensive verification check.
        
        Args:
            whitelist_modules: List of module name patterns to skip
            
        Returns:
            List of detected tamper events
        """
        events = []
        whitelist = whitelist_modules or []
        
        # check modules
        events.extend(self.verify_modules(whitelist))
        
        # check functions
        events.extend(self.verify_functions(whitelist))
        
        # check import hooks
        events.extend(self.verify_import_hooks())
        
        return events
    
    def verify_modules(self, whitelist: List[str] = None) -> List[TamperEvent]:
        """
        Verify all loaded modules.
        
        Args:
            whitelist: Module patterns to skip
            
        Returns:
            List of tamper events
        """
        events = []
        whitelist = whitelist or []
        
        current_modules = set(sys.modules.keys())
        
        # check for new modules (possible injection)
        if self._seen_modules:
            new_modules = current_modules - self._seen_modules
            for module_name in new_modules:
                # skip whitelisted
                if any(self._matches_pattern(module_name, pattern) for pattern in whitelist):
                    continue
                
                events.append(TamperEvent(
                    type=TamperType.MODULE_INJECTION,
                    target=module_name,
                    timestamp=datetime.now(),
                    details=f"New module '{module_name}' loaded after baseline"
                ))
        
        # check for removed modules
        removed_modules = self._seen_modules - current_modules
        for module_name in removed_modules:
            if any(self._matches_pattern(module_name, pattern) for pattern in whitelist):
                continue
            
            events.append(TamperEvent(
                type=TamperType.MODULE_REMOVAL,
                target=module_name,
                timestamp=datetime.now(),
                details=f"Module '{module_name}' was removed"
            ))
        
        # check existing modules for modifications
        for module_name in current_modules:
            if any(self._matches_pattern(module_name, pattern) for pattern in whitelist):
                continue
            
            if not self.baseline.has_module(module_name):
                continue
            
            module = sys.modules.get(module_name)
            if module is None:
                continue
            
            # compute current hash
            try:
                module_hash = self._hash_module(module)
                baseline_hash = self.baseline.get_module_hash(module_name)
                
                if baseline_hash and module_hash != baseline_hash:
                    events.append(TamperEvent(
                        type=TamperType.MODULE_MODIFICATION,
                        target=module_name,
                        timestamp=datetime.now(),
                        baseline_hash=baseline_hash,
                        current_hash=module_hash,
                        details=f"Module '{module_name}' was modified"
                    ))
            except Exception:
                # couldn't hash module, skip it
                pass
        
        # update seen modules
        self._seen_modules = current_modules
        
        return events
    
    def verify_functions(self, whitelist: List[str] = None) -> List[TamperEvent]:
        """
        Verify all tracked functions.
        
        Args:
            whitelist: Module patterns to skip
            
        Returns:
            List of tamper events
        """
        events = []
        whitelist = whitelist or []
        
        # get all function objects from gc
        functions = [obj for obj in gc.get_objects() if isinstance(obj, FunctionType)]
        
        for func in functions:
            # skip if in whitelisted module
            if hasattr(func, '__module__'):
                if any(self._matches_pattern(func.__module__, pattern) for pattern in whitelist):
                    continue
            
            # verify if it's tracked
            event = self.bytecode_analyzer.verify_function(func)
            if event:
                events.append(event)
        
        return events
    
    def verify_import_hooks(self) -> List[TamperEvent]:
        """
        Verify import hooks haven't been manipulated.
        
        Returns:
            List of tamper events
        """
        events = []
        
        # get current import hooks
        current_hooks = [str(type(hook)) for hook in sys.meta_path]
        baseline_hooks = self.baseline.get_import_hooks()
        
        if not baseline_hooks:
            return events
        
        # check if hooks changed
        if set(current_hooks) != set(baseline_hooks):
            events.append(TamperEvent(
                type=TamperType.IMPORT_HOOK_MANIPULATION,
                target="sys.meta_path",
                timestamp=datetime.now(),
                details=f"Import hooks modified: {current_hooks} vs {baseline_hooks}"
            ))
        
        return events
    
    def verify_function(self, func: FunctionType) -> Optional[TamperEvent]:
        """
        Verify a specific function.
        
        Args:
            func: Function to verify
            
        Returns:
            TamperEvent if tampering detected, None otherwise
        """
        return self.bytecode_analyzer.verify_function(func)
    
    def verify_module(self, module_name: str) -> Optional[TamperEvent]:
        """
        Verify a specific module.
        
        Args:
            module_name: Name of module to verify
            
        Returns:
            TamperEvent if tampering detected, None otherwise
        """
        if not self.baseline.has_module(module_name):
            return None
        
        module = sys.modules.get(module_name)
        if module is None:
            return TamperEvent(
                type=TamperType.MODULE_REMOVAL,
                target=module_name,
                timestamp=datetime.now(),
                details=f"Module '{module_name}' no longer loaded"
            )
        
        try:
            current_hash = self._hash_module(module)
            baseline_hash = self.baseline.get_module_hash(module_name)
            
            if baseline_hash and current_hash != baseline_hash:
                return TamperEvent(
                    type=TamperType.MODULE_MODIFICATION,
                    target=module_name,
                    timestamp=datetime.now(),
                    baseline_hash=baseline_hash,
                    current_hash=current_hash,
                    details=f"Module '{module_name}' was modified"
                )
        except Exception as e:
            # couldn't verify module
            pass
        
        return None
    
    def _hash_module(self, module: ModuleType) -> str:
        """
        Compute hash of a module's contents.
        
        Args:
            module: Module to hash
            
        Returns:
            Hash string
        """
        # hash the module's __dict__ contents
        # this is a simplified approach
        module_data = []
        
        for name in sorted(dir(module)):
            # skip private attributes and some special cases
            if name.startswith('_'):
                continue
            
            try:
                attr = getattr(module, name)
                
                # hash functions
                if isinstance(attr, FunctionType):
                    module_data.append(f"{name}:{self.bytecode_analyzer.hash_engine.hash_bytecode(attr.__code__)}")
                # hash other values by their repr
                else:
                    module_data.append(f"{name}:{hash(repr(attr))}")
            except Exception:
                # skip attributes we can't access
                pass
        
        # combine all attribute hashes
        combined = "|".join(module_data)
        return self.hash_engine.hash_bytes(combined.encode())
    
    def _matches_pattern(self, text: str, pattern: str) -> bool:
        """
        Check if text matches a pattern (with wildcards).
        
        Args:
            text: Text to check
            pattern: Pattern (supports * wildcard)
            
        Returns:
            True if matches
        """
        import fnmatch
        return fnmatch.fnmatch(text, pattern)
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get verification statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            'tracked_modules': len(self._seen_modules),
            'tracked_functions': self.bytecode_analyzer.get_baseline_size(),
            'baseline_modules': len([m for m in sys.modules if self.baseline.has_module(m)]),
        }

"""Import hook monitoring for detecting import system manipulation."""

import sys
import importlib.abc
import importlib.machinery
from typing import List, Optional, Set
from datetime import datetime

from ..models import TamperEvent, TamperType


class ImportHookMonitor:
    """Monitors Python's import system for manipulation."""
    
    def __init__(self):
        """Initialize import hook monitor."""
        self._baseline_hooks: List[str] = []
        self._cynapse_hook: Optional['CynapseImportHook'] = None
        self._installed = False
    
    def create_baseline(self) -> None:
        """Create baseline of current import hooks."""
        self._baseline_hooks = [self._hook_id(hook) for hook in sys.meta_path]
    
    def install_hook(self) -> None:
        """Install Cynapse's own import hook for monitoring."""
        if self._installed:
            return
        
        self._cynapse_hook = CynapseImportHook()
        sys.meta_path.insert(0, self._cynapse_hook)
        self._installed = True
    
    def uninstall_hook(self) -> None:
        """Remove Cynapse's import hook."""
        if not self._installed or self._cynapse_hook is None:
            return
        
        try:
            sys.meta_path.remove(self._cynapse_hook)
        except ValueError:
            pass
        
        self._installed = False
        self._cynapse_hook = None
    
    def check_for_manipulation(self) -> List[TamperEvent]:
        """
        Check if import hooks have been manipulated.
        
        Returns:
            List of tamper events
        """
        events = []
        
        if not self._baseline_hooks:
            return events
        
        current_hooks = [self._hook_id(hook) for hook in sys.meta_path]
        
        # filter out our own hook
        current_hooks_filtered = [
            h for h in current_hooks 
            if not h.startswith('CynapseImportHook')
        ]
        
        baseline_set = set(self._baseline_hooks)
        current_set = set(current_hooks_filtered)
        
        # check for new hooks
        new_hooks = current_set - baseline_set
        if new_hooks:
            events.append(TamperEvent(
                type=TamperType.IMPORT_HOOK_MANIPULATION,
                target="sys.meta_path",
                timestamp=datetime.now(),
                details=f"New import hooks added: {new_hooks}"
            ))
        
        # check for removed hooks
        removed_hooks = baseline_set - current_set
        if removed_hooks:
            events.append(TamperEvent(
                type=TamperType.IMPORT_HOOK_MANIPULATION,
                target="sys.meta_path",
                timestamp=datetime.now(),
                details=f"Import hooks removed: {removed_hooks}"
            ))
        
        return events
    
    def get_import_log(self) -> List[dict]:
        """
        Get log of imports since hook was installed.
        
        Returns:
            List of import events
        """
        if self._cynapse_hook:
            return self._cynapse_hook.get_log()
        return []
    
    def _hook_id(self, hook) -> str:
        """
        Get identifier for an import hook.
        
        Args:
            hook: Import hook object
            
        Returns:
            String identifier
        """
        return f"{type(hook).__name__}:{id(hook)}"


class CynapseImportHook(importlib.abc.MetaPathFinder):
    """Custom import hook for monitoring module imports."""
    
    def __init__(self):
        """Initialize the hook."""
        self._import_log: List[dict] = []
    
    def find_spec(self, fullname, path, target=None):
        """
        Called when importing a module.
        
        We log the import but don't actually handle it - return None
        to let other finders handle it.
        
        Args:
            fullname: Full module name being imported
            path: Path where to search
            target: Target module (optional)
            
        Returns:
            None (let other finders handle it)
        """
        # log the import attempt
        self._import_log.append({
            'timestamp': datetime.now(),
            'module': fullname,
            'path': path,
        })
        
        # return None to let other finders handle it
        return None
    
    def get_log(self) -> List[dict]:
        """Get the import log."""
        return self._import_log.copy()
    
    def clear_log(self) -> None:
        """Clear the import log."""
        self._import_log.clear()

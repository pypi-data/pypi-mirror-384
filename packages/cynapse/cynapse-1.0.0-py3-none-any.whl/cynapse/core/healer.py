"""Auto-healing module for restoring tampered code."""

import sys
from types import FunctionType, ModuleType
from typing import Optional

from ..models import TamperEvent, TamperType
from ..exceptions import RestorationError


class AutoHealer:
    """Automatically restores tampered code to baseline state."""
    
    def __init__(self, baseline, bytecode_analyzer):
        """
        Initialize auto-healer.
        
        Args:
            baseline: Baseline storage instance
            bytecode_analyzer: BytecodeAnalyzer instance
        """
        self.baseline = baseline
        self.bytecode_analyzer = bytecode_analyzer
        self._restoration_log = []
    
    def can_heal(self, event: TamperEvent) -> bool:
        """
        Check if an event can be auto-healed.
        
        Args:
            event: Tamper event to check
            
        Returns:
            True if healing is possible
        """
        return event.can_restore
    
    def heal(self, event: TamperEvent) -> bool:
        """
        Attempt to heal a tamper event.
        
        Args:
            event: Tamper event to heal
            
        Returns:
            True if healing succeeded, False otherwise
        """
        if not self.can_heal(event):
            return False
        
        try:
            if event.type == TamperType.BYTECODE_MODIFICATION:
                return self._heal_bytecode(event)
            elif event.type == TamperType.FUNCTION_REPLACEMENT:
                return self._heal_function_replacement(event)
            elif event.type == TamperType.MODULE_MODIFICATION:
                return self._heal_module(event)
            else:
                return False
        except Exception as e:
            # healing failed
            self._log_restoration(event, False, str(e))
            return False
    
    def _heal_bytecode(self, event: TamperEvent) -> bool:
        """
        Restore modified bytecode.
        
        Args:
            event: Tamper event
            
        Returns:
            True if successful
        """
        if not isinstance(event.target, FunctionType):
            return False
        
        func = event.target
        success = self.bytecode_analyzer.restore_function(func)
        
        self._log_restoration(event, success)
        return success
    
    def _heal_function_replacement(self, event: TamperEvent) -> bool:
        """
        Restore replaced function.
        
        Args:
            event: Tamper event
            
        Returns:
            True if successful
        """
        # same as bytecode restoration for now
        return self._heal_bytecode(event)
    
    def _heal_module(self, event: TamperEvent) -> bool:
        """
        Restore modified module.
        
        This is more complex as we need to restore all functions
        and attributes in the module.
        
        Args:
            event: Tamper event
            
        Returns:
            True if successful
        """
        if not isinstance(event.target, str):
            return False
        
        module_name = event.target
        module = sys.modules.get(module_name)
        
        if module is None:
            return False
        
        # for now, we can only restore functions within the module
        # full module restoration would require storing original module state
        success_count = 0
        total_count = 0
        
        for attr_name in dir(module):
            attr = getattr(module, attr_name, None)
            if isinstance(attr, FunctionType):
                total_count += 1
                if self.bytecode_analyzer.restore_function(attr):
                    success_count += 1
        
        success = success_count > 0 and success_count == total_count
        self._log_restoration(event, success, f"Restored {success_count}/{total_count} functions")
        
        return success
    
    def _log_restoration(self, event: TamperEvent, success: bool, message: str = ""):
        """
        Log a restoration attempt.
        
        Args:
            event: Tamper event
            success: Whether restoration succeeded
            message: Additional message
        """
        from datetime import datetime
        
        self._restoration_log.append({
            'timestamp': datetime.now(),
            'event_type': event.type.value,
            'target': str(event.target),
            'success': success,
            'message': message,
        })
    
    def get_restoration_log(self):
        """
        Get log of restoration attempts.
        
        Returns:
            List of restoration log entries
        """
        return self._restoration_log.copy()
    
    def clear_log(self):
        """Clear restoration log."""
        self._restoration_log.clear()
    
    def get_statistics(self):
        """
        Get healing statistics.
        
        Returns:
            Dictionary with statistics
        """
        total = len(self._restoration_log)
        successful = sum(1 for entry in self._restoration_log if entry['success'])
        
        return {
            'total_attempts': total,
            'successful': successful,
            'failed': total - successful,
            'success_rate': successful / total if total > 0 else 0.0,
        }

"""Monkey patch detection."""

from types import FunctionType
from typing import Dict, Set, List
from datetime import datetime

from ..models import TamperEvent, TamperType


class MonkeyPatchDetector:
    """Detects runtime function and attribute modifications."""
    
    def __init__(self):
        """Initialize monkey patch detector."""
        # track function.__dict__ for each monitored function
        self._function_dicts: Dict[int, dict] = {}
        
        # track object IDs
        self._function_ids: Dict[str, int] = {}
    
    def track_function(self, func: FunctionType) -> None:
        """
        Start tracking a function for monkey patching.
        
        Args:
            func: Function to track
        """
        func_key = self._get_function_key(func)
        func_id = id(func)
        
        # store the function ID
        self._function_ids[func_key] = func_id
        
        # store a copy of the function's __dict__
        self._function_dicts[func_id] = func.__dict__.copy()
    
    def check_function(self, func: FunctionType) -> List[TamperEvent]:
        """
        Check if a function has been monkey patched.
        
        Args:
            func: Function to check
            
        Returns:
            List of tamper events
        """
        events = []
        func_key = self._get_function_key(func)
        
        if func_key not in self._function_ids:
            return events
        
        baseline_id = self._function_ids[func_key]
        current_id = id(func)
        
        # check if the function object itself was replaced
        if current_id != baseline_id:
            events.append(TamperEvent(
                type=TamperType.FUNCTION_REPLACEMENT,
                target=func,
                timestamp=datetime.now(),
                details=f"Function {func.__name__} object was replaced"
            ))
            return events
        
        # check if __dict__ was modified
        if current_id in self._function_dicts:
            baseline_dict = self._function_dicts[current_id]
            current_dict = func.__dict__
            
            # check for new attributes
            new_attrs = set(current_dict.keys()) - set(baseline_dict.keys())
            if new_attrs:
                events.append(TamperEvent(
                    type=TamperType.ATTRIBUTE_MODIFICATION,
                    target=func,
                    timestamp=datetime.now(),
                    details=f"New attributes added to {func.__name__}: {new_attrs}"
                ))
            
            # check for removed attributes
            removed_attrs = set(baseline_dict.keys()) - set(current_dict.keys())
            if removed_attrs:
                events.append(TamperEvent(
                    type=TamperType.ATTRIBUTE_MODIFICATION,
                    target=func,
                    timestamp=datetime.now(),
                    details=f"Attributes removed from {func.__name__}: {removed_attrs}"
                ))
            
            # check for modified attributes
            for key in set(baseline_dict.keys()) & set(current_dict.keys()):
                if baseline_dict[key] != current_dict[key]:
                    events.append(TamperEvent(
                        type=TamperType.ATTRIBUTE_MODIFICATION,
                        target=func,
                        timestamp=datetime.now(),
                        details=f"Attribute {key} modified on {func.__name__}"
                    ))
        
        return events
    
    def check_class_methods(self, cls: type) -> List[TamperEvent]:
        """
        Check all methods in a class for monkey patching.
        
        Args:
            cls: Class to check
            
        Returns:
            List of tamper events
        """
        events = []
        
        for attr_name in dir(cls):
            if attr_name.startswith('_'):
                continue
            
            try:
                attr = getattr(cls, attr_name)
                if isinstance(attr, FunctionType):
                    events.extend(self.check_function(attr))
            except Exception:
                pass
        
        return events
    
    def _get_function_key(self, func: FunctionType) -> str:
        """
        Get a unique key for a function.
        
        Args:
            func: Function to key
            
        Returns:
            Unique key string
        """
        module = func.__module__ if hasattr(func, '__module__') else ''
        qualname = func.__qualname__ if hasattr(func, '__qualname__') else func.__name__
        return f"{module}.{qualname}"

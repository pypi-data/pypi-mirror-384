"""Decorators for easy function and class protection."""

import functools
from types import FunctionType
from typing import TypeVar, Callable, Any

from .monitor import Monitor

# type variables for decorator typing
F = TypeVar('F', bound=Callable[..., Any])
T = TypeVar('T', bound=type)


def protect_function(func: F) -> F:
    """
    Decorator to protect a function from tampering.
    
    Usage:
        @protect_function
        def sensitive_operation():
            pass
    
    Args:
        func: Function to protect
        
    Returns:
        Protected function
    """
    # get or create monitor instance
    monitor = Monitor()
    
    # protect the function
    monitor.protect_function(func)
    
    # return the function unchanged
    return func


def protect_class(cls: T) -> T:
    """
    Decorator to protect all methods in a class.
    
    Usage:
        @protect_class
        class SecureAPI:
            def authenticate(self):
                pass
    
    Args:
        cls: Class to protect
        
    Returns:
        Protected class
    """
    # get or create monitor instance
    monitor = Monitor()
    
    # protect all methods
    for attr_name in dir(cls):
        if attr_name.startswith('_'):
            continue
        
        attr = getattr(cls, attr_name)
        if isinstance(attr, FunctionType):
            monitor.protect_function(attr)
    
    return cls


def protect_method(func: F) -> F:
    """
    Decorator to protect a class method.
    
    Usage:
        class API:
            @protect_method
            def authenticate(self):
                pass
    
    Args:
        func: Method to protect
        
    Returns:
        Protected method
    """
    return protect_function(func)


def monitored(interval: float = 3.0, strict: bool = False):
    """
    Decorator to run a function with active monitoring.
    
    The monitor starts before the function runs and stops after.
    
    Usage:
        @monitored(interval=2.0)
        def main():
            # code runs with active monitoring
            pass
    
    Args:
        interval: Monitoring interval in seconds
        strict: If True, terminates on any tampering
        
    Returns:
        Decorator function
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            monitor = Monitor(interval=interval)
            
            with monitor:
                return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def async_monitored(interval: float = 3.0, strict: bool = False):
    """
    Decorator to run an async function with active monitoring.
    
    Usage:
        @async_monitored(interval=2.0)
        async def main():
            # async code runs with active monitoring
            pass
    
    Args:
        interval: Monitoring interval in seconds
        strict: If True, terminates on any tampering
        
    Returns:
        Decorator function
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            from .async_monitor import AsyncMonitor
            monitor = AsyncMonitor(interval=interval)
            
            async with monitor:
                return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator

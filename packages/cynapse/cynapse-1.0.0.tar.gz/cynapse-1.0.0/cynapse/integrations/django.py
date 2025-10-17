"""Django integration for cynapse."""

from typing import Optional, Callable

from ..monitor import Monitor
from ..models import MonitorConfig


class CynapseMiddleware:
    """Django middleware for cynapse monitoring."""
    
    _monitor: Optional[Monitor] = None
    
    def __init__(self, get_response: Callable):
        """
        Initialize Django middleware.
        
        Args:
            get_response: Django's get_response callable
        """
        self.get_response = get_response
        
        # create monitor if not already created
        if CynapseMiddleware._monitor is None:
            # get configuration from Django settings
            from django.conf import settings
            
            config_dict = getattr(settings, 'CYNAPSE_CONFIG', {})
            
            CynapseMiddleware._monitor = Monitor(**config_dict)
            CynapseMiddleware._monitor.start()
    
    def __call__(self, request):
        """
        Process request.
        
        Args:
            request: Django request object
            
        Returns:
            Response
        """
        # monitoring happens in background thread
        # just pass through the request
        response = self.get_response(request)
        return response
    
    @classmethod
    def get_monitor(cls) -> Optional[Monitor]:
        """
        Get the monitor instance.
        
        Returns:
            Monitor instance or None
        """
        return cls._monitor


def protect_view(view_func):
    """
    Decorator to protect a Django view.
    
    Usage:
        @protect_view
        def my_view(request):
            return HttpResponse("protected")
    
    Args:
        view_func: View function to protect
        
    Returns:
        Protected view function
    """
    monitor = CynapseMiddleware.get_monitor()
    if monitor:
        monitor.protect_function(view_func)
    return view_func

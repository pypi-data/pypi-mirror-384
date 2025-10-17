"""FastAPI integration for cynapse."""

from typing import List, Optional

try:
    from fastapi import FastAPI, Request
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

from ..async_monitor import AsyncMonitor
from ..models import MonitorConfig


class FastAPIMonitor:
    """FastAPI integration for cynapse monitoring."""
    
    def __init__(
        self, 
        app: Optional['FastAPI'] = None, 
        interval: float = 5.0,
        protect_routes: Optional[List[str]] = None,
        **kwargs
    ):
        """
        Initialize FastAPI monitor.
        
        Args:
            app: FastAPI application instance
            interval: Monitoring interval
            protect_routes: List of route patterns to protect
            **kwargs: Additional monitor configuration
        """
        if not FASTAPI_AVAILABLE:
            raise ImportError("FastAPI is not installed. Install it with: pip install fastapi")
        
        self.app = app
        self.protect_routes = protect_routes or []
        
        # create async monitor
        self.monitor = AsyncMonitor(interval=interval, **kwargs)
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: 'FastAPI') -> None:
        """
        Initialize with FastAPI app.
        
        Args:
            app: FastAPI application instance
        """
        self.app = app
        
        # register startup event to start monitoring
        @app.on_event("startup")
        async def start_monitoring():
            await self.monitor.start_async()
        
        # register shutdown event to stop monitoring
        @app.on_event("shutdown")
        async def stop_monitoring():
            await self.monitor.stop_async()
        
        # add middleware for monitoring
        @app.middleware("http")
        async def cynapse_middleware(request: Request, call_next):
            # monitoring happens in background task
            response = await call_next(request)
            return response
    
    def protect_endpoint(self, func):
        """
        Decorator to protect a specific FastAPI endpoint.
        
        Usage:
            @app.get("/secure")
            @monitor.protect_endpoint
            async def secure_endpoint():
                return {"status": "protected"}
        
        Args:
            func: Endpoint function to protect
            
        Returns:
            Protected function
        """
        self.monitor.protect_function(func)
        return func

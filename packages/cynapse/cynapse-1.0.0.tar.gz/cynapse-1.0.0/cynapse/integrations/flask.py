"""Flask integration for cynapse."""

from typing import List, Optional

try:
    from flask import Flask, request
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

from ..monitor import Monitor
from ..models import MonitorConfig


class FlaskMonitor:
    """Flask integration for cynapse monitoring."""
    
    def __init__(
        self, 
        app: Optional['Flask'] = None, 
        interval: float = 5.0,
        protect_routes: Optional[List[str]] = None,
        **kwargs
    ):
        """
        Initialize Flask monitor.
        
        Args:
            app: Flask application instance
            interval: Monitoring interval
            protect_routes: List of route patterns to protect
            **kwargs: Additional monitor configuration
        """
        if not FLASK_AVAILABLE:
            raise ImportError("Flask is not installed. Install it with: pip install flask")
        
        self.app = app
        self.protect_routes = protect_routes or []
        
        # create monitor
        self.monitor = Monitor(interval=interval, **kwargs)
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: 'Flask') -> None:
        """
        Initialize with Flask app.
        
        Args:
            app: Flask application instance
        """
        self.app = app
        
        # register before_first_request to start monitoring
        @app.before_first_request
        def start_monitoring():
            self.monitor.start()
        
        # register teardown to stop monitoring
        @app.teardown_appcontext
        def stop_monitoring(exception=None):
            self.monitor.stop()
        
        # protect route handlers if specified
        if self.protect_routes:
            self._protect_routes()
    
    def _protect_routes(self) -> None:
        """Protect specified routes."""
        if not self.app:
            return
        
        for rule in self.app.url_map.iter_rules():
            # check if this route should be protected
            should_protect = any(
                pattern in rule.rule 
                for pattern in self.protect_routes
            )
            
            if should_protect and rule.endpoint:
                view_func = self.app.view_functions.get(rule.endpoint)
                if view_func:
                    self.monitor.protect_function(view_func)
    
    def protect_endpoint(self, func):
        """
        Decorator to protect a specific Flask endpoint.
        
        Usage:
            @app.route('/secure')
            @monitor.protect_endpoint
            def secure_view():
                return "protected"
        
        Args:
            func: View function to protect
            
        Returns:
            Protected function
        """
        self.monitor.protect_function(func)
        return func

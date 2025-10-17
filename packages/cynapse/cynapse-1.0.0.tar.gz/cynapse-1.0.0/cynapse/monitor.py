"""Main monitor class for cynapse."""

import gc
import sys
import threading
import time
from types import FunctionType
from typing import List, Optional, Callable
from datetime import datetime

from .models import (
    MonitorConfig, MonitorStatus, TamperEvent, TamperResponse,
    ProtectionLevel, TamperType
)
from .exceptions import InitializationError, ConfigurationError
from .core.hash_engine import HashEngine
from .core.baseline import Baseline
from .core.bytecode import BytecodeAnalyzer
from .core.verifier import IntegrityVerifier
from .core.healer import AutoHealer
from .introspection.modules import ModuleTracker
from .introspection.imports import ImportHookMonitor
from .detection.monkey_patch import MonkeyPatchDetector


class Monitor:
    """Main integrity monitoring class."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """Ensure only one monitor instance exists (singleton)."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Optional[MonitorConfig] = None, **kwargs):
        """
        Initialize monitor.
        
        Args:
            config: Monitor configuration
            **kwargs: Configuration parameters as keywords
        """
        # avoid re-initialization
        if hasattr(self, '_initialized'):
            return
        
        # create config from kwargs if not provided
        if config is None:
            config = MonitorConfig(**kwargs)
        
        self.config = config
        
        # initialize components
        self.hash_engine = HashEngine(
            algorithm=config.hash_algorithm,
            cache_size=1024
        )
        self.baseline = Baseline(compress=True)
        self.bytecode_analyzer = BytecodeAnalyzer(self.hash_engine)
        self.verifier = IntegrityVerifier(
            self.baseline,
            self.bytecode_analyzer,
            self.hash_engine
        )
        self.healer = AutoHealer(self.baseline, self.bytecode_analyzer)
        self.module_tracker = ModuleTracker(self.hash_engine)
        self.import_monitor = ImportHookMonitor()
        self.monkey_patch_detector = MonkeyPatchDetector()
        
        # monitoring state
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # statistics
        self._checks_performed = 0
        self._tamper_events: List[TamperEvent] = []
        self._last_check: Optional[datetime] = None
        
        # callback handlers
        self._tamper_callbacks: List[Callable[[TamperEvent], Optional[TamperResponse]]] = []
        
        if config.on_tamper:
            self._tamper_callbacks.append(config.on_tamper)
        
        self._initialized = True
    
    @classmethod
    def builder(cls):
        """
        Get a builder for fluent configuration.
        
        Returns:
            MonitorBuilder instance
        """
        from .utils.config import MonitorBuilder
        return MonitorBuilder()
    
    def start(self) -> None:
        """Start integrity monitoring."""
        if self._running:
            return
        
        # create baseline
        self._create_baseline()
        
        # install import hooks if enabled
        if self.config.enable_import_hooks:
            self.import_monitor.install_hook()
        
        # start monitoring thread
        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="cynapse-monitor"
        )
        self._thread.start()
    
    def stop(self) -> None:
        """Stop integrity monitoring."""
        if not self._running:
            return
        
        self._running = False
        self._stop_event.set()
        
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None
        
        # uninstall import hooks
        if self.config.enable_import_hooks:
            self.import_monitor.uninstall_hook()
    
    def protect_function(self, func: FunctionType) -> None:
        """
        Add a function to be protected.
        
        Args:
            func: Function to protect
        """
        # register with bytecode analyzer
        code_hash = self.bytecode_analyzer.register_function(func)
        
        # add to baseline
        func_id = self.bytecode_analyzer._get_function_id(func)
        self.baseline.add_function(func_id, code_hash)
        
        # track for monkey patching
        self.monkey_patch_detector.track_function(func)
    
    def protect_module(self, module_name: str) -> None:
        """
        Add a module to be protected.
        
        Args:
            module_name: Name of module to protect
        """
        if module_name not in self.config.protect_modules:
            self.config.protect_modules.append(module_name)
    
    def verify_now(self) -> List[TamperEvent]:
        """
        Perform immediate verification check.
        
        Returns:
            List of detected tamper events
        """
        events = []
        
        # check modules
        if self.config.enable_module_tracking:
            events.extend(self.module_tracker.check_for_changes(
                self.config.whitelist_modules
            ))
        
        # check bytecode
        if self.config.enable_bytecode_verification:
            events.extend(self.verifier.verify_functions(
                self.config.whitelist_modules
            ))
        
        # check import hooks
        if self.config.enable_import_hooks:
            events.extend(self.import_monitor.check_for_manipulation())
        
        return events
    
    def get_status(self) -> MonitorStatus:
        """
        Get current monitoring status.
        
        Returns:
            MonitorStatus object
        """
        import os
        
        # get process info for CPU and memory usage
        # psutil is optional, gracefully degrade if not available
        cpu_usage = 0.0
        memory_usage = 0
        
        try:
            import psutil
            process = psutil.Process(os.getpid())
            cpu_usage = process.cpu_percent()
            memory_usage = process.memory_info().rss
        except ImportError:
            # psutil not installed, that's okay
            pass
        except Exception:
            # other error getting process info
            pass
        
        return MonitorStatus(
            running=self._running,
            baseline_created=self.baseline.created_at,
            last_check=self._last_check,
            checks_performed=self._checks_performed,
            tamper_events=len(self._tamper_events),
            protected_functions=self.bytecode_analyzer.get_baseline_size(),
            protected_modules=len(self.config.protect_modules),
            cpu_usage=cpu_usage,
            memory_usage=memory_usage
        )
    
    def on_tamper(self, callback: Callable[[TamperEvent], Optional[TamperResponse]]) -> None:
        """
        Register a callback for tamper events.
        
        Args:
            callback: Function to call when tampering is detected
        """
        self._tamper_callbacks.append(callback)
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False
    
    def _create_baseline(self) -> None:
        """Create integrity baseline."""
        # create baseline timestamp
        self.baseline.create()
        
        # baseline modules
        if self.config.enable_module_tracking:
            self.module_tracker.create_baseline(self.config.whitelist_modules)
        
        # baseline import hooks
        if self.config.enable_import_hooks:
            self.import_monitor.create_baseline()
            hooks = [str(type(h)) for h in sys.meta_path]
            for hook in hooks:
                self.baseline.add_import_hook(hook)
        
        # baseline all functions
        if self.config.enable_bytecode_verification:
            self._baseline_all_functions()
    
    def _baseline_all_functions(self) -> None:
        """Create baseline for all existing functions."""
        # get all function objects
        functions = [obj for obj in gc.get_objects() if isinstance(obj, FunctionType)]
        
        for func in functions:
            # skip if in whitelisted module
            if hasattr(func, '__module__'):
                module = func.__module__
                if any(module.startswith(pattern.rstrip('*')) 
                       for pattern in self.config.whitelist_modules):
                    continue
            
            try:
                self.protect_function(func)
            except Exception:
                # couldn't baseline this function
                pass
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop running in background thread."""
        while not self._stop_event.is_set():
            try:
                # perform verification
                events = self.verify_now()
                
                # update statistics
                self._checks_performed += 1
                self._last_check = datetime.now()
                
                # handle any detected events
                if events:
                    for event in events:
                        self._handle_tamper_event(event)
                
                # wait for next interval
                self._stop_event.wait(self.config.interval)
                
            except Exception as e:
                # log error but keep running
                import logging
                logging.error(f"Error in monitoring loop: {e}")
                self._stop_event.wait(self.config.interval)
    
    def _handle_tamper_event(self, event: TamperEvent) -> None:
        """
        Handle a detected tamper event.
        
        Args:
            event: TamperEvent to handle
        """
        # add to event list
        self._tamper_events.append(event)
        
        # determine response
        response = self.config.tamper_response
        
        # call callbacks
        for callback in self._tamper_callbacks:
            try:
                result = callback(event)
                if result is not None:
                    response = result
                    break
            except Exception as e:
                import logging
                logging.error(f"Error in tamper callback: {e}")
        
        # execute response
        self._execute_response(event, response)
    
    def _execute_response(self, event: TamperEvent, response: TamperResponse) -> None:
        """
        Execute a tamper response.
        
        Args:
            event: TamperEvent that triggered response
            response: TamperResponse to execute
        """
        import logging
        
        if response == TamperResponse.ALERT:
            logging.warning(f"Tamper detected: {event}")
        
        elif response == TamperResponse.RESTORE:
            if self.config.enable_auto_healing and event.can_restore:
                success = self.healer.heal(event)
                if success:
                    logging.info(f"Successfully restored: {event}")
                else:
                    logging.error(f"Failed to restore: {event}")
        
        elif response == TamperResponse.SNAPSHOT:
            if self.config.enable_forensics:
                self._capture_forensic_snapshot(event)
        
        elif response == TamperResponse.TERMINATE:
            logging.critical(f"Terminating due to tamper event: {event}")
            self.stop()
            sys.exit(1)
    
    def _capture_forensic_snapshot(self, event: TamperEvent) -> None:
        """
        Capture forensic snapshot of a tamper event.
        
        Args:
            event: TamperEvent to capture
        """
        # implementation would save detailed forensic data
        # for now, just log it
        import logging
        logging.info(f"Capturing forensic snapshot for: {event}")

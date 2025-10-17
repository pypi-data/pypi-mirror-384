"""Async version of the monitor for asyncio applications."""

import asyncio
import sys
from types import FunctionType
from typing import List, Optional, Callable
from datetime import datetime

from .models import (
    MonitorConfig, MonitorStatus, TamperEvent, TamperResponse,
    ProtectionLevel
)
from .monitor import Monitor


class AsyncMonitor(Monitor):
    """Async version of Monitor for asyncio applications."""
    
    def __init__(self, config: Optional[MonitorConfig] = None, **kwargs):
        """
        Initialize async monitor.
        
        Args:
            config: Monitor configuration
            **kwargs: Configuration parameters as keywords
        """
        super().__init__(config, **kwargs)
        self._task: Optional[asyncio.Task] = None
    
    async def start_async(self) -> None:
        """Start integrity monitoring in async mode."""
        if self._running:
            return
        
        # create baseline
        self._create_baseline()
        
        # install import hooks if enabled
        if self.config.enable_import_hooks:
            self.import_monitor.install_hook()
        
        # start monitoring task
        self._running = True
        self._task = asyncio.create_task(self._monitoring_loop_async())
    
    async def stop_async(self) -> None:
        """Stop integrity monitoring."""
        if not self._running:
            return
        
        self._running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        
        # uninstall import hooks
        if self.config.enable_import_hooks:
            self.import_monitor.uninstall_hook()
    
    async def verify_now_async(self) -> List[TamperEvent]:
        """
        Perform immediate verification check (async).
        
        Returns:
            List of detected tamper events
        """
        # run verification in executor to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.verify_now)
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_async()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop_async()
        return False
    
    async def _monitoring_loop_async(self) -> None:
        """Async monitoring loop."""
        while self._running:
            try:
                # perform verification (run in executor to avoid blocking)
                loop = asyncio.get_event_loop()
                events = await loop.run_in_executor(None, self.verify_now)
                
                # update statistics
                self._checks_performed += 1
                self._last_check = datetime.now()
                
                # handle any detected events
                if events:
                    for event in events:
                        self._handle_tamper_event(event)
                
                # wait for next interval
                await asyncio.sleep(self.config.interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                # log error but keep running
                import logging
                logging.error(f"Error in async monitoring loop: {e}")
                await asyncio.sleep(self.config.interval)

"""Tests for the Monitor class."""

import pytest
import time
from cynapse import Monitor, MonitorConfig, ProtectionLevel, TamperResponse

def test_monitor_initialization():
    """Test monitor can be initialized."""
    monitor = Monitor()
    assert monitor is not None
    assert not monitor._running

def test_monitor_singleton():
    """Test monitor follows singleton pattern."""
    monitor1 = Monitor()
    monitor2 = Monitor()
    assert monitor1 is monitor2

def test_monitor_start_stop():
    """Test monitor can start and stop."""
    monitor = Monitor(interval=1.0)
    
    monitor.start()
    assert monitor._running
    
    time.sleep(2)  # let it run a bit
    
    monitor.stop()
    assert not monitor._running

def test_monitor_context_manager():
    """Test monitor works as context manager."""
    with Monitor(interval=1.0) as monitor:
        assert monitor._running
        time.sleep(1)
    
    # should be stopped after exiting context
    assert not monitor._running

def test_protect_function():
    """Test protecting a function."""
    def test_func():
        return "test"
    
    monitor = Monitor()
    monitor.protect_function(test_func)
    
    # should be in baseline
    func_id = monitor.bytecode_analyzer._get_function_id(test_func)
    assert func_id in monitor.bytecode_analyzer._baseline

def test_monitor_config():
    """Test monitor configuration."""
    config = MonitorConfig(
        interval=5.0,
        protection_level=ProtectionLevel.HIGH,
        enable_bytecode_verification=True,
        enable_module_tracking=False,
    )
    
    monitor = Monitor(config=config)
    assert monitor.config.interval == 5.0
    assert monitor.config.protection_level == ProtectionLevel.HIGH
    assert monitor.config.enable_bytecode_verification
    assert not monitor.config.enable_module_tracking

def test_monitor_builder():
    """Test monitor builder pattern."""
    monitor = Monitor.builder() \
        .interval(2.0) \
        .protection_level(ProtectionLevel.PARANOID) \
        .enable_auto_healing(True) \
        .build()
    
    assert monitor.config.interval == 2.0
    assert monitor.config.protection_level == ProtectionLevel.PARANOID
    assert monitor.config.enable_auto_healing

def test_verify_now():
    """Test immediate verification."""
    monitor = Monitor(interval=1.0)
    monitor.start()
    
    time.sleep(1)
    events = monitor.verify_now()
    
    assert isinstance(events, list)
    monitor.stop()

def test_get_status():
    """Test getting monitor status."""
    monitor = Monitor(interval=1.0)
    monitor.start()
    
    time.sleep(2)
    status = monitor.get_status()
    
    assert status.running
    assert status.checks_performed > 0
    assert status.baseline_created is not None
    
    monitor.stop()

def test_tamper_callback():
    """Test tamper event callback."""
    callback_called = []
    
    def my_callback(event):
        callback_called.append(event)
        return TamperResponse.ALERT
    
    monitor = Monitor(interval=1.0)
    monitor.on_tamper(my_callback)
    
    # callbacks registered
    assert len(monitor._tamper_callbacks) > 0

def test_whitelist_modules():
    """Test module whitelisting."""
    monitor = Monitor(
        whitelist_modules=['pytest', '_pytest', 'pluggy']
    )
    
    assert 'pytest' in monitor.config.whitelist_modules

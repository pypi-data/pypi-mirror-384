"""Tests for decorators."""

import pytest
import asyncio
from cynapse import protect_function, protect_class, Monitor

def test_protect_function_decorator():
    """Test protect_function decorator."""
    
    @protect_function
    def secure_func():
        return "secure"
    
    # function should still work
    result = secure_func()
    assert result == "secure"
    
    # should be registered with monitor
    monitor = Monitor()
    func_id = monitor.bytecode_analyzer._get_function_id(secure_func)
    assert func_id in monitor.bytecode_analyzer._baseline

def test_protect_class_decorator():
    """Test protect_class decorator."""
    
    @protect_class
    class SecureClass:
        def method1(self):
            return "method1"
        
        def method2(self):
            return "method2"
    
    # class should still work
    obj = SecureClass()
    assert obj.method1() == "method1"
    assert obj.method2() == "method2"
    
    # methods should be protected
    monitor = Monitor()
    # check at least one method is registered
    assert monitor.bytecode_analyzer.get_baseline_size() > 0

def test_multiple_protections():
    """Test protecting multiple functions."""
    
    @protect_function
    def func1():
        return 1
    
    @protect_function
    def func2():
        return 2
    
    @protect_function
    def func3():
        return 3
    
    assert func1() == 1
    assert func2() == 2
    assert func3() == 3
    
    monitor = Monitor()
    # all should be registered
    assert monitor.bytecode_analyzer.get_baseline_size() >= 3

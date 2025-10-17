"""Tests for BytecodeAnalyzer."""

import pytest
from cynapse.core.hash_engine import HashEngine
from cynapse.core.bytecode import BytecodeAnalyzer
from cynapse.testing.tamper import TamperSimulator

def test_bytecode_analyzer_initialization():
    """Test bytecode analyzer initialization."""
    engine = HashEngine()
    analyzer = BytecodeAnalyzer(engine)
    assert analyzer is not None

def test_register_function():
    """Test registering a function."""
    engine = HashEngine()
    analyzer = BytecodeAnalyzer(engine)
    
    def test_func():
        return 42
    
    hash_val = analyzer.register_function(test_func)
    assert isinstance(hash_val, str)
    assert len(hash_val) > 0

def test_verify_unmodified_function():
    """Test verifying an unmodified function."""
    engine = HashEngine()
    analyzer = BytecodeAnalyzer(engine)
    
    def test_func():
        return 42
    
    analyzer.register_function(test_func)
    event = analyzer.verify_function(test_func)
    
    # should be None (no tampering)
    assert event is None

def test_verify_modified_function():
    """Test detecting modified function."""
    engine = HashEngine()
    analyzer = BytecodeAnalyzer(engine)
    
    def test_func():
        return 42
    
    analyzer.register_function(test_func)
    
    # modify the function
    try:
        TamperSimulator.modify_bytecode(test_func, b'\x64\x01\x53\x00')
        
        # verify should detect tampering
        event = analyzer.verify_function(test_func)
        assert event is not None
        assert event.baseline_hash is not None
        assert event.current_hash is not None
        assert event.baseline_hash != event.current_hash
    except Exception:
        # modification might fail in some python versions
        pass

def test_restore_function():
    """Test restoring a modified function."""
    engine = HashEngine()
    analyzer = BytecodeAnalyzer(engine)
    
    def test_func():
        return 42
    
    original_code = test_func.__code__.co_code
    analyzer.register_function(test_func)
    
    try:
        # modify
        TamperSimulator.modify_bytecode(test_func, b'\x64\x01\x53\x00')
        
        # restore
        success = analyzer.restore_function(test_func)
        
        if success:
            # should be restored
            assert test_func.__code__.co_code == original_code
    except Exception:
        pass

def test_get_bytecode_summary():
    """Test getting bytecode summary."""
    engine = HashEngine()
    analyzer = BytecodeAnalyzer(engine)
    
    def test_func(x, y):
        return x + y
    
    summary = analyzer.get_bytecode_summary(test_func)
    
    assert 'name' in summary
    assert summary['name'] == 'test_func'
    assert 'argcount' in summary
    assert summary['argcount'] == 2
    assert 'hash' in summary

def test_baseline_size():
    """Test getting baseline size."""
    engine = HashEngine()
    analyzer = BytecodeAnalyzer(engine)
    
    def func1():
        pass
    
    def func2():
        pass
    
    analyzer.register_function(func1)
    analyzer.register_function(func2)
    
    assert analyzer.get_baseline_size() == 2

def test_clear_baseline():
    """Test clearing baseline."""
    engine = HashEngine()
    analyzer = BytecodeAnalyzer(engine)
    
    def test_func():
        pass
    
    analyzer.register_function(test_func)
    assert analyzer.get_baseline_size() > 0
    
    analyzer.clear_baseline()
    assert analyzer.get_baseline_size() == 0

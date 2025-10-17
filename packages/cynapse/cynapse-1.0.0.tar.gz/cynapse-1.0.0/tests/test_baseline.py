"""Tests for Baseline storage."""

import pytest
import tempfile
import os
from datetime import datetime
from cynapse.core.baseline import Baseline

def test_baseline_initialization():
    """Test baseline initialization."""
    baseline = Baseline()
    assert baseline is not None
    assert baseline.created_at is None

def test_baseline_create():
    """Test creating baseline."""
    baseline = Baseline()
    baseline.create()
    
    assert baseline.created_at is not None
    assert isinstance(baseline.created_at, datetime)

def test_add_function():
    """Test adding function to baseline."""
    baseline = Baseline()
    baseline.add_function("test.func", "abc123hash")
    
    assert baseline.has_function("test.func")
    assert baseline.get_function_hash("test.func") == "abc123hash"

def test_add_module():
    """Test adding module to baseline."""
    baseline = Baseline()
    baseline.add_module("test_module", "def456hash")
    
    assert baseline.has_module("test_module")
    assert baseline.get_module_hash("test_module") == "def456hash"

def test_add_memory_region():
    """Test adding memory region to baseline."""
    baseline = Baseline()
    hashes = ["hash1", "hash2", "hash3"]
    baseline.add_memory_region("region_1", hashes)
    
    retrieved = baseline.get_memory_hashes("region_1")
    assert retrieved == hashes

def test_add_import_hook():
    """Test adding import hook."""
    baseline = Baseline()
    baseline.add_import_hook("TestFinder")
    baseline.add_import_hook("AnotherFinder")
    
    hooks = baseline.get_import_hooks()
    assert "TestFinder" in hooks
    assert "AnotherFinder" in hooks

def test_get_statistics():
    """Test getting baseline statistics."""
    baseline = Baseline()
    baseline.create()
    baseline.add_function("func1", "hash1")
    baseline.add_function("func2", "hash2")
    baseline.add_module("mod1", "hash3")
    
    stats = baseline.get_statistics()
    assert stats['function_count'] == 2
    assert stats['module_count'] == 1
    assert 'created_at' in stats

def test_save_and_load():
    """Test saving and loading baseline."""
    baseline = Baseline()
    baseline.create()
    baseline.add_function("test_func", "hash123")
    baseline.add_module("test_mod", "hash456")
    
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        # save
        baseline.save(tmp_path)
        assert os.path.exists(tmp_path)
        
        # load into new baseline
        baseline2 = Baseline()
        baseline2.load(tmp_path)
        
        assert baseline2.has_function("test_func")
        assert baseline2.get_function_hash("test_func") == "hash123"
        assert baseline2.has_module("test_mod")
        
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

def test_export_json():
    """Test exporting baseline as JSON."""
    baseline = Baseline()
    baseline.create()
    baseline.add_function("func1", "hash1")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp:
        tmp_path = tmp.name
    
    try:
        baseline.export_json(tmp_path)
        assert os.path.exists(tmp_path)
        
        # read and verify it's valid JSON
        import json
        with open(tmp_path, 'r') as f:
            data = json.load(f)
        
        assert 'function_hashes' in data
        assert 'func1' in data['function_hashes']
        
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

def test_clear():
    """Test clearing baseline."""
    baseline = Baseline()
    baseline.create()
    baseline.add_function("func1", "hash1")
    baseline.add_module("mod1", "hash2")
    
    baseline.clear()
    
    assert not baseline.has_function("func1")
    assert not baseline.has_module("mod1")
    assert baseline.created_at is None

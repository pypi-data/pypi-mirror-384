"""Tests for HashEngine."""

import pytest
from cynapse.core.hash_engine import HashEngine

def test_hash_engine_initialization():
    """Test hash engine initialization."""
    engine = HashEngine()
    assert engine.algorithm == "sha256"

def test_hash_bytes():
    """Test hashing bytes."""
    engine = HashEngine()
    data = b"test data"
    
    hash1 = engine.hash_bytes(data)
    hash2 = engine.hash_bytes(data)
    
    # same data should produce same hash
    assert hash1 == hash2
    assert len(hash1) == 64  # sha256 produces 64 hex chars

def test_hash_bytecode():
    """Test hashing function bytecode."""
    engine = HashEngine()
    
    def test_func():
        return 42
    
    hash1 = engine.hash_bytecode(test_func.__code__)
    assert isinstance(hash1, str)
    assert len(hash1) == 64

def test_hash_caching():
    """Test hash caching."""
    engine = HashEngine(cache_size=10)
    data = b"cached data"
    
    # first call - cache miss
    hash1 = engine.hash_bytes(data)
    info1 = engine.get_cache_info()
    
    # second call - cache hit
    hash2 = engine.hash_bytes(data)
    info2 = engine.get_cache_info()
    
    assert hash1 == hash2
    assert info2['hits'] > info1['hits']

def test_cache_clear():
    """Test clearing cache."""
    engine = HashEngine()
    engine.hash_bytes(b"test")
    
    info_before = engine.get_cache_info()
    assert info_before['size'] > 0
    
    engine.clear_cache()
    info_after = engine.get_cache_info()
    assert info_after['size'] == 0

def test_blake3_fallback():
    """Test graceful fallback when blake3 not available."""
    # request blake3 but it might not be installed
    engine = HashEngine(algorithm="blake3")
    
    # should fall back to sha256 if blake3 not available
    hash_result = engine.hash_bytes(b"test")
    assert isinstance(hash_result, str)
    assert len(hash_result) > 0

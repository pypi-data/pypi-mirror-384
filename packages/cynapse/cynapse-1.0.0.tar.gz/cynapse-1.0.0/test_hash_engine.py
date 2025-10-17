"""Quick test to verify HashEngine implementation."""

import sys
from types import CodeType

# Add cynapse to path
sys.path.insert(0, 'cynapse')

from cynapse.core import HashEngine
from cynapse.models import MemoryRegion


def test_hash_bytes():
    """Test basic hash_bytes functionality."""
    engine = HashEngine(algorithm="sha256")
    
    # Test hashing
    data = b"Hello, World!"
    hash1 = engine.hash_bytes(data)
    
    print(f"✓ hash_bytes works: {hash1[:16]}...")
    
    # Test caching - same data should return same hash
    hash2 = engine.hash_bytes(data)
    assert hash1 == hash2, "Hashes should match"
    print("✓ Caching works (same input returns same hash)")
    
    # Check cache stats
    cache_info = engine.get_cache_info()
    print(f"✓ Cache info: hits={cache_info['hits']}, misses={cache_info['misses']}")
    assert cache_info['hits'] >= 1, "Should have at least one cache hit"


def test_hash_bytecode():
    """Test bytecode hashing."""
    engine = HashEngine()
    
    # Create a simple function
    def sample_function(x, y):
        return x + y
    
    # Hash its bytecode
    hash1 = engine.hash_bytecode(sample_function.__code__)
    print(f"✓ hash_bytecode works: {hash1[:16]}...")
    
    # Hash again - should be same
    hash2 = engine.hash_bytecode(sample_function.__code__)
    assert hash1 == hash2, "Bytecode hashes should match"
    print("✓ Bytecode hashing is consistent")
    
    # Different function should have different hash
    def different_function(x, y):
        return x * y
    
    hash3 = engine.hash_bytecode(different_function.__code__)
    assert hash1 != hash3, "Different functions should have different hashes"
    print("✓ Different bytecode produces different hashes")


def test_blake3_fallback():
    """Test BLAKE3 with graceful fallback."""
    # Try to create engine with blake3
    engine = HashEngine(algorithm="blake3")
    
    # Should work regardless of whether blake3 is installed
    data = b"Test data"
    hash_result = engine.hash_bytes(data)
    
    print(f"✓ BLAKE3 fallback works: algorithm={engine.algorithm}, hash={hash_result[:16]}...")
    
    # If blake3 not available, should fall back to sha256
    if not engine._blake3_available:
        print("  (BLAKE3 not available, fell back to SHA-256)")
    else:
        print("  (BLAKE3 is available)")


def test_memory_region_hashing():
    """Test memory region chunked hashing."""
    engine = HashEngine()
    
    # Create a mock memory region
    class MockMemoryRegion:
        def __init__(self, data):
            self.data = data
            self.size = len(data)
            self.start = 0
            self.end = self.size
            self.permissions = "r-x"
            self.path = None
        
        def read(self, offset, size):
            return self.data[offset:offset + size]
    
    # Create test data (16KB)
    test_data = b"A" * 16384
    region = MockMemoryRegion(test_data)
    
    # Hash in 4KB chunks
    hashes = engine.hash_memory_region(region, chunk_size=4096)
    
    print(f"✓ hash_memory_region works: {len(hashes)} chunks")
    assert len(hashes) == 4, "Should have 4 chunks for 16KB data with 4KB chunks"
    
    # All chunks should be the same since data is uniform
    assert all(h == hashes[0] for h in hashes), "All chunks should have same hash (uniform data)"
    print("✓ Chunked hashing produces expected number of hashes")


def test_cache_clearing():
    """Test cache clearing functionality."""
    engine = HashEngine()
    
    # Add some data to cache
    for i in range(10):
        engine.hash_bytes(f"data{i}".encode())
    
    info_before = engine.get_cache_info()
    print(f"✓ Cache before clear: size={info_before['size']}")
    
    # Clear cache
    engine.clear_cache()
    
    info_after = engine.get_cache_info()
    print(f"✓ Cache after clear: size={info_after['size']}")
    assert info_after['size'] == 0, "Cache should be empty after clear"


if __name__ == "__main__":
    print("Testing HashEngine implementation...\n")
    
    try:
        test_hash_bytes()
        print()
        
        test_hash_bytecode()
        print()
        
        test_blake3_fallback()
        print()
        
        test_memory_region_hashing()
        print()
        
        test_cache_clearing()
        print()
        
        print("=" * 50)
        print("✓ All tests passed!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

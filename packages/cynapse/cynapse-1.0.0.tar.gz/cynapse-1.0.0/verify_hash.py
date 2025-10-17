#!/usr/bin/env python3
import sys
sys.path.insert(0, 'cynapse')

from cynapse.core import HashEngine

# Test 1: Basic hashing
engine = HashEngine()
h = engine.hash_bytes(b"test")
assert len(h) == 64  # SHA-256 produces 64 hex chars
print("PASS: hash_bytes")

# Test 2: Bytecode hashing
def f(x): return x + 1
h = engine.hash_bytecode(f.__code__)
assert len(h) == 64
print("PASS: hash_bytecode")

# Test 3: Cache
h1 = engine.hash_bytes(b"cached")
h2 = engine.hash_bytes(b"cached")
assert h1 == h2
info = engine.get_cache_info()
assert info['hits'] > 0
print("PASS: caching")

# Test 4: BLAKE3 fallback
engine2 = HashEngine(algorithm="blake3")
h = engine2.hash_bytes(b"test")
assert len(h) > 0
print("PASS: blake3_fallback")

print("\nAll tests passed!")

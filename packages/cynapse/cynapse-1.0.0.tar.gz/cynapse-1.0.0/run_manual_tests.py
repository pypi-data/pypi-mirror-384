#!/usr/bin/env python3
"""Manual tests to verify cynapse works before PyPI publication."""

import sys
import time

# Add current directory to path
sys.path.insert(0, '.')

print("=" * 60)
print("CYNAPSE PRE-PUBLICATION TEST SUITE")
print("=" * 60)

test_results = []

# Test 1: Core Imports
print("\n[1/8] Testing Core Imports...")
try:
    from cynapse import (
        Monitor,
        AsyncMonitor,
        protect_function,
        protect_class,
        MonitorConfig,
        TamperEvent,
        TamperResponse,
        ProtectionLevel,
    )
    print("  ✅ All core imports successful")
    test_results.append(("Core Imports", True, None))
except Exception as e:
    print(f"  ❌ Import failed: {e}")
    test_results.append(("Core Imports", False, str(e)))
    sys.exit(1)

# Test 2: Monitor Creation
print("\n[2/8] Testing Monitor Creation...")
try:
    monitor = Monitor(interval=1.0)
    print("  ✅ Monitor created successfully")
    test_results.append(("Monitor Creation", True, None))
except Exception as e:
    print(f"  ❌ Failed: {e}")
    test_results.append(("Monitor Creation", False, str(e)))

# Test 3: Protect Function Decorator
print("\n[3/8] Testing @protect_function Decorator...")
try:
    @protect_function
    def test_func():
        return "test"
    
    result = test_func()
    assert result == "test", f"Expected 'test', got '{result}'"
    print("  ✅ Decorator works correctly")
    test_results.append(("@protect_function", True, None))
except Exception as e:
    print(f"  ❌ Failed: {e}")
    test_results.append(("@protect_function", False, str(e)))

# Test 4: Monitor Start/Stop
print("\n[4/8] Testing Monitor Start/Stop...")
try:
    # Use whitelist to avoid warnings about multiprocessing modules
    monitor = Monitor(interval=1.0, whitelist_modules=['multiprocessing', 'concurrent', 'queue', '_queue', '__mp_main__', '_multiprocessing'])
    monitor.start()
    time.sleep(0.5)
    assert monitor._running, "Monitor should be running"
    monitor.stop()
    assert not monitor._running, "Monitor should be stopped"
    print("  ✅ Start/Stop works correctly")
    test_results.append(("Start/Stop", True, None))
except Exception as e:
    print(f"  ❌ Failed: {e}")
    test_results.append(("Start/Stop", False, str(e)))

# Test 5: Context Manager
print("\n[5/8] Testing Context Manager...")
try:
    with Monitor(interval=1.0) as monitor:
        assert monitor._running, "Monitor should be running in context"
    assert not monitor._running, "Monitor should be stopped after context"
    print("  ✅ Context manager works correctly")
    test_results.append(("Context Manager", True, None))
except Exception as e:
    print(f"  ❌ Failed: {e}")
    test_results.append(("Context Manager", False, str(e)))

# Test 6: Hash Engine
print("\n[6/8] Testing Hash Engine...")
try:
    from cynapse.core import HashEngine
    
    engine = HashEngine()
    test_data = b"test data"
    hash1 = engine.hash_bytes(test_data)
    hash2 = engine.hash_bytes(test_data)
    
    assert hash1 == hash2, "Same data should produce same hash"
    assert len(hash1) == 64, f"SHA-256 hash should be 64 chars, got {len(hash1)}"
    print(f"  ✅ Hash engine works (hash: {hash1[:16]}...)")
    test_results.append(("Hash Engine", True, None))
except Exception as e:
    print(f"  ❌ Failed: {e}")
    test_results.append(("Hash Engine", False, str(e)))

# Test 7: Platform Detection
print("\n[7/8] Testing Platform Detection...")
try:
    from cynapse.platform import get_platform
    
    platform = get_platform()
    platform_name = platform.get_platform_name()
    print(f"  ✅ Platform detected: {platform_name}")
    test_results.append(("Platform Detection", True, None))
except Exception as e:
    print(f"  ❌ Failed: {e}")
    test_results.append(("Platform Detection", False, str(e)))

# Test 8: Builder Pattern
print("\n[8/8] Testing Builder Pattern...")
try:
    # Reset singleton for builder test
    Monitor._instance = None
    
    monitor = Monitor.builder() \
        .interval(2.0) \
        .protection_level(ProtectionLevel.HIGH) \
        .enable_auto_healing(False) \
        .build()
    
    assert monitor.config.interval == 2.0, f"Expected interval 2.0, got {monitor.config.interval}"
    assert monitor.config.protection_level == ProtectionLevel.HIGH, f"Expected HIGH, got {monitor.config.protection_level}"
    assert not monitor.config.enable_auto_healing, f"Expected auto_healing False, got {monitor.config.enable_auto_healing}"
    print("  ✅ Builder pattern works correctly")
    test_results.append(("Builder Pattern", True, None))
except AssertionError as e:
    print(f"  ❌ Assertion Failed: {e}")
    test_results.append(("Builder Pattern", False, str(e)))
except Exception as e:
    print(f"  ❌ Failed: {e}")
    import traceback
    traceback.print_exc()
    test_results.append(("Builder Pattern", False, str(e)))

# Summary
print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)

passed = sum(1 for _, success, _ in test_results if success)
total = len(test_results)

for test_name, success, error in test_results:
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {test_name}")
    if error:
        print(f"         Error: {error}")

print(f"\nTotal: {passed}/{total} tests passed ({passed*100//total}%)")

if passed == total:
    print("\n🎉 ALL TESTS PASSED! Ready for PyPI publication!")
    sys.exit(0)
else:
    print(f"\n⚠️  {total - passed} test(s) failed. Fix issues before publishing.")
    sys.exit(1)

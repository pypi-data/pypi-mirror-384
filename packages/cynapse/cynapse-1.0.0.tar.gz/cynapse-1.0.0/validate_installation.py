"""Validation script to test cynapse installation."""

import sys

def test_imports():
    """Test that all main imports work."""
    print("Testing imports...")
    
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
        print("  ✓ Core imports successful")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False

def test_basic_functionality():
    """Test basic monitor functionality."""
    print("\nTesting basic functionality...")
    
    try:
        from cynapse import Monitor, protect_function
        
        # create monitor
        monitor = Monitor(interval=1.0)
        print("  ✓ Monitor created")
        
        # protect a function
        @protect_function
        def test_func():
            return "test"
        
        result = test_func()
        assert result == "test"
        print("  ✓ Function protection works")
        
        # start and stop
        monitor.start()
        print("  ✓ Monitor started")
        
        import time
        time.sleep(1)
        
        status = monitor.get_status()
        assert status.running
        print(f"  ✓ Monitor running (performed {status.checks_performed} checks)")
        
        monitor.stop()
        assert not monitor._running
        print("  ✓ Monitor stopped")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_platform_detection():
    """Test platform detection."""
    print("\nTesting platform detection...")
    
    try:
        from cynapse.platform import get_platform
        
        platform = get_platform()
        print(f"  ✓ Detected platform: {platform.get_platform_name()}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Platform detection failed: {e}")
        return False

def test_hash_engine():
    """Test hash engine."""
    print("\nTesting hash engine...")
    
    try:
        from cynapse.core import HashEngine
        
        engine = HashEngine()
        test_data = b"test data"
        hash_result = engine.hash_bytes(test_data)
        
        assert len(hash_result) == 64  # SHA-256
        print(f"  ✓ Hash engine works: {hash_result[:16]}...")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Hash engine test failed: {e}")
        return False

def check_optional_dependencies():
    """Check which optional dependencies are available."""
    print("\nChecking optional dependencies...")
    
    optional = {
        'blake3': 'Faster hashing',
        'flask': 'Flask integration',
        'django': 'Django integration',
        'fastapi': 'FastAPI integration',
        'psutil': 'CPU/memory monitoring',
    }
    
    available = []
    missing = []
    
    for dep, description in optional.items():
        try:
            __import__(dep)
            available.append(f"{dep} ({description})")
        except ImportError:
            missing.append(f"{dep} ({description})")
    
    if available:
        print("  Available:")
        for dep in available:
            print(f"    ✓ {dep}")
    
    if missing:
        print("  Not installed (optional):")
        for dep in missing:
            print(f"    - {dep}")
    
    return True

def main():
    """Run all validation tests."""
    print("=" * 60)
    print("Cynapse Installation Validation")
    print("=" * 60)
    
    print(f"\nPython version: {sys.version}")
    print(f"Platform: {sys.platform}")
    
    tests = [
        ("Imports", test_imports),
        ("Basic Functionality", test_basic_functionality),
        ("Platform Detection", test_platform_detection),
        ("Hash Engine", test_hash_engine),
        ("Optional Dependencies", check_optional_dependencies),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n✗ {name} failed with exception: {e}")
            results.append((name, False))
    
    # summary
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Cynapse is properly installed.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

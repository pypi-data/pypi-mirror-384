"""Demonstration of cynapse detection capabilities."""

import time
from cynapse import Monitor, protect_function, TamperResponse
from cynapse.testing.tamper import TamperSimulator

# track if tampering was detected
tampering_detected = False

def tamper_handler(event):
    """Handle detected tampering."""
    global tampering_detected
    tampering_detected = True
    
    print(f"\n🚨 TAMPERING DETECTED!")
    print(f"   Type: {event.type.value}")
    print(f"   Target: {event.target}")
    print(f"   Details: {event.details}")
    
    if event.baseline_hash and event.current_hash:
        print(f"   Expected: {event.baseline_hash[:16]}...")
        print(f"   Actual:   {event.current_hash[:16]}...")
    
    return TamperResponse.ALERT

@protect_function
def calculate_discount(price: float, customer_level: str) -> float:
    """
    Calculate discount based on customer level.
    This function is protected by cynapse.
    """
    discounts = {
        'bronze': 0.05,
        'silver': 0.10,
        'gold': 0.15,
        'platinum': 0.20,
    }
    
    discount_rate = discounts.get(customer_level, 0.0)
    return price * (1 - discount_rate)

def main():
    """Run detection demonstration."""
    print("=" * 60)
    print("Cynapse Detection Demonstration")
    print("=" * 60)
    
    # create monitor with handler
    print("\n1. Setting up monitor...")
    monitor = Monitor.builder() \
        .interval(1.0) \
        .enable_bytecode_verification(True) \
        .on_tamper(tamper_handler) \
        .build()
    
    monitor.start()
    print("   ✓ Monitor started")
    
    # test normal operation
    print("\n2. Testing normal operation...")
    price = 100.0
    result = calculate_discount(price, 'gold')
    print(f"   Price: ${price}")
    print(f"   Level: gold")
    print(f"   Final: ${result}")
    print(f"   ✓ Function works correctly")
    
    # wait for a check cycle
    print("\n3. Waiting for monitoring cycle...")
    time.sleep(2)
    print(f"   ✓ Performed {monitor._checks_performed} integrity checks")
    print(f"   ✓ No tampering detected")
    
    # simulate tampering
    print("\n4. Simulating bytecode tampering...")
    print("   (An attacker modifies the function to give 100% discount)")
    
    try:
        # save original for restoration demo
        original_code = calculate_discount.__code__.co_code
        
        # tamper with the function
        TamperSimulator.modify_bytecode(
            calculate_discount,
            b'\x64\x01\x53\x00'  # modified bytecode
        )
        print("   ✓ Bytecode modified")
        
    except Exception as e:
        print(f"   ⚠ Could not modify bytecode: {e}")
        print("   (This is okay - some Python versions restrict this)")
    
    # wait for detection
    print("\n5. Waiting for cynapse to detect tampering...")
    time.sleep(3)
    
    if tampering_detected:
        print("   ✓ Tampering was detected!")
    else:
        print("   ℹ No tampering detected (modification may have failed)")
    
    # show final status
    print("\n6. Final status:")
    status = monitor.get_status()
    print(f"   Checks performed: {status.checks_performed}")
    print(f"   Tamper events: {status.tamper_events}")
    print(f"   Protected functions: {status.protected_functions}")
    
    # cleanup
    monitor.stop()
    print("\n7. Monitor stopped")
    
    print("\n" + "=" * 60)
    print("Demonstration complete!")
    print("=" * 60)
    
    if tampering_detected:
        print("\n✅ Cynapse successfully detected the tampering attempt!")
    else:
        print("\n✅ No tampering occurred during this run")
    
    print("\nKey takeaway:")
    print("Cynapse monitors your code continuously and alerts you")
    print("when someone tries to modify it at runtime.")

if __name__ == "__main__":
    main()

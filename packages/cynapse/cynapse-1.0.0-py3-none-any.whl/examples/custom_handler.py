"""Example with custom tamper event handler."""

import time
from cynapse import Monitor, TamperResponse
from cynapse.testing.tamper import TamperSimulator

def my_tamper_handler(event):
    """Custom handler for tamper events."""
    print(f"\n⚠️  TAMPER DETECTED!")
    print(f"  Type: {event.type.value}")
    print(f"  Target: {event.target}")
    print(f"  Time: {event.timestamp}")
    
    if event.baseline_hash and event.current_hash:
        print(f"  Expected hash: {event.baseline_hash[:16]}...")
        print(f"  Current hash:  {event.current_hash[:16]}...")
    
    # decide response
    if event.can_restore:
        print("  → Attempting auto-restore...")
        return TamperResponse.RESTORE
    else:
        print("  → Cannot restore, alerting only")
        return TamperResponse.ALERT

def sensitive_function():
    """A function we want to protect."""
    return "sensitive data"

def main():
    """Demonstrate custom tamper handling."""
    print("Setting up monitor with custom handler...\n")
    
    # create monitor with custom handler and auto-healing
    monitor = Monitor.builder() \
        .interval(1.0) \
        .enable_auto_healing(True) \
        .on_tamper(my_tamper_handler) \
        .build()
    
    # protect our function
    monitor.protect_function(sensitive_function)
    
    # start monitoring
    monitor.start()
    print("Monitor started\n")
    
    # call function normally
    print("Calling function normally:")
    result = sensitive_function()
    print(f"  Result: {result}\n")
    
    # wait a bit
    time.sleep(2)
    
    # simulate tampering
    print("Simulating bytecode tampering...")
    try:
        # this will modify the function's bytecode
        original_code = sensitive_function.__code__.co_code
        TamperSimulator.modify_bytecode(
            sensitive_function,
            b'\x64\x01\x53\x00'  # different bytecode
        )
        print("  Bytecode modified!\n")
    except Exception as e:
        print(f"  Failed to modify: {e}\n")
    
    # wait for monitor to detect it
    print("Waiting for detection...")
    time.sleep(3)
    
    # check final status
    status = monitor.get_status()
    print(f"\nFinal Status:")
    print(f"  Checks performed: {status.checks_performed}")
    print(f"  Tamper events detected: {status.tamper_events}")
    
    monitor.stop()
    print("\nMonitor stopped.")

if __name__ == "__main__":
    main()

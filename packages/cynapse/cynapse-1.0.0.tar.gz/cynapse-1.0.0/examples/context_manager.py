"""Example using context manager for automatic start/stop."""

import time
from cynapse import Monitor

def run_secure_operation():
    """Simulate a secure operation."""
    print("Running secure operation...")
    for i in range(5):
        print(f"  Step {i+1}/5")
        time.sleep(1)
    print("Operation completed!")

def main():
    """Demonstrate context manager usage."""
    print("Using context manager for automatic monitoring\n")
    
    # monitor automatically starts on enter and stops on exit
    with Monitor(interval=2.0) as monitor:
        print("Monitor is active\n")
        run_secure_operation()
        
        # check status before exit
        status = monitor.get_status()
        print(f"\nPerformed {status.checks_performed} checks during operation")
    
    print("\nMonitor automatically stopped!")

if __name__ == "__main__":
    main()

"""Basic usage example for cynapse."""

import time
from cynapse import Monitor

def main():
    """Demonstrate basic monitoring."""
    print("Starting cynapse monitor...")
    
    # create monitor with 3 second interval
    monitor = Monitor(interval=3.0)
    
    # start monitoring
    monitor.start()
    print("Monitor started. Running for 10 seconds...")
    
    # simulate application running
    time.sleep(10)
    
    # get status
    status = monitor.get_status()
    print(f"\nMonitor Status:")
    print(f"  Running: {status.running}")
    print(f"  Checks performed: {status.checks_performed}")
    print(f"  Tamper events: {status.tamper_events}")
    print(f"  Protected functions: {status.protected_functions}")
    
    # stop monitoring
    monitor.stop()
    print("\nMonitor stopped.")

if __name__ == "__main__":
    main()

"""Example using decorators to protect functions."""

import time
from cynapse import protect_function, protect_class, Monitor

# protect a single function
@protect_function
def process_payment(amount: float) -> bool:
    """Process a payment - this function is protected."""
    print(f"Processing payment of ${amount}")
    return True

# protect all methods in a class
@protect_class
class UserAuthentication:
    """User authentication class - all methods are protected."""
    
    def login(self, username: str, password: str) -> bool:
        """Authenticate user login."""
        print(f"Authenticating user: {username}")
        return True
    
    def logout(self, username: str) -> bool:
        """Log out user."""
        print(f"Logging out user: {username}")
        return True

def main():
    """Run protected code."""
    print("Starting monitor...")
    
    # start monitor
    monitor = Monitor(interval=2.0)
    monitor.start()
    
    # use protected functions
    print("\nCalling protected functions:")
    process_payment(99.99)
    
    auth = UserAuthentication()
    auth.login("alice", "secret123")
    auth.logout("alice")
    
    # run for a bit
    print("\nMonitoring for 5 seconds...")
    time.sleep(5)
    
    # check status
    status = monitor.get_status()
    print(f"\nProtected {status.protected_functions} functions")
    print(f"Performed {status.checks_performed} integrity checks")
    
    monitor.stop()
    print("Done!")

if __name__ == "__main__":
    main()

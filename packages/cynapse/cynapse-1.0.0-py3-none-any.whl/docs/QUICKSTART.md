# Cynapse Quick Start Guide

Get up and running with cynapse in 5 minutes!

## Installation

```bash
pip install cynapse
```

## 1. Basic Monitoring (30 seconds)

```python
from cynapse import Monitor
import time

# Create and start monitor
monitor = Monitor(interval=3.0)
monitor.start()

# Your application code runs here
time.sleep(10)

# Check status
status = monitor.get_status()
print(f"Performed {status.checks_performed} integrity checks")

# Stop monitoring
monitor.stop()
```

## 2. Protect Specific Functions (1 minute)

```python
from cynapse import protect_function

@protect_function
def process_payment(amount: float) -> bool:
    """This function is now protected from tampering."""
    print(f"Processing ${amount}")
    return True

# Function works normally
process_payment(99.99)

# But cynapse will detect if someone modifies it at runtime!
```

## 3. Use as Context Manager (1 minute)

```python
from cynapse import Monitor

with Monitor(interval=2.0) as monitor:
    # Monitoring is active here
    run_your_application()
    
# Monitor automatically stops when exiting
```

## 4. Custom Tamper Handler (2 minutes)

```python
from cynapse import Monitor, TamperResponse

def my_handler(event):
    print(f"⚠️  Tampering detected: {event.type.value}")
    
    if event.can_restore:
        return TamperResponse.RESTORE  # Auto-heal
    return TamperResponse.ALERT  # Just log it

monitor = Monitor.builder() \
    .interval(2.0) \
    .enable_auto_healing(True) \
    .on_tamper(my_handler) \
    .build()

monitor.start()
```

## 5. Flask Integration (2 minutes)

```python
from flask import Flask
from cynapse.integrations.flask import FlaskMonitor

app = Flask(__name__)
monitor = FlaskMonitor(app, interval=5.0, protect_routes=['admin'])

@app.route('/admin')
def admin():
    return "Protected admin page"

app.run()
```

## Common Patterns

### Protect a Class

```python
from cynapse import protect_class

@protect_class
class SecureAPI:
    def authenticate(self, creds):
        return verify(creds)
```

### High Security Mode

```python
from cynapse import Monitor, ProtectionLevel

monitor = Monitor.builder() \
    .protection_level(ProtectionLevel.PARANOID) \
    .enable_auto_healing(True) \
    .enable_forensics(True) \
    .build()
```

### Async Support

```python
from cynapse import AsyncMonitor

async with AsyncMonitor(interval=3.0) as monitor:
    await run_async_app()
```

## What's Being Protected?

When you start the monitor, cynapse automatically:

1. ✅ Creates a baseline of all loaded code
2. ✅ Monitors function bytecode for modifications
3. ✅ Tracks module loading and changes
4. ✅ Watches for import hook manipulation
5. ✅ Detects monkey patching attempts

## Configuration Options

```python
from cynapse import Monitor, ProtectionLevel

monitor = Monitor(
    interval=3.0,                          # Check every 3 seconds
    protection_level=ProtectionLevel.HIGH, # HIGH security mode
    enable_bytecode_verification=True,     # Monitor bytecode
    enable_module_tracking=True,           # Track modules
    enable_import_hooks=True,              # Monitor imports
    enable_auto_healing=False,             # Auto-restore (use carefully!)
    whitelist_modules=['pytest', 'debugpy'] # Skip these modules
)
```

## Testing Detection

Try the detection demo:

```bash
python examples/detection_demo.py
```

This shows cynapse detecting a simulated tampering attempt!

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check out [examples/](examples/) for more code samples
- Review [CONTRIBUTING.md](CONTRIBUTING.md) to contribute
- Visit the documentation site for in-depth guides

## Troubleshooting

**Monitor not detecting changes?**
- Check if modules are whitelisted
- Increase protection level
- Ensure monitoring interval is appropriate

**Performance impact?**
- Reduce check frequency (increase interval)
- Use adaptive sampling
- Whitelist stable modules

**Import errors?**
- Verify installation: `pip show cynapse`
- Run validation: `python validate_installation.py`

## Need Help?

- 📖 [Full Documentation](https://cynapse.readthedocs.io)
- 🐛 [Report Issues](https://gitlab.com/TIVisionOSS/python/cynapse/-/issues)
- 💬 [Discussions](https://gitlab.com/TIVisionOSS/python/cynapse/-/issues)
- ✉️  Email: oss@tivision.dev

---

**Happy Monitoring! 🛡️**

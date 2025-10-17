# User Documentation

## Installation guide
```bash
pip install cynapse              # core
pip install cynapse[all]         # optional extras
```
From source:
```bash
pip install -e .
```

## Usage instructions
- Basic:
```python
from cynapse import Monitor
with Monitor(interval=3.0) as monitor:
    run_secure_operation()
```
- Decorators:
```python
from cynapse import protect_function, protect_class
@protect_function
def sensitive(): ...
@protect_class
class SecureAPI: ...
```
- Builder & callbacks:
```python
from cynapse import Monitor, ProtectionLevel, TamperResponse
monitor = Monitor.builder() \
  .protection_level(ProtectionLevel.HIGH) \
  .enable_auto_healing(True) \
  .build()
```
- Frameworks: see `cynapse/integrations/` and `examples/flask_app.py`.

## Troubleshooting
- False positives: add stable modules to `whitelist_modules`.
- Performance: increase `interval`, reduce scope, use `blake3`.
- Import hook alerts: verify test tools (`pytest`, `debugpy`) are whitelisted.

## FAQ
- Does it block code execution? No, it monitors and responds per configuration.
- Will dynamic code break? Whitelist dynamic modules/patterns.
- Can it auto-restore? Yes, for supported event types when enabled.

References: `docs/QUICKSTART.md`, `examples/`.

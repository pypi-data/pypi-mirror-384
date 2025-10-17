# Cynapse Examples

This directory contains example applications demonstrating various features of cynapse.

## Basic Examples

### basic_usage.py
Simple example showing how to start and stop the monitor.

```bash
python basic_usage.py
```

### decorator_protection.py
Demonstrates using decorators to protect functions and classes.

```bash
python decorator_protection.py
```

### context_manager.py
Shows how to use cynapse as a context manager for automatic start/stop.

```bash
python context_manager.py
```

### custom_handler.py
Example with a custom tamper event handler.

```bash
python custom_handler.py
```

### async_example.py
Demonstrates async/await support with AsyncMonitor.

```bash
python async_example.py
```

### detection_demo.py
Interactive demonstration of tampering detection.

```bash
python detection_demo.py
```

## Framework Integrations

### flask_app.py
Flask web application with cynapse monitoring.

```bash
# Install Flask first
pip install flask

# Run the app
python flask_app.py
```

Visit http://localhost:5000 to test the endpoints.

## Running Examples

1. Install cynapse:
   ```bash
   cd ..
   pip install -e .
   ```

2. Install optional dependencies for specific examples:
   ```bash
   # For Flask example
   pip install flask
   
   # For all examples
   pip install cynapse[all]
   ```

3. Run any example:
   ```bash
   python examples/basic_usage.py
   ```

## What to Try

1. **Start with basic_usage.py** to understand the fundamentals
2. **Try decorator_protection.py** to see how easy protection is
3. **Run detection_demo.py** to see tampering detection in action
4. **Experiment with flask_app.py** for web application protection
5. **Check async_example.py** if you use asyncio

## Tips

- Start with low protection levels and increase as needed
- Use whitelists to exclude testing/debugging tools
- Monitor the status endpoint to see what's happening
- Check the logs for detailed information
- Experiment with different configuration options

## Need Help?

- Read the main README.md
- Check the documentation
- Open an issue on GitLab
- Email: oss@tivision.dev

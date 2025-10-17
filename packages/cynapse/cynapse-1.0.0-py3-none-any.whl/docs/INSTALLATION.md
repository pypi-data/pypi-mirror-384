# Installation Guide for Cynapse

## Quick Installation

### From PyPI (when published)
```bash
pip install cynapse
```

### From Source (Development)
```bash
# Clone the repository
git clone https://gitlab.com/TIVisionOSS/python/cynapse.git
cd cynapse

# Install in development mode
pip install -e .

# Or install with all optional dependencies
pip install -e ".[all]"
```

## Installation Options

### Minimal Installation (Core Only)
```bash
pip install cynapse
```
- Zero dependencies
- Pure Python implementation
- Works on all platforms

### With Optional Features

#### Faster Hashing (Blake3)
```bash
pip install cynapse[blake3]
```

#### Web Framework Integrations
```bash
# Flask
pip install cynapse[flask]

# Django
pip install cynapse[django]

# FastAPI
pip install cynapse[fastapi]

# All frameworks
pip install cynapse[all]
```

#### Development Tools
```bash
pip install cynapse[dev]
```
Includes: pytest, black, isort, mypy, ruff, coverage

## Verify Installation

Run the validation script:
```bash
python validate_installation.py
```

Or quick test:
```python
from cynapse import Monitor
print("✓ Cynapse installed successfully!")
```

## Platform-Specific Notes

### Linux
Works out of the box. No special requirements.

### Windows
- Requires Python 3.8+
- Works on Windows 7+
- No special dependencies

### macOS
- Requires Python 3.8+
- Works on macOS 10.12+
- For full memory mapping, Xcode Command Line Tools recommended:
  ```bash
  xcode-select --install
  ```

## Python Version Support

Cynapse supports Python 3.8 through 3.13:
- ✅ Python 3.8
- ✅ Python 3.9
- ✅ Python 3.10
- ✅ Python 3.11
- ✅ Python 3.12
- ✅ Python 3.13

## Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Install cynapse
pip install cynapse
```

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError: No module named 'cynapse'`:

1. Verify installation:
   ```bash
   pip show cynapse
   ```

2. Check Python path:
   ```python
   import sys
   print(sys.path)
   ```

3. Reinstall:
   ```bash
   pip uninstall cynapse
   pip install cynapse
   ```

### Platform Detection Issues

If platform detection fails:
```python
from cynapse.platform import get_platform
platform = get_platform()
print(f"Detected: {platform.get_platform_name()}")
```

### Permission Errors

On Linux/macOS, some memory operations may require:
```bash
# Run with appropriate permissions
sudo python your_script.py  # Use cautiously!
```

Or adjust security policies as needed.

## Upgrading

```bash
# Upgrade to latest version
pip install --upgrade cynapse

# Upgrade with all features
pip install --upgrade cynapse[all]
```

## Uninstallation

```bash
pip uninstall cynapse
```

## Dependencies Overview

### Core (Required)
- **None!** Pure Python, standard library only

### Optional
- `blake3>=0.3.0` - Faster hashing (10x speed improvement)
- `flask>=2.0.0` - Flask integration
- `django>=3.2.0` - Django integration  
- `fastapi>=0.100.0` - FastAPI integration
- `psutil>=5.9.0` - CPU/memory monitoring (recommended)

### Development
- `pytest>=7.0.0` - Testing framework
- `pytest-cov>=4.0.0` - Coverage reporting
- `pytest-asyncio>=0.21.0` - Async test support
- `black>=23.0.0` - Code formatting
- `isort>=5.12.0` - Import sorting
- `mypy>=1.0.0` - Type checking
- `ruff>=0.1.0` - Fast linting

## Next Steps

After installation:
1. Read [QUICKSTART.md](QUICKSTART.md) for quick tutorial
2. Check [examples/](examples/) for code samples
3. Review [README.md](README.md) for full documentation
4. Run `python validate_installation.py` to verify everything works

## Support

- **Issues**: [GitLab Issues](https://gitlab.com/TIVisionOSS/python/cynapse/-/issues)
- **Documentation**: [cynapse.readthedocs.io](https://cynapse.readthedocs.io)
- **Email**: oss@tivision.dev

Happy monitoring! 🛡️

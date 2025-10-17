# Changelog

All notable changes to cynapse will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-10-16

### Added
- Initial release of cynapse
- Core integrity monitoring functionality
- Bytecode verification
- Module tracking
- Import hook monitoring
- Monkey patch detection
- Auto-healing capabilities
- Cross-platform support (Linux, Windows, macOS)
- Flask integration
- Django integration
- FastAPI integration
- Async/await support
- Decorator-based API
- Context manager API
- Builder pattern for configuration
- Comprehensive test suite
- Example applications
- Full documentation

### Features
- **Zero Dependencies** - Pure Python with only stdlib
- **Real-time Monitoring** - Continuous background verification
- **Multiple Protection Levels** - LOW, MEDIUM, HIGH, PARANOID
- **Flexible Response System** - Alert, restore, snapshot, terminate
- **Adaptive Sampling** - Smart monitoring intervals
- **Merkle Trees** - Efficient integrity verification
- **Forensic Snapshots** - Capture evidence of tampering
- **Whitelist Support** - Exclude safe modules from monitoring
- **Type Hints** - Full type annotation support
- **Comprehensive Logging** - Structured logging with multiple formats

### Performance
- CPU overhead < 2% when idle
- Memory overhead < 20MB per GB monitored
- Hash throughput 500 MB/sec (pure Python)
- Startup time < 500ms

### Security
- Detects bytecode modification
- Detects function replacement
- Detects module injection
- Detects import hook manipulation
- Detects monkey patching
- Monitors deserialization operations

## [Unreleased]

### Planned for 1.1.0
- ML-based anomaly detection
- Behavioral profiling
- Enhanced cloud integration
- Kubernetes operator
- Additional framework integrations
- Performance optimizations with optional C/Rust extensions

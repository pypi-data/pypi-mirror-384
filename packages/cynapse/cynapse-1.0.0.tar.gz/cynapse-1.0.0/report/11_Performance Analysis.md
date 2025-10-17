# Performance Analysis

## Benchmark results (from `README.md`)
- CPU Usage: < 2% when idle
- Memory Overhead: < 20MB per GB of monitored code
- Hash Throughput: ~500 MB/sec (hashlib)
- Bytecode Scan: < 10ms per 1000 functions
- Startup Time: < 500ms for baseline

## Resource utilization
- `Monitor.get_status()` exposes checks performed, protected functions, optional CPU/memory via `psutil`.

## Scalability and load testing outcomes
- Runtime overhead scales primarily with number of tracked functions/modules and interval frequency. Use whitelists and interval tuning under load.

## Optimization strategies
- Increase `interval` to reduce frequency of checks.
- Enable adaptive settings via `ProtectionLevel` and toggles.
- Use `blake3` for faster hashing where available.
- Leverage LRU caching in `HashEngine` and avoid protecting extremely hot dynamic code.

References: `cynapse/core/hash_engine.py`, `cynapse/monitor.py`, `README.md`.

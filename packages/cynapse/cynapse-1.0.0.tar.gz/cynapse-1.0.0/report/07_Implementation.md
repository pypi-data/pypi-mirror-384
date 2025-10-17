# Implementation

## Development methodology
- Codebase emphasizes modularity, type hints, and tests (`tests/`).
- Examples (`examples/`) serve as executable documentation.

## Core module descriptions
- `monitor.py`: singleton orchestrator; baseline + background verification + responses.
- `core/bytecode.py`: compute/compare function code hashes; diff/restore support.
- `core/verifier.py`: verifies modules, functions, import hooks; emits `TamperEvent`s.
- `core/baseline.py`: in-memory baseline with save/load/export.
- `core/hash_engine.py`: LRU caching, optional `blake3` fallback.
- `core/healer.py`: auto-restore for supported events.

## Algorithms and logic overview
- Bytecode hashing: combine `co_code`, `co_consts`, `co_names` for robust detection.
- Module hashing: hash function bytecodes and attribute representations.
- Import hook baseline vs current comparison excluding the project’s own hook.
- Verification loop: background thread/task executes checks at `interval`.

## Important pseudocode
```python
# monitor.py
while running:
    events = []
    if cfg.enable_module_tracking:
        events += module_tracker.check_for_changes(cfg.whitelist_modules)
    if cfg.enable_bytecode_verification:
        events += verifier.verify_functions(cfg.whitelist_modules)
    if cfg.enable_import_hooks:
        events += import_monitor.check_for_manipulation()

    for e in events:
        response = cfg.tamper_response
        for cb in callbacks:
            r = cb(e)
            if r is not None:
                response = r; break
        execute_response(e, response)  # alert/restore/terminate/snapshot

    sleep(cfg.interval)
```

## Challenges and optimizations
- Low overhead: LRU-cached hashing, adaptive configuration via `ProtectionLevel` and whitelists.
- Cross-platform: abstracted memory ops in `platform/` with OS-specific behavior and graceful fallback.
- Safety: catch-and-continue in background loops; avoid crashing host process.

References: `cynapse/monitor.py`, `cynapse/core/*`, `cynapse/introspection/*`.

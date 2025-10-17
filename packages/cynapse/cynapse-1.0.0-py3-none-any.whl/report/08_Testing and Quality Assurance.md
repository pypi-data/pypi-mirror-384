# Testing and Quality Assurance

## Testing strategy
- Unit tests focus on baseline storage, bytecode analysis, decorators, and monitor behavior.
- Integration via examples (`examples/`) demonstrating end-to-end behavior.

## Test cases and results
- `tests/test_baseline.py`: create/save/load/export/clear baseline.
- `tests/test_bytecode.py`: register/verify functions, detect bytecode tampering, restore, baseline size.
- `tests/test_decorators.py`: `@protect_function` and `@protect_class` integration with monitor.
- `tests/test_monitor.py`: singleton behavior, start/stop/context, builder config, `verify_now`, `get_status`, whitelist.

Run:
```bash
pytest -v
pytest --cov=cynapse --cov-report=term-missing
```

## Bug tracking and resolution
- Use GitLab Issues (`README.md`) for tracking and triage. Reproduce with examples/tests, add coverage.

## Performance and security testing
- Performance characteristics documented in `README.md` (CPU/memory/throughput).
- Security scenarios demonstrated in `examples/detection_demo.py` using `TamperSimulator` to modify bytecode.

References: `tests/`, `examples/`, `README.md`.

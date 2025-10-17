# System Design

## Architecture Design

### System architecture diagram (logical)
```mermaid
graph TB
  subgraph API Layer
    DEC[Decorators]
    CTX[Context Manager]
    BLD[MonitorBuilder]
    AM[AsyncMonitor]
  end
  subgraph Core Engine
    MON[Monitor]
    VER[IntegrityVerifier]
    BASE[Baseline]
    HASH[HashEngine]
    MERK[MerkleTree]
  end
  subgraph Introspection & Detection
    BC[BytecodeAnalyzer]
    MOD[ModuleTracker]
    IMP[ImportHookMonitor]
    MP[MonkeyPatchDetector]
  end
  subgraph Response
    HEAL[AutoHealer]
    CB[Callbacks]
  end
  DEC-->MON
  CTX-->MON
  BLD-->MON
  AM-->VER
  MON-->VER
  VER-->BASE
  VER-->HASH
  VER-->BC
  VER-->MOD
  VER-->IMP
  MON-->HEAL
  MON-->CB
```

### Modules and submodules
- `cynapse/monitor.py`: Orchestrator, baseline + verify loop, responses.
- `cynapse/async_monitor.py`: Async variant using `asyncio` task loop.
- `cynapse/core/`: `baseline.py`, `bytecode.py`, `hash_engine.py`, `merkle.py`, `verifier.py`, `healer.py`.
- `cynapse/introspection/`: `modules.py`, `imports.py`.
- `cynapse/detection/`: `monkey_patch.py`.
- `cynapse/integrations/`: `flask.py`, `django.py`, `fastapi.py`.
- `cynapse/utils/config.py`: Builder and config helpers.

### Data flow diagram (DFD)
```mermaid
flowchart LR
  Code[Protected Code] -->|register| BC[BytecodeAnalyzer]
  sys.modules --> MOD[ModuleTracker]
  sys.meta_path --> IMP[ImportHookMonitor]
  BC & MOD & IMP --> VER[IntegrityVerifier]
  VER -->|events| MON[Monitor]
  MON -->|TamperResponse| HEAL[AutoHealer]
  MON -->|Callbacks| UserHandlers
```

### ER/schema design (conceptual)
```mermaid
classDiagram
  class Baseline {
    created_at: datetime
    function_hashes: dict[str,str]
    module_hashes: dict[str,str]
    import_hooks: list[str]
  }
  class TamperEvent {
    type: TamperType
    target: any
    baseline_hash: str
    current_hash: str
    timestamp: datetime
    details: str
  }
  class MonitorConfig {
    interval: float
    protection_level: enum
    feature_toggles: flags
    whitelist_modules: list[str]
  }
  Baseline <.. TamperEvent
  MonitorConfig <.. Monitor
```

## Component Design
- `Monitor` (`cynapse/monitor.py`): Singleton orchestrator; baseline creation, background loop, callbacks, responses.
- `IntegrityVerifier` (`cynapse/core/verifier.py`): Aggregates checks for functions, modules, import hooks.
- `BytecodeAnalyzer` (`cynapse/core/bytecode.py`): Hashes and compares `CodeType` objects; supports restore.
- `Baseline` (`cynapse/core/baseline.py`): Stores trusted hashes; supports save/load/export.
- `HashEngine` (`cynapse/core/hash_engine.py`): LRU-cached hashing; optional `blake3`.
- `AutoHealer` (`cynapse/core/healer.py`): Attempts restoration based on `TamperEvent.can_restore`.
- `ModuleTracker`, `ImportHookMonitor`, `MonkeyPatchDetector`: Detect module/import/monkey-patch anomalies.
- `AsyncMonitor` (`cynapse/async_monitor.py`): Async loop variant for FastAPI and asyncio apps.

## Interfaces and interactions
- `Monitor.protect_function(func)` adds to baseline and tracking.
- `Monitor.verify_now()` runs modular checks respecting whitelists.
- `Monitor.on_tamper(cb)` registers a callback to influence response.
- `Monitor.get_status()` exposes metrics (optionally via `psutil`).

## UI/UX Design
- Pythonic APIs: decorators for zero-friction protection, builder for fluent config, context managers for lifecycle.
- Example flows in `examples/` demonstrate common UX patterns.

References: `docs/design.md`, `cynapse/` modules.

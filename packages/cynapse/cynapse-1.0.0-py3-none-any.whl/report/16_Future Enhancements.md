# Future Enhancements

## Planned features and improvements
- Mature forensics snapshot pipeline and evidence retention controls.
- Expand detectors (deserialization guard, anomaly detection heuristics).
- Richer monkey-patch detection (class/instance attribute graph diffing).
- Enhanced module hashing with source snapshotting where feasible.

## Integration with other systems
- Remote attestation support leveraging config toggles in `MonitorConfig`.
- SIEM/SOC integration via structured logging or callback bridges.

## Scalability and modernization goals
- Adaptive sampling strategies informed by runtime metrics.
- Pluggable backends for hashing/telemetry.
- Typed public API evolution and stability guarantees.

References: `cynapse/models.py` (config toggles), `docs/design.md`.

"""Core data models for Cynapse."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional, List, Callable


class TamperType(Enum):
    """Types of tampering that can be detected."""
    BYTECODE_MODIFICATION = "bytecode_modification"
    FUNCTION_REPLACEMENT = "function_replacement"
    MODULE_INJECTION = "module_injection"
    MODULE_MODIFICATION = "module_modification"
    MODULE_REMOVAL = "module_removal"
    ATTRIBUTE_MODIFICATION = "attribute_modification"
    IMPORT_HOOK_MANIPULATION = "import_hook_manipulation"
    SUSPICIOUS_DESERIALIZATION = "suspicious_deserialization"
    MEMORY_MODIFICATION = "memory_modification"


class TamperResponse(Enum):
    """Response actions for tamper events."""
    ALERT = "alert"           # log and continue
    RESTORE = "restore"       # auto-heal
    SNAPSHOT = "snapshot"     # capture forensics
    TERMINATE = "terminate"   # shut down
    CUSTOM = "custom"         # user-defined


class ProtectionLevel(Enum):
    """Protection levels with different trade-offs."""
    LOW = "low"           # minimal checks, lowest overhead
    MEDIUM = "medium"     # balanced
    HIGH = "high"         # comprehensive checks
    PARANOID = "paranoid" # maximum security, higher overhead


@dataclass
class MemoryRegion:
    """Represents a memory region."""
    start: int
    end: int
    size: int
    permissions: str  # e.g., "r-xp"
    path: Optional[str] = None
    
    def read(self, offset: int, size: int) -> bytes:
        """Read bytes from this region."""
        # this will be implemented by platform-specific code
        raise NotImplementedError("Memory reading must be implemented by platform layer")


@dataclass
class MerkleNode:
    """Node in Merkle tree."""
    hash: str
    left: Optional["MerkleNode"] = None
    right: Optional["MerkleNode"] = None


@dataclass
class TamperEvent:
    """Represents a detected tamper event."""
    type: TamperType
    target: Any
    timestamp: datetime
    baseline_hash: Optional[str] = None
    current_hash: Optional[str] = None
    details: Optional[str] = None
    stack_trace: Optional[List[str]] = None
    
    @property
    def can_restore(self) -> bool:
        """Check if this event can be auto-restored."""
        return self.type in [
            TamperType.BYTECODE_MODIFICATION,
            TamperType.FUNCTION_REPLACEMENT,
            TamperType.MODULE_MODIFICATION,
        ]
    
    def __str__(self) -> str:
        """String representation of tamper event."""
        return (
            f"TamperEvent(type={self.type.name}, target={self.target}, "
            f"timestamp={self.timestamp.isoformat()})"
        )


@dataclass
class MonitorStatus:
    """Current status of monitoring."""
    running: bool
    baseline_created: Optional[datetime]
    last_check: Optional[datetime]
    checks_performed: int
    tamper_events: int
    protected_functions: int
    protected_modules: int
    cpu_usage: float
    memory_usage: int


@dataclass
class MonitorConfig:
    """Configuration for Monitor."""
    interval: float = 3.0
    protection_level: ProtectionLevel = ProtectionLevel.MEDIUM
    hash_algorithm: str = "sha256"
    adaptive_sampling: bool = True
    
    # feature toggles
    enable_bytecode_verification: bool = True
    enable_module_tracking: bool = True
    enable_import_hooks: bool = True
    enable_merkle_trees: bool = True
    enable_auto_healing: bool = False
    enable_forensics: bool = False
    
    # whitelisting
    whitelist_modules: List[str] = field(default_factory=lambda: ["pytest", "debugpy", "_pytest", "pluggy"])
    whitelist_patterns: List[str] = field(default_factory=list)
    protect_modules: List[str] = field(default_factory=list)
    
    # response
    tamper_response: TamperResponse = TamperResponse.ALERT
    on_tamper: Optional[Callable[[TamperEvent], TamperResponse]] = None
    
    # logging
    log_level: str = "INFO"
    log_format: str = "text"
    log_output: str = "stdout"
    
    # forensics
    snapshot_dir: str = "./cynapse_snapshots"
    max_snapshot_size: int = 10 * 1024 * 1024  # 10MB
    retention_days: int = 30
    
    # attestation
    attestation_enabled: bool = False
    attestation_server: Optional[str] = None
    attestation_api_key: Optional[str] = None

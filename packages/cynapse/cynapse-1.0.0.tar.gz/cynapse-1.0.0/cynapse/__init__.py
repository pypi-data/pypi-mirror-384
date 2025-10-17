"""
Cynapse - Runtime Memory Integrity Monitor for Python

A pure Python security library that detects and responds to code tampering
in running Python applications.
"""

__version__ = "1.0.0"

# main monitor classes
from .monitor import Monitor
from .async_monitor import AsyncMonitor

# decorators
from .decorators import (
    protect_function,
    protect_class,
    protect_method,
    monitored,
    async_monitored,
)

# models and enums
from .models import (
    MonitorConfig,
    MonitorStatus,
    TamperEvent,
    TamperType,
    TamperResponse,
    ProtectionLevel,
)

# exceptions
from .exceptions import (
    CynapseError,
    InitializationError,
    BaselineError,
    VerificationError,
    RestorationError,
    PlatformError,
    ConfigurationError,
)

__all__ = [
    # version
    "__version__",
    
    # main classes
    "Monitor",
    "AsyncMonitor",
    
    # decorators
    "protect_function",
    "protect_class",
    "protect_method",
    "monitored",
    "async_monitored",
    
    # models
    "MonitorConfig",
    "MonitorStatus",
    "TamperEvent",
    "TamperType",
    "TamperResponse",
    "ProtectionLevel",
    
    # exceptions
    "CynapseError",
    "InitializationError",
    "BaselineError",
    "VerificationError",
    "RestorationError",
    "PlatformError",
    "ConfigurationError",
]

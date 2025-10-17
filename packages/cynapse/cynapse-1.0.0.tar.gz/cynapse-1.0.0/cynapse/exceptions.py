"""Custom exceptions for Cynapse."""


class CynapseError(Exception):
    """Base exception for Cynapse."""
    pass


class InitializationError(CynapseError):
    """Raised when initialization fails."""
    pass


class BaselineError(CynapseError):
    """Raised when baseline operations fail."""
    pass


class VerificationError(CynapseError):
    """Raised when verification fails."""
    pass


class RestorationError(CynapseError):
    """Raised when auto-healing fails."""
    pass


class PlatformError(CynapseError):
    """Raised when platform-specific operations fail."""
    pass


class ConfigurationError(CynapseError):
    """Raised when configuration is invalid."""
    pass

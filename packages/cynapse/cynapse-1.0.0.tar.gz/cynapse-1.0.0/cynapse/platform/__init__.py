"""Platform-specific implementations."""

from .factory import get_platform, reset_platform
from .base import PlatformBase

__all__ = ['get_platform', 'reset_platform', 'PlatformBase']

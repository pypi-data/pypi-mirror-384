"""Platform factory for automatically selecting the correct platform."""

import sys
from typing import Optional

from .base import PlatformBase
from ..exceptions import PlatformError


_platform_instance: Optional[PlatformBase] = None


def get_platform() -> PlatformBase:
    """
    Get the appropriate platform implementation for the current OS.
    
    Returns:
        PlatformBase implementation for current OS
        
    Raises:
        PlatformError: If platform is not supported
    """
    global _platform_instance
    
    if _platform_instance is not None:
        return _platform_instance
    
    platform_name = sys.platform
    
    if platform_name.startswith('linux'):
        from .linux import LinuxPlatform
        _platform_instance = LinuxPlatform()
    elif platform_name.startswith('win'):
        from .windows import WindowsPlatform
        _platform_instance = WindowsPlatform()
    elif platform_name == 'darwin':
        from .macos import MacOSPlatform
        _platform_instance = MacOSPlatform()
    else:
        raise PlatformError(f"Unsupported platform: {platform_name}")
    
    return _platform_instance


def reset_platform():
    """Reset the cached platform instance (useful for testing)."""
    global _platform_instance
    _platform_instance = None

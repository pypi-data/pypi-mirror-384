"""Linux-specific memory operations."""

import os
import ctypes
from typing import List

from .base import PlatformBase
from ..models import MemoryRegion
from ..exceptions import PlatformError


class LinuxPlatform(PlatformBase):
    """Linux platform implementation."""
    
    def get_platform_name(self) -> str:
        """Get platform name."""
        return "linux"
    
    def get_memory_regions(self) -> List[MemoryRegion]:
        """
        Read memory regions from /proc/self/maps.
        
        Returns:
            List of MemoryRegion objects
        """
        regions = []
        
        try:
            with open('/proc/self/maps', 'r') as f:
                for line in f:
                    region = self._parse_maps_line(line.strip())
                    if region:
                        regions.append(region)
        except FileNotFoundError:
            raise PlatformError("/proc/self/maps not found - not on Linux?")
        except PermissionError:
            raise PlatformError("Permission denied reading /proc/self/maps")
        except Exception as e:
            raise PlatformError(f"Failed to read memory regions: {e}")
        
        return regions
    
    def _parse_maps_line(self, line: str) -> MemoryRegion:
        """
        Parse a line from /proc/self/maps.
        
        Format: address perms offset dev inode pathname
        Example: 7f8b2c000000-7f8b2c021000 r-xp 00000000 08:01 1234 /lib/x86_64-linux-gnu/ld-2.31.so
        
        Args:
            line: Line from maps file
            
        Returns:
            MemoryRegion object or None if parsing fails
        """
        if not line:
            return None
        
        parts = line.split()
        if len(parts) < 5:
            return None
        
        # parse address range
        address_range = parts[0]
        try:
            start_str, end_str = address_range.split('-')
            start = int(start_str, 16)
            end = int(end_str, 16)
        except (ValueError, IndexError):
            return None
        
        # parse permissions
        permissions = parts[1]
        
        # parse path (may not exist for anonymous mappings)
        path = parts[5] if len(parts) >= 6 else None
        
        # skip if path is empty or special
        if path in ['', '[stack]', '[heap]', '[vvar]', '[vdso]', '[vsyscall]']:
            path = None
        
        return MemoryRegion(
            start=start,
            end=end,
            size=end - start,
            permissions=permissions,
            path=path
        )
    
    def read_memory(self, address: int, size: int) -> bytes:
        """
        Read memory from a specific address.
        
        On Linux, we can use /proc/self/mem or ctypes.
        
        Args:
            address: Memory address to read from
            size: Number of bytes to read
            
        Returns:
            Bytes read from memory
        """
        try:
            # create a ctypes buffer pointing to the address
            # this works because we're reading our own process memory
            ptr = ctypes.cast(address, ctypes.POINTER(ctypes.c_char * size))
            return bytes(ptr.contents)
        except Exception as e:
            raise PlatformError(f"Failed to read memory at 0x{address:x}: {e}")

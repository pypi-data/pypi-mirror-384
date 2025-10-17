"""macOS-specific memory operations."""

import subprocess
import re
import ctypes
from typing import List

from .base import PlatformBase
from ..models import MemoryRegion
from ..exceptions import PlatformError


class MacOSPlatform(PlatformBase):
    """macOS platform implementation."""
    
    def get_platform_name(self) -> str:
        """Get platform name."""
        return "darwin"
    
    def get_memory_regions(self) -> List[MemoryRegion]:
        """
        Get memory regions using vmmap command.
        
        Returns:
            List of MemoryRegion objects
        """
        import os
        
        try:
            # run vmmap on our own PID
            pid = os.getpid()
            result = subprocess.run(
                ['vmmap', str(pid)],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                raise PlatformError(f"vmmap failed: {result.stderr}")
            
            return self._parse_vmmap_output(result.stdout)
            
        except FileNotFoundError:
            # vmmap not found, try alternative approach
            return self._get_regions_fallback()
        except Exception as e:
            raise PlatformError(f"Failed to get memory regions: {e}")
    
    def _parse_vmmap_output(self, output: str) -> List[MemoryRegion]:
        """
        Parse output from vmmap command.
        
        Args:
            output: vmmap command output
            
        Returns:
            List of MemoryRegion objects
        """
        regions = []
        
        # vmmap output format varies, but generally:
        # REGION TYPE       START    -    END     [ VSIZE] PRT/MAX SHRMOD REGION DETAIL
        # __TEXT         7fff20000000-7fff21000000 [16.0M] r-x/rwx SM=COW /usr/lib/dyld
        
        for line in output.split('\n'):
            # skip header and empty lines
            if not line.strip() or line.startswith('==') or 'REGION TYPE' in line:
                continue
            
            # try to extract address range
            match = re.search(r'([0-9a-f]+)-([0-9a-f]+)', line)
            if not match:
                continue
            
            try:
                start = int(match.group(1), 16)
                end = int(match.group(2), 16)
                
                # extract permissions if available
                perm_match = re.search(r'\s([r-][w-][x-]/[r-][w-][x-])\s', line)
                if perm_match:
                    # take the current permissions (before /)
                    perms = perm_match.group(1).split('/')[0] + 'p'
                else:
                    perms = "r--p"  # default
                
                # extract path if available
                path = None
                parts = line.split()
                if len(parts) > 5:
                    # last part might be a path
                    last_part = parts[-1]
                    if '/' in last_part:
                        path = last_part
                
                regions.append(MemoryRegion(
                    start=start,
                    end=end,
                    size=end - start,
                    permissions=perms,
                    path=path
                ))
                
            except (ValueError, IndexError):
                continue
        
        return regions
    
    def _get_regions_fallback(self) -> List[MemoryRegion]:
        """
        Fallback method using ctypes (less reliable).
        
        Returns:
            List of MemoryRegion objects
        """
        # on macOS, we have limited options without root privileges
        # we can only read our own memory using ctypes like on Linux
        # but we can't enumerate regions without special privileges
        
        # return empty list - in a real implementation, we'd use
        # mach kernel APIs with proper privileges
        raise PlatformError(
            "vmmap not available and no fallback implemented. "
            "Install Xcode Command Line Tools: xcode-select --install"
        )
    
    def read_memory(self, address: int, size: int) -> bytes:
        """
        Read memory from a specific address.
        
        Args:
            address: Memory address to read from
            size: Number of bytes to read
            
        Returns:
            Bytes read from memory
        """
        try:
            # similar to Linux, use ctypes to read our own memory
            ptr = ctypes.cast(address, ctypes.POINTER(ctypes.c_char * size))
            return bytes(ptr.contents)
        except Exception as e:
            raise PlatformError(f"Failed to read memory at 0x{address:x}: {e}")

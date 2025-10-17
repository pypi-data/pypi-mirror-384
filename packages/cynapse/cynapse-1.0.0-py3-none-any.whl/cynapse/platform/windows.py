"""Windows-specific memory operations."""

import ctypes
import ctypes.wintypes
from typing import List

from .base import PlatformBase
from ..models import MemoryRegion
from ..exceptions import PlatformError


# Windows API structures and constants
class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", ctypes.wintypes.DWORD),
        ("RegionSize", ctypes.c_size_t),
        ("State", ctypes.wintypes.DWORD),
        ("Protect", ctypes.wintypes.DWORD),
        ("Type", ctypes.wintypes.DWORD),
    ]


# Memory protection constants
PAGE_NOACCESS = 0x01
PAGE_READONLY = 0x02
PAGE_READWRITE = 0x04
PAGE_WRITECOPY = 0x08
PAGE_EXECUTE = 0x10
PAGE_EXECUTE_READ = 0x20
PAGE_EXECUTE_READWRITE = 0x40
PAGE_EXECUTE_WRITECOPY = 0x80

# Memory state constants
MEM_COMMIT = 0x1000
MEM_RESERVE = 0x2000
MEM_FREE = 0x10000


class WindowsPlatform(PlatformBase):
    """Windows platform implementation."""
    
    def __init__(self):
        """Initialize Windows platform."""
        try:
            # load kernel32.dll
            self.kernel32 = ctypes.windll.kernel32
            
            # set up VirtualQuery function
            self.kernel32.VirtualQuery.argtypes = [
                ctypes.c_void_p,
                ctypes.POINTER(MEMORY_BASIC_INFORMATION),
                ctypes.c_size_t
            ]
            self.kernel32.VirtualQuery.restype = ctypes.c_size_t
            
            # set up ReadProcessMemory
            self.kernel32.ReadProcessMemory.argtypes = [
                ctypes.wintypes.HANDLE,
                ctypes.c_void_p,
                ctypes.c_void_p,
                ctypes.c_size_t,
                ctypes.POINTER(ctypes.c_size_t)
            ]
            self.kernel32.ReadProcessMemory.restype = ctypes.wintypes.BOOL
            
            # get current process handle
            self.process_handle = self.kernel32.GetCurrentProcess()
            
        except AttributeError:
            raise PlatformError("Not on Windows or kernel32.dll not available")
    
    def get_platform_name(self) -> str:
        """Get platform name."""
        return "windows"
    
    def get_memory_regions(self) -> List[MemoryRegion]:
        """
        Query memory regions using VirtualQuery.
        
        Returns:
            List of MemoryRegion objects
        """
        regions = []
        address = 0
        max_address = 0x7FFFFFFFFFFFFFFF  # max user-space address on 64-bit
        
        mbi = MEMORY_BASIC_INFORMATION()
        mbi_size = ctypes.sizeof(mbi)
        
        while address < max_address:
            # query this memory region
            result = self.kernel32.VirtualQuery(
                ctypes.c_void_p(address),
                ctypes.byref(mbi),
                mbi_size
            )
            
            if result == 0:
                # no more regions
                break
            
            # skip free/reserved regions, only interested in committed memory
            if mbi.State == MEM_COMMIT:
                region = self._create_region_from_mbi(mbi)
                if region:
                    regions.append(region)
            
            # move to next region
            address = mbi.BaseAddress + mbi.RegionSize
            
            # safety check to avoid infinite loop
            if mbi.RegionSize == 0:
                address += 0x1000  # skip by page size
        
        return regions
    
    def _create_region_from_mbi(self, mbi: MEMORY_BASIC_INFORMATION) -> MemoryRegion:
        """
        Create MemoryRegion from MEMORY_BASIC_INFORMATION.
        
        Args:
            mbi: MEMORY_BASIC_INFORMATION structure
            
        Returns:
            MemoryRegion object
        """
        start = mbi.BaseAddress
        size = mbi.RegionSize
        end = start + size
        
        # convert protection flags to permissions string
        permissions = self._protection_to_string(mbi.Protect)
        
        return MemoryRegion(
            start=start,
            end=end,
            size=size,
            permissions=permissions,
            path=None  # Windows doesn't provide path info via VirtualQuery
        )
    
    def _protection_to_string(self, protect: int) -> str:
        """
        Convert Windows protection flags to Unix-style permission string.
        
        Args:
            protect: Protection flags
            
        Returns:
            Permission string like "r-x" or "rw-"
        """
        perms = ""
        
        # check for read
        if protect in [PAGE_READONLY, PAGE_READWRITE, PAGE_EXECUTE_READ, 
                       PAGE_EXECUTE_READWRITE, PAGE_WRITECOPY, PAGE_EXECUTE_WRITECOPY]:
            perms += "r"
        else:
            perms += "-"
        
        # check for write
        if protect in [PAGE_READWRITE, PAGE_EXECUTE_READWRITE, 
                       PAGE_WRITECOPY, PAGE_EXECUTE_WRITECOPY]:
            perms += "w"
        else:
            perms += "-"
        
        # check for execute
        if protect in [PAGE_EXECUTE, PAGE_EXECUTE_READ, 
                       PAGE_EXECUTE_READWRITE, PAGE_EXECUTE_WRITECOPY]:
            perms += "x"
        else:
            perms += "-"
        
        # add 'p' for private (Windows doesn't distinguish shared/private easily)
        perms += "p"
        
        return perms
    
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
            # create buffer to hold the data
            buffer = ctypes.create_string_buffer(size)
            bytes_read = ctypes.c_size_t(0)
            
            # read from our own process
            success = self.kernel32.ReadProcessMemory(
                self.process_handle,
                ctypes.c_void_p(address),
                buffer,
                size,
                ctypes.byref(bytes_read)
            )
            
            if not success:
                raise PlatformError(f"ReadProcessMemory failed at 0x{address:x}")
            
            return bytes(buffer[:bytes_read.value])
            
        except Exception as e:
            raise PlatformError(f"Failed to read memory at 0x{address:x}: {e}")

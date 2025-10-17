"""Base interface for platform-specific memory operations."""

from abc import ABC, abstractmethod
from typing import List

from ..models import MemoryRegion


class PlatformBase(ABC):
    """Abstract base class for platform-specific operations."""
    
    @abstractmethod
    def get_memory_regions(self) -> List[MemoryRegion]:
        """
        Get list of memory regions for the current process.
        
        Returns:
            List of MemoryRegion objects
        """
        pass
    
    @abstractmethod
    def read_memory(self, address: int, size: int) -> bytes:
        """
        Read memory from a specific address.
        
        Args:
            address: Memory address to read from
            size: Number of bytes to read
            
        Returns:
            Bytes read from memory
        """
        pass
    
    @abstractmethod
    def get_platform_name(self) -> str:
        """
        Get the platform name.
        
        Returns:
            Platform name (e.g., 'linux', 'windows', 'darwin')
        """
        pass
    
    def filter_executable_regions(self, regions: List[MemoryRegion]) -> List[MemoryRegion]:
        """
        Filter for executable memory regions.
        
        Args:
            regions: List of memory regions
            
        Returns:
            List of executable regions
        """
        return [r for r in regions if 'x' in r.permissions or 'X' in r.permissions]
    
    def filter_readable_regions(self, regions: List[MemoryRegion]) -> List[MemoryRegion]:
        """
        Filter for readable memory regions.
        
        Args:
            regions: List of memory regions
            
        Returns:
            List of readable regions
        """
        return [r for r in regions if 'r' in r.permissions or 'R' in r.permissions]

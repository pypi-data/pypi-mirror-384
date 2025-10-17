"""Configuration utilities and builder pattern."""

from typing import List, Callable, Optional

from ..models import MonitorConfig, ProtectionLevel, TamperResponse, TamperEvent
from ..monitor import Monitor


class MonitorBuilder:
    """Builder for fluent Monitor configuration."""
    
    def __init__(self):
        """Initialize builder with default config."""
        self._config = MonitorConfig()
    
    def interval(self, seconds: float) -> 'MonitorBuilder':
        """
        Set monitoring interval.
        
        Args:
            seconds: Interval in seconds
            
        Returns:
            Self for chaining
        """
        self._config.interval = seconds
        return self
    
    def protection_level(self, level: ProtectionLevel) -> 'MonitorBuilder':
        """
        Set protection level.
        
        Args:
            level: ProtectionLevel enum value
            
        Returns:
            Self for chaining
        """
        self._config.protection_level = level
        
        # adjust other settings based on level
        if level == ProtectionLevel.LOW:
            self._config.enable_bytecode_verification = True
            self._config.enable_module_tracking = False
            self._config.enable_import_hooks = False
            self._config.adaptive_sampling = False
        elif level == ProtectionLevel.MEDIUM:
            self._config.enable_bytecode_verification = True
            self._config.enable_module_tracking = True
            self._config.enable_import_hooks = False
            self._config.adaptive_sampling = True
        elif level == ProtectionLevel.HIGH:
            self._config.enable_bytecode_verification = True
            self._config.enable_module_tracking = True
            self._config.enable_import_hooks = True
            self._config.adaptive_sampling = True
        elif level == ProtectionLevel.PARANOID:
            self._config.enable_bytecode_verification = True
            self._config.enable_module_tracking = True
            self._config.enable_import_hooks = True
            self._config.enable_merkle_trees = True
            self._config.enable_forensics = True
            self._config.adaptive_sampling = True
        
        return self
    
    def hash_algorithm(self, algorithm: str) -> 'MonitorBuilder':
        """
        Set hash algorithm.
        
        Args:
            algorithm: 'sha256' or 'blake3'
            
        Returns:
            Self for chaining
        """
        self._config.hash_algorithm = algorithm
        return self
    
    def enable_bytecode_verification(self, enabled: bool = True) -> 'MonitorBuilder':
        """Enable or disable bytecode verification."""
        self._config.enable_bytecode_verification = enabled
        return self
    
    def enable_module_tracking(self, enabled: bool = True) -> 'MonitorBuilder':
        """Enable or disable module tracking."""
        self._config.enable_module_tracking = enabled
        return self
    
    def enable_import_hooks(self, enabled: bool = True) -> 'MonitorBuilder':
        """Enable or disable import hook monitoring."""
        self._config.enable_import_hooks = enabled
        return self
    
    def enable_merkle_trees(self, enabled: bool = True) -> 'MonitorBuilder':
        """Enable or disable Merkle trees."""
        self._config.enable_merkle_trees = enabled
        return self
    
    def enable_auto_healing(self, enabled: bool = True) -> 'MonitorBuilder':
        """Enable or disable auto-healing."""
        self._config.enable_auto_healing = enabled
        return self
    
    def enable_forensics(self, enabled: bool = True) -> 'MonitorBuilder':
        """Enable or disable forensic snapshots."""
        self._config.enable_forensics = enabled
        return self
    
    def adaptive_sampling(self, enabled: bool = True) -> 'MonitorBuilder':
        """Enable or disable adaptive sampling."""
        self._config.adaptive_sampling = enabled
        return self
    
    def whitelist_modules(self, modules: List[str]) -> 'MonitorBuilder':
        """
        Set whitelisted modules.
        
        Args:
            modules: List of module patterns to whitelist
            
        Returns:
            Self for chaining
        """
        self._config.whitelist_modules = modules
        return self
    
    def protect_modules(self, modules: List[str]) -> 'MonitorBuilder':
        """
        Set modules to protect.
        
        Args:
            modules: List of module names to protect
            
        Returns:
            Self for chaining
        """
        self._config.protect_modules = modules
        return self
    
    def tamper_response(self, response: TamperResponse) -> 'MonitorBuilder':
        """
        Set default tamper response.
        
        Args:
            response: TamperResponse enum value
            
        Returns:
            Self for chaining
        """
        self._config.tamper_response = response
        return self
    
    def on_tamper(self, callback: Callable[[TamperEvent], Optional[TamperResponse]]) -> 'MonitorBuilder':
        """
        Set tamper event callback.
        
        Args:
            callback: Callback function
            
        Returns:
            Self for chaining
        """
        self._config.on_tamper = callback
        return self
    
    def log_level(self, level: str) -> 'MonitorBuilder':
        """
        Set log level.
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR)
            
        Returns:
            Self for chaining
        """
        self._config.log_level = level
        return self
    
    def log_format(self, format: str) -> 'MonitorBuilder':
        """
        Set log format.
        
        Args:
            format: 'text' or 'json'
            
        Returns:
            Self for chaining
        """
        self._config.log_format = format
        return self
    
    def snapshot_dir(self, directory: str) -> 'MonitorBuilder':
        """
        Set forensic snapshot directory.
        
        Args:
            directory: Path to snapshot directory
            
        Returns:
            Self for chaining
        """
        self._config.snapshot_dir = directory
        return self
    
    def build(self) -> Monitor:
        """
        Build and return the Monitor instance.
        
        Returns:
            Configured Monitor instance
        """
        return Monitor(config=self._config)

"""Bytecode analysis and verification."""

import dis
import sys
from types import FunctionType, CodeType
from typing import Dict, List, Optional, Tuple

from ..models import TamperType, TamperEvent
from ..exceptions import VerificationError
from datetime import datetime


class BytecodeAnalyzer:
    """Analyzes and verifies Python bytecode integrity."""
    
    def __init__(self, hash_engine):
        """
        Initialize bytecode analyzer.
        
        Args:
            hash_engine: HashEngine instance for computing hashes
        """
        self.hash_engine = hash_engine
        self._baseline = {}  # func_id -> hash
        self._code_objects = {}  # func_id -> code object
    
    def register_function(self, func: FunctionType) -> str:
        """
        Register a function for monitoring.
        
        Args:
            func: Function to register
            
        Returns:
            Hash of the function's bytecode
        """
        func_id = self._get_function_id(func)
        code_hash = self.hash_engine.hash_bytecode(func.__code__)
        
        self._baseline[func_id] = code_hash
        self._code_objects[func_id] = func.__code__
        
        return code_hash
    
    def verify_function(self, func: FunctionType) -> Optional[TamperEvent]:
        """
        Verify a function hasn't been tampered with.
        
        Args:
            func: Function to verify
            
        Returns:
            TamperEvent if tampering detected, None otherwise
        """
        func_id = self._get_function_id(func)
        
        # if we're not tracking this function, nothing to verify
        if func_id not in self._baseline:
            return None
        
        expected_hash = self._baseline[func_id]
        current_hash = self.hash_engine.hash_bytecode(func.__code__)
        
        if current_hash != expected_hash:
            return TamperEvent(
                type=TamperType.BYTECODE_MODIFICATION,
                target=func,
                timestamp=datetime.now(),
                baseline_hash=expected_hash,
                current_hash=current_hash,
                details=f"Function {func.__name__} bytecode modified"
            )
        
        # also check if the function object itself was replaced
        if func.__code__ is not self._code_objects[func_id]:
            return TamperEvent(
                type=TamperType.FUNCTION_REPLACEMENT,
                target=func,
                timestamp=datetime.now(),
                baseline_hash=expected_hash,
                current_hash=current_hash,
                details=f"Function {func.__name__} code object replaced"
            )
        
        return None
    
    def diff_bytecode(self, func: FunctionType) -> Optional[List[Tuple[int, str, str]]]:
        """
        Show differences between current and baseline bytecode.
        
        Args:
            func: Function to diff
            
        Returns:
            List of (offset, baseline_instruction, current_instruction) tuples
            or None if function not in baseline
        """
        func_id = self._get_function_id(func)
        
        if func_id not in self._code_objects:
            return None
        
        baseline_code = self._code_objects[func_id]
        current_code = func.__code__
        
        if baseline_code.co_code == current_code.co_code:
            return []  # no differences
        
        # disassemble both versions
        baseline_instructions = list(dis.get_instructions(baseline_code))
        current_instructions = list(dis.get_instructions(current_code))
        
        differences = []
        
        # compare instruction by instruction
        max_len = max(len(baseline_instructions), len(current_instructions))
        for i in range(max_len):
            baseline_instr = baseline_instructions[i] if i < len(baseline_instructions) else None
            current_instr = current_instructions[i] if i < len(current_instructions) else None
            
            if baseline_instr != current_instr:
                baseline_str = f"{baseline_instr.opname} {baseline_instr.argval}" if baseline_instr else "MISSING"
                current_str = f"{current_instr.opname} {current_instr.argval}" if current_instr else "MISSING"
                offset = baseline_instr.offset if baseline_instr else (current_instr.offset if current_instr else i)
                
                differences.append((offset, baseline_str, current_str))
        
        return differences
    
    def restore_function(self, func: FunctionType) -> bool:
        """
        Restore a function to its baseline bytecode.
        
        Args:
            func: Function to restore
            
        Returns:
            True if restored, False if not in baseline
        """
        func_id = self._get_function_id(func)
        
        if func_id not in self._code_objects:
            return False
        
        # restore the original code object
        original_code = self._code_objects[func_id]
        
        # replace the code object on the function
        # this is a bit tricky because we can't directly assign to __code__
        # but we can create a new function with the old code
        try:
            func.__code__ = original_code
            return True
        except (AttributeError, TypeError):
            return False
    
    def get_bytecode_summary(self, func: FunctionType) -> Dict[str, any]:
        """
        Get detailed summary of function bytecode.
        
        Args:
            func: Function to analyze
            
        Returns:
            Dictionary with bytecode details
        """
        code = func.__code__
        
        return {
            'name': func.__name__,
            'filename': code.co_filename,
            'lineno': code.co_firstlineno,
            'argcount': code.co_argcount,
            'nlocals': code.co_nlocals,
            'stacksize': code.co_stacksize,
            'flags': code.co_flags,
            'code_size': len(code.co_code),
            'constants': code.co_consts,
            'names': code.co_names,
            'varnames': code.co_varnames,
            'hash': self.hash_engine.hash_bytecode(code),
        }
    
    def _get_function_id(self, func: FunctionType) -> str:
        """
        Generate a unique identifier for a function.
        
        Args:
            func: Function to identify
            
        Returns:
            Unique string identifier
        """
        # use module name, qualified name, and id as identifier
        module = func.__module__ if hasattr(func, '__module__') else ''
        qualname = func.__qualname__ if hasattr(func, '__qualname__') else func.__name__
        return f"{module}.{qualname}:{id(func)}"
    
    def get_baseline_size(self) -> int:
        """Get number of functions in baseline."""
        return len(self._baseline)
    
    def clear_baseline(self) -> None:
        """Clear all baseline data."""
        self._baseline.clear()
        self._code_objects.clear()

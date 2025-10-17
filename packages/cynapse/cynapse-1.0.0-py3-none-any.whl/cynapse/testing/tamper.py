"""Tamper simulation tools for testing detection."""

import types
from types import FunctionType
from typing import Callable


class TamperSimulator:
    """Simulates various types of tampering for testing."""
    
    @staticmethod
    def modify_bytecode(func: FunctionType, new_code: bytes) -> None:
        """
        Modify a function's bytecode.
        
        WARNING: This is for testing only!
        
        Args:
            func: Function to modify
            new_code: New bytecode
        """
        # create a new code object with modified bytecode
        old_code = func.__code__
        
        new_code_obj = types.CodeType(
            old_code.co_argcount,
            old_code.co_posonlyargcount if hasattr(old_code, 'co_posonlyargcount') else 0,
            old_code.co_kwonlyargcount,
            old_code.co_nlocals,
            old_code.co_stacksize,
            old_code.co_flags,
            new_code,  # modified bytecode
            old_code.co_consts,
            old_code.co_names,
            old_code.co_varnames,
            old_code.co_filename,
            old_code.co_name,
            old_code.co_firstlineno,
            old_code.co_lnotab,
            old_code.co_freevars,
            old_code.co_cellvars
        )
        
        func.__code__ = new_code_obj
    
    @staticmethod
    def replace_function(obj, func_name: str, new_func: Callable) -> Callable:
        """
        Replace a function/method on an object.
        
        Args:
            obj: Object or module to modify
            func_name: Name of function to replace
            new_func: New function to use
            
        Returns:
            Original function
        """
        original = getattr(obj, func_name)
        setattr(obj, func_name, new_func)
        return original
    
    @staticmethod
    def inject_attribute(func: FunctionType, attr_name: str, value) -> None:
        """
        Inject an attribute into a function.
        
        Args:
            func: Function to modify
            attr_name: Attribute name
            value: Attribute value
        """
        func.__dict__[attr_name] = value
    
    @staticmethod
    def monkey_patch_method(cls: type, method_name: str, new_method: Callable) -> Callable:
        """
        Monkey patch a class method.
        
        Args:
            cls: Class to modify
            method_name: Method name to replace
            new_method: New method implementation
            
        Returns:
            Original method
        """
        original = getattr(cls, method_name)
        setattr(cls, method_name, new_method)
        return original
    
    @staticmethod
    def create_malicious_function() -> FunctionType:
        """
        Create a simple malicious function for testing.
        
        Returns:
            Malicious function
        """
        def malicious():
            # simulated malicious behavior
            return "malicious"
        
        return malicious


def inject_code_constant(func: FunctionType, new_const) -> None:
    """
    Inject a new constant into function's co_consts.
    
    Args:
        func: Function to modify
        new_const: Constant to inject
    """
    old_code = func.__code__
    new_consts = old_code.co_consts + (new_const,)
    
    new_code_obj = types.CodeType(
        old_code.co_argcount,
        old_code.co_posonlyargcount if hasattr(old_code, 'co_posonlyargcount') else 0,
        old_code.co_kwonlyargcount,
        old_code.co_nlocals,
        old_code.co_stacksize,
        old_code.co_flags,
        old_code.co_code,
        new_consts,  # modified constants
        old_code.co_names,
        old_code.co_varnames,
        old_code.co_filename,
        old_code.co_name,
        old_code.co_firstlineno,
        old_code.co_lnotab,
        old_code.co_freevars,
        old_code.co_cellvars
    )
    
    func.__code__ = new_code_obj

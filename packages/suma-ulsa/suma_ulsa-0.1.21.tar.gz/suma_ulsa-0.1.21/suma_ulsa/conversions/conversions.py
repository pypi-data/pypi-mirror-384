"""
Number conversion utilities.
"""
try:
    # Import from Rust extension
    from ..suma_ulsa.conversions import *
except ImportError:
    # Fallback for type checkers
    pass

__all__ = [
    "NumberConverter",
    "binary_to_decimal",
    "decimal_to_binary", 
    "decimal_to_hex",
    "decimal_to_letters",
    "binary_to_hex",
    "hex_to_decimal",
    "hex_to_binary",
    "letters_to_decimal", 
    "convert_number",
    "SUPPORTED_FORMATS"
]
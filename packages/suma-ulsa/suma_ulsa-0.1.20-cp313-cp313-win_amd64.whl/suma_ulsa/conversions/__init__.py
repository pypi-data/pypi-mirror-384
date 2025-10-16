"""
Number conversion utilities.
"""
from .conversions import (
    NumberConverter,
    binary_to_decimal,
    decimal_to_binary,
    decimal_to_hex, 
    decimal_to_letters,
    binary_to_hex,
    hex_to_decimal,
    hex_to_binary,
    letters_to_decimal,
    convert_number,
    SUPPORTED_FORMATS
)

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

# Re-exporta explícitamente para linters
if False:
    # Esto nunca se ejecuta pero ayuda a linters
    from .conversions import *
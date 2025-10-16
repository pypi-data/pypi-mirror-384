"""
Internal module that imports from the actual Rust extension.
"""
try:
    from ..suma_ulsa import *
except ImportError:
    # Fallback for type checkers
    pass
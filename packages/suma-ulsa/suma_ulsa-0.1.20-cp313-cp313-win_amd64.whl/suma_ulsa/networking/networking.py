"""
Networking module bindings
"""
try:
    # Import from Rust extension
    from ..suma_ulsa.networking import *
except ImportError:
    # Fallback for type checkers
    pass

__all__ = [
    "SubnetCalculator",
    "create_subnet_calculator",
    "calculate_subnets",
    "SubnetRow"
]
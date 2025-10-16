"""
Boolean algebra module interface.
"""
try:
    # Import from Rust extension
    from ..suma_ulsa.boolean_algebra import *
except ImportError:
    # Fallback for type checkers
    pass

__all__ = [
    "BooleanExpr",
    "TruthTable", 
    "parse_expression_debug",
    "truth_table_from_expr",
]
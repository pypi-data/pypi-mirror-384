"""
Boolean algebra utilities.
"""
from .boolean_algebra import (
    BooleanExpr,
    TruthTable,
    parse_expression_debug, 
    truth_table_from_expr
)

__all__ = [
    "BooleanExpr",
    "TruthTable",
    "parse_expression_debug",
    "truth_table_from_expr"
]

# Re-exporta explícitamente para linters
if False:
    from .boolean_algebra import *
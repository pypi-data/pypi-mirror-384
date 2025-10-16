"""
SUMA ULSA - Sistema Unificado de Métodos Avanzados
"""
import importlib
try:
    _native = importlib.import_module("suma_ulsa.suma_ulsa_native")
except ImportError as e:
    raise ImportError(
        "No se pudo cargar el módulo nativo 'suma_ulsa_native'. "
        "Asegúrate de instalar el paquete compilado correctamente."
    ) from e

# Importa explícitamente submódulos Python para linters
from .conversions import *
from .boolean_algebra import *
from .networking import *

__version__ = "0.1.13"

__all__ = [
    # Conversions
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
    "SUPPORTED_FORMATS",
    
    # Boolean Algebra
    "BooleanExpr",
    "TruthTable",
    "parse_expression_debug",
    "truth_table_from_expr",

    # Networking
    "SubnetCalculator",
    "SubnetRow",
    "create_subnet_calculator",
    "calculate_subnets"
]

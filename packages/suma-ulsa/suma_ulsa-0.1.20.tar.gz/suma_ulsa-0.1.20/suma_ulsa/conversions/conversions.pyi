from typing import List, Literal

NumberFormat = Literal["decimal", "binary", "hex", "letters"]

class NumberConverter:
    """
    A number converter that maintains conversion history.
    
    This class allows converting numbers between decimal, binary, hexadecimal,
    and letter representations while keeping track of all conversions performed.
    
    Example:
        >>> converter = NumberConverter(42)
        >>> converter.to_binary()
        '101010'
        >>> converter.to_hex()
        '2A'
        >>> converter.get_history()
        ['decimal=42', 'binary=101010', 'hex=2A']
    """
    
    def __init__(self, value: int) -> None:
        """
        Initialize the converter with a decimal value.
        
        Args:
            value: Initial decimal value
        """
        ...
    
    def to_binary(self) -> str:
        """
        Convert the current value to binary representation.
        
        Returns:
            Binary string representation (e.g., "1010" for decimal 10)
        """
        ...
    
    def to_hex(self) -> str:
        """
        Convert the current value to hexadecimal representation.
        
        Returns:
            Hexadecimal string in uppercase (e.g., "FF" for decimal 255)
        """
        ...
    
    def to_letters(self) -> str:
        """
        Convert the current value to letter representation.
        
        Uses the scheme where A=1, B=2, ..., Z=26, AA=27, AB=28, etc.
        
        Returns:
            Letter representation (e.g., "A" for 1, "ABC" for 731)
        
        Raises:
            ValueError: If the value is not positive
        """
        ...
    
    def get_history(self) -> List[str]:
        """
        Get the complete conversion history.
        
        Returns:
            List of conversion records in chronological order
        """
        ...
    
    @property
    def value(self) -> int:
        """The current decimal value as integer."""
        ...
    
    @value.setter
    def value(self, value: int) -> None:
        """
        Set a new decimal value and add to history.
        
        Args:
            value: New decimal value to set
        """
        ...
    
    def __repr__(self) -> str:
        """Official string representation."""
        ...
    
    def __str__(self) -> str:
        """Informal string representation."""
        ...

def binary_to_decimal(s: str) -> int:
    """
    Convert binary string to decimal integer.
    
    Args:
        s: Binary string (e.g., "1010")
    
    Returns:
        Decimal integer
    
    Raises:
        ValueError: If the string contains invalid binary characters
    """
    ...

def decimal_to_binary(n: int) -> str:
    """
    Convert decimal integer to binary string.
    
    Args:
        n: Decimal integer
    
    Returns:
        Binary string without leading zeros
    """
    ...

def decimal_to_hex(n: int) -> str:
    """
    Convert decimal integer to hexadecimal string.
    
    Args:
        n: Decimal integer
    
    Returns:
        Hexadecimal string in uppercase
    """
    ...

def decimal_to_letters(n: int) -> str:
    """
    Convert decimal integer to letter representation.
    
    Args:
        n: Positive decimal integer
    
    Returns:
        Letter representation
    
    Raises:
        ValueError: If n is not positive
    """
    ...

def binary_to_hex(s: str) -> str:
    """
    Convert binary string to hexadecimal string.
    
    Args:
        s: Binary string
    
    Returns:
        Hexadecimal string
    
    Raises:
        ValueError: If the binary string is invalid
    """
    ...

def hex_to_decimal(s: str) -> int:
    """
    Convert hexadecimal string to decimal integer.
    
    Args:
        s: Hexadecimal string (case insensitive)
    
    Returns:
        Decimal integer
    
    Raises:
        ValueError: If the hexadecimal string is invalid
    """
    ...

def hex_to_binary(s: str) -> str:
    """
    Convert hexadecimal string to binary string.
    
    Args:
        s: Hexadecimal string
    
    Returns:
        Binary string
    
    Raises:
        ValueError: If the hexadecimal string is invalid
    """
    ...

def letters_to_decimal(s: str) -> int:
    """
    Convert letter representation to decimal integer.
    
    Args:
        s: String containing only uppercase letters A-Z
    
    Returns:
        Decimal integer
    
    Raises:
        ValueError: If the string contains invalid characters or is empty
    """
    ...

def convert_number(value: str, from_format: str, to_format: str) -> str:
    """
    General-purpose number conversion between supported formats.
    
    Args:
        value: The number as string
        from_format: Source format: "decimal", "binary", "hex", or "letters"
        to_format: Target format: "decimal", "binary", "hex", or "letters"
    
    Returns:
        Converted number as string
    
    Raises:
        ValueError: If conversion fails or formats are not supported
    
    Example:
        >>> convert_number("1010", "binary", "hex")
        'A'
        >>> convert_number("255", "decimal", "letters")
        'IU'
    """
    ...

# Supported conversion formats
SUPPORTED_FORMATS: List[str]
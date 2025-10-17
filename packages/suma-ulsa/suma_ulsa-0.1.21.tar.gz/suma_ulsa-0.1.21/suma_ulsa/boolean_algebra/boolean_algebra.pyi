from typing import Dict, List, Optional, Callable
import polars as pl

class TruthTable:
    """
    A class representing a truth table for boolean logic operations.
    
    This class provides methods for creating, manipulating, and analyzing 
    truth tables with support for various output formats and operations.
    
    Attributes:
        variables: List of variable names used in the truth table
        combinations: List of boolean combinations for each row
        columns: Dictionary mapping column names to their boolean values
        column_order: List of column names in display order
    
    Example:
        >>> tt = TruthTable(
        ...     variables=['A', 'B'],
        ...     columns={
        ...         'A': [False, False, True, True],
        ...         'B': [False, True, False, True],
        ...         'A AND B': [False, False, False, True]
        ...     },
        ...     column_order=['A', 'B', 'A AND B'],
        ...     combinations=[[False, False], [False, True], [True, False], [True, True]]
        ... )
        >>> print(tt)
        A      B      A AND B
        False  False  False  
        False  True   False  
        True   False  False  
        True   True   True   
    """
    
    variables: List[str]
    combinations: List[List[bool]]
    columns: Dict[str, List[bool]]
    column_order: List[str]

    def __init__(self, variables: List[str], columns: Dict[str, List[bool]], 
                 column_order: List[str], combinations: List[List[bool]]) -> None:
        """
        Initialize a TruthTable.

        Args:
            variables: List of variable names (e.g., ['A', 'B', 'C'])
            columns: Dictionary mapping column names to their boolean values
            column_order: List of column names in the desired display order
            combinations: List of boolean combinations for each row

        Raises:
            ValueError: If inputs have inconsistent lengths or invalid data

        Example:
            >>> tt = TruthTable(
            ...     variables=['A', 'B'],
            ...     columns={'A': [F, F, T, T], 'B': [F, T, F, T], 'A AND B': [F, F, F, T]},
            ...     column_order=['A', 'B', 'A AND B'],
            ...     combinations=[[F, F], [F, T], [T, F], [T, T]]
            ... )
        """
        ...

    def to_polars(self) -> pl.DataFrame:
        """
        Convert the truth table to a Polars DataFrame.

        Returns:
            A Polars DataFrame representing the truth table.

        Example:
            >>> df = tt.to_polars()
            >>> print(df)
            shape: (4, 3)
            ┌───────┬───────┬─────────┐
            │ A     ┆ B     ┆ A AND B │
            │ ---   ┆ ---   ┆ ---     │
            │ bool  ┆ bool  ┆ bool    │
            ╞═══════╪═══════╪═════════╡
            │ false ┆ false ┆ false   │
            │ false ┆ true  ┆ false   │
            │ true  ┆ false ┆ false   │
            │ true  ┆ true  ┆ true    │
            └───────┴───────┴─────────┘
        """
        ...

    def to_lazyframe(self) -> pl.LazyFrame:
        """
        Convert the truth table to a Polars LazyFrame for lazy evaluation.

        Returns:
            A Polars LazyFrame representing the truth table.

        Example:
            >>> lf = tt.to_lazyframe()
            >>> result = lf.filter(pl.col("A AND B") == True).collect()
        """
        ...

    def to_column_dict(self) -> Dict[str, List[bool]]:
        """
        Convert the truth table to a dictionary of columns.

        Returns:
            Dictionary mapping column names to lists of boolean values.

        Example:
            >>> col_dict = tt.to_column_dict()
            >>> print(col_dict['A AND B'])
            [False, False, False, True]
        """
        ...

    def to_list(self) -> List[List[bool]]:
        """
        Convert the truth table to a list of boolean combinations.

        Returns:
            List of lists, where each inner list is a row of boolean values.

        Example:
            >>> rows = tt.to_list()
            >>> print(rows[0])  # First row
            [False, False, False]
        """
        ...

    def to_named_rows(self) -> List[Dict[str, bool]]:
        """
        Convert the truth table to a list of dictionaries mapping column names to values.

        Returns:
            List of dictionaries, where each dictionary represents a row.

        Example:
            >>> named_rows = tt.to_named_rows()
            >>> print(named_rows[0])
            {'A': False, 'B': False, 'A AND B': False}
        """
        ...

    def get_row(self, index: int) -> Optional[Dict[str, bool]]:
        """
        Get a specific row by index.

        Args:
            index: The row index (0-based).

        Returns:
            A dictionary mapping column names to boolean values, or None if index is out of range.

        Example:
            >>> row = tt.get_row(2)
            >>> print(row)
            {'A': True, 'B': False, 'A AND B': False}
        """
        ...

    def get_column(self, variable: str) -> Optional[List[bool]]:
        """
        Get the values for a specific column.

        Args:
            variable: The column name.

        Returns:
            A list of boolean values for the column, or None if the column does not exist.

        Example:
            >>> col_values = tt.get_column('A')
            >>> print(col_values)
            [False, False, True, True]
        """
        ...

    def filter_true(self) -> 'TruthTable':
        """
        Filter rows where the result column (last column) is True.

        Returns:
            A new TruthTable containing only rows where the last column is True.

        Raises:
            ValueError: If the truth table has no columns.

        Example:
            >>> true_tt = tt.filter_true()
            >>> print(len(true_tt))
            1  # Only one row where A AND B is True
        """
        ...

    def filter_false(self) -> 'TruthTable':
        """
        Filter rows where the result column (last column) is False.

        Returns:
            A new TruthTable containing only rows where the last column is False.

        Raises:
            ValueError: If the truth table has no columns.

        Example:
            >>> false_tt = tt.filter_false()
            >>> print(len(false_tt))
            3  # Three rows where A AND B is False
        """
        ...

    def satisfiable_assignments(self, value: bool = True) -> List[Dict[str, bool]]:
        """
        Get variable assignments where the result column equals the specified value.

        Args:
            value: The boolean value to filter by (default: True).

        Returns:
            List of dictionaries mapping variable names to boolean values.

        Raises:
            ValueError: If the truth table has no columns.

        Example:
            >>> satisfiable = tt.satisfiable_assignments(True)
            >>> print(satisfiable)
            [{'A': True, 'B': True, 'A AND B': True}]
        """
        ...

    def select_columns(self, columns: List[str]) -> 'TruthTable':
        """
        Select specific columns to create a new TruthTable.

        Args:
            columns: List of column names to select.

        Returns:
            A new TruthTable containing only the specified columns.

        Raises:
            ValueError: If any specified column does not exist.

        Example:
            >>> simplified_tt = tt.select_columns(['A', 'A AND B'])
            >>> print(simplified_tt.column_order)
            ['A', 'A AND B']
        """
        ...

    def filter(self, column: str, predicate: Callable[[bool], bool]) -> 'TruthTable':
        """
        Filter rows based on a predicate applied to a specific column.

        Args:
            column: The column name to filter on.
            predicate: A callable that takes a boolean value and returns True/False.

        Returns:
            A new TruthTable containing only rows where the predicate is True.

        Raises:
            ValueError: If the column does not exist.

        Example:
            >>> filtered_tt = tt.filter('A', lambda x: x == True)  # Keep only rows where A is True
            >>> print(len(filtered_tt))
            2
        """
        ...

    def equivalent_to(self, other: 'TruthTable') -> bool:
        """
        Check if this truth table is logically equivalent to another.

        Two truth tables are equivalent if they have the same variables
        and produce the same results for all combinations.

        Args:
            other: Another TruthTable to compare with.

        Returns:
            True if the truth tables are equivalent, False otherwise.

        Raises:
            ValueError: If the truth tables have different variables.

        Example:
            >>> tt1 = BooleanExpr("A AND B").truth_table()
            >>> tt2 = BooleanExpr("B AND A").truth_table()
            >>> print(tt1.equivalent_to(tt2))
            True
        """
        ...

    def to_csv(self) -> str:
        """
        Export the truth table to CSV format.

        Returns:
            A string containing the CSV representation.

        Example:
            >>> csv_data = tt.to_csv()
            >>> print(csv_data)
            A,B,A AND B
            False,False,False
            False,True,False
            True,False,False
            True,True,True
        """
        ...

    def to_json(self) -> str:
        """
        Export the truth table to JSON format.

        Returns:
            A string containing the JSON representation.

        Example:
            >>> json_data = tt.to_json()
            >>> print(json_data)
            [{"A": false, "B": false, "A AND B": false}, ...]
        """
        ...

    def column_stats(self, column: str) -> Dict[str, float]:
        """
        Compute statistics for a specific column.

        Args:
            column: The column name to analyze.

        Returns:
            Dictionary with:
            - 'true_count': Number of True values
            - 'false_count': Number of False values  
            - 'true_percentage': Percentage of True values (0-100)

        Raises:
            ValueError: If the column does not exist.

        Example:
            >>> stats = tt.column_stats('A AND B')
            >>> print(stats)
            {'true_count': 1, 'false_count': 3, 'true_percentage': 25.0}
        """
        ...

    def summary(self) -> Dict[str, float]:
        """
        Generate a comprehensive summary of the truth table.

        Returns:
            Dictionary containing:
            - num_variables: Number of variables
            - total_combinations: Number of rows (2^num_variables)
            - true_count: Number of True values in the result column
            - false_count: Number of False values in the result column
            - true_percentage: Percentage of True values in the result column
            - For each variable: <variable>_true_count

        Raises:
            ValueError: If the truth table has no columns.

        Example:
            >>> summary = tt.summary()
            >>> print(summary)
            {
                'num_variables': 2,
                'total_combinations': 4,
                'true_count': 1,
                'false_count': 3,
                'true_percentage': 25.0,
                'A_true_count': 2,
                'B_true_count': 2
            }
        """
        ...

    def to_pretty_string(self) -> str:
        """
        Generate a pretty-printed string representation of the truth table.

        Returns:
            A formatted string representation with aligned columns.

        Example:
            >>> print(tt.to_pretty_string())
            A      B      A AND B
            ────── ────── ────────
            False  False  False  
            False  True   False  
            True   False  False  
            True   True   True   
        """
        ...

    def __len__(self) -> int:
        """
        Get the number of rows in the truth table.

        Returns:
            The number of rows.

        Example:
            >>> print(len(tt))
            4
        """
        ...

    def __getitem__(self, index: int) -> Dict[str, bool]:
        """
        Get a row by index using subscript notation.

        Args:
            index: The row index (0-based).

        Returns:
            A dictionary mapping column names to boolean values.

        Raises:
            IndexError: If the index is out of range.

        Example:
            >>> row = tt[0]
            >>> print(row['A'])
            False
        """
        ...

    def __str__(self) -> str:
        """
        Return the string representation of the truth table.

        Returns:
            A pretty-printed string representation.
        """
        ...

    def __repr__(self) -> str:
        """
        Return the official string representation of the truth table.

        Returns:
            A string representation suitable for debugging.
        """
        ...


class BooleanExpr:
    """
    A class for parsing and evaluating boolean expressions.
    
    Supports logical operators: AND, OR, NOT, and parentheses for grouping.
    
    Example:
        >>> expr = BooleanExpr("(A AND B) OR NOT C")
        >>> result = expr.evaluate({'A': True, 'B': False, 'C': True})
        >>> print(result)
        False
    """
    
    def __init__(self, expr: str) -> None:
        """
        Initialize a Boolean expression parser.

        Args:
            expr: String representing a boolean expression using variables,
                  AND, OR, NOT operations. Example: "(A AND B) OR NOT C"

        Raises:
            ValueError: If the expression is empty, too complex, or contains invalid syntax.

        Example:
            >>> expr = BooleanExpr("A AND (B OR C)")
            >>> print(expr.variables)
            ['A', 'B', 'C']
        """
        ...

    def evaluate(self, values: Dict[str, bool]) -> bool:
        """
        Evaluate the boolean expression with the given variable values.

        Args:
            values: Dictionary mapping variable names to their boolean values.

        Returns:
            The result of evaluating the expression.

        Raises:
            ValueError: If any variable in the expression is missing from the values dict.

        Example:
            >>> expr = BooleanExpr("A AND B")
            >>> result = expr.evaluate({'A': True, 'B': True})
            >>> print(result)
            True
        """
        ...

    def evaluate_with_defaults(self, values: Dict[str, bool], default: bool = False) -> bool:
        """
        Evaluate the boolean expression with default values for missing variables.

        Args:
            values: Dictionary mapping variable names to their boolean values.
            default: Default value to use for any variables missing from the values dict.

        Returns:
            The result of evaluating the expression.

        Example:
            >>> expr = BooleanExpr("A AND B")
            >>> result = expr.evaluate_with_defaults({'A': True}, default=False)
            >>> print(result)  # B defaults to False
            False
        """
        ...

    def truth_table(self) -> TruthTable:
        """
        Generate the truth table for the expression.

        Returns:
            A TruthTable object representing the truth table.

        Example:
            >>> expr = BooleanExpr("A AND B")
            >>> tt = expr.truth_table()
            >>> print(tt)
            A      B      A AND B
            False  False  False  
            False  True   False  
            True   False  False  
            True   True   True   
        """
        ...

    def full_truth_table(self) -> TruthTable:
        """
        Generate the complete truth table for all variables in the expression.

        This method automatically determines the variables from the expression.

        Returns:
            A TruthTable object representing the complete truth table.

        Example:
            >>> expr = BooleanExpr("A AND B")
            >>> tt = expr.full_truth_table()
            >>> print(tt.column_order)
            ['A', 'B', 'A AND B']
        """
        ...

    def to_prefix_notation(self) -> str:
        """
        Convert the expression to prefix notation (Polish notation).

        Useful for debugging and understanding the expression structure.

        Returns:
            The expression in prefix (Polish) notation.

        Example:
            >>> expr = BooleanExpr("A AND B")
            >>> print(expr.to_prefix_notation())
            AND(A, B)
        """
        ...

    def is_tautology(self) -> bool:
        """
        Check if the expression is a tautology (always true for all inputs).

        Returns:
            True if the expression is a tautology, False otherwise.

        Example:
            >>> expr = BooleanExpr("A OR NOT A")
            >>> print(expr.is_tautology())
            True
        """
        ...

    def is_contradiction(self) -> bool:
        """
        Check if the expression is a contradiction (always false for all inputs).

        Returns:
            True if the expression is a contradiction, False otherwise.

        Example:
            >>> expr = BooleanExpr("A AND NOT A")
            >>> print(expr.is_contradiction())
            True
        """
        ...

    def equivalent_to(self, other: 'BooleanExpr') -> bool:
        """
        Check if two expressions are logically equivalent.

        Args:
            other: Another BooleanExpr to compare with.

        Returns:
            True if both expressions produce the same results for all variable combinations.

        Example:
            >>> expr1 = BooleanExpr("A AND B")
            >>> expr2 = BooleanExpr("B AND A")
            >>> print(expr1.equivalent_to(expr2))
            True
        """
        ...

    @property
    def variables(self) -> List[str]:
        """
        Get the list of unique variables used in the expression.

        Returns:
            List of variable names used in the expression, sorted alphabetically.

        Example:
            >>> expr = BooleanExpr("(A AND B) OR C")
            >>> print(expr.variables)
            ['A', 'B', 'C']
        """
        ...

    @property
    def complexity(self) -> int:
        """
        Get the complexity of the expression (number of operators).

        Returns:
            The number of operators in the expression.

        Example:
            >>> expr = BooleanExpr("A AND B OR C")
            >>> print(expr.complexity)
            2
        """
        ...

    def __str__(self) -> str:
        """
        Return the string representation of the expression.

        Returns:
            The expression in infix notation.
        """
        ...

    def __repr__(self) -> str:
        """
        Return the official string representation of the expression.

        Returns:
            A string representation suitable for debugging.
        """
        ...

    def __and__(self, other: 'BooleanExpr') -> 'BooleanExpr':
        """
        Return a new BooleanExpr representing the AND of this and another expression.

        Args:
            other: Another BooleanExpr to combine with.

        Returns:
            A new BooleanExpr representing the AND operation.

        Example:
            >>> expr1 = BooleanExpr("A")
            >>> expr2 = BooleanExpr("B")
            >>> expr3 = expr1 & expr2  # Equivalent to "A AND B"
        """
        ...

    def __or__(self, other: 'BooleanExpr') -> 'BooleanExpr':
        """
        Return a new BooleanExpr representing the OR of this and another expression.

        Args:
            other: Another BooleanExpr to combine with.

        Returns:
            A new BooleanExpr representing the OR operation.

        Example:
            >>> expr1 = BooleanExpr("A")
            >>> expr2 = BooleanExpr("B")
            >>> expr3 = expr1 | expr2  # Equivalent to "A OR B"
        """
        ...

    def __invert__(self) -> 'BooleanExpr':
        """
        Return a new BooleanExpr representing the NOT of this expression.

        Returns:
            A new BooleanExpr representing the NOT operation.

        Example:
            >>> expr1 = BooleanExpr("A")
            >>> expr2 = ~expr1  # Equivalent to "NOT A"
        """
        ...


def parse_expression_debug(expression: str) -> str:
    """
    Parse an expression and return its AST in prefix notation (for debugging).

    Args:
        expression: Boolean expression string to parse.

    Returns:
        The expression in prefix (Polish) notation.

    Raises:
        ValueError: If the expression is invalid.

    Example:
        >>> result = parse_expression_debug("A AND B")
        >>> print(result)
        AND(A, B)
    """
    ...


def truth_table_from_expr(variables: List[str], results: List[bool]) -> BooleanExpr:
    """
    Create a BooleanExpr from a truth table specification using Quine-McCluskey algorithm.

    Args:
        variables: List of variable names (e.g., ['A', 'B', 'C']).
        results: List of boolean results for each combination (in standard binary order).

    Returns:
        A BooleanExpr that matches the specified truth table.

    Raises:
        ValueError: If the length of results doesn't match 2^len(variables).

    Example:
        >>> # Create expression for A AND B truth table
        >>> variables = ['A', 'B']
        >>> results = [False, False, False, True]  # FF, FT, TF, TT
        >>> expr = truth_table_from_expr(variables, results)
        >>> print(expr)
        A AND B
    """
    ...
"""
Mathematical functions for Mock Spark.

This module provides comprehensive mathematical functions that match PySpark's
math function API. Includes arithmetic operations, rounding functions, trigonometric
functions, and mathematical transformations for numerical processing in DataFrames.

Key Features:
    - Complete PySpark math function API compatibility
    - Arithmetic operations (abs, round, ceil, floor)
    - Advanced math functions (sqrt, exp, log, pow)
    - Trigonometric functions (sin, cos, tan)
    - Type-safe operations with proper return types
    - Support for both column references and numeric literals
    - Proper handling of edge cases and null values

Example:
    >>> from mock_spark import MockSparkSession, F
    >>> spark = MockSparkSession("test")
    >>> data = [{"value": 3.7, "angle": 1.57}]
    >>> df = spark.createDataFrame(data)
    >>> df.select(
    ...     F.round(F.col("value"), 1),
    ...     F.ceil(F.col("value")),
    ...     F.sin(F.col("angle"))
    ... ).show()
    +--- MockDataFrame: 1 rows ---+
    round(value, 1) |  ceil(value) |   sin(angle)
    ---------------------------------------------
             4.0 |            4 |         1.57
"""

from typing import Union, Optional
from mock_spark.functions.base import MockColumn, MockColumnOperation


class MathFunctions:
    """Collection of mathematical functions."""

    @staticmethod
    def abs(column: Union[MockColumn, str]) -> MockColumnOperation:
        """Get absolute value.

        Args:
            column: The column to get absolute value of.

        Returns:
            MockColumnOperation representing the abs function.
        """
        if isinstance(column, str):
            column = MockColumn(column)

        operation = MockColumnOperation(column, "abs", name=f"abs({column.name})")
        return operation

    @staticmethod
    def round(column: Union[MockColumn, str], scale: int = 0) -> MockColumnOperation:
        """Round to specified number of decimal places.

        Args:
            column: The column to round.
            scale: Number of decimal places (default: 0).

        Returns:
            MockColumnOperation representing the round function.
        """
        if isinstance(column, str):
            column = MockColumn(column)

        operation = MockColumnOperation(
            column, "round", scale, name=f"round({column.name}, {scale})"
        )
        return operation

    @staticmethod
    def ceil(column: Union[MockColumn, str]) -> MockColumnOperation:
        """Round up to nearest integer.

        Args:
            column: The column to round up.

        Returns:
            MockColumnOperation representing the ceil function.
        """
        if isinstance(column, str):
            column = MockColumn(column)

        operation = MockColumnOperation(column, "ceil", name=f"ceil({column.name})")
        return operation

    @staticmethod
    def floor(column: Union[MockColumn, str]) -> MockColumnOperation:
        """Round down to nearest integer.

        Args:
            column: The column to round down.

        Returns:
            MockColumnOperation representing the floor function.
        """
        if isinstance(column, str):
            column = MockColumn(column)

        operation = MockColumnOperation(column, "floor", name=f"floor({column.name})")
        return operation

    @staticmethod
    def sqrt(column: Union[MockColumn, str]) -> MockColumnOperation:
        """Get square root.

        Args:
            column: The column to get square root of.

        Returns:
            MockColumnOperation representing the sqrt function.
        """
        if isinstance(column, str):
            column = MockColumn(column)

        operation = MockColumnOperation(column, "sqrt", name=f"sqrt({column.name})")
        return operation

    @staticmethod
    def exp(column: Union[MockColumn, str]) -> MockColumnOperation:
        """Get exponential (e^x).

        Args:
            column: The column to get exponential of.

        Returns:
            MockColumnOperation representing the exp function.
        """
        if isinstance(column, str):
            column = MockColumn(column)

        operation = MockColumnOperation(column, "exp", name=f"exp({column.name})")
        return operation

    @staticmethod
    def log(column: Union[MockColumn, str], base: Optional[float] = None) -> MockColumnOperation:
        """Get logarithm.

        Args:
            column: The column to get logarithm of.
            base: Optional base for logarithm (default: natural log).

        Returns:
            MockColumnOperation representing the log function.
        """
        if isinstance(column, str):
            column = MockColumn(column)

        name = f"log({base}, {column.name})" if base is not None else f"log({column.name})"
        operation = MockColumnOperation(column, "log", base, name=name)
        return operation

    @staticmethod
    def pow(
        column: Union[MockColumn, str], exponent: Union[MockColumn, float, int]
    ) -> MockColumnOperation:
        """Raise to power.

        Args:
            column: The column to raise to power.
            exponent: The exponent.

        Returns:
            MockColumnOperation representing the pow function.
        """
        if isinstance(column, str):
            column = MockColumn(column)

        operation = MockColumnOperation(
            column, "pow", exponent, name=f"pow({column.name}, {exponent})"
        )
        return operation

    @staticmethod
    def sin(column: Union[MockColumn, str]) -> MockColumnOperation:
        """Get sine.

        Args:
            column: The column to get sine of.

        Returns:
            MockColumnOperation representing the sin function.
        """
        if isinstance(column, str):
            column = MockColumn(column)

        operation = MockColumnOperation(column, "sin", name=f"sin({column.name})")
        return operation

    @staticmethod
    def cos(column: Union[MockColumn, str]) -> MockColumnOperation:
        """Get cosine.

        Args:
            column: The column to get cosine of.

        Returns:
            MockColumnOperation representing the cos function.
        """
        if isinstance(column, str):
            column = MockColumn(column)

        operation = MockColumnOperation(column, "cos", name=f"cos({column.name})")
        return operation

    @staticmethod
    def tan(column: Union[MockColumn, str]) -> MockColumnOperation:
        """Get tangent.

        Args:
            column: The column to get tangent of.

        Returns:
            MockColumnOperation representing the tan function.
        """
        if isinstance(column, str):
            column = MockColumn(column)

        operation = MockColumnOperation(column, "tan", name=f"tan({column.name})")
        return operation

    @staticmethod
    def sign(column: Union[MockColumn, str]) -> MockColumnOperation:
        """Get sign of number (-1, 0, or 1).

        Args:
            column: The column to get sign of.

        Returns:
            MockColumnOperation representing the sign function.
        """
        if isinstance(column, str):
            column = MockColumn(column)

        # PySpark 3.2 uses signum, not sign, as the function name
        operation = MockColumnOperation(column, "signum", name=f"signum({column.name})")
        return operation

    @staticmethod
    def greatest(*columns: Union[MockColumn, str]) -> MockColumnOperation:
        """Get the greatest value among columns.

        Args:
            *columns: Columns to compare.

        Returns:
            MockColumnOperation representing the greatest function.
        """
        if not columns:
            raise ValueError("At least one column must be provided")

        base_column = MockColumn(columns[0]) if isinstance(columns[0], str) else columns[0]
        column_names = [col.name if hasattr(col, "name") else str(col) for col in columns]
        operation = MockColumnOperation(
            base_column,
            "greatest",
            columns[1:],
            name=f"greatest({', '.join(column_names)})",
        )
        return operation

    @staticmethod
    def least(*columns: Union[MockColumn, str]) -> MockColumnOperation:
        """Get the least value among columns.

        Args:
            *columns: Columns to compare.

        Returns:
            MockColumnOperation representing the least function.
        """
        if not columns:
            raise ValueError("At least one column must be provided")

        base_column = MockColumn(columns[0]) if isinstance(columns[0], str) else columns[0]
        column_names = [col.name if hasattr(col, "name") else str(col) for col in columns]
        operation = MockColumnOperation(
            base_column, "least", columns[1:], name=f"least({', '.join(column_names)})"
        )
        return operation

"""Testing utilities for PySpark DataFrames.

This module provides utilities to assist with testing Spark transformations
and validating DataFrame outputs.
"""

from typing import List, Optional

from polyspark.exceptions import PolysparkError
from polyspark.protocols import DataFrameProtocol, StructTypeProtocol, is_pyspark_available


class DataFrameComparisonError(PolysparkError):
    """Raised when DataFrame comparison fails."""

    pass


def assert_dataframe_equal(
    df1: DataFrameProtocol,
    df2: DataFrameProtocol,
    check_order: bool = False,
    rtol: float = 1e-5,
    atol: float = 1e-8,
    check_nullable: bool = True,
    check_column_order: bool = False,
) -> None:
    """Assert that two DataFrames are equal.

    This function compares two DataFrames for equality, checking:
    - Row counts
    - Schemas (field names, types, and optionally nullability)
    - Data content (with optional ordering)
    - Floating point values (with tolerance)

    Args:
        df1: First DataFrame to compare.
        df2: Second DataFrame to compare.
        check_order: If True, row order must match. If False, DataFrames are sorted
                    before comparison. Default is False.
        rtol: Relative tolerance for floating point comparisons. Default is 1e-5.
        atol: Absolute tolerance for floating point comparisons. Default is 1e-8.
        check_nullable: If True, check that nullable property matches in schema.
                       Default is True.
        check_column_order: If True, column order must match. If False, columns are
                           compared regardless of order. Default is False.

    Raises:
        DataFrameComparisonError: If DataFrames are not equal, with details about
                                 the differences.

    Example:
        ```python
        from polyspark.testing import assert_dataframe_equal

        df1 = spark.createDataFrame([{"id": 1, "name": "Alice"}])
        df2 = spark.createDataFrame([{"id": 1, "name": "Alice"}])

        assert_dataframe_equal(df1, df2)  # Passes
        ```
    """
    if not is_pyspark_available():
        raise DataFrameComparisonError(
            "PySpark is required for DataFrame comparison. " "Install it with: pip install pyspark"
        )


    # Check row counts
    count1 = df1.count()
    count2 = df2.count()

    if count1 != count2:
        raise DataFrameComparisonError(
            f"DataFrame row counts don't match: {count1} != {count2}\n"
            f"  df1.count() = {count1}\n"
            f"  df2.count() = {count2}"
        )

    # Check schemas
    try:
        assert_schema_equal(
            df1.schema, df2.schema, check_nullable=check_nullable, check_order=check_column_order
        )
    except DataFrameComparisonError as e:
        raise DataFrameComparisonError(f"DataFrame schemas don't match:\n{str(e)}") from e

    # If column order doesn't matter, sort columns
    if not check_column_order:
        cols = sorted(df1.columns)
        df1 = df1.select(cols)
        df2 = df2.select(cols)

    # If row order doesn't matter, sort rows
    if not check_order and count1 > 0:
        # Sort by all columns for deterministic comparison
        df1 = df1.orderBy(*df1.columns)
        df2 = df2.orderBy(*df2.columns)

    # Collect and compare data
    rows1 = df1.collect()
    rows2 = df2.collect()

    differences = []
    for i, (row1, row2) in enumerate(zip(rows1, rows2)):
        row1_dict = row1.asDict()
        row2_dict = row2.asDict()

        for col_name in row1_dict.keys():
            val1 = row1_dict[col_name]
            val2 = row2_dict[col_name]

            if val1 != val2:
                # Special handling for floats
                if isinstance(val1, float) and isinstance(val2, float):
                    if not _floats_are_close(val1, val2, rtol, atol):
                        differences.append(
                            f"  Row {i}, column '{col_name}': {val1} != {val2} "
                            f"(diff={abs(val1 - val2):.2e}, rtol={rtol}, atol={atol})"
                        )
                else:
                    differences.append(f"  Row {i}, column '{col_name}': {val1} != {val2}")

    if differences:
        error_msg = "DataFrames have differing values:\n" + "\n".join(differences[:10])
        if len(differences) > 10:
            error_msg += f"\n  ... and {len(differences) - 10} more differences"
        raise DataFrameComparisonError(error_msg)


def assert_schema_equal(
    schema1: StructTypeProtocol,
    schema2: StructTypeProtocol,
    check_nullable: bool = True,
    check_order: bool = False,
) -> None:
    """Assert that two schemas are equal.

    Args:
        schema1: First schema to compare.
        schema2: Second schema to compare.
        check_nullable: If True, check that nullable property matches. Default is True.
        check_order: If True, field order must match. Default is False.

    Raises:
        DataFrameComparisonError: If schemas are not equal, with details about
                                 the differences.

    Example:
        ```python
        from polyspark.testing import assert_schema_equal
        from pyspark.sql.types import StructType, StructField, StringType

        schema1 = StructType([StructField("name", StringType(), True)])
        schema2 = StructType([StructField("name", StringType(), True)])

        assert_schema_equal(schema1, schema2)  # Passes
        ```
    """
    if not is_pyspark_available():
        raise DataFrameComparisonError(
            "PySpark is required for schema comparison. Install it with: pip install pyspark"
        )

    fields1 = schema1.fields
    fields2 = schema2.fields

    if len(fields1) != len(fields2):
        raise DataFrameComparisonError(
            f"Schemas have different number of fields: {len(fields1)} != {len(fields2)}\n"
            f"  schema1 fields: {[f.name for f in fields1]}\n"
            f"  schema2 fields: {[f.name for f in fields2]}"
        )

    # Create field maps
    fields1_map = {f.name: f for f in fields1}
    fields2_map = {f.name: f for f in fields2}

    # Check that all field names match
    names1 = set(fields1_map.keys())
    names2 = set(fields2_map.keys())

    if names1 != names2:
        missing_in_2 = names1 - names2
        missing_in_1 = names2 - names1
        error_parts = ["Schemas have different field names:"]
        if missing_in_2:
            error_parts.append(f"  Fields in schema1 but not schema2: {sorted(missing_in_2)}")
        if missing_in_1:
            error_parts.append(f"  Fields in schema2 but not schema1: {sorted(missing_in_1)}")
        raise DataFrameComparisonError("\n".join(error_parts))

    # Check field order if required
    if check_order:
        for i, (f1, f2) in enumerate(zip(fields1, fields2)):
            if f1.name != f2.name:
                raise DataFrameComparisonError(
                    f"Field order mismatch at position {i}:\n"
                    f"  schema1: {f1.name}\n"
                    f"  schema2: {f2.name}"
                )

    # Check field types and nullable
    differences = []
    for field_name in sorted(names1):
        field1 = fields1_map[field_name]
        field2 = fields2_map[field_name]

        # Compare data types
        if field1.dataType != field2.dataType:
            differences.append(
                f"  Field '{field_name}' has different types:\n"
                f"    schema1: {field1.dataType}\n"
                f"    schema2: {field2.dataType}"
            )

        # Compare nullable if required
        if check_nullable and field1.nullable != field2.nullable:
            differences.append(
                f"  Field '{field_name}' has different nullable:\n"
                f"    schema1: {field1.nullable}\n"
                f"    schema2: {field2.nullable}"
            )

    if differences:
        error_msg = "Schemas have differing field properties:\n" + "\n".join(differences)
        raise DataFrameComparisonError(error_msg)


def assert_approx_count(df: DataFrameProtocol, expected_count: int, tolerance: float = 0.1) -> None:
    """Assert that DataFrame row count is approximately equal to expected.

    Useful for testing data generation or sampling operations where exact
    count may vary but should be close to expected.

    Args:
        df: DataFrame to check.
        expected_count: Expected row count.
        tolerance: Allowed relative difference (0.1 = 10%). Default is 0.1.

    Raises:
        DataFrameComparisonError: If count is outside tolerance range.

    Example:
        ```python
        from polyspark.testing import assert_approx_count

        df = spark.range(0, 95)  # Expected ~100 with some variation
        assert_approx_count(df, 100, tolerance=0.1)  # Passes (within 10%)
        ```
    """
    actual_count = df.count()
    min_count = int(expected_count * (1 - tolerance))
    max_count = int(expected_count * (1 + tolerance))

    if not (min_count <= actual_count <= max_count):
        raise DataFrameComparisonError(
            f"DataFrame count {actual_count} is not within {tolerance * 100:.1f}% "
            f"of expected {expected_count}\n"
            f"  Expected range: [{min_count}, {max_count}]\n"
            f"  Actual count: {actual_count}"
        )


def get_column_stats(df: DataFrameProtocol, column: str) -> dict:
    """Get basic statistics for a column.

    Args:
        df: DataFrame to analyze.
        column: Column name.

    Returns:
        Dictionary with statistics (count, null_count, distinct_count, etc.)

    Example:
        ```python
        from polyspark.testing import get_column_stats

        df = spark.createDataFrame([{"value": 1}, {"value": 2}, {"value": None}])
        stats = get_column_stats(df, "value")
        print(stats)  # {'count': 3, 'null_count': 1, 'distinct_count': 2, ...}
        ```
    """
    if not is_pyspark_available():
        raise DataFrameComparisonError(
            "PySpark is required for column stats. Install it with: pip install pyspark"
        )

    from pyspark.sql.functions import col, countDistinct

    total_count = df.count()
    non_null_count = df.filter(col(column).isNotNull()).count()
    null_count = total_count - non_null_count
    distinct_count = df.select(countDistinct(column)).collect()[0][0]

    stats = {
        "count": total_count,
        "non_null_count": non_null_count,
        "null_count": null_count,
        "distinct_count": distinct_count,
    }

    # Add type-specific stats
    dtype = dict(df.dtypes)[column]
    if dtype in ("int", "bigint", "double", "float", "decimal"):
        desc = df.describe(column).collect()
        stats["min"] = float(desc[3][column]) if desc[3][column] else None
        stats["max"] = float(desc[4][column]) if desc[4][column] else None
        stats["mean"] = float(desc[1][column]) if desc[1][column] else None
        stats["stddev"] = float(desc[2][column]) if desc[2][column] else None

    return stats


def assert_column_exists(df: DataFrameProtocol, *columns: str) -> None:
    """Assert that specified columns exist in DataFrame.

    Args:
        df: DataFrame to check.
        *columns: Column names to check for existence.

    Raises:
        DataFrameComparisonError: If any column is missing.

    Example:
        ```python
        from polyspark.testing import assert_column_exists

        df = spark.createDataFrame([{"id": 1, "name": "Alice"}])
        assert_column_exists(df, "id", "name")  # Passes
        assert_column_exists(df, "age")  # Raises error
        ```
    """
    df_columns = set(df.columns)
    missing = [col for col in columns if col not in df_columns]

    if missing:
        raise DataFrameComparisonError(
            f"Columns missing from DataFrame: {missing}\n"
            f"  Available columns: {sorted(df_columns)}\n"
            f"  Missing columns: {sorted(missing)}"
        )


def assert_no_duplicates(df: DataFrameProtocol, columns: Optional[List[str]] = None) -> None:
    """Assert that DataFrame has no duplicate rows.

    Args:
        df: DataFrame to check.
        columns: Optional list of columns to check for duplicates.
                If None, checks all columns.

    Raises:
        DataFrameComparisonError: If duplicates are found.

    Example:
        ```python
        from polyspark.testing import assert_no_duplicates

        df = spark.createDataFrame([{"id": 1}, {"id": 2}])
        assert_no_duplicates(df)  # Passes

        df_dup = spark.createDataFrame([{"id": 1}, {"id": 1}])
        assert_no_duplicates(df_dup, columns=["id"])  # Raises error
        ```
    """
    if columns is None:
        unique_count = df.distinct().count()
    else:
        unique_count = df.dropDuplicates(columns).count()

    total_count = df.count()

    if unique_count != total_count:
        duplicate_count = total_count - unique_count
        raise DataFrameComparisonError(
            f"DataFrame contains {duplicate_count} duplicate row(s)\n"
            f"  Total rows: {total_count}\n"
            f"  Unique rows: {unique_count}\n"
            f"  Duplicate rows: {duplicate_count}"
        )


def _floats_are_close(a: float, b: float, rtol: float, atol: float) -> bool:
    """Check if two floats are approximately equal.

    Uses the formula: abs(a - b) <= (atol + rtol * abs(b))
    """
    return abs(a - b) <= (atol + rtol * abs(b))

"""Data export and import utilities for polyspark."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from polyspark.exceptions import PolysparkError
from polyspark.protocols import DataFrameProtocol, SparkSessionProtocol, is_pyspark_available


class DataIOError(PolysparkError):
    """Raised when data I/O operations fail."""

    pass


def save_as_parquet(
    df: DataFrameProtocol,
    path: str,
    mode: str = "overwrite",
    partition_by: Optional[Union[str, List[str]]] = None,
    **options: Any,
) -> None:
    """Save DataFrame as Parquet file.

    Args:
        df: DataFrame to save.
        path: Output path for Parquet file.
        mode: Save mode ('overwrite', 'append', 'ignore', 'error'). Default is 'overwrite'.
        partition_by: Column(s) to partition by. Can be a single column name or list of names.
        **options: Additional Spark writer options.

    Raises:
        DataIOError: If save operation fails.

    Example:
        ```python
        from polyspark import spark_factory
        from polyspark.io import save_as_parquet

        @spark_factory
        @dataclass
        class User:
            id: int
            name: str
            date: str

        df = User.build_dataframe(spark, size=1000)
        save_as_parquet(df, "users.parquet", partition_by="date")
        ```
    """
    if not is_pyspark_available():
        raise DataIOError("PySpark is required for Parquet operations")

    try:
        writer = df.write.mode(mode)

        if partition_by:
            if isinstance(partition_by, str):
                partition_by = [partition_by]
            writer = writer.partitionBy(*partition_by)

        if options:
            writer = writer.options(**options)

        writer.parquet(path)

    except Exception as e:
        raise DataIOError(f"Failed to save Parquet file: {e}") from e


def save_as_json(df: DataFrameProtocol, path: str, mode: str = "overwrite", **options: Any) -> None:
    """Save DataFrame as JSON file.

    Args:
        df: DataFrame to save.
        path: Output path for JSON file.
        mode: Save mode ('overwrite', 'append', 'ignore', 'error'). Default is 'overwrite'.
        **options: Additional Spark writer options.

    Raises:
        DataIOError: If save operation fails.

    Example:
        ```python
        from polyspark.io import save_as_json

        df = User.build_dataframe(spark, size=100)
        save_as_json(df, "users.json")
        ```
    """
    if not is_pyspark_available():
        raise DataIOError("PySpark is required for JSON operations")

    try:
        writer = df.write.mode(mode)

        if options:
            writer = writer.options(**options)

        writer.json(path)

    except Exception as e:
        raise DataIOError(f"Failed to save JSON file: {e}") from e


def save_as_csv(
    df: DataFrameProtocol,
    path: str,
    mode: str = "overwrite",
    header: bool = True,
    **options: Any,
) -> None:
    """Save DataFrame as CSV file.

    Args:
        df: DataFrame to save.
        path: Output path for CSV file.
        mode: Save mode ('overwrite', 'append', 'ignore', 'error'). Default is 'overwrite'.
        header: Whether to include header row. Default is True.
        **options: Additional Spark writer options.

    Raises:
        DataIOError: If save operation fails.

    Example:
        ```python
        from polyspark.io import save_as_csv

        df = Product.build_dataframe(spark, size=500)
        save_as_csv(df, "products.csv", sep="|")
        ```
    """
    if not is_pyspark_available():
        raise DataIOError("PySpark is required for CSV operations")

    try:
        writer = df.write.mode(mode).option("header", header)

        if options:
            writer = writer.options(**options)

        writer.csv(path)

    except Exception as e:
        raise DataIOError(f"Failed to save CSV file: {e}") from e


def load_parquet(spark: SparkSessionProtocol, path: str, **options: Any) -> DataFrameProtocol:
    """Load DataFrame from Parquet file.

    Args:
        spark: SparkSession instance.
        path: Path to Parquet file.
        **options: Additional Spark reader options.

    Returns:
        Loaded DataFrame.

    Raises:
        DataIOError: If load operation fails.

    Example:
        ```python
        from polyspark.io import load_parquet

        df = load_parquet(spark, "users.parquet")
        print(df.count())
        ```
    """
    if not is_pyspark_available():
        raise DataIOError("PySpark is required for Parquet operations")

    try:
        reader = spark.read

        if options:
            reader = reader.options(**options)

        return reader.parquet(path)  # type: ignore[no-any-return]

    except Exception as e:
        raise DataIOError(f"Failed to load Parquet file: {e}") from e


def load_json(spark: SparkSessionProtocol, path: str, **options: Any) -> DataFrameProtocol:
    """Load DataFrame from JSON file.

    Args:
        spark: SparkSession instance.
        path: Path to JSON file.
        **options: Additional Spark reader options.

    Returns:
        Loaded DataFrame.

    Raises:
        DataIOError: If load operation fails.

    Example:
        ```python
        from polyspark.io import load_json

        df = load_json(spark, "users.json")
        df.show()
        ```
    """
    if not is_pyspark_available():
        raise DataIOError("PySpark is required for JSON operations")

    try:
        reader = spark.read

        if options:
            reader = reader.options(**options)

        return reader.json(path)  # type: ignore[no-any-return]

    except Exception as e:
        raise DataIOError(f"Failed to load JSON file: {e}") from e


def load_csv(
    spark: SparkSessionProtocol,
    path: str,
    header: bool = True,
    infer_schema: bool = True,
    **options: Any,
) -> DataFrameProtocol:
    """Load DataFrame from CSV file.

    Args:
        spark: SparkSession instance.
        path: Path to CSV file.
        header: Whether CSV has header row. Default is True.
        infer_schema: Whether to infer schema automatically. Default is True.
        **options: Additional Spark reader options.

    Returns:
        Loaded DataFrame.

    Raises:
        DataIOError: If load operation fails.

    Example:
        ```python
        from polyspark.io import load_csv

        df = load_csv(spark, "products.csv", sep="|")
        df.printSchema()
        ```
    """
    if not is_pyspark_available():
        raise DataIOError("PySpark is required for CSV operations")

    try:
        reader = spark.read.option("header", header).option("inferSchema", infer_schema)

        if options:
            reader = reader.options(**options)

        return reader.csv(path)  # type: ignore[no-any-return]

    except Exception as e:
        raise DataIOError(f"Failed to load CSV file: {e}") from e


def load_and_validate(
    spark: SparkSessionProtocol,
    path: str,
    expected_schema: Optional[Any] = None,
    validate_schema: bool = True,
) -> DataFrameProtocol:
    """Load data file and optionally validate against expected schema.

    Args:
        spark: SparkSession instance.
        path: Path to data file (.parquet, .json, or .csv).
        expected_schema: Expected schema (PySpark StructType). If None, no validation.
        validate_schema: Whether to validate schema. Default is True.

    Returns:
        Loaded and validated DataFrame.

    Raises:
        DataIOError: If load or validation fails.

    Example:
        ```python
        from polyspark import infer_schema
        from polyspark.io import load_and_validate

        expected = infer_schema(User)
        df = load_and_validate(spark, "users.parquet", expected_schema=expected)
        ```
    """
    if not is_pyspark_available():
        raise DataIOError("PySpark is required for data loading")

    try:
        # Detect format from file extension
        file_path = Path(path)
        suffix = file_path.suffix.lower()

        if suffix == ".parquet":
            df = load_parquet(spark, path)
        elif suffix == ".json":
            df = load_json(spark, path)
        elif suffix == ".csv":
            df = load_csv(spark, path)
        else:
            raise DataIOError(
                f"Unsupported file format: {suffix}\n" "Supported formats: .parquet, .json, .csv"
            )

        # Validate schema if requested
        if validate_schema and expected_schema is not None:
            from polyspark.testing import assert_schema_equal

            try:
                assert_schema_equal(
                    expected_schema, df.schema, check_nullable=False, check_order=False
                )
            except Exception as e:
                raise DataIOError(f"Schema validation failed: {e}") from e

        return df

    except DataIOError:
        raise
    except Exception as e:
        raise DataIOError(f"Failed to load and validate data: {e}") from e


def save_dicts_as_json(data: List[Dict[str, Any]], path: str) -> None:
    """Save list of dictionaries as JSON lines file.

    This function works without PySpark installed.

    Args:
        data: List of dictionaries to save.
        path: Output file path.

    Raises:
        DataIOError: If save operation fails.

    Example:
        ```python
        from polyspark.io import save_dicts_as_json

        dicts = User.build_dicts(size=100)
        save_dicts_as_json(dicts, "users.jsonl")
        ```
    """
    import json

    try:
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w") as f:
            for record in data:
                json.dump(record, f, default=str)
                f.write("\n")

    except Exception as e:
        raise DataIOError(f"Failed to save JSON file: {e}") from e


def load_dicts_from_json(path: str) -> List[Dict[str, Any]]:
    """Load list of dictionaries from JSON lines file.

    This function works without PySpark installed.

    Args:
        path: Path to JSON lines file.

    Returns:
        List of dictionaries.

    Raises:
        DataIOError: If load operation fails.

    Example:
        ```python
        from polyspark.io import load_dicts_from_json

        dicts = load_dicts_from_json("users.jsonl")
        print(f"Loaded {len(dicts)} records")
        ```
    """
    import json

    try:
        file_path = Path(path)

        if not file_path.exists():
            raise DataIOError(f"File not found: {path}")

        data = []
        with open(file_path) as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))

        return data

    except DataIOError:
        raise
    except Exception as e:
        raise DataIOError(f"Failed to load JSON file: {e}") from e

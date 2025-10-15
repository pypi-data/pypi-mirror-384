"""Polyspark - Generate PySpark DataFrames using polyfactory.

This package provides tools to generate PySpark DataFrames for testing and
development using the polyfactory library. It supports dataclasses, Pydantic
models, and TypedDicts without requiring PySpark as a hard dependency.
"""

from polyspark.exceptions import (
    PolysparkError,
    PySparkNotAvailableError,
    SchemaInferenceError,
    UnsupportedTypeError,
)
from polyspark.factory import SparkFactory, build_spark_dataframe, spark_factory
from polyspark.protocols import is_pyspark_available
from polyspark.schema import (
    dataclass_to_ddl_schema,
    dataclass_to_struct_type,
    export_ddl_schema,
    infer_ddl_schema,
    infer_schema,
    pydantic_to_ddl_schema,
    pydantic_to_struct_type,
    python_type_to_ddl_type,
    python_type_to_spark_type,
    save_schema_ddl,
    typed_dict_to_ddl_schema,
    typed_dict_to_struct_type,
)

__version__ = "0.3.0"

__all__ = [
    # Main factory
    "SparkFactory",
    "build_spark_dataframe",
    "spark_factory",
    # Schema utilities
    "dataclass_to_struct_type",
    "infer_schema",
    "pydantic_to_struct_type",
    "python_type_to_spark_type",
    "typed_dict_to_struct_type",
    # DDL schema utilities (work without PySpark)
    "dataclass_to_ddl_schema",
    "export_ddl_schema",
    "infer_ddl_schema",
    "pydantic_to_ddl_schema",
    "python_type_to_ddl_type",
    "save_schema_ddl",
    "typed_dict_to_ddl_schema",
    # Runtime checks
    "is_pyspark_available",
    # Exceptions
    "PolysparkError",
    "PySparkNotAvailableError",
    "SchemaInferenceError",
    "UnsupportedTypeError",
]

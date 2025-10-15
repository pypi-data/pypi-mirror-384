"""Schema inference and conversion logic."""

from dataclasses import fields as dataclass_fields
from dataclasses import is_dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Type, Union, get_args, get_origin

from typing_extensions import get_type_hints

from polyspark.exceptions import SchemaInferenceError, UnsupportedTypeError
from polyspark.protocols import (
    StructTypeProtocol,
    get_pyspark_types,
    is_pyspark_available,
)


def is_optional(type_hint: Type) -> bool:
    """Check if a type hint is Optional (Union with None).

    Args:
        type_hint: The type hint to check.

    Returns:
        bool: True if the type is Optional, False otherwise.
    """
    origin = get_origin(type_hint)
    if origin is Union:
        args = get_args(type_hint)
        return type(None) in args
    return False


def unwrap_optional(type_hint: Type) -> Type:
    """Unwrap Optional type to get the inner type.

    Args:
        type_hint: The Optional type hint.

    Returns:
        The unwrapped type.
    """
    if is_optional(type_hint):
        args = get_args(type_hint)
        # Filter out NoneType
        non_none_args = [arg for arg in args if arg is not type(None)]
        if len(non_none_args) == 1:
            return non_none_args[0]  # type: ignore[no-any-return]
        # Handle Union[X, Y, None] - return first non-None type
        # This is a simplification but works for most cases
        if non_none_args:
            return non_none_args[0]  # type: ignore[no-any-return]
    return type_hint


def python_type_to_ddl_type(python_type: Type) -> str:
    """Convert a Python type to a DDL type string.

    Args:
        python_type: The Python type to convert.

    Returns:
        A DDL type string like "string", "long", "double", etc.

    Raises:
        UnsupportedTypeError: If the type cannot be converted.
    """
    # Handle Optional types
    if is_optional(python_type):
        python_type = unwrap_optional(python_type)

    origin = get_origin(python_type)
    args = get_args(python_type)

    # Handle basic types
    type_mapping = {
        str: "string",
        int: "long",
        float: "double",
        bool: "boolean",
        bytes: "binary",
        bytearray: "binary",
        date: "date",
        datetime: "timestamp",
        Decimal: "decimal(10,0)",
    }

    if python_type in type_mapping:
        return type_mapping[python_type]

    # Handle List/list -> array<T>
    if origin in (list, List):
        if not args:
            raise SchemaInferenceError(f"Cannot infer array element type from {python_type}")
        element_type = python_type_to_ddl_type(args[0])
        return f"array<{element_type}>"

    # Handle Dict/dict -> map<K,V>
    if origin in (dict, Dict):
        if not args or len(args) < 2:
            raise SchemaInferenceError(f"Cannot infer map types from {python_type}")
        key_type = python_type_to_ddl_type(args[0])
        value_type = python_type_to_ddl_type(args[1])
        return f"map<{key_type},{value_type}>"

    # Handle dataclasses and Pydantic models -> struct<...>
    if is_dataclass(python_type):
        return dataclass_to_ddl_schema(python_type)

    # Try Pydantic model
    if hasattr(python_type, "model_fields"):
        return pydantic_to_ddl_schema(python_type)

    # Try TypedDict
    if hasattr(python_type, "__annotations__"):
        try:
            return typed_dict_to_ddl_schema(python_type)
        except Exception:
            pass

    raise UnsupportedTypeError(f"Cannot convert type {python_type} to DDL type")


def dataclass_to_ddl_schema(dataclass_type: Type) -> str:
    """Convert a dataclass to a DDL schema string.

    Args:
        dataclass_type: The dataclass type to convert.

    Returns:
        A DDL schema string like "id long, name string, email string".
    """
    if not is_dataclass(dataclass_type):
        raise ValueError(f"{dataclass_type} is not a dataclass")

    fields = []
    type_hints = get_type_hints(dataclass_type)

    for field in dataclass_fields(dataclass_type):
        field_type = type_hints.get(field.name, field.type)

        try:
            ddl_type = python_type_to_ddl_type(field_type)
            fields.append(f"{field.name}:{ddl_type}")
        except UnsupportedTypeError as e:
            raise SchemaInferenceError(f"Cannot infer type for field {field.name}: {e}") from e

    return "struct<" + ",".join(fields) + ">"


def pydantic_to_ddl_schema(model_type: Type) -> str:
    """Convert a Pydantic model to a DDL schema string.

    Args:
        model_type: The Pydantic model type to convert.

    Returns:
        A DDL schema string.
    """
    if not hasattr(model_type, "model_fields"):
        raise ValueError(f"{model_type} is not a Pydantic v2 model")

    fields = []

    for field_name, field_info in model_type.model_fields.items():
        field_type = field_info.annotation

        try:
            ddl_type = python_type_to_ddl_type(field_type)
            fields.append(f"{field_name}:{ddl_type}")
        except UnsupportedTypeError as e:
            raise SchemaInferenceError(f"Cannot infer type for field {field_name}: {e}") from e

    return "struct<" + ",".join(fields) + ">"


def typed_dict_to_ddl_schema(typed_dict_type: Type) -> str:
    """Convert a TypedDict to a DDL schema string.

    Args:
        typed_dict_type: The TypedDict type to convert.

    Returns:
        A DDL schema string.
    """
    if not hasattr(typed_dict_type, "__annotations__"):
        raise ValueError(f"{typed_dict_type} does not have type annotations")

    fields = []

    for field_name, field_type in typed_dict_type.__annotations__.items():
        try:
            ddl_type = python_type_to_ddl_type(field_type)
            fields.append(f"{field_name}:{ddl_type}")
        except UnsupportedTypeError as e:
            raise SchemaInferenceError(f"Cannot infer type for field {field_name}: {e}") from e

    return "struct<" + ",".join(fields) + ">"


def infer_ddl_schema(model: Type) -> str:
    """Infer a DDL schema string from a model type.

    Args:
        model: The model type (dataclass, Pydantic, TypedDict).

    Returns:
        A DDL schema string.

    Raises:
        SchemaInferenceError: If schema cannot be inferred.
    """
    # Infer schema from model
    if is_dataclass(model):
        return dataclass_to_ddl_schema(model)
    elif hasattr(model, "model_fields"):
        return pydantic_to_ddl_schema(model)
    elif hasattr(model, "__annotations__"):
        try:
            return typed_dict_to_ddl_schema(model)
        except Exception as e:
            raise SchemaInferenceError(f"Cannot infer schema from {model}: {e}") from e
    else:
        raise SchemaInferenceError(f"Cannot infer schema from {model}")


def python_type_to_spark_type(python_type: Type, nullable: bool = True) -> Any:
    """Convert a Python type to a PySpark DataType.

    Args:
        python_type: The Python type to convert.
        nullable: Whether the field should be nullable.

    Returns:
        A PySpark DataType instance.

    Raises:
        UnsupportedTypeError: If the type cannot be converted.
        PySparkNotAvailableError: If PySpark is not installed.
    """
    if not is_pyspark_available():
        from polyspark.exceptions import PySparkNotAvailableError

        raise PySparkNotAvailableError()

    pyspark_types = get_pyspark_types()
    assert pyspark_types is not None  # Type guard for mypy

    # Handle Optional types
    if is_optional(python_type):
        python_type = unwrap_optional(python_type)

    origin = get_origin(python_type)
    args = get_args(python_type)

    # Handle basic types
    type_mapping = {
        str: pyspark_types.StringType(),
        int: pyspark_types.LongType(),
        float: pyspark_types.DoubleType(),
        bool: pyspark_types.BooleanType(),
        bytes: pyspark_types.BinaryType(),
        bytearray: pyspark_types.BinaryType(),
        date: pyspark_types.DateType(),
        datetime: pyspark_types.TimestampType(),
        Decimal: pyspark_types.DecimalType(),
    }

    if python_type in type_mapping:
        return type_mapping[python_type]

    # Handle List/list -> ArrayType
    if origin in (list, List):
        if not args:
            raise SchemaInferenceError(f"Cannot infer array element type from {python_type}")
        element_type = python_type_to_spark_type(args[0], nullable=True)
        return pyspark_types.ArrayType(element_type, containsNull=True)

    # Handle Dict/dict -> MapType
    if origin in (dict, Dict):
        if not args or len(args) < 2:
            raise SchemaInferenceError(f"Cannot infer map types from {python_type}")
        key_type = python_type_to_spark_type(args[0], nullable=False)
        value_type = python_type_to_spark_type(args[1], nullable=True)
        return pyspark_types.MapType(key_type, value_type, valueContainsNull=True)

    # Handle dataclasses and Pydantic models -> StructType
    if is_dataclass(python_type):
        return dataclass_to_struct_type(python_type)

    # Try Pydantic model
    if hasattr(python_type, "model_fields"):
        return pydantic_to_struct_type(python_type)

    # Try TypedDict (Python 3.8+)
    if hasattr(python_type, "__annotations__"):
        try:
            return typed_dict_to_struct_type(python_type)
        except Exception:
            pass

    raise UnsupportedTypeError(f"Cannot convert type {python_type} to PySpark type")


def dataclass_to_struct_type(dataclass_type: Type) -> Any:
    """Convert a dataclass to a PySpark StructType.

    Args:
        dataclass_type: The dataclass type to convert.

    Returns:
        A PySpark StructType instance.
    """
    if not is_pyspark_available():
        from polyspark.exceptions import PySparkNotAvailableError

        raise PySparkNotAvailableError()

    pyspark_types = get_pyspark_types()
    assert pyspark_types is not None  # Type guard for mypy

    if not is_dataclass(dataclass_type):
        raise ValueError(f"{dataclass_type} is not a dataclass")

    fields = []
    type_hints = get_type_hints(dataclass_type)

    for field in dataclass_fields(dataclass_type):
        field_type = type_hints.get(field.name, field.type)
        nullable = is_optional(field_type)

        try:
            spark_type = python_type_to_spark_type(field_type, nullable=nullable)
            struct_field = pyspark_types.StructField(field.name, spark_type, nullable=nullable)
            fields.append(struct_field)
        except UnsupportedTypeError as e:
            raise SchemaInferenceError(f"Cannot infer type for field {field.name}: {e}") from e

    return pyspark_types.StructType(fields)


def pydantic_to_struct_type(model_type: Type) -> Any:
    """Convert a Pydantic model to a PySpark StructType.

    Args:
        model_type: The Pydantic model type to convert.

    Returns:
        A PySpark StructType instance.
    """
    if not is_pyspark_available():
        from polyspark.exceptions import PySparkNotAvailableError

        raise PySparkNotAvailableError()

    pyspark_types = get_pyspark_types()
    assert pyspark_types is not None  # Type guard for mypy

    if not hasattr(model_type, "model_fields"):
        raise ValueError(f"{model_type} is not a Pydantic v2 model")

    fields = []

    for field_name, field_info in model_type.model_fields.items():
        field_type = field_info.annotation
        nullable = not field_info.is_required() or is_optional(field_type)

        try:
            spark_type = python_type_to_spark_type(field_type, nullable=nullable)
            struct_field = pyspark_types.StructField(field_name, spark_type, nullable=nullable)
            fields.append(struct_field)
        except UnsupportedTypeError as e:
            raise SchemaInferenceError(f"Cannot infer type for field {field_name}: {e}") from e

    return pyspark_types.StructType(fields)


def typed_dict_to_struct_type(typed_dict_type: Type) -> Any:
    """Convert a TypedDict to a PySpark StructType.

    Args:
        typed_dict_type: The TypedDict type to convert.

    Returns:
        A PySpark StructType instance.
    """
    if not is_pyspark_available():
        from polyspark.exceptions import PySparkNotAvailableError

        raise PySparkNotAvailableError()

    pyspark_types = get_pyspark_types()
    assert pyspark_types is not None  # Type guard for mypy

    if not hasattr(typed_dict_type, "__annotations__"):
        raise ValueError(f"{typed_dict_type} does not have type annotations")

    fields = []

    # Get required and optional keys for TypedDict
    required_keys: Any = getattr(typed_dict_type, "__required_keys__", set())

    for field_name, field_type in typed_dict_type.__annotations__.items():
        nullable = field_name not in required_keys or is_optional(field_type)

        try:
            spark_type = python_type_to_spark_type(field_type, nullable=nullable)
            struct_field = pyspark_types.StructField(field_name, spark_type, nullable=nullable)
            fields.append(struct_field)
        except UnsupportedTypeError as e:
            raise SchemaInferenceError(f"Cannot infer type for field {field_name}: {e}") from e

    return pyspark_types.StructType(fields)


def infer_schema(
    model: Type,
    schema: Optional[Union[StructTypeProtocol, List[str]]] = None,
) -> Any:
    """Infer or validate a PySpark schema from a model type.

    Args:
        model: The model type (dataclass, Pydantic, TypedDict).
        schema: Optional explicit schema to use. If provided as StructType, it's returned as-is.
                If provided as list of strings, column names are validated against model.

    Returns:
        A PySpark StructType instance or DDL schema string (if PySpark is unavailable).

    Raises:
        SchemaInferenceError: If schema cannot be inferred.
    """
    # If PySpark is not available, return DDL schema string
    if not is_pyspark_available():
        # If explicit schema provided as list of strings, validate column names
        if schema is not None and isinstance(schema, list):
            # Infer DDL schema to validate column names
            ddl_schema = infer_ddl_schema(model)
            # Extract field names from DDL schema (simple parsing)
            # DDL format: "struct<field1:type1,field2:type2>"
            schema_str = ddl_schema.replace("struct<", "").replace(">", "")
            field_names = {field.split(":")[0] for field in schema_str.split(",")}

            for col_name in schema:
                if col_name not in field_names:
                    raise SchemaInferenceError(f"Column '{col_name}' not found in model {model}")

        # Return DDL schema string when PySpark is unavailable
        return infer_ddl_schema(model)

    pyspark_types = get_pyspark_types()
    assert pyspark_types is not None  # Type guard for mypy

    # If explicit StructType provided, use it
    if schema is not None and isinstance(schema, pyspark_types.StructType):
        return schema

    # Infer schema from model
    if is_dataclass(model):
        inferred_schema = dataclass_to_struct_type(model)
    elif hasattr(model, "model_fields"):
        inferred_schema = pydantic_to_struct_type(model)
    elif hasattr(model, "__annotations__"):
        try:
            inferred_schema = typed_dict_to_struct_type(model)
        except Exception as e:
            raise SchemaInferenceError(f"Cannot infer schema from {model}: {e}") from e
    else:
        raise SchemaInferenceError(f"Cannot infer schema from {model}")

    # If column names provided, validate them
    if schema is not None and isinstance(schema, list):
        inferred_field_names = {f.name for f in inferred_schema.fields}
        for col_name in schema:
            if col_name not in inferred_field_names:
                raise SchemaInferenceError(f"Column '{col_name}' not found in model {model}")

    return inferred_schema


def export_ddl_schema(model: Type) -> str:
    """Export a model schema as a DDL string.

    This function works without PySpark installed and can be used to
    generate schema strings for sharing or storage.

    Args:
        model: The model type (dataclass, Pydantic, TypedDict).

    Returns:
        A DDL schema string.

    Raises:
        SchemaInferenceError: If schema cannot be inferred.

    Example:
        ```python
        from dataclasses import dataclass
        from polyspark.schema import export_ddl_schema

        @dataclass
        class User:
            id: int
            name: str
            email: Optional[str]

        schema = export_ddl_schema(User)
        print(schema)  # "struct<id:long,name:string,email:string>"
        ```
    """
    return infer_ddl_schema(model)


def save_schema_ddl(model: Type, filepath: str) -> None:
    """Save a model schema as a DDL string to a file.

    This function works without PySpark installed.

    Args:
        model: The model type (dataclass, Pydantic, TypedDict).
        filepath: Path to the file where the schema will be saved.

    Raises:
        SchemaInferenceError: If schema cannot be inferred.

    Example:
        ```python
        from dataclasses import dataclass
        from polyspark.schema import save_schema_ddl

        @dataclass
        class Product:
            id: int
            name: str
            price: float

        save_schema_ddl(Product, "product_schema.ddl")
        ```
    """
    ddl_schema = infer_ddl_schema(model)
    with open(filepath, "w") as f:
        f.write(ddl_schema)

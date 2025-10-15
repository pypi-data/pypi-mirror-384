"""Tests for schema inference logic."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional

import pytest

try:
    from pyspark.sql import types as T

    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False

from polyspark.exceptions import SchemaInferenceError, UnsupportedTypeError
from polyspark.schema import (
    dataclass_to_struct_type,
    infer_schema,
    is_optional,
    python_type_to_spark_type,
    unwrap_optional,
)

pytestmark = pytest.mark.skipif(not PYSPARK_AVAILABLE, reason="PySpark not installed")


class TestOptionalHelpers:
    """Test Optional type helpers."""

    def test_is_optional_with_optional_type(self):
        assert is_optional(Optional[str]) is True
        assert is_optional(Optional[int]) is True

    def test_is_optional_with_non_optional_type(self):
        assert is_optional(str) is False
        assert is_optional(int) is False
        assert is_optional(List[str]) is False

    def test_unwrap_optional(self):
        assert unwrap_optional(Optional[str]) is str
        assert unwrap_optional(Optional[int]) is int

    def test_unwrap_non_optional(self):
        assert unwrap_optional(str) is str
        assert unwrap_optional(int) is int


class TestPythonTypeToSparkType:
    """Test Python type to Spark type conversion."""

    def test_basic_types(self):
        assert isinstance(python_type_to_spark_type(str), T.StringType)
        assert isinstance(python_type_to_spark_type(int), T.LongType)
        assert isinstance(python_type_to_spark_type(float), T.DoubleType)
        assert isinstance(python_type_to_spark_type(bool), T.BooleanType)
        assert isinstance(python_type_to_spark_type(bytes), T.BinaryType)
        assert isinstance(python_type_to_spark_type(bytearray), T.BinaryType)

    def test_datetime_types(self):
        assert isinstance(python_type_to_spark_type(date), T.DateType)
        assert isinstance(python_type_to_spark_type(datetime), T.TimestampType)

    def test_decimal_type(self):
        assert isinstance(python_type_to_spark_type(Decimal), T.DecimalType)

    def test_list_type(self):
        array_type = python_type_to_spark_type(List[str])
        assert isinstance(array_type, T.ArrayType)
        assert isinstance(array_type.elementType, T.StringType)
        assert array_type.containsNull is True

    def test_nested_list_type(self):
        array_type = python_type_to_spark_type(List[List[int]])
        assert isinstance(array_type, T.ArrayType)
        assert isinstance(array_type.elementType, T.ArrayType)
        assert isinstance(array_type.elementType.elementType, T.LongType)

    def test_dict_type(self):
        map_type = python_type_to_spark_type(Dict[str, int])
        assert isinstance(map_type, T.MapType)
        assert isinstance(map_type.keyType, T.StringType)
        assert isinstance(map_type.valueType, T.LongType)
        assert map_type.valueContainsNull is True

    def test_optional_type(self):
        # Optional should be unwrapped and nullable set to True
        spark_type = python_type_to_spark_type(Optional[str])
        assert isinstance(spark_type, T.StringType)

    def test_unsupported_type(self):
        with pytest.raises(UnsupportedTypeError):
            python_type_to_spark_type(object)


class TestDataclassToStructType:
    """Test dataclass to StructType conversion."""

    def test_simple_dataclass(self):
        @dataclass
        class Person:
            name: str
            age: int

        struct_type = dataclass_to_struct_type(Person)
        assert isinstance(struct_type, T.StructType)
        assert len(struct_type.fields) == 2

        name_field = struct_type.fields[0]
        assert name_field.name == "name"
        assert isinstance(name_field.dataType, T.StringType)

        age_field = struct_type.fields[1]
        assert age_field.name == "age"
        assert isinstance(age_field.dataType, T.LongType)

    def test_dataclass_with_optional(self):
        @dataclass
        class User:
            id: int
            email: Optional[str]

        struct_type = dataclass_to_struct_type(User)
        assert len(struct_type.fields) == 2

        email_field = struct_type.fields[1]
        assert email_field.name == "email"
        assert email_field.nullable is True

    def test_nested_dataclass(self):
        @dataclass
        class Address:
            street: str
            city: str

        @dataclass
        class Person:
            name: str
            address: Address

        struct_type = dataclass_to_struct_type(Person)
        assert len(struct_type.fields) == 2

        address_field = struct_type.fields[1]
        assert address_field.name == "address"
        assert isinstance(address_field.dataType, T.StructType)
        assert len(address_field.dataType.fields) == 2

    def test_dataclass_with_list(self):
        @dataclass
        class Team:
            name: str
            members: List[str]

        struct_type = dataclass_to_struct_type(Team)
        members_field = struct_type.fields[1]
        assert isinstance(members_field.dataType, T.ArrayType)
        assert isinstance(members_field.dataType.elementType, T.StringType)


class TestInferSchema:
    """Test schema inference."""

    def test_infer_from_dataclass(self):
        @dataclass
        class Product:
            id: int
            name: str
            price: float

        schema = infer_schema(Product)
        assert isinstance(schema, T.StructType)
        assert len(schema.fields) == 3

    def test_infer_with_explicit_struct_type(self):
        @dataclass
        class Item:
            id: int
            name: str

        explicit_schema = T.StructType(
            [
                T.StructField("id", T.IntegerType(), False),
                T.StructField("name", T.StringType(), True),
            ]
        )

        schema = infer_schema(Item, schema=explicit_schema)
        assert schema is explicit_schema

    def test_infer_with_column_names(self):
        @dataclass
        class Record:
            id: int
            name: str
            email: str

        # Should infer full schema even with column names
        schema = infer_schema(Record, schema=["id", "name"])
        assert isinstance(schema, T.StructType)
        assert len(schema.fields) == 3

    def test_infer_invalid_column_name(self):
        @dataclass
        class Record:
            id: int
            name: str

        with pytest.raises(SchemaInferenceError):
            infer_schema(Record, schema=["id", "invalid_field"])

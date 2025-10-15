"""Tests for DDL schema inference functionality."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional, TypedDict

import pytest

from polyspark.schema import (
    dataclass_to_ddl_schema,
    export_ddl_schema,
    infer_ddl_schema,
    pydantic_to_ddl_schema,
    python_type_to_ddl_type,
    save_schema_ddl,
    typed_dict_to_ddl_schema,
)


class TestPythonTypeToDdlType:
    """Test basic type to DDL type conversion."""

    def test_basic_types(self):
        """Test basic Python types."""
        assert python_type_to_ddl_type(str) == "string"
        assert python_type_to_ddl_type(int) == "long"
        assert python_type_to_ddl_type(float) == "double"
        assert python_type_to_ddl_type(bool) == "boolean"
        assert python_type_to_ddl_type(bytes) == "binary"
        assert python_type_to_ddl_type(bytearray) == "binary"
        assert python_type_to_ddl_type(date) == "date"
        assert python_type_to_ddl_type(datetime) == "timestamp"
        assert python_type_to_ddl_type(Decimal) == "decimal(10,0)"

    def test_optional_types(self):
        """Test Optional types."""
        assert python_type_to_ddl_type(Optional[str]) == "string"
        assert python_type_to_ddl_type(Optional[int]) == "long"

    def test_list_types(self):
        """Test list/array types."""
        assert python_type_to_ddl_type(List[str]) == "array<string>"
        assert python_type_to_ddl_type(List[int]) == "array<long>"
        assert python_type_to_ddl_type(List[float]) == "array<double>"

    def test_dict_types(self):
        """Test dict/map types."""
        assert python_type_to_ddl_type(Dict[str, str]) == "map<string,string>"
        assert python_type_to_ddl_type(Dict[str, int]) == "map<string,long>"
        assert python_type_to_ddl_type(Dict[int, str]) == "map<long,string>"

    def test_nested_types(self):
        """Test nested complex types."""
        assert python_type_to_ddl_type(List[Dict[str, int]]) == "array<map<string,long>>"
        assert python_type_to_ddl_type(Dict[str, List[int]]) == "map<string,array<long>>"


class TestDataclassToDdlSchema:
    """Test dataclass to DDL schema conversion."""

    def test_simple_dataclass(self):
        """Test simple dataclass."""

        @dataclass
        class User:
            id: int
            name: str
            email: str

        schema = dataclass_to_ddl_schema(User)
        assert schema == "struct<id:long,name:string,email:string>"

    def test_dataclass_with_optional(self):
        """Test dataclass with optional fields."""

        @dataclass
        class User:
            id: int
            name: str
            email: Optional[str]

        schema = dataclass_to_ddl_schema(User)
        assert schema == "struct<id:long,name:string,email:string>"

    def test_dataclass_with_complex_types(self):
        """Test dataclass with complex types."""

        @dataclass
        class Product:
            id: int
            name: str
            tags: List[str]
            prices: Dict[str, float]

        schema = dataclass_to_ddl_schema(Product)
        assert schema == "struct<id:long,name:string,tags:array<string>,prices:map<string,double>>"

    def test_nested_dataclass(self):
        """Test nested dataclass."""

        @dataclass
        class Address:
            street: str
            city: str
            zipcode: str

        @dataclass
        class User:
            id: int
            name: str
            address: Address

        schema = dataclass_to_ddl_schema(User)
        expected = "struct<id:long,name:string,address:struct<street:string,city:string,zipcode:string>>"
        assert schema == expected


class TestPydanticToDdlSchema:
    """Test Pydantic model to DDL schema conversion."""

    def test_simple_pydantic_model(self):
        """Test simple Pydantic model."""
        try:
            from pydantic import BaseModel

            class User(BaseModel):
                id: int
                name: str
                email: str

            schema = pydantic_to_ddl_schema(User)
            assert schema == "struct<id:long,name:string,email:string>"
        except ImportError:
            pytest.skip("Pydantic not installed")

    def test_pydantic_with_optional(self):
        """Test Pydantic model with optional fields."""
        try:
            from pydantic import BaseModel

            class User(BaseModel):
                id: int
                name: str
                email: Optional[str] = None

            schema = pydantic_to_ddl_schema(User)
            assert schema == "struct<id:long,name:string,email:string>"
        except ImportError:
            pytest.skip("Pydantic not installed")


class TestTypedDictToDdlSchema:
    """Test TypedDict to DDL schema conversion."""

    def test_simple_typed_dict(self):
        """Test simple TypedDict."""

        class User(TypedDict):
            id: int
            name: str
            email: str

        schema = typed_dict_to_ddl_schema(User)
        assert schema == "struct<id:long,name:string,email:string>"

    def test_typed_dict_with_optional(self):
        """Test TypedDict with optional fields."""

        class User(TypedDict, total=False):
            id: int
            name: str
            email: Optional[str]

        schema = typed_dict_to_ddl_schema(User)
        assert schema == "struct<id:long,name:string,email:string>"


class TestInferDdlSchema:
    """Test main DDL schema inference function."""

    def test_infer_dataclass(self):
        """Test inferring schema from dataclass."""

        @dataclass
        class User:
            id: int
            name: str

        schema = infer_ddl_schema(User)
        assert schema == "struct<id:long,name:string>"

    def test_infer_pydantic(self):
        """Test inferring schema from Pydantic model."""
        try:
            from pydantic import BaseModel

            class User(BaseModel):
                id: int
                name: str

            schema = infer_ddl_schema(User)
            assert schema == "struct<id:long,name:string>"
        except ImportError:
            pytest.skip("Pydantic not installed")

    def test_infer_typed_dict(self):
        """Test inferring schema from TypedDict."""

        class User(TypedDict):
            id: int
            name: str

        schema = infer_ddl_schema(User)
        assert schema == "struct<id:long,name:string>"


class TestExportDdlSchema:
    """Test DDL schema export utilities."""

    def test_export_ddl_schema(self):
        """Test export_ddl_schema function."""

        @dataclass
        class User:
            id: int
            name: str

        schema = export_ddl_schema(User)
        assert schema == "struct<id:long,name:string>"

    def test_save_schema_ddl(self, tmp_path):
        """Test save_schema_ddl function."""

        @dataclass
        class User:
            id: int
            name: str

        filepath = tmp_path / "user_schema.ddl"
        save_schema_ddl(User, str(filepath))

        assert filepath.exists()
        content = filepath.read_text()
        assert content == "struct<id:long,name:string>"


class TestDdlSchemaWithoutPyspark:
    """Test DDL schema functions work without PySpark."""

    def test_ddl_schema_works_without_pyspark(self):
        """Test that DDL schema inference works without PySpark installed."""

        @dataclass
        class User:
            id: int
            name: str
            email: Optional[str]

        # This should work even if PySpark is not installed
        schema = export_ddl_schema(User)
        assert schema == "struct<id:long,name:string,email:string>"

    def test_complex_types_without_pyspark(self):
        """Test complex types work without PySpark."""

        @dataclass
        class Product:
            id: int
            name: str
            tags: List[str]
            prices: Dict[str, float]
            metadata: Dict[str, List[str]]

        schema = export_ddl_schema(Product)
        expected = "struct<id:long,name:string,tags:array<string>,prices:map<string,double>,metadata:map<string,array<string>>>"
        assert schema == expected


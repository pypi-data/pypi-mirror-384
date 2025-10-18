"""Tests for @spark_factory decorator."""

from dataclasses import dataclass
from typing import List, Optional

import pytest

try:
    from pyspark.sql import types as T

    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False

from polyspark import spark_factory

pytestmark = pytest.mark.skipif(not PYSPARK_AVAILABLE, reason="PySpark not installed")


@spark_factory
@dataclass
class DecoratedUser:
    id: int
    username: str
    email: str


@spark_factory
@dataclass
class DecoratedUserWithOptional:
    id: int
    username: str
    nickname: Optional[str]


@spark_factory
@dataclass
class DecoratedAddress:
    street: str
    city: str


@spark_factory
@dataclass
class DecoratedPerson:
    id: int
    name: str
    address: DecoratedAddress
    tags: List[str]


class TestDecoratorBasic:
    """Test basic decorator functionality."""

    def test_decorator_preserves_class(self):
        """Test that decorator preserves the original class."""
        from dataclasses import fields

        assert DecoratedUser.__name__ == "DecoratedUser"
        # Check dataclass fields
        field_names = {f.name for f in fields(DecoratedUser)}
        assert field_names == {"id", "username", "email"}

    def test_decorator_adds_build_dataframe(self):
        """Test that decorator adds build_dataframe method."""
        assert hasattr(DecoratedUser, "build_dataframe")
        assert callable(DecoratedUser.build_dataframe)

    def test_decorator_adds_build_dicts(self):
        """Test that decorator adds build_dicts method."""
        assert hasattr(DecoratedUser, "build_dicts")
        assert callable(DecoratedUser.build_dicts)

    def test_decorator_adds_create_dataframe_from_dicts(self):
        """Test that decorator adds create_dataframe_from_dicts method."""
        assert hasattr(DecoratedUser, "create_dataframe_from_dicts")
        assert callable(DecoratedUser.create_dataframe_from_dicts)

    def test_decorator_stores_factory_reference(self):
        """Test that decorator stores reference to internal factory."""
        assert hasattr(DecoratedUser, "_polyspark_factory")
        assert DecoratedUser._polyspark_factory.__model__ == DecoratedUser

    def test_can_still_instantiate_class(self):
        """Test that decorated class can still be instantiated normally."""
        user = DecoratedUser(id=1, username="test", email="test@example.com")
        assert user.id == 1
        assert user.username == "test"
        assert user.email == "test@example.com"


class TestDecoratorDataGeneration:
    """Test data generation with decorator."""

    def test_build_dicts_works(self):
        """Test build_dicts generates correct data."""
        dicts = DecoratedUser.build_dicts(size=5)

        assert len(dicts) == 5
        assert all(isinstance(d, dict) for d in dicts)
        assert all(set(d.keys()) == {"id", "username", "email"} for d in dicts)

    def test_build_dicts_custom_size(self):
        """Test build_dicts with custom size."""
        dicts = DecoratedUser.build_dicts(size=20)
        assert len(dicts) == 20

    def test_build_dataframe_works(self, spark):
        """Test build_dataframe generates DataFrame."""
        df = DecoratedUser.build_dataframe(spark, size=10)

        assert df.count() == 10
        assert set(df.columns) == {"id", "username", "email"}

    def test_build_dataframe_custom_size(self, spark):
        """Test build_dataframe with custom size."""
        df = DecoratedUser.build_dataframe(spark, size=50)
        assert df.count() == 50

    def test_build_dataframe_schema(self, spark):
        """Test build_dataframe infers correct schema."""
        df = DecoratedUser.build_dataframe(spark, size=5)

        schema = df.schema
        assert isinstance(schema["id"].dataType, T.LongType)
        assert isinstance(schema["username"].dataType, T.StringType)
        assert isinstance(schema["email"].dataType, T.StringType)

    def test_create_dataframe_from_dicts_works(self, spark):
        """Test create_dataframe_from_dicts."""
        dicts = DecoratedUser.build_dicts(size=10)
        df = DecoratedUser.create_dataframe_from_dicts(spark, dicts)

        assert df.count() == 10
        assert set(df.columns) == {"id", "username", "email"}


class TestDecoratorWithOptional:
    """Test decorator with optional fields."""

    def test_optional_field_in_schema(self, spark):
        """Test that optional fields are nullable in schema."""
        df = DecoratedUserWithOptional.build_dataframe(spark, size=5)

        nickname_field = df.schema["nickname"]
        assert nickname_field.nullable is True

    def test_required_field_schema(self, spark):
        """Test that required fields work correctly."""
        df = DecoratedUserWithOptional.build_dataframe(spark, size=5)

        assert "id" in df.columns
        assert "username" in df.columns
        assert "nickname" in df.columns


class TestDecoratorWithComplexTypes:
    """Test decorator with complex types."""

    def test_nested_struct(self, spark):
        """Test decorator with nested dataclass."""
        df = DecoratedPerson.build_dataframe(spark, size=5)

        assert df.count() == 5
        assert "address" in df.columns

        # Check nested struct
        address_field = df.schema["address"]
        assert isinstance(address_field.dataType, T.StructType)

        # Check nested fields
        nested_fields = {f.name for f in address_field.dataType.fields}
        assert nested_fields == {"street", "city"}

    def test_array_type(self, spark):
        """Test decorator with array field."""
        df = DecoratedPerson.build_dataframe(spark, size=5)

        tags_field = df.schema["tags"]
        assert isinstance(tags_field.dataType, T.ArrayType)
        assert isinstance(tags_field.dataType.elementType, T.StringType)

    def test_nested_struct_in_dicts(self):
        """Test that nested structs work in build_dicts."""
        dicts = DecoratedPerson.build_dicts(size=3)

        assert len(dicts) == 3
        for person in dicts:
            assert "address" in person
            assert isinstance(person["address"], dict)
            assert "street" in person["address"]
            assert "city" in person["address"]
            assert isinstance(person["tags"], list)


class TestDecoratorMultipleClasses:
    """Test that multiple decorated classes don't interfere."""

    def test_multiple_classes_independent(self):
        """Test that decorating multiple classes works independently."""
        user_dicts = DecoratedUser.build_dicts(size=3)
        address_dicts = DecoratedAddress.build_dicts(size=3)

        # Check User dicts
        assert all(set(d.keys()) == {"id", "username", "email"} for d in user_dicts)

        # Check Address dicts
        assert all(set(d.keys()) == {"street", "city"} for d in address_dicts)

    def test_multiple_classes_different_factories(self):
        """Test that each class has its own factory."""
        assert DecoratedUser._polyspark_factory is not DecoratedAddress._polyspark_factory
        assert DecoratedUser._polyspark_factory.__model__ == DecoratedUser
        assert DecoratedAddress._polyspark_factory.__model__ == DecoratedAddress


class TestDecoratorWithPydantic:
    """Test decorator with Pydantic models."""

    def test_pydantic_model(self):
        """Test decorator with Pydantic model."""
        try:
            from pydantic import BaseModel

            @spark_factory
            class PydanticUser(BaseModel):
                id: int
                name: str
                active: bool

            dicts = PydanticUser.build_dicts(size=5)

            assert len(dicts) == 5
            assert all(set(d.keys()) == {"id", "name", "active"} for d in dicts)

        except ImportError:
            pytest.skip("Pydantic not installed")

    def test_pydantic_with_dataframe(self, spark):
        """Test Pydantic model with DataFrame generation."""
        try:
            from pydantic import BaseModel

            @spark_factory
            class PydanticProduct(BaseModel):
                product_id: int
                name: str
                price: float

            df = PydanticProduct.build_dataframe(spark, size=10)

            assert df.count() == 10
            assert set(df.columns) == {"product_id", "name", "price"}

        except ImportError:
            pytest.skip("Pydantic not installed")


class TestDecoratorWithoutPyspark:
    """Test decorator behavior when PySpark is not available."""

    def test_build_dicts_works_without_pyspark(self):
        """Test that build_dicts works without PySpark."""
        # This should work regardless of PySpark availability
        dicts = DecoratedUser.build_dicts(size=5)

        assert len(dicts) == 5
        assert all(isinstance(d, dict) for d in dicts)


class TestDecoratorExplicitSchema:
    """Test decorator with explicit schemas."""

    def test_explicit_struct_type(self, spark):
        """Test with explicit PySpark schema."""
        explicit_schema = T.StructType(
            [
                T.StructField("id", T.IntegerType(), False),
                T.StructField("username", T.StringType(), True),
                T.StructField("email", T.StringType(), True),
            ]
        )

        df = DecoratedUser.build_dataframe(spark, size=5, schema=explicit_schema)

        assert df.count() == 5
        assert isinstance(df.schema["id"].dataType, T.IntegerType)

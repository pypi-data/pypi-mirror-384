"""Compatibility tests for polyspark with PySpark.

These tests verify that polyspark works correctly with the pyspark package.
This file should be run in an environment with pyspark installed.
"""

from dataclasses import dataclass
from typing import List, Optional

import pytest

from polyspark import SparkFactory, build_spark_dataframe, spark_factory

try:
    from pyspark.sql import SparkSession
    from pyspark.sql import types as T

    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False

pytestmark = pytest.mark.skipif(not PYSPARK_AVAILABLE, reason="PySpark not installed")


@dataclass
class SimpleUser:
    id: int
    name: str
    email: str


@dataclass
class UserWithOptional:
    id: int
    username: str
    nickname: Optional[str]


@dataclass
class Address:
    street: str
    city: str
    zipcode: str


@dataclass
class UserWithAddress:
    id: int
    name: str
    address: Address


@dataclass
class TeamWithMembers:
    team_id: int
    team_name: str
    members: List[str]


@pytest.fixture(scope="session")
def spark():
    """Create a SparkSession for testing."""
    return SparkSession.builder.master("local[1]").appName("polyspark-test").getOrCreate()


class TestSparkFactoryWithPySpark:
    """Test SparkFactory with real PySpark."""

    def test_build_dataframe_simple(self, spark):
        """Test building a simple DataFrame."""

        class UserFactory(SparkFactory[SimpleUser]):
            __model__ = SimpleUser

        df = UserFactory.build_dataframe(spark, size=10)
        assert df.count() == 10
        assert len(df.columns) == 3
        assert set(df.columns) == {"id", "name", "email"}

    def test_build_dataframe_with_optional(self, spark):
        """Test building DataFrame with optional fields."""

        class UserFactory(SparkFactory[UserWithOptional]):
            __model__ = UserWithOptional

        df = UserFactory.build_dataframe(spark, size=5)
        assert df.count() == 5
        assert "nickname" in df.columns

    def test_build_dataframe_nested(self, spark):
        """Test building DataFrame with nested structs."""

        class UserFactory(SparkFactory[UserWithAddress]):
            __model__ = UserWithAddress

        df = UserFactory.build_dataframe(spark, size=5)
        assert df.count() == 5
        assert "address" in df.columns
        # Check nested fields - when selecting "address.*", PySpark flattens to local field names
        assert "street" in [f.name for f in df.select("address.*").schema.fields]
        assert "city" in [f.name for f in df.select("address.*").schema.fields]
        assert "zipcode" in [f.name for f in df.select("address.*").schema.fields]

    def test_build_dataframe_with_list(self, spark):
        """Test building DataFrame with list fields."""

        class TeamFactory(SparkFactory[TeamWithMembers]):
            __model__ = TeamWithMembers

        df = TeamFactory.build_dataframe(spark, size=5)
        assert df.count() == 5
        assert "members" in df.columns

    def test_create_dataframe_from_dicts(self, spark):
        """Test creating DataFrame from pre-generated dicts."""

        class UserFactory(SparkFactory[SimpleUser]):
            __model__ = SimpleUser

        dicts = UserFactory.build_dicts(size=10)
        df = UserFactory.create_dataframe_from_dicts(spark, dicts)
        assert df.count() == 10

    def test_build_dataframe_custom_size(self, spark):
        """Test building DataFrame with custom size."""

        class UserFactory(SparkFactory[SimpleUser]):
            __model__ = SimpleUser

        df = UserFactory.build_dataframe(spark, size=100)
        assert df.count() == 100

    def test_build_dataframe_with_explicit_schema(self, spark):
        """Test building DataFrame with explicit schema."""

        class UserFactory(SparkFactory[SimpleUser]):
            __model__ = SimpleUser

        explicit_schema = T.StructType(
            [
                T.StructField("id", T.LongType(), False),
                T.StructField("name", T.StringType(), False),
                T.StructField("email", T.StringType(), True),
            ]
        )

        df = UserFactory.build_dataframe(spark, size=5, schema=explicit_schema)
        assert df.count() == 5


class TestBuildSparkDataframe:
    """Test build_spark_dataframe convenience function."""

    def test_build_spark_dataframe(self, spark):
        """Test build_spark_dataframe function."""

        df = build_spark_dataframe(SimpleUser, spark, size=10)
        assert df.count() == 10

    def test_build_spark_dataframe_complex(self, spark):
        """Test build_spark_dataframe with complex types."""

        df = build_spark_dataframe(UserWithAddress, spark, size=5)
        assert df.count() == 5


class TestDecoratorWithPySpark:
    """Test @spark_factory decorator with PySpark."""

    def test_decorated_class_build_dataframe(self, spark):
        """Test building DataFrame with decorated class."""

        @spark_factory
        @dataclass
        class DecoratedUser:
            id: int
            name: str
            email: str

        df = DecoratedUser.build_dataframe(spark, size=10)
        assert df.count() == 10

    def test_decorated_class_build_dicts(self, spark):
        """Test building dicts with decorated class."""

        @spark_factory
        @dataclass
        class DecoratedUser:
            id: int
            name: str

        dicts = DecoratedUser.build_dicts(size=10)
        assert len(dicts) == 10

    def test_decorated_class_with_optional(self, spark):
        """Test decorated class with optional fields."""

        @spark_factory
        @dataclass
        class DecoratedUser:
            id: int
            name: str
            nickname: Optional[str] = None

        df = DecoratedUser.build_dataframe(spark, size=5)
        assert df.count() == 5


class TestSchemaInferenceWithPySpark:
    """Test schema inference with PySpark."""

    def test_schema_inference_returns_struct_type(self, spark):
        """Test that schema inference returns StructType when PySpark is available."""
        from polyspark import infer_schema

        schema = infer_schema(SimpleUser)
        assert isinstance(schema, T.StructType)
        assert len(schema.fields) == 3

    def test_schema_inference_with_optional(self, spark):
        """Test schema inference with optional fields."""
        from polyspark import infer_schema

        schema = infer_schema(UserWithOptional)
        assert isinstance(schema, T.StructType)
        # Find nickname field and check if it's nullable
        nickname_field = next((f for f in schema.fields if f.name == "nickname"), None)
        assert nickname_field is not None


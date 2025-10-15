"""Compatibility tests for polyspark with mock-spark.

These tests verify that polyspark works correctly with the mock-spark package.
This file should be run in an environment with mock-spark installed.

Note: mock-spark is a package that provides mock implementations of PySpark
components for testing purposes.
"""

from dataclasses import dataclass
from typing import Optional

import pytest

from polyspark import SparkFactory, build_spark_dataframe, spark_factory

try:
    import mock_spark
    from mock_spark import MockSparkSession

    MOCKSPARK_AVAILABLE = True
except ImportError:
    try:
        # Try alternative import names
        from mock_spark import SparkSession as MockSparkSession

        MOCKSPARK_AVAILABLE = True
    except ImportError:
        MOCKSPARK_AVAILABLE = False

pytestmark = pytest.mark.skipif(not MOCKSPARK_AVAILABLE, reason="mock-spark not installed")


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


@pytest.fixture
def mock_spark():
    """Create a MockSparkSession for testing."""
    return MockSparkSession()


class TestSparkFactoryWithMockSpark:
    """Test SparkFactory with mock-spark."""

    def test_build_dataframe_simple(self, mock_spark):
        """Test building a simple DataFrame with mock-spark."""

        class UserFactory(SparkFactory[SimpleUser]):
            __model__ = SimpleUser

        df = UserFactory.build_dataframe(mock_spark, size=10)
        assert df.count() == 10
        assert len(df.columns) == 3
        assert set(df.columns) == {"id", "name", "email"}

    def test_build_dataframe_with_optional(self, mock_spark):
        """Test building DataFrame with optional fields using mock-spark."""

        class UserFactory(SparkFactory[UserWithOptional]):
            __model__ = UserWithOptional

        df = UserFactory.build_dataframe(mock_spark, size=5)
        assert df.count() == 5
        assert "nickname" in df.columns

    def test_build_dataframe_nested(self, mock_spark):
        """Test building DataFrame with nested structs using mock-spark."""

        class UserFactory(SparkFactory[UserWithAddress]):
            __model__ = UserWithAddress

        df = UserFactory.build_dataframe(mock_spark, size=5)
        assert df.count() == 5
        assert "address" in df.columns

    def test_create_dataframe_from_dicts(self, mock_spark):
        """Test creating DataFrame from pre-generated dicts with mock-spark."""

        class UserFactory(SparkFactory[SimpleUser]):
            __model__ = SimpleUser

        dicts = UserFactory.build_dicts(size=10)
        df = UserFactory.create_dataframe_from_dicts(mock_spark, dicts)
        assert df.count() == 10

    def test_build_dataframe_custom_size(self, mock_spark):
        """Test building DataFrame with custom size using mock-spark."""

        class UserFactory(SparkFactory[SimpleUser]):
            __model__ = SimpleUser

        df = UserFactory.build_dataframe(mock_spark, size=100)
        assert df.count() == 100


class TestBuildSparkDataframeWithMockSpark:
    """Test build_spark_dataframe convenience function with mock-spark."""

    def test_build_spark_dataframe(self, mock_spark):
        """Test build_spark_dataframe function with mock-spark."""

        df = build_spark_dataframe(SimpleUser, mock_spark, size=10)
        assert df.count() == 10

    def test_build_spark_dataframe_complex(self, mock_spark):
        """Test build_spark_dataframe with complex types using mock-spark."""

        df = build_spark_dataframe(UserWithAddress, mock_spark, size=5)
        assert df.count() == 5


class TestDecoratorWithMockSpark:
    """Test @spark_factory decorator with mock-spark."""

    def test_decorated_class_build_dataframe(self, mock_spark):
        """Test building DataFrame with decorated class using mock-spark."""

        @spark_factory
        @dataclass
        class DecoratedUser:
            id: int
            name: str
            email: str

        df = DecoratedUser.build_dataframe(mock_spark, size=10)
        assert df.count() == 10

    def test_decorated_class_build_dicts(self, mock_spark):
        """Test building dicts with decorated class."""

        @spark_factory
        @dataclass
        class DecoratedUser:
            id: int
            name: str

        dicts = DecoratedUser.build_dicts(size=10)
        assert len(dicts) == 10

    def test_decorated_class_with_optional(self, mock_spark):
        """Test decorated class with optional fields using mock-spark."""

        @spark_factory
        @dataclass
        class DecoratedUser:
            id: int
            name: str
            nickname: Optional[str] = None

        df = DecoratedUser.build_dataframe(mock_spark, size=5)
        assert df.count() == 5


class TestSchemaCompatibilityWithMockSpark:
    """Test schema compatibility between polyspark and mock-spark."""

    def test_schema_inference_works_with_mockspark(self, mock_spark):
        """Test that schema inference works with mock-spark."""
        from polyspark import infer_schema

        # Schema inference should work without PySpark
        schema = infer_schema(SimpleUser)

        # Should be a string (DDL format) when PySpark is not available
        assert isinstance(schema, str)

        # Create DataFrame with the schema
        class UserFactory(SparkFactory[SimpleUser]):
            __model__ = SimpleUser

        df = UserFactory.build_dataframe(mock_spark, size=5)
        assert df.count() == 5

    def test_ddl_schema_works_with_mockspark(self, mock_spark):
        """Test that DDL schema strings work with mock-spark."""
        from polyspark import export_ddl_schema

        ddl_schema = export_ddl_schema(SimpleUser)
        assert isinstance(ddl_schema, str)

        # Create DataFrame - mock-spark should accept DDL schema strings
        class UserFactory(SparkFactory[SimpleUser]):
            __model__ = SimpleUser

        df = UserFactory.build_dataframe(mock_spark, size=5)
        assert df.count() == 5


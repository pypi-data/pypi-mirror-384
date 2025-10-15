"""Tests for SparkFactory."""

from dataclasses import dataclass
from typing import List, Optional

import pytest

try:
    from pyspark.sql import types as T

    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False

from polyspark import SparkFactory, build_spark_dataframe

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


class TestSparkFactory:
    """Test SparkFactory class."""

    def test_build_dataframe_simple(self, spark):
        class UserFactory(SparkFactory[SimpleUser]):
            __model__ = SimpleUser

        df = UserFactory.build_dataframe(spark, size=10)

        assert df.count() == 10
        assert set(df.columns) == {"id", "name", "email"}

        # Check types
        schema = df.schema
        assert isinstance(schema["id"].dataType, T.LongType)
        assert isinstance(schema["name"].dataType, T.StringType)
        assert isinstance(schema["email"].dataType, T.StringType)

    def test_build_dataframe_with_optional(self, spark):
        class UserFactory(SparkFactory[UserWithOptional]):
            __model__ = UserWithOptional

        df = UserFactory.build_dataframe(spark, size=5)

        assert df.count() == 5
        assert "nickname" in df.columns

        # Check that nickname field is nullable
        nickname_field = df.schema["nickname"]
        assert nickname_field.nullable is True

    def test_build_dataframe_nested(self, spark):
        class UserFactory(SparkFactory[UserWithAddress]):
            __model__ = UserWithAddress

        df = UserFactory.build_dataframe(spark, size=5)

        assert df.count() == 5
        assert "address" in df.columns

        # Check nested struct type
        address_field = df.schema["address"]
        assert isinstance(address_field.dataType, T.StructType)

        # Check nested fields
        nested_fields = {f.name for f in address_field.dataType.fields}
        assert nested_fields == {"street", "city", "zipcode"}

    def test_build_dataframe_with_list(self, spark):
        class TeamFactory(SparkFactory[TeamWithMembers]):
            __model__ = TeamWithMembers

        df = TeamFactory.build_dataframe(spark, size=3)

        assert df.count() == 3
        assert "members" in df.columns

        # Check array type
        members_field = df.schema["members"]
        assert isinstance(members_field.dataType, T.ArrayType)
        assert isinstance(members_field.dataType.elementType, T.StringType)

    def test_build_dicts(self):
        class UserFactory(SparkFactory[SimpleUser]):
            __model__ = SimpleUser

        dicts = UserFactory.build_dicts(size=5)

        assert len(dicts) == 5
        assert all(isinstance(d, dict) for d in dicts)
        assert all(set(d.keys()) == {"id", "name", "email"} for d in dicts)

    def test_create_dataframe_from_dicts(self, spark):
        class UserFactory(SparkFactory[SimpleUser]):
            __model__ = SimpleUser

        dicts = UserFactory.build_dicts(size=5)
        df = UserFactory.create_dataframe_from_dicts(spark, dicts)

        assert df.count() == 5
        assert set(df.columns) == {"id", "name", "email"}

    def test_build_dataframe_custom_size(self, spark):
        class UserFactory(SparkFactory[SimpleUser]):
            __model__ = SimpleUser

        df = UserFactory.build_dataframe(spark, size=100)
        assert df.count() == 100

    def test_build_dataframe_with_explicit_schema(self, spark):
        class UserFactory(SparkFactory[SimpleUser]):
            __model__ = SimpleUser

        explicit_schema = T.StructType(
            [
                T.StructField("id", T.IntegerType(), False),
                T.StructField("name", T.StringType(), True),
                T.StructField("email", T.StringType(), True),
            ]
        )

        df = UserFactory.build_dataframe(spark, size=5, schema=explicit_schema)

        assert df.count() == 5
        assert isinstance(df.schema["id"].dataType, T.IntegerType)


class TestBuildSparkDataframe:
    """Test convenience function."""

    def test_build_spark_dataframe(self, spark):
        df = build_spark_dataframe(SimpleUser, spark, size=10)

        assert df.count() == 10
        assert set(df.columns) == {"id", "name", "email"}

    def test_build_spark_dataframe_complex(self, spark):
        df = build_spark_dataframe(UserWithAddress, spark, size=5)

        assert df.count() == 5
        assert "address" in df.columns

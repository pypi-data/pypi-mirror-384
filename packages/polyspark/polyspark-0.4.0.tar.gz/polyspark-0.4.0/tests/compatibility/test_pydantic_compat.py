"""Compatibility tests for polyspark with Pydantic.

These tests verify that polyspark works correctly with Pydantic models.
This file should be run in an environment with pydantic installed.
"""

from typing import List, Optional

import pytest
from polyfactory.exceptions import ConfigurationException

from polyspark import SparkFactory, spark_factory

try:
    from pydantic import BaseModel, Field

    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = None  # type: ignore[assignment, misc]
    Field = None  # type: ignore[assignment, misc]

pytestmark = pytest.mark.skipif(not PYDANTIC_AVAILABLE, reason="Pydantic not installed")

if PYDANTIC_AVAILABLE:

    class PydanticUser(BaseModel):
        """Test Pydantic model."""

        id: int
        name: str
        email: str

    class PydanticUserWithOptional(BaseModel):
        """Test Pydantic model with optional fields."""

        id: int
        username: str
        nickname: Optional[str] = None
        age: Optional[int] = None

    class PydanticProduct(BaseModel):
        """Test Pydantic model with validation."""

        product_id: int = Field(gt=0)
        name: str = Field(min_length=1, max_length=100)
        price: float = Field(gt=0)
        tags: List[str] = Field(default_factory=list)

    class PydanticAddress(BaseModel):
        """Test Pydantic model for nested structure."""

        street: str
        city: str
        zipcode: str
        country: str = "USA"

    class PydanticUserWithAddress(BaseModel):
        """Test Pydantic model with nested Pydantic model."""

        id: int
        name: str
        address: PydanticAddress

    @spark_factory
    class DecoratedPydanticUser(BaseModel):
        id: int
        name: str
        email: str


class TestPydanticWithSchemaInference:
    """Test Pydantic model schema inference."""

    def test_pydantic_schema_inference(self):
        """Test inferring schema from Pydantic model."""
        from polyspark import infer_schema, is_pyspark_available

        if is_pyspark_available():
            from pyspark.sql import types as T

            schema = infer_schema(PydanticUser)
            assert isinstance(schema, T.StructType)
            assert len(schema.fields) == 3
        else:
            # Without PySpark, should return DDL string
            schema = infer_schema(PydanticUser)
            assert isinstance(schema, str)
            assert "id:long" in schema
            assert "name:string" in schema
            assert "email:string" in schema

    def test_pydantic_with_optional_schema_inference(self):
        """Test schema inference with Pydantic optional fields."""
        from polyspark import infer_schema, is_pyspark_available

        if is_pyspark_available():
            from pyspark.sql import types as T

            schema = infer_schema(PydanticUserWithOptional)
            assert isinstance(schema, T.StructType)
            assert len(schema.fields) == 4
        else:
            schema = infer_schema(PydanticUserWithOptional)
            assert isinstance(schema, str)
            assert "nickname:string" in schema

    def test_pydantic_ddl_schema(self):
        """Test DDL schema generation for Pydantic models."""
        from polyspark import export_ddl_schema

        schema = export_ddl_schema(PydanticUser)
        assert isinstance(schema, str)
        assert "struct<" in schema
        assert "id:long" in schema
        assert "name:string" in schema
        assert "email:string" in schema

    def test_pydantic_nested_ddl_schema(self):
        """Test DDL schema generation for nested Pydantic models."""
        from polyspark import export_ddl_schema

        schema = export_ddl_schema(PydanticUserWithAddress)
        assert isinstance(schema, str)
        assert "struct<" in schema
        assert "address:struct<" in schema


class TestPydanticWithFactory:
    """Test Pydantic models with SparkFactory."""

    def test_pydantic_factory_raises_configuration_exception(self):
        """Test that SparkFactory raises ConfigurationException for Pydantic models."""

        # SparkFactory doesn't support Pydantic models directly
        # Exception is raised during class definition
        with pytest.raises(ConfigurationException) as exc_info:

            class UserFactory(SparkFactory[PydanticUser]):
                __model__ = PydanticUser

        assert "PydanticUser" in str(exc_info.value)
        assert "not supported" in str(exc_info.value)

    def test_pydantic_factory_with_validation_raises_exception(self):
        """Test that SparkFactory raises exception for Pydantic models with validation."""

        # SparkFactory doesn't support Pydantic models directly
        # Exception is raised during class definition
        with pytest.raises(ConfigurationException) as exc_info:

            class ProductFactory(SparkFactory[PydanticProduct]):
                __model__ = PydanticProduct

        assert "PydanticProduct" in str(exc_info.value)
        assert "not supported" in str(exc_info.value)

    def test_pydantic_with_dataframe_raises_exception(self):
        """Test that building DataFrame from Pydantic model raises exception."""
        from polyspark import is_pyspark_available

        if not is_pyspark_available():
            pytest.skip("PySpark not available")

        from pyspark.sql import SparkSession

        spark = SparkSession.builder.master("local[1]").appName("test").getOrCreate()

        # SparkFactory doesn't support Pydantic models directly
        # Exception is raised during class definition
        with pytest.raises(ConfigurationException) as exc_info:

            class ProductFactory(SparkFactory[PydanticProduct]):
                __model__ = PydanticProduct

        assert "PydanticProduct" in str(exc_info.value)
        assert "not supported" in str(exc_info.value)

        spark.stop()


class TestPydanticWithDecorator:
    """Test Pydantic models with @spark_factory decorator."""

    def test_decorated_pydantic_build_dicts(self):
        """Test that decorated Pydantic model can build dicts."""

        # The @spark_factory decorator creates a SparkFactory subclass
        # that works with Pydantic models
        dicts = DecoratedPydanticUser.build_dicts(size=10)
        assert len(dicts) == 10
        assert all("id" in d and "name" in d and "email" in d for d in dicts)

    def test_decorated_pydantic_with_dataframe(self):
        """Test that decorated Pydantic model works with DataFrame."""
        from polyspark import is_pyspark_available

        if not is_pyspark_available():
            pytest.skip("PySpark not available")

        from pyspark.sql import SparkSession

        spark = SparkSession.builder.master("local[1]").appName("test").getOrCreate()

        # The @spark_factory decorator creates a SparkFactory subclass
        # that works with Pydantic models
        df = DecoratedPydanticUser.build_dataframe(spark, size=10)
        assert df.count() == 10
        assert set(df.columns) == {"id", "name", "email"}

        spark.stop()

"""Tests for graceful degradation when PySpark is not available."""

from dataclasses import dataclass
from unittest.mock import patch

import pytest

from polyspark import SparkFactory, export_ddl_schema, infer_schema, is_pyspark_available
from polyspark.exceptions import PySparkNotAvailableError


@dataclass
class SimpleModel:
    id: int
    name: str


class TestWithoutPyspark:
    """Test behavior when PySpark is not installed."""

    def test_is_pyspark_available(self):
        # This test will vary based on whether pyspark is actually installed
        result = is_pyspark_available()
        assert isinstance(result, bool)

    def test_build_dicts_without_pyspark(self):
        """build_dicts should work without PySpark."""

        class ModelFactory(SparkFactory[SimpleModel]):
            __model__ = SimpleModel

        # This should work regardless of PySpark availability
        dicts = ModelFactory.build_dicts(size=5)

        assert len(dicts) == 5
        assert all(isinstance(d, dict) for d in dicts)
        assert all(set(d.keys()) == {"id", "name"} for d in dicts)

    @patch("polyspark.factory.is_pyspark_available", return_value=False)
    def test_build_dataframe_raises_without_pyspark(self, mock_check):
        """build_dataframe should raise clear error without PySpark."""

        class ModelFactory(SparkFactory[SimpleModel]):
            __model__ = SimpleModel

        # Without PySpark, it should raise PySparkNotAvailableError
        with pytest.raises(PySparkNotAvailableError):
            ModelFactory.build_dataframe(None, size=10)

    @patch("polyspark.factory.is_pyspark_available", return_value=False)
    def test_create_dataframe_from_dicts_raises_without_pyspark(self, mock_check):
        """create_dataframe_from_dicts should raise clear error without PySpark."""

        class ModelFactory(SparkFactory[SimpleModel]):
            __model__ = SimpleModel

        dicts = ModelFactory.build_dicts(size=5)

        # Without PySpark, it should raise PySparkNotAvailableError
        with pytest.raises(PySparkNotAvailableError):
            ModelFactory.create_dataframe_from_dicts(None, dicts)

    @patch("polyspark.schema.is_pyspark_available", return_value=False)
    def test_infer_schema_returns_ddl_string_without_pyspark(self, mock_check):
        """infer_schema should return DDL string when PySpark is unavailable."""

        schema = infer_schema(SimpleModel)
        assert isinstance(schema, str)
        assert schema == "struct<id:long,name:string>"

    @patch("polyspark.schema.is_pyspark_available", return_value=False)
    def test_export_ddl_schema_works_without_pyspark(self, mock_check):
        """export_ddl_schema should work without PySpark."""

        schema = export_ddl_schema(SimpleModel)
        assert isinstance(schema, str)
        assert schema == "struct<id:long,name:string>"

    @patch("polyspark.schema.is_pyspark_available", return_value=False)
    def test_infer_schema_validates_column_names_without_pyspark(self, mock_check):
        """infer_schema should validate column names even without PySpark."""

        # Valid column names should work
        schema = infer_schema(SimpleModel, schema=["id", "name"])
        assert isinstance(schema, str)

        # Invalid column name should raise error
        with pytest.raises(
            Exception, match="Column 'invalid_field' not found"
        ):  # Should raise SchemaInferenceError
            infer_schema(SimpleModel, schema=["id", "name", "invalid_field"])

    @patch("polyspark.schema.is_pyspark_available", return_value=False)
    def test_python_type_to_spark_type_graceful_degradation(self, mock_check):
        """python_type_to_spark_type should return DDL when PySpark unavailable."""
        from typing import Dict, List

        from polyspark.schema import python_type_to_spark_type

        # Should return DDL type string instead of raising error
        result = python_type_to_spark_type(str)
        assert isinstance(result, str)
        assert result == "string"

        # Test with int
        result = python_type_to_spark_type(int)
        assert isinstance(result, str)
        assert result == "long"

        # Test with complex type
        result = python_type_to_spark_type(List[str])
        assert isinstance(result, str)
        assert result == "array<string>"

        # Test with dict
        result = python_type_to_spark_type(Dict[str, int])
        assert isinstance(result, str)
        assert result == "map<string,long>"

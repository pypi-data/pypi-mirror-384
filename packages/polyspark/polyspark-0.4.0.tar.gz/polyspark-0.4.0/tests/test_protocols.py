"""Tests for protocol definitions and runtime checks."""

import pytest

from polyspark.protocols import get_pyspark_types, get_spark_session, is_pyspark_available


class TestRuntimeChecks:
    """Test runtime availability checks."""

    def test_is_pyspark_available(self):
        """Test PySpark availability check."""
        result = is_pyspark_available()
        assert isinstance(result, bool)

    def test_get_pyspark_types(self):
        """Test getting PySpark types module."""
        types = get_pyspark_types()

        if is_pyspark_available():
            assert types is not None
            # Check that it has expected types
            assert hasattr(types, "StringType")
            assert hasattr(types, "IntegerType")
            assert hasattr(types, "StructType")
        else:
            assert types is None

    def test_get_spark_session(self):
        """Test getting SparkSession class."""
        spark_session_class = get_spark_session()

        if is_pyspark_available():
            assert spark_session_class is not None
            assert hasattr(spark_session_class, "builder")
        else:
            assert spark_session_class is None


@pytest.mark.skipif(not is_pyspark_available(), reason="PySpark not installed")
class TestProtocolsWithPyspark:
    """Test protocols when PySpark is available."""

    def test_dataframe_protocol_with_real_dataframe(self, spark):
        """Test that PySpark DataFrame matches protocol."""
        from polyspark.protocols import DataFrameProtocol

        df = spark.createDataFrame([(1, "test")], ["id", "name"])

        # Check protocol match
        assert isinstance(df, DataFrameProtocol)
        assert hasattr(df, "schema")
        assert hasattr(df, "show")
        assert hasattr(df, "collect")
        assert hasattr(df, "count")

    def test_spark_session_protocol(self, spark):
        """Test that SparkSession matches protocol."""
        from polyspark.protocols import SparkSessionProtocol

        assert isinstance(spark, SparkSessionProtocol)
        assert hasattr(spark, "createDataFrame")

    def test_struct_type_protocol(self):
        """Test that StructType matches protocol."""
        from pyspark.sql.types import StringType, StructField, StructType

        from polyspark.protocols import StructTypeProtocol

        struct = StructType([StructField("name", StringType(), True)])

        assert isinstance(struct, StructTypeProtocol)
        assert hasattr(struct, "fields")
        assert hasattr(struct, "add")

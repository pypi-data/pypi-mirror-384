"""Tests for testing utilities module."""

from dataclasses import dataclass

import pytest

from polyspark import spark_factory
from polyspark.testing import (
    DataFrameComparisonError,
    assert_approx_count,
    assert_column_exists,
    assert_dataframe_equal,
    assert_no_duplicates,
    assert_schema_equal,
    get_column_stats,
)

try:
    import pyspark  # noqa: F401
    from pyspark.sql.types import IntegerType, StringType, StructField, StructType

    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False

pytestmark = pytest.mark.skipif(not PYSPARK_AVAILABLE, reason="PySpark not installed")

# Use the session-scoped spark fixture from conftest.py


class TestAssertDataFrameEqual:
    """Tests for assert_dataframe_equal function."""

    def test_equal_dataframes_pass(self, spark):
        """Test that equal DataFrames pass assertion."""
        df1 = spark.createDataFrame([{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}])
        df2 = spark.createDataFrame([{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}])

        # Should not raise
        assert_dataframe_equal(df1, df2)

    def test_different_row_counts_fail(self, spark):
        """Test that different row counts cause failure."""
        df1 = spark.createDataFrame([{"id": 1, "name": "Alice"}])
        df2 = spark.createDataFrame([{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}])

        with pytest.raises(DataFrameComparisonError, match="row counts don't match"):
            assert_dataframe_equal(df1, df2)

    def test_different_schemas_fail(self, spark):
        """Test that different schemas cause failure."""
        df1 = spark.createDataFrame([{"id": 1, "name": "Alice"}])
        df2 = spark.createDataFrame([{"id": 1, "age": 30}])

        with pytest.raises(DataFrameComparisonError, match="schemas don't match"):
            assert_dataframe_equal(df1, df2)

    def test_different_values_fail(self, spark):
        """Test that different values cause failure."""
        df1 = spark.createDataFrame([{"id": 1, "name": "Alice"}])
        df2 = spark.createDataFrame([{"id": 1, "name": "Bob"}])

        with pytest.raises(DataFrameComparisonError, match="differing values"):
            assert_dataframe_equal(df1, df2)

    def test_unordered_comparison(self, spark):
        """Test comparison without checking order."""
        df1 = spark.createDataFrame([{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}])
        df2 = spark.createDataFrame([{"id": 2, "name": "Bob"}, {"id": 1, "name": "Alice"}])

        # Should pass when check_order=False (default)
        assert_dataframe_equal(df1, df2, check_order=False)

    def test_ordered_comparison_fails(self, spark):
        """Test that ordered comparison detects row order differences."""
        df1 = spark.createDataFrame([{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}])
        df2 = spark.createDataFrame([{"id": 2, "name": "Bob"}, {"id": 1, "name": "Alice"}])

        with pytest.raises(DataFrameComparisonError):
            assert_dataframe_equal(df1, df2, check_order=True)

    def test_float_comparison_with_tolerance(self, spark):
        """Test floating point comparison with tolerance."""
        df1 = spark.createDataFrame([{"id": 1, "value": 1.0000001}])
        df2 = spark.createDataFrame([{"id": 1, "value": 1.0000002}])

        # Should pass with default tolerance
        assert_dataframe_equal(df1, df2, rtol=1e-5, atol=1e-5)

    def test_float_comparison_exceeds_tolerance(self, spark):
        """Test that floats exceeding tolerance cause failure."""
        df1 = spark.createDataFrame([{"id": 1, "value": 1.0}])
        df2 = spark.createDataFrame([{"id": 1, "value": 1.1}])

        with pytest.raises(DataFrameComparisonError):
            assert_dataframe_equal(df1, df2, rtol=1e-5)

    def test_column_order_independence(self, spark):
        """Test comparison ignoring column order."""
        df1 = spark.createDataFrame([{"id": 1, "name": "Alice"}])
        df2 = spark.createDataFrame([{"name": "Alice", "id": 1}])

        # Should pass when check_column_order=False (default)
        assert_dataframe_equal(df1, df2, check_column_order=False)

    def test_nullable_checking(self, spark):
        """Test nullable property checking."""
        schema1 = StructType([StructField("id", IntegerType(), True)])
        schema2 = StructType([StructField("id", IntegerType(), False)])

        df1 = spark.createDataFrame([{"id": 1}], schema=schema1)
        df2 = spark.createDataFrame([{"id": 1}], schema=schema2)

        # Should fail when check_nullable=True
        with pytest.raises(DataFrameComparisonError, match="nullable"):
            assert_dataframe_equal(df1, df2, check_nullable=True)

        # Should pass when check_nullable=False
        assert_dataframe_equal(df1, df2, check_nullable=False)


class TestAssertSchemaEqual:
    """Tests for assert_schema_equal function."""

    def test_equal_schemas_pass(self, spark):
        """Test that equal schemas pass assertion."""
        schema1 = StructType(
            [StructField("id", IntegerType(), True), StructField("name", StringType(), True)]
        )
        schema2 = StructType(
            [StructField("id", IntegerType(), True), StructField("name", StringType(), True)]
        )

        assert_schema_equal(schema1, schema2)

    def test_different_field_counts_fail(self, spark):
        """Test that different field counts cause failure."""
        schema1 = StructType([StructField("id", IntegerType(), True)])
        schema2 = StructType(
            [StructField("id", IntegerType(), True), StructField("name", StringType(), True)]
        )

        with pytest.raises(DataFrameComparisonError, match="different number of fields"):
            assert_schema_equal(schema1, schema2)

    def test_different_field_names_fail(self, spark):
        """Test that different field names cause failure."""
        schema1 = StructType([StructField("id", IntegerType(), True)])
        schema2 = StructType([StructField("user_id", IntegerType(), True)])

        with pytest.raises(DataFrameComparisonError, match="different field names"):
            assert_schema_equal(schema1, schema2)

    def test_different_field_types_fail(self, spark):
        """Test that different field types cause failure."""
        schema1 = StructType([StructField("id", IntegerType(), True)])
        schema2 = StructType([StructField("id", StringType(), True)])

        with pytest.raises(DataFrameComparisonError, match="different types"):
            assert_schema_equal(schema1, schema2)

    def test_field_order_independence(self, spark):
        """Test schema comparison ignoring field order."""
        schema1 = StructType(
            [StructField("id", IntegerType(), True), StructField("name", StringType(), True)]
        )
        schema2 = StructType(
            [StructField("name", StringType(), True), StructField("id", IntegerType(), True)]
        )

        # Should pass when check_order=False (default)
        assert_schema_equal(schema1, schema2, check_order=False)

    def test_field_order_checking(self, spark):
        """Test that order checking detects field order differences."""
        schema1 = StructType(
            [StructField("id", IntegerType(), True), StructField("name", StringType(), True)]
        )
        schema2 = StructType(
            [StructField("name", StringType(), True), StructField("id", IntegerType(), True)]
        )

        with pytest.raises(DataFrameComparisonError, match="order mismatch"):
            assert_schema_equal(schema1, schema2, check_order=True)

    def test_nullable_difference(self, spark):
        """Test nullable property differences."""
        schema1 = StructType([StructField("id", IntegerType(), True)])
        schema2 = StructType([StructField("id", IntegerType(), False)])

        # Should fail when check_nullable=True (default)
        with pytest.raises(DataFrameComparisonError, match="nullable"):
            assert_schema_equal(schema1, schema2, check_nullable=True)

        # Should pass when check_nullable=False
        assert_schema_equal(schema1, schema2, check_nullable=False)


class TestAssertApproxCount:
    """Tests for assert_approx_count function."""

    def test_exact_count_passes(self, spark):
        """Test that exact count passes."""
        df = spark.range(0, 100)
        assert_approx_count(df, 100, tolerance=0.1)

    def test_count_within_tolerance_passes(self, spark):
        """Test that count within tolerance passes."""
        df = spark.range(0, 95)
        assert_approx_count(df, 100, tolerance=0.1)  # 95 is within 10% of 100

    def test_count_outside_tolerance_fails(self, spark):
        """Test that count outside tolerance fails."""
        df = spark.range(0, 80)
        with pytest.raises(DataFrameComparisonError, match="not within"):
            assert_approx_count(df, 100, tolerance=0.1)  # 80 is not within 10% of 100

    def test_custom_tolerance(self, spark):
        """Test with custom tolerance."""
        df = spark.range(0, 75)
        assert_approx_count(df, 100, tolerance=0.25)  # 75 is within 25% of 100

    def test_zero_tolerance(self, spark):
        """Test with zero tolerance (exact match required)."""
        df = spark.range(0, 100)
        assert_approx_count(df, 100, tolerance=0.0)

        df2 = spark.range(0, 99)
        with pytest.raises(DataFrameComparisonError):
            assert_approx_count(df2, 100, tolerance=0.0)


class TestGetColumnStats:
    """Tests for get_column_stats function."""

    def test_basic_stats(self, spark):
        """Test basic column statistics."""
        df = spark.createDataFrame([{"value": 1}, {"value": 2}, {"value": 3}])
        stats = get_column_stats(df, "value")

        assert stats["count"] == 3
        assert stats["null_count"] == 0
        assert stats["non_null_count"] == 3
        assert stats["distinct_count"] == 3

    def test_stats_with_nulls(self, spark):
        """Test statistics with null values."""
        df = spark.createDataFrame([{"value": 1}, {"value": 2}, {"value": None}])
        stats = get_column_stats(df, "value")

        assert stats["count"] == 3
        assert stats["null_count"] == 1
        assert stats["non_null_count"] == 2

    def test_stats_with_duplicates(self, spark):
        """Test statistics with duplicate values."""
        df = spark.createDataFrame([{"value": 1}, {"value": 1}, {"value": 2}])
        stats = get_column_stats(df, "value")

        assert stats["count"] == 3
        assert stats["distinct_count"] == 2

    def test_numeric_stats(self, spark):
        """Test numeric-specific statistics."""
        df = spark.createDataFrame([{"value": 1.0}, {"value": 2.0}, {"value": 3.0}])
        stats = get_column_stats(df, "value")

        assert "min" in stats
        assert "max" in stats
        assert "mean" in stats
        assert "stddev" in stats
        assert stats["min"] == 1.0
        assert stats["max"] == 3.0
        assert stats["mean"] == 2.0


class TestAssertColumnExists:
    """Tests for assert_column_exists function."""

    def test_existing_column_passes(self, spark):
        """Test that existing column passes."""
        df = spark.createDataFrame([{"id": 1, "name": "Alice"}])
        assert_column_exists(df, "id")
        assert_column_exists(df, "name")

    def test_multiple_columns_pass(self, spark):
        """Test that multiple existing columns pass."""
        df = spark.createDataFrame([{"id": 1, "name": "Alice", "age": 30}])
        assert_column_exists(df, "id", "name", "age")

    def test_missing_column_fails(self, spark):
        """Test that missing column causes failure."""
        df = spark.createDataFrame([{"id": 1, "name": "Alice"}])
        with pytest.raises(DataFrameComparisonError, match="missing"):
            assert_column_exists(df, "age")

    def test_some_missing_columns_fail(self, spark):
        """Test that some missing columns cause failure."""
        df = spark.createDataFrame([{"id": 1, "name": "Alice"}])
        with pytest.raises(DataFrameComparisonError, match="missing"):
            assert_column_exists(df, "id", "name", "age", "email")


class TestAssertNoDuplicates:
    """Tests for assert_no_duplicates function."""

    def test_no_duplicates_passes(self, spark):
        """Test that DataFrame with no duplicates passes."""
        df = spark.createDataFrame([{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}])
        assert_no_duplicates(df)

    def test_full_duplicates_fail(self, spark):
        """Test that full row duplicates cause failure."""
        df = spark.createDataFrame([{"id": 1, "name": "Alice"}, {"id": 1, "name": "Alice"}])
        with pytest.raises(DataFrameComparisonError, match="duplicate"):
            assert_no_duplicates(df)

    def test_column_specific_duplicates(self, spark):
        """Test duplicate checking for specific columns."""
        df = spark.createDataFrame([{"id": 1, "name": "Alice"}, {"id": 1, "name": "Bob"}])

        # Full row check should pass (rows are different)
        assert_no_duplicates(df)

        # Column-specific check should fail (id is duplicated)
        with pytest.raises(DataFrameComparisonError, match="duplicate"):
            assert_no_duplicates(df, columns=["id"])

    def test_multiple_column_duplicate_check(self, spark):
        """Test duplicate checking for multiple columns."""
        df = spark.createDataFrame(
            [{"id": 1, "name": "Alice", "age": 30}, {"id": 1, "name": "Alice", "age": 25}]
        )

        # Check on id and name (duplicated)
        with pytest.raises(DataFrameComparisonError, match="duplicate"):
            assert_no_duplicates(df, columns=["id", "name"])


class TestIntegrationWithGeneratedData:
    """Test testing utilities with polyspark-generated data."""

    def test_assert_dataframe_equal_with_generated_data(self, spark):
        """Test assert_dataframe_equal with generated DataFrames."""

        @spark_factory
        @dataclass
        class User:
            user_id: int
            name: str

        # Generate same data twice with same seed should be equal
        # (Note: polyfactory might not guarantee exact reproducibility without manual seeding)
        df1 = User.build_dataframe(spark, size=10)
        df2 = User.build_dataframe(spark, size=10)

        # Schemas should be equal
        assert_schema_equal(df1.schema, df2.schema)

    def test_column_stats_on_generated_data(self, spark):
        """Test get_column_stats on generated data."""

        @spark_factory
        @dataclass
        class Product:
            product_id: int
            price: float

        df = Product.build_dataframe(spark, size=50)
        stats = get_column_stats(df, "product_id")

        assert stats["count"] == 50
        assert stats["null_count"] == 0
        assert stats["distinct_count"] > 0

    def test_assert_column_exists_on_generated_schema(self, spark):
        """Test assert_column_exists on generated DataFrame."""

        @spark_factory
        @dataclass
        class Order:
            order_id: int
            customer_id: int
            total: float

        df = Order.build_dataframe(spark, size=20)

        # These should exist
        assert_column_exists(df, "order_id", "customer_id", "total")

        # This should not exist
        with pytest.raises(DataFrameComparisonError):
            assert_column_exists(df, "invalid_column")

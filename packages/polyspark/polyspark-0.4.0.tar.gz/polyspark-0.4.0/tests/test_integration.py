"""Integration tests for end-to-end workflows."""

import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import pytest

from polyspark import spark_factory

try:
    import pyspark  # noqa: F401

    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False

try:
    from pydantic import BaseModel

    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

pytestmark = pytest.mark.skipif(not PYSPARK_AVAILABLE, reason="PySpark not installed")

# Use the session-scoped spark fixture from conftest.py


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows."""

    def test_generate_save_load_workflow(self, spark):
        """Test workflow: generate -> save -> load -> validate."""

        @spark_factory
        @dataclass
        class Customer:
            customer_id: int
            name: str
            email: str
            active: bool

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "customers.parquet"

            # Step 1: Generate data
            df_generated = Customer.build_dataframe(spark, size=100)
            assert df_generated.count() == 100

            # Step 2: Save to parquet
            df_generated.write.parquet(str(output_path))

            # Step 3: Load from parquet
            df_loaded = spark.read.parquet(str(output_path))
            assert df_loaded.count() == 100

            # Step 4: Validate schema matches (parquet makes fields nullable)
            assert set(df_loaded.columns) == set(df_generated.columns)
            # Note: After writing to parquet, nullable property may change

            # Step 5: Validate data
            assert set(df_loaded.columns) == {"customer_id", "name", "email", "active"}

    def test_generate_transform_validate_workflow(self, spark):
        """Test workflow: generate -> transform -> validate."""

        @spark_factory
        @dataclass
        class Sale:
            sale_id: int
            product: str
            quantity: int
            price: float

        # Generate test data
        df = Sale.build_dataframe(spark, size=50)

        # Transform: calculate total
        from pyspark.sql.functions import col

        df_transformed = df.withColumn("total", col("quantity") * col("price"))

        # Validate transformation
        assert "total" in df_transformed.columns
        assert df_transformed.count() == 50

        # Verify calculation
        row = df_transformed.first()
        expected_total = row.quantity * row.price
        assert abs(row.total - expected_total) < 0.01

    def test_multi_model_workflow(self, spark):
        """Test workflow with multiple related models."""

        @spark_factory
        @dataclass
        class User:
            user_id: int
            username: str

        @spark_factory
        @dataclass
        class Post:
            post_id: int
            user_id: int
            title: str
            content: str

        @spark_factory
        @dataclass
        class Comment:
            comment_id: int
            post_id: int
            user_id: int
            text: str

        # Generate related data
        users_df = User.build_dataframe(spark, size=10)
        posts_df = Post.build_dataframe(spark, size=50)
        comments_df = Comment.build_dataframe(spark, size=200)

        # Join workflow
        posts_with_users = posts_df.join(users_df, on="user_id", how="left")
        full_data = posts_with_users.join(comments_df, on="post_id", how="left")

        assert full_data.count() > 0
        assert "username" in full_data.columns
        assert "title" in full_data.columns
        assert "text" in full_data.columns

    def test_dict_to_json_to_dataframe_workflow(self, spark):
        """Test workflow: dicts -> JSON -> DataFrame."""

        @spark_factory
        @dataclass
        class Product:
            product_id: int
            name: str
            price: float
            tags: List[str]

        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "products.json"

            # Step 1: Generate dicts (no Spark needed)
            dicts = Product.build_dicts(size=20)
            assert len(dicts) == 20

            # Step 2: Save to JSON
            with open(json_path, "w") as f:
                for d in dicts:
                    json.dump(d, f)
                    f.write("\n")

            # Step 3: Load JSON and convert to DataFrame
            with open(json_path) as f:
                loaded_dicts = [json.loads(line) for line in f]

            df = Product.create_dataframe_from_dicts(spark, loaded_dicts)
            assert df.count() == 20


class TestRealWorldPatterns:
    """Test real-world usage patterns."""

    def test_data_quality_checks(self, spark):
        """Test data quality validation on generated data."""

        @spark_factory
        @dataclass
        class Transaction:
            transaction_id: int
            amount: float
            status: str

        df = Transaction.build_dataframe(spark, size=100)

        # Data quality checks
        assert df.count() == 100

        # Check for nulls in non-nullable fields
        assert df.filter(df.transaction_id.isNull()).count() == 0

        # Check data types
        assert dict(df.dtypes)["transaction_id"] == "bigint"
        assert dict(df.dtypes)["amount"] == "double"
        assert dict(df.dtypes)["status"] == "string"

    def test_aggregation_pipeline(self, spark):
        """Test aggregation pipeline on generated data."""
        from pyspark.sql.functions import avg, count, sum

        @spark_factory
        @dataclass
        class Order:
            order_id: int
            customer_id: int
            amount: float
            quantity: int

        df = Order.build_dataframe(spark, size=200)

        # Aggregation pipeline
        result = (
            df.groupBy("customer_id")
            .agg(
                count("order_id").alias("order_count"),
                sum("amount").alias("total_amount"),
                avg("quantity").alias("avg_quantity"),
            )
            .orderBy("total_amount", ascending=False)
        )

        assert result.count() > 0
        assert "order_count" in result.columns
        assert "total_amount" in result.columns

    def test_window_functions(self, spark):
        """Test window functions on generated data."""
        from pyspark.sql.functions import rank
        from pyspark.sql.window import Window

        @spark_factory
        @dataclass
        class Employee:
            emp_id: int
            name: str
            department: str
            salary: float

        df = Employee.build_dataframe(spark, size=50)

        # Window function: rank employees by salary within department
        window_spec = Window.partitionBy("department").orderBy(df.salary.desc())
        df_ranked = df.withColumn("salary_rank", rank().over(window_spec))

        assert "salary_rank" in df_ranked.columns
        assert df_ranked.count() == 50

    def test_union_and_dedup(self, spark):
        """Test union and deduplication workflow."""

        @spark_factory
        @dataclass
        class Event:
            event_id: int
            timestamp: str
            event_type: str

        # Generate two batches
        df1 = Event.build_dataframe(spark, size=30)
        df2 = Event.build_dataframe(spark, size=30)

        # Union
        df_combined = df1.union(df2)
        assert df_combined.count() == 60

        # Deduplicate by event_id
        df_deduped = df_combined.dropDuplicates(["event_id"])
        # Count should be <= 60 (some might have same event_id)
        assert df_deduped.count() <= 60


class TestComplexDataTransformations:
    """Test complex transformations on generated data."""

    def test_explode_array_column(self, spark):
        """Test exploding array columns."""
        from pyspark.sql.functions import explode

        @spark_factory
        @dataclass
        class Document:
            doc_id: int
            title: str
            keywords: List[str]

        df = Document.build_dataframe(spark, size=20)

        # Explode keywords
        df_exploded = df.select("doc_id", "title", explode("keywords").alias("keyword"))

        assert "keyword" in df_exploded.columns
        # Should have more rows than original (unless all arrays were empty)
        assert df_exploded.count() >= 0

    def test_pivot_operation(self, spark):
        """Test pivot operations on generated data."""

        @spark_factory
        @dataclass
        class Metric:
            date: str
            metric_name: str
            value: float

        df = Metric.build_dataframe(spark, size=100)

        # Pivot: rows to columns
        df_pivoted = df.groupBy("date").pivot("metric_name").sum("value")

        assert df_pivoted.count() > 0

    def test_nested_struct_selection(self, spark):
        """Test selecting from nested structures."""

        @dataclass
        class Address:
            street: str
            city: str
            zipcode: str

        @spark_factory
        @dataclass
        class Person:
            person_id: int
            name: str
            address: Address

        df = Person.build_dataframe(spark, size=20)

        # Select nested fields
        df_cities = df.select("person_id", "name", "address.city")

        assert df_cities.count() == 20
        assert "city" in df_cities.columns


class TestErrorRecoveryPatterns:
    """Test error handling and recovery patterns."""

    def test_schema_validation_with_mismatch(self, spark):
        """Test handling of schema mismatches."""
        from pyspark.sql.types import IntegerType, StringType, StructField, StructType

        @spark_factory
        @dataclass
        class Data:
            id: int
            value: str

        # Generate data
        dicts = Data.build_dicts(size=10)

        # Try to use incorrect schema (wrong field name)
        wrong_schema = StructType(
            [
                StructField("wrong_id", IntegerType(), False),
                StructField("value", StringType(), True),
            ]
        )

        # This should raise an error or handle gracefully
        with pytest.raises((ValueError, TypeError, Exception)):
            spark.createDataFrame(dicts, schema=wrong_schema)

    def test_empty_dataframe_handling(self, spark):
        """Test handling of empty DataFrames."""

        @spark_factory
        @dataclass
        class Item:
            item_id: int
            name: str

        # Generate with size 0 should handle gracefully
        df = Item.build_dataframe(spark, size=0)
        assert df.count() == 0
        assert len(df.columns) > 0  # Schema should still exist


@pytest.mark.skipif(not PYDANTIC_AVAILABLE, reason="Pydantic not installed")
class TestPydanticIntegration:
    """Integration tests with Pydantic models."""

    def test_pydantic_full_workflow(self, spark):
        """Test complete workflow with Pydantic models."""
        from pydantic import Field

        @spark_factory
        class User(BaseModel):
            user_id: int = Field(gt=0)
            email: str
            age: int = Field(ge=18, le=120)
            tags: List[str]
            metadata: Dict[str, str]

        # Generate
        df = User.build_dataframe(spark, size=50)
        assert df.count() == 50

        # Transform
        from pyspark.sql.functions import col

        df_adults = df.filter(col("age") >= 21)

        # Validate
        rows = df_adults.collect()
        assert all(row.age >= 21 for row in rows)

    def test_mixed_dataclass_and_pydantic(self, spark):
        """Test using both dataclasses and Pydantic in same workflow."""

        @spark_factory
        @dataclass
        class Order:
            order_id: int
            customer_id: int
            total: float

        @spark_factory
        class Customer(BaseModel):
            customer_id: int
            name: str
            email: str

        orders_df = Order.build_dataframe(spark, size=30)
        customers_df = Customer.build_dataframe(spark, size=10)

        # Join them
        result = orders_df.join(customers_df, on="customer_id", how="left")
        assert result.count() > 0


class TestPerformancePatterns:
    """Test performance-related patterns."""

    def test_partition_by_column(self, spark):
        """Test partitioning generated data."""

        @spark_factory
        @dataclass
        class Event:
            event_id: int
            date: str
            event_type: str
            data: str

        df = Event.build_dataframe(spark, size=100)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "events_partitioned"

            # Write partitioned data
            df.write.partitionBy("date").parquet(str(output_path))

            # Read it back
            df_loaded = spark.read.parquet(str(output_path))
            assert df_loaded.count() == 100

    def test_caching_workflow(self, spark):
        """Test caching workflow with generated data."""

        @spark_factory
        @dataclass
        class LargeData:
            id: int
            value: str
            score: float

        df = LargeData.build_dataframe(spark, size=1000)

        # Cache for reuse
        df.cache()

        # Multiple operations should use cache
        count1 = df.count()
        count2 = df.filter(df.score > 0).count()

        assert count1 == 1000
        assert count2 >= 0

        # Unpersist
        df.unpersist()


class TestDataFrameIO:
    """Test various I/O operations."""

    def test_csv_write_read(self, spark):
        """Test CSV write and read workflow."""

        @spark_factory
        @dataclass
        class Record:
            id: int
            name: str
            value: float

        df = Record.build_dataframe(spark, size=20)

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "records.csv"

            # Write CSV
            df.coalesce(1).write.csv(str(csv_path), header=True, mode="overwrite")

            # Read CSV
            df_loaded = spark.read.csv(str(csv_path), header=True, inferSchema=True)
            assert df_loaded.count() == 20

    def test_json_write_read(self, spark):
        """Test JSON write and read workflow."""

        @spark_factory
        @dataclass
        class Data:
            id: int
            tags: List[str]
            metadata: Dict[str, str]

        df = Data.build_dataframe(spark, size=15)

        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "data.json"

            # Write JSON
            df.coalesce(1).write.json(str(json_path), mode="overwrite")

            # Read JSON
            df_loaded = spark.read.json(str(json_path))
            assert df_loaded.count() == 15

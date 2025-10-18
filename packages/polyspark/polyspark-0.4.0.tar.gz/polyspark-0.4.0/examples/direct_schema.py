"""Example using PySpark schema directly."""

from dataclasses import dataclass

from polyspark import SparkFactory

try:
    from pyspark.sql import SparkSession
    from pyspark.sql.types import (
        BooleanType,
        DateType,
        DoubleType,
        IntegerType,
        StringType,
        StructField,
        StructType,
        TimestampType,
    )

    # Define a simple model
    @dataclass
    class Transaction:
        transaction_id: int
        customer_id: int
        amount: float
        description: str
        is_completed: bool

    class TransactionFactory(SparkFactory[Transaction]):
        __model__ = Transaction

    def example_inferred_schema():
        """Use inferred schema from dataclass."""
        spark = (
            SparkSession.builder.appName("polyspark-schema-example")
            .master("local[*]")
            .getOrCreate()
        )

        # No explicit schema - inferred from dataclass
        df = TransactionFactory.build_dataframe(spark, size=10)

        print("DataFrame with inferred schema:")
        df.show(5)
        print("\nInferred schema:")
        df.printSchema()

        spark.stop()

    def example_explicit_schema():
        """Use explicit PySpark schema."""
        spark = (
            SparkSession.builder.appName("polyspark-schema-example")
            .master("local[*]")
            .getOrCreate()
        )

        # Define explicit schema with specific types
        explicit_schema = StructType(
            [
                StructField("transaction_id", IntegerType(), False),
                StructField("customer_id", IntegerType(), True),
                StructField("amount", DoubleType(), True),
                StructField("description", StringType(), True),
                StructField("is_completed", BooleanType(), True),
            ]
        )

        # Use explicit schema
        df = TransactionFactory.build_dataframe(spark, size=10, schema=explicit_schema)

        print("DataFrame with explicit schema:")
        df.show(5)
        print("\nExplicit schema:")
        df.printSchema()

        # Note: transaction_id is not nullable in the explicit schema
        print(f"transaction_id nullable: {df.schema['transaction_id'].nullable}")

        spark.stop()

    def example_custom_schema_types():
        """Use custom PySpark types."""
        from datetime import date, datetime

        @dataclass
        class Event:
            event_id: int
            event_name: str
            event_date: date
            timestamp: datetime
            priority: int

        class EventFactory(SparkFactory[Event]):
            __model__ = Event

        spark = (
            SparkSession.builder.appName("polyspark-schema-example")
            .master("local[*]")
            .getOrCreate()
        )

        # Inferred schema will use DateType and TimestampType
        df = EventFactory.build_dataframe(spark, size=10)

        print("DataFrame with date/timestamp types:")
        df.show(5, truncate=False)
        print("\nSchema with date/timestamp:")
        df.printSchema()

        # Custom schema with explicit types
        custom_schema = StructType(
            [
                StructField("event_id", IntegerType(), False),
                StructField("event_name", StringType(), True),
                StructField("event_date", DateType(), True),
                StructField("timestamp", TimestampType(), True),
                StructField("priority", IntegerType(), True),
            ]
        )

        df2 = EventFactory.build_dataframe(spark, size=5, schema=custom_schema)
        print("\nDataFrame with custom schema:")
        df2.show(5, truncate=False)

        spark.stop()

    def example_partial_columns():
        """Select specific columns using schema parameter."""
        spark = (
            SparkSession.builder.appName("polyspark-schema-example")
            .master("local[*]")
            .getOrCreate()
        )

        # Generate full data but specify column names
        # Note: Full schema is still inferred, but you can validate column names
        df = TransactionFactory.build_dataframe(
            spark, size=10, schema=["transaction_id", "amount", "description"]
        )

        print("DataFrame with column name validation:")
        df.show(5)

        # Select specific columns after generation
        df_subset = df.select("transaction_id", "amount", "description")
        print("\nSubset of columns:")
        df_subset.show(5)

        spark.stop()

    if __name__ == "__main__":
        print("=" * 80)
        print("Example 1: Inferred Schema")
        print("=" * 80)
        example_inferred_schema()

        print("\n" + "=" * 80)
        print("Example 2: Explicit Schema")
        print("=" * 80)
        example_explicit_schema()

        print("\n" + "=" * 80)
        print("Example 3: Custom Schema Types")
        print("=" * 80)
        example_custom_schema_types()

        print("\n" + "=" * 80)
        print("Example 4: Partial Columns")
        print("=" * 80)
        example_partial_columns()

except ImportError:
    print("PySpark is not installed. Install it with: pip install pyspark")

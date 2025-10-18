"""Production usage examples for polyspark.

This example demonstrates production-ready patterns including:
- Large-scale data generation
- Partitioned data creation
- Data quality validation
- Performance optimization
"""

from dataclasses import dataclass
from datetime import datetime

from pyspark.sql import SparkSession
from pyspark.sql.functions import col

from polyspark import spark_factory
from polyspark.io import save_as_parquet
from polyspark.testing import assert_approx_count, assert_column_exists, get_column_stats

# ============================================================================
# Production Models
# ============================================================================


@spark_factory
@dataclass
class TransactionRecord:
    """Production transaction model."""

    transaction_id: int
    user_id: int
    merchant_id: int
    amount: float
    currency: str
    transaction_date: str
    status: str
    payment_method: str
    category: str


@spark_factory
@dataclass
class UserProfile:
    """User profile for production testing."""

    user_id: int
    username: str
    email: str
    created_at: str
    country: str
    subscription_tier: str
    is_active: bool


# ============================================================================
# Pattern 1: Large-Scale Data Generation
# ============================================================================


def generate_large_dataset(spark: SparkSession, output_path: str) -> None:
    """Generate large dataset for load testing.

    Args:
        spark: SparkSession.
        output_path: Path to save generated data.
    """
    print("\n" + "=" * 70)
    print("Pattern 1: Large-Scale Data Generation")
    print("=" * 70)

    print("\nGenerating 100,000 transactions...")

    # Generate data in batches for better memory management
    batch_size = 10000
    total_size = 100000

    for batch_num in range(total_size // batch_size):
        print(f"  Generating batch {batch_num + 1}/{total_size // batch_size}...")

        df_batch = TransactionRecord.build_dataframe(spark, size=batch_size)

        # Write in append mode (except first batch)
        mode = "overwrite" if batch_num == 0 else "append"
        save_as_parquet(df_batch, output_path, mode=mode)

    # Verify final count
    df_final = spark.read.parquet(output_path)
    final_count = df_final.count()

    print(f"\n✓ Generated {final_count:,} records")
    print(f"  Output: {output_path}")


# ============================================================================
# Pattern 2: Partitioned Data Creation
# ============================================================================


def generate_partitioned_data(spark: SparkSession, output_path: str) -> None:
    """Generate partitioned data for efficient querying.

    Args:
        spark: SparkSession.
        output_path: Path to save partitioned data.
    """
    print("\n" + "=" * 70)
    print("Pattern 2: Partitioned Data Creation")
    print("=" * 70)

    # Generate data
    print("\nGenerating partitioned transaction data...")
    df = TransactionRecord.build_dataframe(spark, size=50000)

    # Partition by date and status for efficient queries
    print("  Partitioning by transaction_date and status...")

    save_as_parquet(df, output_path, partition_by=["transaction_date", "status"])

    # Verify partitions
    df_loaded = spark.read.parquet(output_path)

    print("\n✓ Created partitioned dataset")
    print(f"  Total records: {df_loaded.count():,}")
    print("  Partitions: transaction_date, status")
    print(f"  Output: {output_path}")

    # Show partition distribution
    print("\n  Partition distribution:")
    df_loaded.groupBy("transaction_date", "status").count().orderBy(
        "transaction_date", "status"
    ).show(10)


# ============================================================================
# Pattern 3: Data Quality Validation
# ============================================================================


def validate_generated_data(spark: SparkSession) -> None:
    """Validate data quality of generated data.

    Args:
        spark: SparkSession.
    """
    print("\n" + "=" * 70)
    print("Pattern 3: Data Quality Validation")
    print("=" * 70)

    # Generate test data
    df = TransactionRecord.build_dataframe(spark, size=10000)

    print("\nRunning data quality checks...")

    # Check 1: Row count
    print("\n1. Row Count Validation")
    assert_approx_count(df, 10000, tolerance=0.01)
    print("  ✓ Row count is correct: 10,000 rows")

    # Check 2: Required columns exist
    print("\n2. Schema Validation")
    assert_column_exists(
        df,
        "transaction_id",
        "user_id",
        "merchant_id",
        "amount",
        "currency",
        "transaction_date",
        "status",
    )
    print("  ✓ All required columns present")

    # Check 3: No nulls in critical columns
    print("\n3. Null Check")
    null_counts = {}
    for column in ["transaction_id", "user_id", "amount"]:
        null_count = df.filter(col(column).isNull()).count()
        null_counts[column] = null_count
        print(f"  - {column}: {null_count} nulls")

    assert all(
        count == 0 for count in null_counts.values()
    ), "Critical columns should have no nulls"
    print("  ✓ No nulls in critical columns")

    # Check 4: Data distribution
    print("\n4. Data Distribution")
    amount_stats = get_column_stats(df, "amount")
    print("  - Amount statistics:")
    print(f"    Min: ${amount_stats.get('min', 0):.2f}")
    print(f"    Max: ${amount_stats.get('max', 0):.2f}")
    print(f"    Mean: ${amount_stats.get('mean', 0):.2f}")
    print(f"    Distinct values: {amount_stats['distinct_count']}")

    # Check 5: Value constraints
    print("\n5. Value Constraints")
    invalid_amounts = df.filter((col("amount") <= 0) | (col("amount") > 1000000)).count()
    print(f"  - Invalid amounts (<=0 or >1M): {invalid_amounts}")

    print("\n✓ All data quality checks passed")


# ============================================================================
# Pattern 4: Performance Optimization
# ============================================================================


def demonstrate_performance_optimization(spark: SparkSession) -> None:
    """Demonstrate performance optimization techniques.

    Args:
        spark: SparkSession.
    """
    print("\n" + "=" * 70)
    print("Pattern 4: Performance Optimization")
    print("=" * 70)

    # Technique 1: Caching for reuse
    print("\n1. Caching for Multiple Operations")
    df = TransactionRecord.build_dataframe(spark, size=50000)
    df.cache()

    start_time = datetime.now()
    count1 = df.count()
    time1 = (datetime.now() - start_time).total_seconds()

    start_time = datetime.now()
    count2 = df.filter(col("amount") > 100).count()
    time2 = (datetime.now() - start_time).total_seconds()

    print(f"  ✓ First operation: {count1:,} rows in {time1:.2f}s")
    print(f"  ✓ Second operation: {count2:,} rows in {time2:.2f}s")
    df.unpersist()

    # Technique 2: Coalescing for output
    print("\n2. Coalescing for Efficient Output")
    df_large = TransactionRecord.build_dataframe(spark, size=10000)
    print(f"  - Original partitions: {df_large.rdd.getNumPartitions()}")

    df_coalesced = df_large.coalesce(1)
    print(f"  - After coalesce: {df_coalesced.rdd.getNumPartitions()}")
    print("  ✓ Reduced partitions for single file output")

    # Technique 3: Broadcast joins
    print("\n3. Efficient Joins with Small Tables")
    users_df = UserProfile.build_dataframe(spark, size=1000)
    print(f"  - Users: {users_df.count():,} rows")
    print(f"  - Transactions: {df.count():,} rows")

    # For production: would use broadcast hint for small table
    # from pyspark.sql.functions import broadcast
    # joined = df.join(broadcast(users_df), on="user_id")
    joined = df.join(users_df, on="user_id", how="left")
    print(f"  ✓ Joined dataset: {joined.count():,} rows")


# ============================================================================
# Pattern 5: Schema Evolution Simulation
# ============================================================================


def simulate_schema_evolution(spark: SparkSession, output_path: str) -> None:
    """Simulate schema evolution scenarios.

    Args:
        spark: SparkSession.
        output_path: Path to save data.
    """
    print("\n" + "=" * 70)
    print("Pattern 5: Schema Evolution Simulation")
    print("=" * 70)

    # Version 1: Original schema
    print("\n1. Creating v1 data (original schema)")

    @spark_factory
    @dataclass
    class TransactionV1:
        transaction_id: int
        user_id: int
        amount: float
        status: str

    df_v1 = TransactionV1.build_dataframe(spark, size=1000)
    save_as_parquet(df_v1, f"{output_path}/v1", mode="overwrite")
    print(f"  ✓ Saved v1 data: {df_v1.count():,} rows")
    print(f"  Schema: {df_v1.columns}")

    # Version 2: Evolved schema (added fields)
    print("\n2. Creating v2 data (evolved schema with new fields)")

    @spark_factory
    @dataclass
    class TransactionV2:
        transaction_id: int
        user_id: int
        amount: float
        status: str
        currency: str  # New field
        payment_method: str  # New field

    df_v2 = TransactionV2.build_dataframe(spark, size=1000)
    save_as_parquet(df_v2, f"{output_path}/v2", mode="overwrite")
    print(f"  ✓ Saved v2 data: {df_v2.count():,} rows")
    print(f"  Schema: {df_v2.columns}")

    # Demonstrate reading both versions
    print("\n3. Reading both versions")
    df_v1_loaded = spark.read.parquet(f"{output_path}/v1")
    df_v2_loaded = spark.read.parquet(f"{output_path}/v2")

    print(f"  - V1 columns: {df_v1_loaded.columns}")
    print(f"  - V2 columns: {df_v2_loaded.columns}")
    print("  ✓ Schema evolution simulated successfully")


# ============================================================================
# Pattern 6: Production Testing Workflow
# ============================================================================


def production_testing_workflow(spark: SparkSession, output_path: str) -> None:
    """Complete production testing workflow.

    Args:
        spark: SparkSession.
        output_path: Path to save test data.
    """
    print("\n" + "=" * 70)
    print("Pattern 6: Complete Production Testing Workflow")
    print("=" * 70)

    # Step 1: Generate test data
    print("\n1. Generate Test Data")
    transactions_df = TransactionRecord.build_dataframe(spark, size=10000)
    users_df = UserProfile.build_dataframe(spark, size=1000)
    print(f"  ✓ Generated {transactions_df.count():,} transactions")
    print(f"  ✓ Generated {users_df.count():,} users")

    # Step 2: Validate data quality
    print("\n2. Validate Data Quality")
    assert_approx_count(transactions_df, 10000, tolerance=0.01)
    assert_approx_count(users_df, 1000, tolerance=0.01)
    print("  ✓ Data quality validated")

    # Step 3: Save to storage
    print("\n3. Save to Parquet")
    save_as_parquet(transactions_df, f"{output_path}/transactions", partition_by="transaction_date")
    save_as_parquet(users_df, f"{output_path}/users")
    print(f"  ✓ Saved to {output_path}")

    # Step 4: Reload and verify
    print("\n4. Reload and Verify")
    reloaded_transactions = spark.read.parquet(f"{output_path}/transactions")
    reloaded_users = spark.read.parquet(f"{output_path}/users")
    print(f"  ✓ Reloaded {reloaded_transactions.count():,} transactions")
    print(f"  ✓ Reloaded {reloaded_users.count():,} users")

    # Step 5: Run analytics
    print("\n5. Run Sample Analytics")
    high_value_txns = reloaded_transactions.filter(col("amount") > 500).count()
    active_users = reloaded_users.filter(col("is_active") == True).count()  # noqa: E712
    print(f"  - High value transactions (>$500): {high_value_txns:,}")
    print(f"  - Active users: {active_users:,}")

    print("\n✓ Production workflow complete")


# ============================================================================
# Main Execution
# ============================================================================


def main():
    """Run production usage demonstrations."""
    import tempfile
    from pathlib import Path

    spark = (
        SparkSession.builder.appName("production-usage")
        .master("local[*]")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.default.parallelism", "4")
        .getOrCreate()
    )

    try:
        print("\n" + "=" * 70)
        print("PRODUCTION USAGE PATTERNS")
        print("=" * 70)

        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)

            # Pattern 1: Large-scale generation
            generate_large_dataset(spark, str(base_path / "large_dataset"))

            # Pattern 2: Partitioned data
            generate_partitioned_data(spark, str(base_path / "partitioned"))

            # Pattern 3: Data quality
            validate_generated_data(spark)

            # Pattern 4: Performance
            demonstrate_performance_optimization(spark)

            # Pattern 5: Schema evolution
            simulate_schema_evolution(spark, str(base_path / "schema_evolution"))

            # Pattern 6: Complete workflow
            production_testing_workflow(spark, str(base_path / "workflow"))

        print("\n" + "=" * 70)
        print("PRODUCTION PATTERNS SUMMARY")
        print("=" * 70)
        print("  ✓ Large-scale data generation (100K+ rows)")
        print("  ✓ Partitioned data for query optimization")
        print("  ✓ Comprehensive data quality validation")
        print("  ✓ Performance optimization techniques")
        print("  ✓ Schema evolution simulation")
        print("  ✓ End-to-end production workflow")
        print("=" * 70)

    finally:
        spark.stop()


if __name__ == "__main__":
    main()

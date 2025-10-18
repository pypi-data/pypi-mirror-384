"""Testing patterns example for polyspark.

This example demonstrates how to use polyspark for testing Spark transformations,
including unit tests, integration tests, and test fixtures.
"""

from dataclasses import dataclass

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col
from pyspark.sql.functions import sum as spark_sum

from polyspark import spark_factory
from polyspark.testing import assert_schema_equal

# ============================================================================
# Models for Testing
# ============================================================================


@spark_factory
@dataclass
class Order:
    """Test model for orders."""

    order_id: int
    customer_id: int
    product_id: int
    quantity: int
    price: float
    status: str


@spark_factory
@dataclass
class Customer:
    """Test model for customers."""

    customer_id: int
    name: str
    email: str
    tier: str


@spark_factory
@dataclass
class Product:
    """Test model for products."""

    product_id: int
    name: str
    category: str
    price: float


# ============================================================================
# Functions to Test
# ============================================================================


def calculate_order_totals(orders_df: DataFrame) -> DataFrame:
    """Calculate total amount for each order.

    Args:
        orders_df: DataFrame with order data.

    Returns:
        DataFrame with order_id and total_amount columns.
    """
    return orders_df.withColumn("total_amount", col("quantity") * col("price")).select(
        "order_id", "customer_id", "total_amount"
    )


def get_customer_spending(orders_df: DataFrame) -> DataFrame:
    """Calculate total spending per customer.

    Args:
        orders_df: DataFrame with order totals.

    Returns:
        DataFrame with customer_id and total_spending.
    """
    return orders_df.groupBy("customer_id").agg(spark_sum("total_amount").alias("total_spending"))


def enrich_orders_with_customer_data(orders_df: DataFrame, customers_df: DataFrame) -> DataFrame:
    """Enrich orders with customer information.

    Args:
        orders_df: Orders DataFrame.
        customers_df: Customers DataFrame.

    Returns:
        Enriched DataFrame with customer name and tier.
    """
    return orders_df.join(
        customers_df.select("customer_id", "name", "tier"), on="customer_id", how="left"
    )


def filter_premium_customers(enriched_df: DataFrame, min_spending: float = 1000.0) -> DataFrame:
    """Filter for premium customers based on spending.

    Args:
        enriched_df: DataFrame with customer spending.
        min_spending: Minimum spending threshold.

    Returns:
        Filtered DataFrame.
    """
    return enriched_df.filter(col("total_spending") >= min_spending)


# ============================================================================
# Pattern 1: Basic Unit Tests
# ============================================================================


def test_calculate_order_totals(spark: SparkSession) -> None:
    """Unit test for calculate_order_totals function.

    Args:
        spark: SparkSession for testing.
    """
    print("\n" + "=" * 70)
    print("Pattern 1: Basic Unit Test")
    print("=" * 70)

    # Generate test data
    test_orders = Order.build_dataframe(spark, size=10)

    # Apply transformation
    result = calculate_order_totals(test_orders)

    # Assertions
    assert "total_amount" in result.columns, "total_amount column should be present"
    assert result.count() == 10, "Should have same number of rows as input"

    # Verify calculation
    sample_row = result.first()
    print("\n✓ Test passed: calculate_order_totals")
    print(f"  Sample result: order_id={sample_row.order_id}, total={sample_row.total_amount}")


# ============================================================================
# Pattern 2: Testing with Specific Test Data
# ============================================================================


def test_with_known_values(spark: SparkSession) -> None:
    """Test with specific known values.

    Args:
        spark: SparkSession for testing.
    """
    print("\n" + "=" * 70)
    print("Pattern 2: Testing with Known Values")
    print("=" * 70)

    # Generate test data
    dicts = Order.build_dicts(size=5)

    # Override with known values for testing
    dicts[0]["order_id"] = 1
    dicts[0]["quantity"] = 10
    dicts[0]["price"] = 5.5

    # Create DataFrame from modified dicts
    test_orders = Order.create_dataframe_from_dicts(spark, dicts)

    # Apply transformation
    result = calculate_order_totals(test_orders)

    # Verify specific calculation
    order_1 = result.filter(col("order_id") == 1).first()
    expected_total = 10 * 5.5
    actual_total = order_1.total_amount

    assert (
        abs(actual_total - expected_total) < 0.01
    ), f"Expected {expected_total}, got {actual_total}"

    print("\n✓ Test passed: Known value verification")
    print(f"  Expected total: {expected_total}")
    print(f"  Actual total: {actual_total}")


# ============================================================================
# Pattern 3: Integration Testing with Multiple DataFrames
# ============================================================================


def test_integration_workflow(spark: SparkSession) -> None:
    """Integration test for complete workflow.

    Args:
        spark: SparkSession for testing.
    """
    print("\n" + "=" * 70)
    print("Pattern 3: Integration Test")
    print("=" * 70)

    # Generate test data for multiple tables
    orders_df = Order.build_dataframe(spark, size=50)
    customers_df = Customer.build_dataframe(spark, size=10)

    # Execute workflow
    orders_with_totals = calculate_order_totals(orders_df)
    customer_spending = get_customer_spending(orders_with_totals)
    enriched = enrich_orders_with_customer_data(customer_spending, customers_df)
    premium_customers = filter_premium_customers(enriched, min_spending=500.0)

    # Assertions
    assert enriched.count() > 0, "Should have enriched data"
    assert "name" in enriched.columns, "Should have customer name"
    assert "tier" in enriched.columns, "Should have customer tier"

    print("\n✓ Integration test passed")
    print(f"  Total customers: {customer_spending.count()}")
    print(f"  Enriched records: {enriched.count()}")
    print(f"  Premium customers: {premium_customers.count()}")

    # Show sample results
    print("\n  Sample premium customers:")
    premium_customers.select("customer_id", "name", "total_spending").show(5)


# ============================================================================
# Pattern 4: Schema Validation
# ============================================================================


def test_schema_validation(spark: SparkSession) -> None:
    """Test schema validation for transformations.

    Args:
        spark: SparkSession for testing.
    """
    print("\n" + "=" * 70)
    print("Pattern 4: Schema Validation")
    print("=" * 70)

    # Generate test data
    orders_df = Order.build_dataframe(spark, size=10)

    # Apply transformation
    result = calculate_order_totals(orders_df)

    # Validate output schema has expected fields
    assert "order_id" in result.columns
    assert "customer_id" in result.columns
    assert "total_amount" in result.columns

    print("\n✓ Schema validation passed")
    print(f"  Input columns: {orders_df.columns}")
    print(f"  Output columns: {result.columns}")


# ============================================================================
# Pattern 5: Testing Edge Cases
# ============================================================================


def test_edge_cases(spark: SparkSession) -> None:
    """Test edge cases and boundary conditions.

    Args:
        spark: SparkSession for testing.
    """
    print("\n" + "=" * 70)
    print("Pattern 5: Edge Cases")
    print("=" * 70)

    # Test with empty DataFrame
    empty_df = Order.build_dataframe(spark, size=0)
    result_empty = calculate_order_totals(empty_df)
    assert result_empty.count() == 0, "Empty input should produce empty output"
    print("  ✓ Empty DataFrame test passed")

    # Test with single row
    single_df = Order.build_dataframe(spark, size=1)
    result_single = calculate_order_totals(single_df)
    assert result_single.count() == 1, "Single row should produce single row"
    print("  ✓ Single row test passed")

    # Test with large dataset
    large_df = Order.build_dataframe(spark, size=10000)
    result_large = calculate_order_totals(large_df)
    assert result_large.count() == 10000, "Large dataset should maintain row count"
    print("  ✓ Large dataset test passed")


# ============================================================================
# Pattern 6: Testing DataFrame Equality
# ============================================================================


def test_dataframe_equality(spark: SparkSession) -> None:
    """Test DataFrame equality for idempotent operations.

    Args:
        spark: SparkSession for testing.
    """
    print("\n" + "=" * 70)
    print("Pattern 6: DataFrame Equality")
    print("=" * 70)

    # Generate test data
    orders_df = Order.build_dataframe(spark, size=20)

    # Apply transformation twice
    result1 = calculate_order_totals(orders_df)
    result2 = calculate_order_totals(orders_df)

    # Schemas should be equal
    assert_schema_equal(result1.schema, result2.schema)
    print("  ✓ Schema equality test passed")

    # Cache for reuse
    orders_df.cache()
    result3 = calculate_order_totals(orders_df)
    assert_schema_equal(result1.schema, result3.schema)
    print("  ✓ Cached DataFrame test passed")


# ============================================================================
# Pattern 7: Fixture Pattern
# ============================================================================


class TestFixtures:
    """Reusable test fixtures."""

    @staticmethod
    def setup_test_data(spark: SparkSession) -> tuple:
        """Create reusable test datasets.

        Args:
            spark: SparkSession for testing.

        Returns:
            Tuple of (orders_df, customers_df, products_df).
        """
        orders_df = Order.build_dataframe(spark, size=100)
        customers_df = Customer.build_dataframe(spark, size=20)
        products_df = Product.build_dataframe(spark, size=50)

        return orders_df, customers_df, products_df


def test_with_fixtures(spark: SparkSession) -> None:
    """Test using fixtures.

    Args:
        spark: SparkSession for testing.
    """
    print("\n" + "=" * 70)
    print("Pattern 7: Test Fixtures")
    print("=" * 70)

    # Setup test data using fixture
    orders_df, customers_df, products_df = TestFixtures.setup_test_data(spark)

    # Run tests
    result = calculate_order_totals(orders_df)
    assert result.count() == 100

    enriched = enrich_orders_with_customer_data(result, customers_df)
    assert "name" in enriched.columns

    print("\n✓ Fixture pattern test passed")
    print(f"  Orders: {orders_df.count()}")
    print(f"  Customers: {customers_df.count()}")
    print(f"  Products: {products_df.count()}")


# ============================================================================
# Main Execution
# ============================================================================


def main():
    """Run all test patterns."""
    # Create Spark session
    spark = (
        SparkSession.builder.appName("testing-patterns")
        .master("local[*]")
        .config("spark.sql.shuffle.partitions", "2")
        .getOrCreate()
    )

    try:
        print("\n" + "=" * 70)
        print("POLYSPARK TESTING PATTERNS DEMO")
        print("=" * 70)

        # Run all test patterns
        test_calculate_order_totals(spark)
        test_with_known_values(spark)
        test_integration_workflow(spark)
        test_schema_validation(spark)
        test_edge_cases(spark)
        test_dataframe_equality(spark)
        test_with_fixtures(spark)

        print("\n" + "=" * 70)
        print("ALL TESTS PASSED ✓")
        print("=" * 70)

    finally:
        spark.stop()


if __name__ == "__main__":
    main()

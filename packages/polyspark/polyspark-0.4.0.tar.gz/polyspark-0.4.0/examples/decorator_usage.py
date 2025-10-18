"""Examples using the @spark_factory decorator for simplified usage."""

from dataclasses import dataclass
from typing import List, Optional

from polyspark import spark_factory

# Note: You need to have PySpark installed to run DataFrame examples
# pip install pyspark

try:
    from pyspark.sql import SparkSession

    # ========================================================================
    # Example 1: Simple dataclass with decorator
    # ========================================================================

    @spark_factory
    @dataclass
    class User:
        """User model with decorator - no separate factory class needed!"""

        id: int
        username: str
        email: str
        age: int

    def example_simple_decorator():
        """Generate DataFrame using decorated class directly."""
        spark = (
            SparkSession.builder.appName("polyspark-decorator-example")
            .master("local[*]")
            .getOrCreate()
        )

        # Use methods directly on the class!
        df = User.build_dataframe(spark, size=20)

        print("Generated DataFrame using decorated class:")
        df.show(10)
        print(f"Total rows: {df.count()}")

        spark.stop()

    # ========================================================================
    # Example 2: Comparison with traditional approach
    # ========================================================================

    # OLD WAY: Requires two class definitions
    from polyspark import SparkFactory

    @dataclass
    class Product:
        product_id: int
        name: str
        price: float

    class ProductFactory(SparkFactory[Product]):
        __model__ = Product

    # NEW WAY: Just one decorator!
    @spark_factory
    @dataclass
    class ProductNew:
        product_id: int
        name: str
        price: float

    def example_comparison():
        """Compare old and new approaches."""
        spark = (
            SparkSession.builder.appName("polyspark-decorator-example")
            .master("local[*]")
            .getOrCreate()
        )

        # Old way - two classes
        df_old = ProductFactory.build_dataframe(spark, size=10)
        print("Old way (factory class):")
        df_old.show(5)

        # New way - decorator
        df_new = ProductNew.build_dataframe(spark, size=10)
        print("\nNew way (decorator):")
        df_new.show(5)

        spark.stop()

    # ========================================================================
    # Example 3: Complex types with decorator
    # ========================================================================

    @spark_factory
    @dataclass
    class Address:
        street: str
        city: str
        state: str
        zipcode: str

    @spark_factory
    @dataclass
    class Employee:
        employee_id: int
        name: str
        department: str
        skills: List[str]  # Array
        address: Address  # Nested struct
        manager_id: Optional[int]  # Optional field

    def example_complex_types():
        """Use decorator with complex nested types."""
        spark = (
            SparkSession.builder.appName("polyspark-decorator-example")
            .master("local[*]")
            .getOrCreate()
        )

        # Generate employees with nested addresses
        df = Employee.build_dataframe(spark, size=15)

        print("Generated Employees with nested data:")
        df.show(5, truncate=False)

        print("\nSchema:")
        df.printSchema()

        # Access nested fields
        print("\nAccessing nested address fields:")
        df.select("name", "address.city", "address.state").show(5)

        spark.stop()

    # ========================================================================
    # Example 4: Generate dicts without PySpark
    # ========================================================================

    def example_without_spark():
        """Generate data without needing SparkSession."""
        # No SparkSession needed!
        user_dicts = User.build_dicts(size=5)

        print("Generated user dictionaries (no Spark needed):")
        for i, user in enumerate(user_dicts, 1):
            print(f"{i}. {user}")

        # Later, when you have Spark, convert to DataFrame
        print("\n(You can convert these to DataFrame later with create_dataframe_from_dicts)")

    # ========================================================================
    # Example 5: Pydantic models with decorator
    # ========================================================================

    def example_with_pydantic():
        """Use decorator with Pydantic models."""
        try:
            from pydantic import BaseModel, Field

            @spark_factory
            class Order(BaseModel):
                """Order model using Pydantic."""

                order_id: int = Field(gt=0)
                customer_name: str
                total: float = Field(gt=0)
                items: List[str]
                notes: Optional[str] = None

            spark = (
                SparkSession.builder.appName("polyspark-decorator-example")
                .master("local[*]")
                .getOrCreate()
            )

            # Generate orders
            df = Order.build_dataframe(spark, size=10)

            print("Generated Orders from Pydantic model:")
            df.show(5, truncate=False)
            print("\nSchema:")
            df.printSchema()

            spark.stop()

        except ImportError:
            print("Pydantic not installed. Install with: pip install pydantic")

    # ========================================================================
    # Example 6: Multiple decorated classes
    # ========================================================================

    @spark_factory
    @dataclass
    class Customer:
        customer_id: int
        name: str
        email: str

    @spark_factory
    @dataclass
    class Order:
        order_id: int
        customer_id: int
        product_name: str
        quantity: int
        price: float

    def example_multiple_models():
        """Use multiple decorated models together."""
        spark = (
            SparkSession.builder.appName("polyspark-decorator-example")
            .master("local[*]")
            .getOrCreate()
        )

        # Generate customers and orders
        customers_df = Customer.build_dataframe(spark, size=50)
        orders_df = Order.build_dataframe(spark, size=200)

        print(f"Generated {customers_df.count()} customers")
        print(f"Generated {orders_df.count()} orders")

        # You can join them!
        joined = orders_df.join(
            customers_df, orders_df.customer_id == customers_df.customer_id, "left"
        )

        print("\nJoined data sample:")
        joined.select(
            "order_id", customers_df.name.alias("customer_name"), "product_name", "price"
        ).show(10)

        spark.stop()

    # ========================================================================
    # Example 7: Testing workflow
    # ========================================================================

    @spark_factory
    @dataclass
    class Transaction:
        transaction_id: int
        amount: float
        status: str

    def my_spark_job(df):
        """Example Spark transformation to test."""
        from pyspark.sql.functions import col, when

        return df.withColumn(
            "risk_level",
            when(col("amount") > 1000, "high").when(col("amount") > 500, "medium").otherwise("low"),
        )

    def example_testing():
        """Use decorator for testing Spark jobs."""
        spark = (
            SparkSession.builder.appName("polyspark-decorator-example")
            .master("local[*]")
            .getOrCreate()
        )

        # Generate test data easily
        test_df = Transaction.build_dataframe(spark, size=100)

        # Run your job
        result_df = my_spark_job(test_df)

        print("Testing Spark job with generated data:")
        result_df.show(10)

        # Validate results
        assert "risk_level" in result_df.columns
        print("✓ Test passed!")

        spark.stop()

    # ========================================================================
    # Main execution
    # ========================================================================

    if __name__ == "__main__":
        print("=" * 80)
        print("Example 1: Simple Decorator Usage")
        print("=" * 80)
        example_simple_decorator()

        print("\n" + "=" * 80)
        print("Example 2: Comparison - Old vs New")
        print("=" * 80)
        example_comparison()

        print("\n" + "=" * 80)
        print("Example 3: Complex Types")
        print("=" * 80)
        example_complex_types()

        print("\n" + "=" * 80)
        print("Example 4: Without Spark")
        print("=" * 80)
        example_without_spark()

        print("\n" + "=" * 80)
        print("Example 5: Pydantic Models")
        print("=" * 80)
        example_with_pydantic()

        print("\n" + "=" * 80)
        print("Example 6: Multiple Models")
        print("=" * 80)
        example_multiple_models()

        print("\n" + "=" * 80)
        print("Example 7: Testing Workflow")
        print("=" * 80)
        example_testing()

        print("\n" + "=" * 80)
        print("All examples completed!")
        print("=" * 80)

except ImportError:
    print("PySpark is not installed. Install it with: pip install pyspark")
    print("\nYou can still use the decorator to generate dictionaries:")

    @spark_factory
    @dataclass
    class User:
        id: int
        name: str
        email: str

    # This works without PySpark!
    user_dicts = User.build_dicts(size=5)
    print("\nGenerated user dictionaries (no PySpark needed):")
    for i, user in enumerate(user_dicts, 1):
        print(f"{i}. {user}")

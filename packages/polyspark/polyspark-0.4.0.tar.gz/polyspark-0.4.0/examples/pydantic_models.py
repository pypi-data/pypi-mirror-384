"""Example using Pydantic models."""

from typing import Optional

from polyspark import spark_factory

# Note: You need to have PySpark and Pydantic installed to run this example
# pip install pyspark pydantic

try:
    from pydantic import BaseModel, Field
    from pyspark.sql import SparkSession

    # Define your data model using Pydantic with @spark_factory decorator
    # Note: Pydantic models require the decorator, not SparkFactory directly
    @spark_factory
    class User(BaseModel):
        """User model with Pydantic validation."""

        id: int = Field(gt=0, description="User ID")
        username: str = Field(min_length=3, max_length=20)
        email: str  # Using str instead of EmailStr for simplicity
        full_name: Optional[str] = None
        is_active: bool = True

    @spark_factory
    class Product(BaseModel):
        """Product model."""

        product_id: int
        name: str
        description: Optional[str] = None
        price: float = Field(gt=0)
        in_stock: bool

    def example_pydantic_users():
        """Generate DataFrame from Pydantic model."""
        spark = (
            SparkSession.builder.appName("polyspark-pydantic-example")
            .master("local[*]")
            .getOrCreate()
        )

        # Generate users using the decorated class
        df = User.build_dataframe(spark, size=20)

        print("Generated Users DataFrame:")
        df.show(10, truncate=False)
        print("\nSchema:")
        df.printSchema()

        # Note: full_name is optional, so it will be nullable in the schema
        full_name_field = df.schema["full_name"]
        print(f"\nfull_name nullable: {full_name_field.nullable}")

        spark.stop()

    def example_pydantic_products():
        """Generate DataFrame with products."""
        spark = (
            SparkSession.builder.appName("polyspark-pydantic-example")
            .master("local[*]")
            .getOrCreate()
        )

        # Generate products using the decorated class
        df = Product.build_dataframe(spark, size=15)

        print("Generated Products DataFrame:")
        df.show(10, truncate=False)
        print(f"\nTotal products: {df.count()}")

        # Query the data
        expensive_products = df.filter(df.price > 50)
        print(f"Expensive products (price > 50): {expensive_products.count()}")

        spark.stop()

    if __name__ == "__main__":
        print("=" * 80)
        print("Example 1: Pydantic User Model")
        print("=" * 80)
        example_pydantic_users()

        print("\n" + "=" * 80)
        print("Example 2: Pydantic Product Model")
        print("=" * 80)
        example_pydantic_products()

except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install pyspark pydantic")

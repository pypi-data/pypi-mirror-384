"""Basic usage example with dataclasses."""

from dataclasses import dataclass

from polyspark import SparkFactory, build_spark_dataframe

# Note: You need to have PySpark installed to run this example
# pip install pyspark

try:
    from pyspark.sql import SparkSession

    # Define your data model using a dataclass
    @dataclass
    class User:
        id: int
        name: str
        email: str
        age: int

    # Method 1: Using SparkFactory class
    class UserFactory(SparkFactory[User]):
        __model__ = User

    def example_with_factory():
        """Generate DataFrame using factory class."""
        spark = (
            SparkSession.builder.appName("polyspark-basic-example").master("local[*]").getOrCreate()
        )

        # Generate a DataFrame with 50 users
        df = UserFactory.build_dataframe(spark, size=50)

        print("Generated DataFrame with factory:")
        df.show(10)
        print(f"Total rows: {df.count()}")
        print(f"Schema: {df.schema}")

        spark.stop()

    # Method 2: Using convenience function
    def example_with_function():
        """Generate DataFrame using convenience function."""
        spark = (
            SparkSession.builder.appName("polyspark-basic-example").master("local[*]").getOrCreate()
        )

        # Generate a DataFrame with 30 users
        df = build_spark_dataframe(User, spark, size=30)

        print("Generated DataFrame with function:")
        df.show(10)

        spark.stop()

    # Method 3: Generate data without PySpark, convert later
    def example_deferred_conversion():
        """Generate data as dicts first, convert to DataFrame later."""
        # Generate data without needing PySpark
        user_dicts = UserFactory.build_dicts(size=20)

        print("Generated user dictionaries:")
        for user in user_dicts[:3]:
            print(user)

        # Later, when you have a SparkSession, convert to DataFrame
        spark = (
            SparkSession.builder.appName("polyspark-basic-example").master("local[*]").getOrCreate()
        )

        df = UserFactory.create_dataframe_from_dicts(spark, user_dicts)

        print("\nConverted to DataFrame:")
        df.show(5)

        spark.stop()

    if __name__ == "__main__":
        print("=" * 80)
        print("Example 1: Using Factory Class")
        print("=" * 80)
        example_with_factory()

        print("\n" + "=" * 80)
        print("Example 2: Using Convenience Function")
        print("=" * 80)
        example_with_function()

        print("\n" + "=" * 80)
        print("Example 3: Deferred Conversion")
        print("=" * 80)
        example_deferred_conversion()

except ImportError:
    print("PySpark is not installed. Install it with: pip install pyspark")
    print("You can still use build_dicts() to generate data without PySpark:")

    @dataclass
    class User:
        id: int
        name: str
        email: str
        age: int

    class UserFactory(SparkFactory[User]):
        __model__ = User

    # This works without PySpark
    user_dicts = UserFactory.build_dicts(size=5)
    print("\nGenerated user dictionaries (no PySpark needed):")
    for user in user_dicts:
        print(user)

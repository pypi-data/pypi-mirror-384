"""Example with complex types: arrays, maps, and nested structs."""

from dataclasses import dataclass
from typing import Dict, List, Optional

from polyspark import SparkFactory

try:
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import col, explode

    # Nested struct example
    @dataclass
    class Address:
        street: str
        city: str
        state: str
        zipcode: str

    @dataclass
    class Contact:
        email: str
        phone: Optional[str]

    # Complex model with arrays and nested structs
    @dataclass
    class Employee:
        employee_id: int
        name: str
        department: str
        skills: List[str]  # Array type
        address: Address  # Nested struct
        contact: Contact  # Another nested struct
        projects: List[str]  # Another array

    # Model with map type
    @dataclass
    class Product:
        product_id: int
        name: str
        attributes: Dict[str, str]  # Map type
        tags: List[str]  # Array type
        prices_by_region: Dict[str, float]  # Map with different value type

    # Deeply nested example
    @dataclass
    class Department:
        dept_id: int
        dept_name: str

    @dataclass
    class Project:
        project_id: int
        project_name: str
        department: Department

    @dataclass
    class EmployeeWithProjects:
        employee_id: int
        name: str
        projects: List[Project]  # Array of structs

    # Create factories
    class EmployeeFactory(SparkFactory[Employee]):
        __model__ = Employee

    class ProductFactory(SparkFactory[Product]):
        __model__ = Product

    class EmployeeWithProjectsFactory(SparkFactory[EmployeeWithProjects]):
        __model__ = EmployeeWithProjects

    def example_nested_structs():
        """Generate DataFrame with nested structs."""
        spark = (
            SparkSession.builder.appName("polyspark-complex-example")
            .master("local[*]")
            .getOrCreate()
        )

        df = EmployeeFactory.build_dataframe(spark, size=10)

        print("Generated Employees with nested data:")
        df.show(5, truncate=False)

        print("\nSchema:")
        df.printSchema()

        # Access nested fields
        print("\nAccessing nested address fields:")
        df.select("name", "address.city", "address.state").show(5)

        # Explode array fields
        print("\nExploding skills array:")
        df.select("name", explode("skills").alias("skill")).show(10)

        spark.stop()

    def example_map_types():
        """Generate DataFrame with map types."""
        spark = (
            SparkSession.builder.appName("polyspark-complex-example")
            .master("local[*]")
            .getOrCreate()
        )

        df = ProductFactory.build_dataframe(spark, size=10)

        print("Generated Products with maps:")
        df.show(5, truncate=False)

        print("\nSchema:")
        df.printSchema()

        # Access map fields
        print("\nAccessing map values:")
        df.select("name", col("prices_by_region")["US"].alias("us_price")).show(5)

        spark.stop()

    def example_array_of_structs():
        """Generate DataFrame with array of structs."""
        spark = (
            SparkSession.builder.appName("polyspark-complex-example")
            .master("local[*]")
            .getOrCreate()
        )

        df = EmployeeWithProjectsFactory.build_dataframe(spark, size=5)

        print("Generated Employees with project arrays:")
        df.show(3, truncate=False)

        print("\nSchema:")
        df.printSchema()

        # Explode array of structs
        print("\nExploding projects array:")
        projects_df = df.select("name", explode("projects").alias("project"))
        projects_df.select("name", "project.project_name", "project.department.dept_name").show(10)

        spark.stop()

    if __name__ == "__main__":
        print("=" * 80)
        print("Example 1: Nested Structs and Arrays")
        print("=" * 80)
        example_nested_structs()

        print("\n" + "=" * 80)
        print("Example 2: Map Types")
        print("=" * 80)
        example_map_types()

        print("\n" + "=" * 80)
        print("Example 3: Array of Structs")
        print("=" * 80)
        example_array_of_structs()

except ImportError:
    print("PySpark is not installed. Install it with: pip install pyspark")

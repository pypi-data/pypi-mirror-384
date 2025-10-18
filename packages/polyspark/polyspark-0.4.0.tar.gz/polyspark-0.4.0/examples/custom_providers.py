"""Custom providers example for polyspark.

This example demonstrates how to create custom data providers for more realistic
and domain-specific test data generation.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

from polyfactory.factories import DataclassFactory
from pyspark.sql import SparkSession

from polyspark import SparkFactory

# ============================================================================
# Example 1: Custom Email Provider
# ============================================================================


@dataclass
class User:
    """User model."""

    user_id: int
    username: str
    email: str
    first_name: str
    last_name: str
    is_active: bool


class CustomUserFactory(SparkFactory[User]):
    """Custom factory with email generation based on username."""

    __model__ = User

    @classmethod
    def email(cls) -> str:
        """Generate email based on username pattern.

        Returns:
            Email address.
        """
        # Generate a simple username for the email
        import random
        import string

        username = "".join(random.choices(string.ascii_lowercase, k=8))
        domains = ["example.com", "test.com", "demo.org"]
        domain = random.choice(domains)
        return f"{username}@{domain}"


# ============================================================================
# Example 2: Realistic Address Provider
# ============================================================================


@dataclass
class Address:
    """Address model."""

    street: str
    city: str
    state: str
    zipcode: str
    country: str


@dataclass
class Customer:
    """Customer with address."""

    customer_id: int
    name: str
    address: Address


class RealisticAddressFactory(DataclassFactory[Address]):
    """Factory with realistic US addresses."""

    __model__ = Address

    # Realistic US cities and states
    US_CITIES = {
        "CA": ["Los Angeles", "San Francisco", "San Diego", "Sacramento"],
        "NY": ["New York", "Buffalo", "Rochester", "Albany"],
        "TX": ["Houston", "Dallas", "Austin", "San Antonio"],
        "FL": ["Miami", "Orlando", "Tampa", "Jacksonville"],
        "IL": ["Chicago", "Springfield", "Naperville", "Peoria"],
    }

    @classmethod
    def state(cls) -> str:
        """Generate realistic US state code."""
        import random

        return random.choice(list(cls.US_CITIES.keys()))

    @classmethod
    def city(cls) -> str:
        """Generate city matching the state."""
        import random

        state = random.choice(list(cls.US_CITIES.keys()))
        return random.choice(cls.US_CITIES[state])

    @classmethod
    def zipcode(cls) -> str:
        """Generate realistic US zipcode."""
        import random

        return f"{random.randint(10000, 99999)}"

    @classmethod
    def country(cls) -> str:
        """Always return USA for this factory."""
        return "USA"


class CustomCustomerFactory(SparkFactory[Customer]):
    """Customer factory with realistic addresses."""

    __model__ = Customer

    # Use our custom address factory
    address = RealisticAddressFactory


# ============================================================================
# Example 3: Related Data Provider
# ============================================================================


@dataclass
class Order:
    """Order model."""

    order_id: int
    customer_id: int
    product_ids: List[int]
    order_date: str
    total_amount: float
    status: str


class RelatedOrderFactory(SparkFactory[Order]):
    """Factory that generates related data."""

    __model__ = Order

    # Keep track of generated customer IDs for consistency
    _customer_ids: List[int] = []

    @classmethod
    def customer_id(cls) -> int:
        """Generate customer ID from a limited pool for realistic relationships."""
        import random

        if not cls._customer_ids:
            # Generate a pool of customer IDs
            cls._customer_ids = list(range(1, 51))  # 50 customers

        return random.choice(cls._customer_ids)

    @classmethod
    def product_ids(cls) -> List[int]:
        """Generate 1-5 product IDs from a realistic pool."""
        import random

        product_pool = list(range(1, 101))  # 100 products
        num_products = random.randint(1, 5)
        return random.sample(product_pool, num_products)

    @classmethod
    def order_date(cls) -> str:
        """Generate order date in last 90 days."""
        import random

        days_ago = random.randint(0, 90)
        order_date = datetime.now() - timedelta(days=days_ago)
        return order_date.strftime("%Y-%m-%d")

    @classmethod
    def status(cls) -> str:
        """Generate realistic order status with distribution."""
        import random

        # Weighted status distribution (more completed orders)
        statuses = ["completed"] * 7 + ["pending"] * 2 + ["cancelled"] * 1
        return random.choice(statuses)

    @classmethod
    def total_amount(cls) -> float:
        """Generate realistic order total."""
        import random

        # Most orders between $10-$500, some higher
        if random.random() < 0.9:
            return round(random.uniform(10.0, 500.0), 2)
        else:
            return round(random.uniform(500.0, 5000.0), 2)


# ============================================================================
# Example 4: Time-Series Data Provider
# ============================================================================


@dataclass
class Metric:
    """Time-series metric model."""

    timestamp: str
    metric_name: str
    value: float
    tags: List[str]


class TimeSeriesMetricFactory(SparkFactory[Metric]):
    """Factory for time-series metrics."""

    __model__ = Metric

    _base_timestamp = datetime.now() - timedelta(days=7)
    _interval_seconds = 300  # 5 minutes

    @classmethod
    def timestamp(cls) -> str:
        """Generate sequential timestamps."""
        import random

        # Add some variation to intervals
        offset_seconds = random.randint(0, 3600 * 24 * 7)  # Within past week
        ts = cls._base_timestamp + timedelta(seconds=offset_seconds)
        return ts.isoformat()

    @classmethod
    def metric_name(cls) -> str:
        """Generate realistic metric names."""
        import random

        metrics = [
            "cpu_usage_percent",
            "memory_usage_bytes",
            "disk_io_ops",
            "network_throughput_mbps",
            "request_count",
            "error_rate",
            "response_time_ms",
        ]
        return random.choice(metrics)

    @classmethod
    def value(cls) -> float:
        """Generate realistic metric values."""
        import random

        # Value ranges depend on metric type
        return round(random.uniform(0.0, 100.0), 2)

    @classmethod
    def tags(cls) -> List[str]:
        """Generate realistic tags."""
        import random

        environments = ["prod", "staging", "dev"]
        regions = ["us-east-1", "us-west-2", "eu-west-1"]
        services = ["api", "web", "worker", "database"]

        return [
            f"env:{random.choice(environments)}",
            f"region:{random.choice(regions)}",
            f"service:{random.choice(services)}",
        ]


# ============================================================================
# Example 5: Constrained Data Provider
# ============================================================================


@dataclass
class Employee:
    """Employee model with business constraints."""

    employee_id: int
    name: str
    department: str
    role: str
    salary: float
    hire_date: str
    manager_id: Optional[int]


class ConstrainedEmployeeFactory(SparkFactory[Employee]):
    """Factory with business logic constraints."""

    __model__ = Employee

    # Department-role-salary mappings
    DEPT_ROLES = {
        "Engineering": {
            "Junior Developer": (60000, 80000),
            "Senior Developer": (90000, 130000),
            "Staff Engineer": (130000, 180000),
            "Engineering Manager": (140000, 200000),
        },
        "Sales": {
            "Sales Rep": (50000, 70000),
            "Senior Sales": (70000, 100000),
            "Sales Manager": (100000, 150000),
        },
        "Marketing": {
            "Marketing Coordinator": (50000, 65000),
            "Marketing Manager": (80000, 120000),
        },
    }

    @classmethod
    def department(cls) -> str:
        """Generate department."""
        import random

        return random.choice(list(cls.DEPT_ROLES.keys()))

    @classmethod
    def role(cls) -> str:
        """Generate role that matches department."""
        import random

        dept = random.choice(list(cls.DEPT_ROLES.keys()))
        return random.choice(list(cls.DEPT_ROLES[dept].keys()))

    @classmethod
    def salary(cls) -> float:
        """Generate salary appropriate for role."""
        import random

        # Pick a department and role
        dept = random.choice(list(cls.DEPT_ROLES.keys()))
        role = random.choice(list(cls.DEPT_ROLES[dept].keys()))
        min_salary, max_salary = cls.DEPT_ROLES[dept][role]

        return round(random.uniform(min_salary, max_salary), 2)

    @classmethod
    def hire_date(cls) -> str:
        """Generate hire date (1-10 years ago)."""
        import random

        days_ago = random.randint(365, 3650)
        hire_date = datetime.now() - timedelta(days=days_ago)
        return hire_date.strftime("%Y-%m-%d")

    @classmethod
    def manager_id(cls) -> Optional[int]:
        """Generate manager ID (some employees have no manager)."""
        import random

        # 20% chance of no manager (senior leadership)
        if random.random() < 0.2:
            return None

        # Manager ID from a pool
        return random.randint(1, 50)


# ============================================================================
# Demonstration
# ============================================================================


def main():
    """Demonstrate custom providers."""
    spark = (
        SparkSession.builder.appName("custom-providers")
        .master("local[*]")
        .config("spark.sql.shuffle.partitions", "2")
        .getOrCreate()
    )

    try:
        print("\n" + "=" * 70)
        print("CUSTOM PROVIDERS DEMO")
        print("=" * 70)

        # Example 1: Custom email generation
        print("\n1. Custom Email Provider")
        print("-" * 70)
        users_df = CustomUserFactory.build_dataframe(spark, size=5)
        users_df.select("username", "email").show(5, truncate=False)

        # Example 2: Realistic addresses
        print("\n2. Realistic Address Provider")
        print("-" * 70)
        customers_df = CustomCustomerFactory.build_dataframe(spark, size=5)
        customers_df.select("name", "address.city", "address.state", "address.zipcode").show(
            5, truncate=False
        )

        # Example 3: Related data
        print("\n3. Related Data Provider")
        print("-" * 70)
        orders_df = RelatedOrderFactory.build_dataframe(spark, size=10)
        orders_df.select("order_id", "customer_id", "order_date", "total_amount", "status").show(
            10, truncate=False
        )
        print(f"Unique customers in orders: {orders_df.select('customer_id').distinct().count()}")

        # Example 4: Time-series metrics
        print("\n4. Time-Series Data Provider")
        print("-" * 70)
        metrics_df = TimeSeriesMetricFactory.build_dataframe(spark, size=10)
        metrics_df.select("timestamp", "metric_name", "value").show(10, truncate=False)

        # Example 5: Constrained business data
        print("\n5. Constrained Data Provider")
        print("-" * 70)
        employees_df = ConstrainedEmployeeFactory.build_dataframe(spark, size=10)
        employees_df.select("name", "department", "role", "salary").show(10, truncate=False)

        # Show salary distribution by department
        print("\nSalary statistics by department:")
        from pyspark.sql.functions import avg, max, min

        employees_df.groupBy("department").agg(
            avg("salary").alias("avg_salary"),
            min("salary").alias("min_salary"),
            max("salary").alias("max_salary"),
        ).show()

        print("\n" + "=" * 70)
        print("Custom providers allow you to:")
        print("  ✓ Generate realistic domain-specific data")
        print("  ✓ Maintain relationships between entities")
        print("  ✓ Enforce business constraints")
        print("  ✓ Create time-series data")
        print("  ✓ Control data distributions")
        print("=" * 70)

    finally:
        spark.stop()


if __name__ == "__main__":
    main()

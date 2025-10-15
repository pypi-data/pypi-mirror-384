"""Pytest configuration and fixtures."""

import pytest

try:
    from pyspark.sql import SparkSession

    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False


@pytest.fixture(scope="session")
def spark_session():
    """Create a SparkSession for the entire test session."""
    if not PYSPARK_AVAILABLE:
        pytest.skip("PySpark not available")

    spark = (
        SparkSession.builder.appName("polyspark-tests")
        .master("local[1]")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.shuffle.partitions", "1")
        .config("spark.driver.host", "localhost")
        .getOrCreate()
    )

    yield spark

    spark.stop()


@pytest.fixture
def spark(spark_session):
    """Provide SparkSession to individual tests."""
    return spark_session

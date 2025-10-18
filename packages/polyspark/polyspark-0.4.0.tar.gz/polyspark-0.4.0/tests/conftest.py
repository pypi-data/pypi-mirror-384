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

    # Stop any existing sessions first to ensure clean state
    try:
        active_session = SparkSession.getActiveSession()
        if active_session:
            active_session.stop()
    except Exception:
        pass

    spark = (
        SparkSession.builder.appName("polyspark-tests")
        .master("local[1]")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.shuffle.partitions", "1")
        .config("spark.driver.host", "localhost")
        .getOrCreate()
    )

    yield spark

    # Clean up at the very end of the test session
    try:
        spark.stop()
    except Exception:
        pass


@pytest.fixture
def spark(spark_session):
    """Provide SparkSession to individual tests."""
    return spark_session

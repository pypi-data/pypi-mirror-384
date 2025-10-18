"""Tests for I/O module."""

import tempfile
from dataclasses import dataclass
from pathlib import Path

import pytest

from polyspark import spark_factory
from polyspark.io import (
    DataIOError,
    load_and_validate,
    load_csv,
    load_dicts_from_json,
    load_json,
    load_parquet,
    save_as_csv,
    save_as_json,
    save_as_parquet,
    save_dicts_as_json,
)

try:
    import pyspark  # noqa: F401

    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False

pytestmark = pytest.mark.skipif(not PYSPARK_AVAILABLE, reason="PySpark not installed")


@spark_factory
@dataclass
class TestData:
    """Test model for I/O tests."""

    id: int
    name: str
    value: float


class TestSaveAsParquet:
    """Tests for save_as_parquet function."""

    def test_save_parquet_basic(self, spark):
        """Test basic parquet save."""
        df = TestData.build_dataframe(spark, size=10)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "data.parquet"
            save_as_parquet(df, str(output_path))

            assert output_path.exists()
            # Verify we can read it back
            df_loaded = spark.read.parquet(str(output_path))
            assert df_loaded.count() == 10

    def test_save_parquet_with_partitioning(self, spark):
        """Test parquet save with partitioning."""
        df = TestData.build_dataframe(spark, size=20)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "partitioned.parquet"
            save_as_parquet(df, str(output_path), partition_by="id")

            assert output_path.exists()

    def test_save_parquet_append_mode(self, spark):
        """Test parquet save in append mode."""
        df1 = TestData.build_dataframe(spark, size=5)
        df2 = TestData.build_dataframe(spark, size=5)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "append.parquet"

            save_as_parquet(df1, str(output_path), mode="overwrite")
            save_as_parquet(df2, str(output_path), mode="append")

            df_loaded = spark.read.parquet(str(output_path))
            assert df_loaded.count() == 10


class TestSaveAsJSON:
    """Tests for save_as_json function."""

    def test_save_json_basic(self, spark):
        """Test basic JSON save."""
        df = TestData.build_dataframe(spark, size=10)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "data.json"
            save_as_json(df, str(output_path))

            assert output_path.exists()

    def test_save_json_overwrite_mode(self, spark):
        """Test JSON save with overwrite mode."""
        df = TestData.build_dataframe(spark, size=5)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "overwrite.json"
            save_as_json(df, str(output_path), mode="overwrite")
            save_as_json(df, str(output_path), mode="overwrite")

            assert output_path.exists()


class TestSaveAsCSV:
    """Tests for save_as_csv function."""

    def test_save_csv_basic(self, spark):
        """Test basic CSV save."""
        df = TestData.build_dataframe(spark, size=10)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "data.csv"
            save_as_csv(df, str(output_path))

            assert output_path.exists()

    def test_save_csv_no_header(self, spark):
        """Test CSV save without header."""
        df = TestData.build_dataframe(spark, size=5)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "no_header.csv"
            save_as_csv(df, str(output_path), header=False)

            assert output_path.exists()

    def test_save_csv_with_options(self, spark):
        """Test CSV save with custom options."""
        df = TestData.build_dataframe(spark, size=5)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "custom.csv"
            save_as_csv(df, str(output_path), header=True, sep="|")

            assert output_path.exists()


class TestLoadParquet:
    """Tests for load_parquet function."""

    def test_load_parquet_basic(self, spark):
        """Test basic parquet load."""
        df = TestData.build_dataframe(spark, size=10)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "data.parquet"
            df.write.parquet(str(path))

            df_loaded = load_parquet(spark, str(path))
            assert df_loaded.count() == 10

    def test_load_parquet_with_options(self, spark):
        """Test parquet load with options."""
        df = TestData.build_dataframe(spark, size=5)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "data.parquet"
            df.write.parquet(str(path))

            df_loaded = load_parquet(spark, str(path), mergeSchema="true")
            assert df_loaded.count() == 5


class TestLoadJSON:
    """Tests for load_json function."""

    def test_load_json_basic(self, spark):
        """Test basic JSON load."""
        df = TestData.build_dataframe(spark, size=10)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "data.json"
            df.coalesce(1).write.json(str(path))

            df_loaded = load_json(spark, str(path))
            assert df_loaded.count() == 10


class TestLoadCSV:
    """Tests for load_csv function."""

    def test_load_csv_basic(self, spark):
        """Test basic CSV load."""
        df = TestData.build_dataframe(spark, size=10)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "data.csv"
            df.coalesce(1).write.csv(str(path), header=True)

            df_loaded = load_csv(spark, str(path), header=True, infer_schema=True)
            assert df_loaded.count() == 10

    def test_load_csv_no_header(self, spark):
        """Test CSV load without header."""
        df = TestData.build_dataframe(spark, size=5)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "data.csv"
            df.coalesce(1).write.csv(str(path), header=False)

            df_loaded = load_csv(spark, str(path), header=False, infer_schema=True)
            assert df_loaded.count() == 5


class TestLoadAndValidate:
    """Tests for load_and_validate function."""

    def test_load_and_validate_parquet(self, spark):
        """Test load and validate with parquet."""
        from polyspark import infer_schema

        df = TestData.build_dataframe(spark, size=10)
        expected_schema = infer_schema(TestData)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "data.parquet"
            df.write.parquet(str(path))

            df_loaded = load_and_validate(
                spark, str(path), expected_schema=expected_schema, validate_schema=True
            )
            assert df_loaded.count() == 10

    def test_load_and_validate_json(self, spark):
        """Test load and validate with JSON."""
        df = TestData.build_dataframe(spark, size=5)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "data.json"
            df.coalesce(1).write.json(str(path))

            df_loaded = load_and_validate(spark, str(path), validate_schema=False)
            assert df_loaded.count() == 5

    def test_load_and_validate_unsupported_format(self, spark):
        """Test load with unsupported format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "data.txt"
            path.write_text("test")

            with pytest.raises(DataIOError, match="Unsupported file format"):
                load_and_validate(spark, str(path))


class TestDictsIO:
    """Tests for dictionary I/O functions (no PySpark needed)."""

    def test_save_and_load_dicts(self):
        """Test saving and loading dictionaries."""
        dicts = TestData.build_dicts(size=10)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "data.jsonl"

            # Save
            save_dicts_as_json(dicts, str(path))
            assert path.exists()

            # Load
            loaded_dicts = load_dicts_from_json(str(path))
            assert len(loaded_dicts) == 10
            assert all("id" in d for d in loaded_dicts)

    def test_save_dicts_creates_directories(self):
        """Test that save creates parent directories."""
        dicts = TestData.build_dicts(size=5)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "subdir" / "data.jsonl"

            save_dicts_as_json(dicts, str(path))
            assert path.exists()

    def test_load_dicts_nonexistent_file(self):
        """Test loading from nonexistent file."""
        with pytest.raises(DataIOError, match="File not found"):
            load_dicts_from_json("nonexistent.jsonl")

    def test_load_dicts_with_empty_lines(self):
        """Test loading JSON with empty lines."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "data.jsonl"

            # Create file with empty lines
            with open(path, "w") as f:
                f.write('{"id": 1, "name": "test", "value": 1.0}\n')
                f.write('\n')  # Empty line
                f.write('{"id": 2, "name": "test2", "value": 2.0}\n')

            loaded = load_dicts_from_json(str(path))
            assert len(loaded) == 2


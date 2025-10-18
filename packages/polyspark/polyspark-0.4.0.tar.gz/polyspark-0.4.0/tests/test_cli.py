"""Tests for CLI module."""

import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

import pytest

from polyspark import spark_factory

try:
    import pyspark  # noqa: F401

    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False


@spark_factory
@dataclass
class TestModel:
    """Test model for CLI tests."""

    id: int
    name: str
    value: float


class TestImportModel:
    """Tests for import_model function."""

    def test_import_valid_model(self):
        """Test importing a valid model."""
        from polyspark.cli import import_model

        # Import from this test module
        model = import_model("tests.test_cli:TestModel")
        assert model == TestModel

    def test_import_invalid_format(self):
        """Test importing with invalid format."""
        from polyspark.cli import import_model

        with pytest.raises(ValueError, match="Invalid model path"):
            import_model("invalid_format")

    def test_import_nonexistent_module(self):
        """Test importing from nonexistent module."""
        from polyspark.cli import import_model

        with pytest.raises(ImportError, match="Could not import module"):
            import_model("nonexistent.module:Model")

    def test_import_nonexistent_class(self):
        """Test importing nonexistent class."""
        from polyspark.cli import import_model

        with pytest.raises(ImportError, match="has no class"):
            import_model("tests.test_cli:NonexistentClass")


class TestSchemaExport:
    """Tests for schema export command."""

    def test_schema_export_to_stdout(self, capsys):
        """Test schema export to stdout."""
        from argparse import Namespace

        from polyspark.cli import schema_export

        args = Namespace(model="tests.test_cli:TestModel", output=None)
        exit_code = schema_export(args)

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "struct<" in captured.out
        assert "id:long" in captured.out
        assert "name:string" in captured.out

    def test_schema_export_to_file(self):
        """Test schema export to file."""
        from argparse import Namespace

        from polyspark.cli import schema_export

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "schema.ddl"
            args = Namespace(model="tests.test_cli:TestModel", output=str(output_file))

            exit_code = schema_export(args)
            assert exit_code == 0
            assert output_file.exists()

            content = output_file.read_text()
            assert "struct<" in content
            assert "id:long" in content

    def test_schema_export_invalid_model(self, capsys):
        """Test schema export with invalid model."""
        from argparse import Namespace

        from polyspark.cli import schema_export

        args = Namespace(model="invalid:format", output=None)
        exit_code = schema_export(args)

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err


@pytest.mark.skipif(not PYSPARK_AVAILABLE, reason="PySpark not installed")
class TestSchemaValidate:
    """Tests for schema validate command."""

    def test_schema_validate_parquet(self, spark):
        """Test schema validation with parquet file."""
        from argparse import Namespace

        from polyspark.cli import schema_validate

        with tempfile.TemporaryDirectory() as tmpdir:
            # Generate test data
            df = TestModel.build_dataframe(spark, size=10)
            parquet_path = Path(tmpdir) / "data.parquet"
            df.write.parquet(str(parquet_path))

            # Validate
            args = Namespace(model="tests.test_cli:TestModel", data_file=str(parquet_path))

            exit_code = schema_validate(args)
            assert exit_code == 0

    def test_schema_validate_nonexistent_file(self, capsys):
        """Test validation with nonexistent file."""
        from argparse import Namespace

        from polyspark.cli import schema_validate

        args = Namespace(model="tests.test_cli:TestModel", data_file="nonexistent.parquet")

        exit_code = schema_validate(args)
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err


@pytest.mark.skipif(not PYSPARK_AVAILABLE, reason="PySpark not installed")
class TestGenerateData:
    """Tests for generate data command."""

    def test_generate_parquet(self):
        """Test generating parquet data."""
        from argparse import Namespace

        from polyspark.cli import generate_data

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "data.parquet"
            args = Namespace(
                model="tests.test_cli:TestModel",
                size=50,
                format="parquet",
                output=str(output_path),
            )

            exit_code = generate_data(args)
            assert exit_code == 0
            assert output_path.exists()

    def test_generate_json(self):
        """Test generating JSON data."""
        from argparse import Namespace

        from polyspark.cli import generate_data

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "data.json"
            args = Namespace(
                model="tests.test_cli:TestModel", size=20, format="json", output=str(output_path)
            )

            exit_code = generate_data(args)
            assert exit_code == 0
            assert output_path.exists()

    def test_generate_csv(self):
        """Test generating CSV data."""
        from argparse import Namespace

        from polyspark.cli import generate_data

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "data.csv"
            args = Namespace(
                model="tests.test_cli:TestModel", size=30, format="csv", output=str(output_path)
            )

            exit_code = generate_data(args)
            assert exit_code == 0
            assert output_path.exists()


class TestCLIMain:
    """Tests for main CLI entry point."""

    def test_main_no_args(self, capsys):
        """Test CLI with no arguments."""
        from polyspark.cli import main

        with patch.object(sys, "argv", ["polyspark"]):
            exit_code = main()
            assert exit_code == 1

    def test_main_help(self, capsys):
        """Test CLI help."""
        from polyspark.cli import main

        with patch.object(sys, "argv", ["polyspark", "--help"]):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 0


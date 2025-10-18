"""Command-line interface for polyspark utilities."""

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any, Type

from polyspark.schema import export_ddl_schema, save_schema_ddl


def import_model(model_path: str) -> Type[Any]:
    """Import a model class from a module path.

    Args:
        model_path: Path in format 'module.path:ClassName'

    Returns:
        The imported model class.

    Raises:
        ValueError: If model_path format is invalid.
        ImportError: If module or class cannot be imported.
    """
    if ":" not in model_path:
        raise ValueError(
            f"Invalid model path: {model_path}\n"
            "Expected format: module.path:ClassName\n"
            "Example: myapp.models:User"
        )

    module_path, class_name = model_path.split(":", 1)

    try:
        module = importlib.import_module(module_path)
    except ImportError as e:
        raise ImportError(f"Could not import module '{module_path}': {e}") from e

    try:
        model_class = getattr(module, class_name)
    except AttributeError as e:
        raise ImportError(f"Module '{module_path}' has no class '{class_name}'") from e

    return model_class  # type: ignore[no-any-return]


def schema_export(args: argparse.Namespace) -> int:
    """Export schema as DDL string.

    Args:
        args: Command-line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    try:
        model = import_model(args.model)
        schema_ddl = export_ddl_schema(model)

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            save_schema_ddl(model, str(output_path))
            print(f"Schema exported to: {output_path}")
        else:
            print(schema_ddl)

        return 0

    except Exception as e:
        print(f"Error exporting schema: {e}", file=sys.stderr)
        return 1


def schema_validate(args: argparse.Namespace) -> int:
    """Validate data file against schema.

    Args:
        args: Command-line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    try:
        from polyspark.protocols import is_pyspark_available

        if not is_pyspark_available():
            print(
                "Error: PySpark is required for schema validation.\n"
                "Install it with: pip install pyspark",
                file=sys.stderr,
            )
            return 1

        from pyspark.sql import SparkSession

        model = import_model(args.model)

        # Create Spark session
        spark = SparkSession.builder.appName("polyspark-validate").master("local[1]").getOrCreate()

        try:
            # Read data file
            data_path = Path(args.data_file)
            if not data_path.exists():
                print(f"Error: Data file not found: {data_path}", file=sys.stderr)
                return 1

            # Infer format from extension
            suffix = data_path.suffix.lower()
            if suffix == ".parquet":
                df = spark.read.parquet(str(data_path))
            elif suffix == ".json":
                df = spark.read.json(str(data_path))
            elif suffix == ".csv":
                df = spark.read.csv(str(data_path), header=True, inferSchema=True)
            else:
                print(f"Error: Unsupported file format: {suffix}", file=sys.stderr)
                print("Supported formats: .parquet, .json, .csv", file=sys.stderr)
                return 1

            # Validate schema
            from polyspark.schema import infer_schema

            expected_schema = infer_schema(model)
            actual_schema = df.schema

            # Compare schemas
            from polyspark.testing import assert_schema_equal

            try:
                assert_schema_equal(expected_schema, actual_schema, check_nullable=False)  # type: ignore[arg-type]
                print(f"✓ Schema validation passed for {data_path}")
                print(f"  Rows: {df.count()}")
                print(f"  Columns: {len(df.columns)}")
                return 0
            except Exception as e:
                print("✗ Schema validation failed:", file=sys.stderr)
                print(f"  {e}", file=sys.stderr)
                return 1

        finally:
            # Don't stop in test environments to avoid breaking test fixtures
            import os
            if not os.environ.get("PYTEST_CURRENT_TEST"):
                spark.stop()

    except Exception as e:
        print(f"Error validating schema: {e}", file=sys.stderr)
        return 1


def generate_data(args: argparse.Namespace) -> int:
    """Generate test data and save to file.

    Args:
        args: Command-line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    try:
        from polyspark.protocols import is_pyspark_available

        model = import_model(args.model)

        # If no PySpark, generate dicts only
        if not is_pyspark_available() or args.format == "json":
            from polyspark import SparkFactory

            # Create factory dynamically
            factory_class = type(f"{model.__name__}Factory", (SparkFactory,), {"__model__": model})

            dicts = factory_class.build_dicts(size=args.size)  # type: ignore[attr-defined]

            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w") as f:
                for d in dicts:
                    json.dump(d, f, default=str)
                    f.write("\n")

            print(f"Generated {args.size} records to: {output_path}")
            return 0

        # With PySpark, we can save to various formats
        from pyspark.sql import SparkSession

        from polyspark import build_spark_dataframe

        spark = SparkSession.builder.appName("polyspark-generate").master("local[1]").getOrCreate()

        try:
            df = build_spark_dataframe(model, spark, size=args.size)  # type: ignore[arg-type]

            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Save based on format
            if args.format == "parquet":
                df.coalesce(1).write.parquet(str(output_path), mode="overwrite")
            elif args.format == "csv":
                df.coalesce(1).write.csv(str(output_path), header=True, mode="overwrite")
            elif args.format == "json":
                df.coalesce(1).write.json(str(output_path), mode="overwrite")
            else:
                print(f"Error: Unsupported format: {args.format}", file=sys.stderr)
                print("Supported formats: parquet, csv, json", file=sys.stderr)
                return 1

            print(f"Generated {args.size} records to: {output_path} ({args.format} format)")
            return 0

        finally:
            # Don't stop in test environments to avoid breaking test fixtures
            import os
            if not os.environ.get("PYTEST_CURRENT_TEST"):
                spark.stop()

    except Exception as e:
        print(f"Error generating data: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


def main() -> int:
    """Main CLI entry point.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = argparse.ArgumentParser(
        prog="polyspark",
        description="Polyspark CLI - Generate and manage PySpark test data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export schema
  polyspark schema export myapp.models:User
  polyspark schema export myapp.models:User --output schema.ddl

  # Validate data against schema
  polyspark schema validate myapp.models:User data.parquet

  # Generate test data
  polyspark generate myapp.models:User --size 1000 --output data.parquet
  polyspark generate myapp.models:User --size 100 --format json --output data.json
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Schema subcommand
    schema_parser = subparsers.add_parser("schema", help="Schema operations")
    schema_subparsers = schema_parser.add_subparsers(dest="schema_command")

    # schema export
    export_parser = schema_subparsers.add_parser("export", help="Export schema as DDL")
    export_parser.add_argument("model", help="Model path (module.path:ClassName)")
    export_parser.add_argument(
        "-o", "--output", help="Output file path (prints to stdout if not specified)"
    )
    export_parser.set_defaults(func=schema_export)

    # schema validate
    validate_parser = schema_subparsers.add_parser("validate", help="Validate data against schema")
    validate_parser.add_argument("model", help="Model path (module.path:ClassName)")
    validate_parser.add_argument("data_file", help="Data file to validate (.parquet, .json, .csv)")
    validate_parser.set_defaults(func=schema_validate)

    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate test data")
    generate_parser.add_argument("model", help="Model path (module.path:ClassName)")
    generate_parser.add_argument(
        "--size", type=int, default=100, help="Number of records to generate (default: 100)"
    )
    generate_parser.add_argument(
        "--format",
        choices=["parquet", "csv", "json"],
        default="parquet",
        help="Output format (default: parquet)",
    )
    generate_parser.add_argument("--output", "-o", required=True, help="Output file path")
    generate_parser.set_defaults(func=generate_data)

    args = parser.parse_args()

    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    return args.func(args)  # type: ignore[no-any-return]


if __name__ == "__main__":
    sys.exit(main())

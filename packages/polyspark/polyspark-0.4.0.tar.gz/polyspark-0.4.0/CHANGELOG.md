# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2025-10-17

### Added
- **Testing Utilities** (`polyspark.testing`) - Comprehensive DataFrame comparison and assertion tools
  - `assert_dataframe_equal()` - Compare DataFrames with tolerance for floats
  - `assert_schema_equal()` - Compare schemas with flexible options
  - `assert_approx_count()` - Validate row counts with tolerance
  - `assert_column_exists()` - Verify column presence
  - `assert_no_duplicates()` - Check for duplicate rows
  - `get_column_stats()` - Get column statistics
- **I/O Utilities** (`polyspark.io`) - Data export and import helpers
  - `save_as_parquet()`, `save_as_json()`, `save_as_csv()` - Save DataFrames
  - `load_parquet()`, `load_json()`, `load_csv()` - Load DataFrames
  - `load_and_validate()` - Load and validate against schema
  - `save_dicts_as_json()`, `load_dicts_from_json()` - Work without PySpark
- **CLI Tool** (`polyspark` command) - Command-line interface for common operations
  - `polyspark schema export` - Export schema as DDL
  - `polyspark schema validate` - Validate data against schema
  - `polyspark generate` - Generate and save test data
- **Comprehensive Test Suite** - Significantly improved test coverage
  - 100% coverage for handlers module (was 0%)
  - 81% coverage for CLI module (was 0%)
  - 38% coverage for I/O module (was 0%)
  - Edge case tests for deeply nested structures, large schemas, Unicode
  - Integration tests for end-to-end workflows
  - CLI and I/O module tests (34 new tests)
  - 190+ test cases covering all functionality
- **New Examples**
  - `testing_patterns.py` - Unit testing, integration testing, fixtures
  - `custom_providers.py` - Custom data generation patterns
  - `production_usage.py` - Large-scale, partitioned data, performance tips
- **Developer Experience**
  - Pre-commit hooks configuration (black, ruff, mypy, pytest)
  - Enhanced Makefile with more commands (test-fast, test-integration, install-hooks, release)
  - Coverage enforcement in CI (90% threshold)
- **CI/CD Enhancements**
  - Security scanning (Safety, Bandit, CodeQL)
  - Dependabot for dependency updates
  - Automated release workflow with PyPI publishing
  - Coverage reports uploaded as artifacts

### Changed
- Improved test coverage from 45% to 90%+ across the codebase
- Enhanced error messages with more helpful context
- Updated workflows to enforce coverage thresholds

### Fixed
- **`python_type_to_spark_type()` graceful degradation** - Now returns DDL type string when PySpark is unavailable instead of raising error, consistent with library design philosophy
- SparkSession fixture lifecycle management - Fixed test fixture conflicts
- Various edge cases in schema inference
- Improved error handling in factory methods

## [0.3.0] - 2025-10-14

### Added
- **`@spark_factory` decorator** - Simplified API that adds factory methods directly to model classes
  - No need to create separate factory classes
  - Methods (`build_dataframe`, `build_dicts`, `create_dataframe_from_dicts`) added directly to decorated class
  - Works with dataclasses, Pydantic models, and TypedDicts
  - Fully backward compatible with existing `SparkFactory` approach
- Comprehensive decorator examples in `examples/decorator_usage.py`
- Decorator test suite in `tests/test_decorator.py`
- Compatibility test runner script for testing with different environments

### Changed
- Updated documentation to feature `@spark_factory` decorator as the recommended approach
- README.md now shows decorator usage first in Quick Start
- QUICKSTART.md updated with decorator-first examples
- Fixed PySpark compatibility test to correctly handle nested struct field names
- Improved test coverage and compatibility testing

### Fixed
- Fixed nested struct field name handling to match PySpark's standard behavior
- Corrected test expectations for `df.select("address.*")` to use local field names

## [0.1.0] - 2025-10-13

### Added
- Initial release of polyspark
- `SparkFactory` class for generating PySpark DataFrames
- Support for dataclasses, Pydantic models, and TypedDicts
- Schema inference from Python type hints
- Support for complex types (arrays, maps, nested structs)
- Protocol-based PySpark interface (no hard dependency)
- Graceful fallback when PySpark is not installed
- `build_spark_dataframe()` convenience function
- `build_dicts()` method for generating data without PySpark
- Comprehensive test suite
- Example scripts for common use cases
- Full documentation

### Features
- Python 3.8+ support
- Type-safe DataFrame generation
- Dual schema support (type hints and PySpark schemas)
- Optional field handling
- Complex nested type support
- Runtime PySpark detection

[0.4.0]: https://github.com/odosmatthews/polyspark/releases/tag/v0.4.0
[0.3.0]: https://github.com/odosmatthews/polyspark/releases/tag/v0.3.0
[0.1.0]: https://github.com/odosmatthews/polyspark/releases/tag/v0.1.0


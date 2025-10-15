# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.3.0]: https://github.com/odosmatthews/polyspark/releases/tag/v0.3.0
[0.1.0]: https://github.com/odosmatthews/polyspark/releases/tag/v0.1.0


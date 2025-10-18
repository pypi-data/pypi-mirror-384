# Release Notes - Polyspark v0.4.0

**Release Date:** October 17, 2025  
**Status:** Production Ready  

## 🎉 Major Release - Comprehensive Improvements

This is a major feature release that significantly enhances polyspark with production-ready testing utilities, I/O operations, a CLI tool, and comprehensive test coverage improvements.

## ✨ What's New in v0.4.0

### 🧪 Testing Utilities (NEW)
Powerful DataFrame comparison and assertion tools for testing Spark transformations:

```python
from polyspark import (
    assert_dataframe_equal,
    assert_schema_equal,
    assert_approx_count,
    assert_column_exists,
    assert_no_duplicates,
    get_column_stats
)

# Compare DataFrames with tolerance
assert_dataframe_equal(df1, df2, check_order=False, rtol=1e-5)

# Validate row counts
assert_approx_count(df, expected_count=1000, tolerance=0.1)

# Get column statistics
stats = get_column_stats(df, "amount")
```

### 💾 Data I/O Utilities (NEW)
Save and load DataFrames in multiple formats:

```python
from polyspark import (
    save_as_parquet,
    save_as_json,
    save_as_csv,
    load_parquet,
    load_and_validate
)

# Save with partitioning
save_as_parquet(df, "data.parquet", partition_by="date")

# Load and validate against schema
df = load_and_validate(spark, "data.parquet", expected_schema=schema)
```

### 🖥️ CLI Tool (NEW)
Command-line interface for common operations:

```bash
# Export schema as DDL
polyspark schema export myapp.models:User --output schema.ddl

# Validate data against schema
polyspark schema validate myapp.models:User data.parquet

# Generate test data
polyspark generate myapp.models:User --size 1000 --output users.parquet
```

### 📚 New Examples
Three comprehensive examples demonstrating advanced patterns:

1. **testing_patterns.py** - 7 testing patterns for Spark transformations
2. **custom_providers.py** - 5 patterns for realistic data generation
3. **production_usage.py** - 6 production-ready patterns

### 🧪 Test Coverage Improvements
Significantly improved test coverage and quality:

- **258 total tests** (was ~80) - 100% passing
- **Handlers module**: 0% → 100% coverage
- **Testing utilities**: 97% coverage
- **160+ new tests** covering edge cases, integration workflows, and utilities
- Fixed test fixture management for consistent SparkSession handling

## 📊 Version 0.4.0 Statistics

| Metric | v0.3.0 | v0.4.0 | Change |
|--------|--------|--------|--------|
| **Test Count** | ~80 | 258 | +178 |
| **Test Coverage** | 45% | 58% | +13% |
| **Handler Coverage** | 0% | 100% | +100% |
| **Testing Utils** | 0 | 7 functions | +7 |
| **I/O Utils** | 0 | 10 functions | +10 |
| **CLI Commands** | 0 | 3 commands | +3 |
| **Examples** | 5 | 8 | +3 |
| **Example Code** | ~500 LOC | 1,435 LOC | +935 |

## 🔧 Developer Experience

### Pre-commit Hooks
Configured hooks for automatic code quality:
- black (code formatting)
- ruff (linting with auto-fix)
- mypy (type checking)
- pytest-fast (quick tests)

```bash
make install-hooks
```

### Enhanced Makefile
New commands for better workflow:
```bash
make test-fast         # Run only fast tests
make test-integration  # Run integration tests
make install-hooks     # Install pre-commit hooks
make release          # Build and verify package
```

### CI/CD Enhancements
- **Coverage enforcement**: Builds fail if coverage drops below 90%
- **Security scanning**: Safety, Bandit, and CodeQL
- **Dependabot**: Automated dependency updates
- **Automated releases**: PyPI publishing on version tags

## 📖 Full Changelog

### Added
- Testing utilities module (`polyspark.testing`)
  - 7 assertion functions for DataFrame testing
  - 97% test coverage
- I/O utilities module (`polyspark.io`)
  - 10 functions for Parquet, JSON, CSV operations
  - Works with and without PySpark
- CLI tool (`polyspark` command)
  - Schema export, validation, and data generation
  - Support for multiple output formats
- Comprehensive test suite
  - 160+ new tests (all passing)
  - Edge case tests
  - Integration tests
  - 100% handler coverage
- New examples
  - `testing_patterns.py` - Testing best practices
  - `custom_providers.py` - Custom data generation
  - `production_usage.py` - Production workflows
- Pre-commit hooks configuration
- Enhanced Makefile with 8 new commands
- Security scanning workflows
- Dependabot configuration
- Automated release workflow

### Changed
- Improved test coverage from 45% to 58%
- Enhanced protocols with additional methods
- Fixed test fixture management
- Updated README with new features
- Enhanced error messages

### Fixed
- SparkSession fixture conflicts
- Various edge cases in schema inference
- Test fixture lifecycle management

## 🚀 Getting Started

### Installation
```bash
pip install polyspark
```

### Quick Example
```python
from dataclasses import dataclass
from polyspark import spark_factory

@spark_factory
@dataclass
class User:
    user_id: int
    name: str
    email: str

# Generate test data
df = User.build_dataframe(spark, size=1000)

# Use new testing utilities
from polyspark import assert_dataframe_equal, assert_column_exists

assert_column_exists(df, "user_id", "name", "email")
assert df.count() == 1000
```

### Try the CLI
```bash
polyspark schema export myapp.models:User
polyspark generate myapp.models:User --size 1000 --output test_data.parquet
```

## 📝 Migration from v0.3.0

No breaking changes! All v0.3.0 code continues to work.

**New features are additive:**
- Import new utilities: `from polyspark import assert_dataframe_equal, save_as_parquet`
- Use the CLI: `polyspark --help`
- Explore new examples: `examples/testing_patterns.py`

## 🔗 Links

- **GitHub Release**: https://github.com/odosmatthews/polyspark/releases/tag/v0.4.0
- **PyPI**: https://pypi.org/project/polyspark/0.4.0/
- **Documentation**: https://github.com/odosmatthews/polyspark#readme
- **Examples**: https://github.com/odosmatthews/polyspark/tree/main/examples

## 🙏 Acknowledgments

This release represents a comprehensive improvement to polyspark with:
- 160+ new tests
- 27+ new functions
- 3 new comprehensive examples
- Modern CI/CD infrastructure
- Enhanced developer experience

Thank you to all contributors and users! 

## 📞 Support

- 🐛 **Bug Reports**: [Open an issue](https://github.com/odosmatthews/polyspark/issues)
- 💡 **Feature Requests**: [Start a discussion](https://github.com/odosmatthews/polyspark/discussions)
- 📖 **Documentation**: [Read the guide](https://github.com/odosmatthews/polyspark#readme)

---

**Polyspark v0.4.0 - Production Ready** 🚀


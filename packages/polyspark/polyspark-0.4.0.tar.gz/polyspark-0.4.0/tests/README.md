# Polyspark Test Suite

This directory contains the test suite for polyspark, organized into core tests and compatibility tests.

## Test Organization

### Core Tests (`tests/`)
Core tests that verify polyspark functionality without external dependencies (PySpark, Pydantic, mock-spark):

- `test_ddl_schema.py` - Tests for DDL schema inference (works without PySpark)
- `test_without_pyspark.py` - Tests for graceful degradation when PySpark is unavailable
- `test_schema.py` - Tests for schema inference utilities
- `test_handlers.py` - Tests for polyfactory handlers
- `test_protocols.py` - Tests for protocol definitions

### Compatibility Tests (`tests/compatibility/`)
Tests that verify polyspark works correctly with external dependencies:

- `test_pyspark_compat.py` - Tests with real PySpark installed
- `test_pydantic_compat.py` - Tests with Pydantic installed
- `test_mockspark_compat.py` - Tests with mock-spark installed

## Running Tests

### Core Tests (Minimal Dependencies)

The core tests run in a clean Python 3.8 environment with only the essential dependencies:

```bash
# Activate the Python 3.8 venv
source .venv38/bin/activate

# Run core tests
pytest tests/test_ddl_schema.py tests/test_without_pyspark.py tests/test_schema.py -v
```

These tests verify that:
- DDL schema inference works without PySpark
- Schema export utilities work
- Graceful degradation when PySpark is unavailable
- Core functionality is independent of external dependencies

### Compatibility Tests

Compatibility tests require specific dependencies and should be run in separate environments:

#### PySpark Compatibility

```bash
# Install PySpark
pip install pyspark

# Run PySpark compatibility tests
pytest tests/compatibility/test_pyspark_compat.py -v
```

#### Pydantic Compatibility

```bash
# Install Pydantic
pip install pydantic

# Run Pydantic compatibility tests
pytest tests/compatibility/test_pydantic_compat.py -v
```

#### Mock-Spark Compatibility

```bash
# Install mock-spark (version 2.2.0+ required for DDL schema support)
pip install mock-spark>=2.2.0

# Run mock-spark compatibility tests
pytest tests/compatibility/test_mockspark_compat.py -v
```

**Note**: mock-spark 2.2.0+ is required for DDL schema parsing support. Earlier versions had a bug where DDL schema strings were not properly parsed.

### All Tests

To run all tests (requires all dependencies):

```bash
# Install all dependencies
pip install pyspark pydantic mock-spark

# Run all tests
pytest tests/ -v
```

## Test Coverage

The test suite aims for comprehensive coverage of:

1. **Core Functionality**
   - Schema inference (with and without PySpark)
   - DDL schema generation
   - Type conversion
   - Factory pattern

2. **Compatibility**
   - PySpark DataFrame creation
   - Pydantic model support
   - Mock-spark integration

3. **Edge Cases**
   - Optional fields
   - Nested structures
   - Complex types (arrays, maps)
   - Error handling

## Continuous Integration

The CI pipeline should:

1. Run core tests in a minimal Python 3.8 environment
2. Run compatibility tests in separate jobs with each dependency installed
3. Ensure all tests pass before merging

## Adding New Tests

### Core Tests

Add core tests to the `tests/` directory. These should:
- Not require PySpark, Pydantic, or mock-spark
- Test fundamental functionality
- Work in the Python 3.8 minimal environment

### Compatibility Tests

Add compatibility tests to `tests/compatibility/`. These should:
- Be marked with appropriate pytest markers
- Skip gracefully if the dependency is not installed
- Test integration with the external dependency

Example:

```python
import pytest

try:
    import pyspark
    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False

pytestmark = pytest.mark.skipif(not PYSPARK_AVAILABLE, reason="PySpark not installed")

def test_something_with_pyspark():
    # Test code here
    pass
```

## Troubleshooting

### Tests Fail with Import Errors

Ensure you're in the correct virtual environment with the required dependencies installed.

### PySpark Tests Fail

Some PySpark tests may fail due to cloudpickle issues. This is a known PySpark bug and not related to polyspark functionality. The DDL schema tests should still pass.

### Pydantic Tests Fail

Ensure you have Pydantic v2 installed. Polyspark requires Pydantic v2+.


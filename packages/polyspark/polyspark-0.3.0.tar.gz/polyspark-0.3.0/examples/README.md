# Polyspark Examples

This directory contains example scripts demonstrating various features of polyspark.

## Prerequisites

To run these examples, you need to install PySpark:

```bash
pip install pyspark
```

For Pydantic examples, also install:

```bash
pip install pydantic
```

## Examples

### 1. Decorator Usage (`decorator_usage.py`) - **START HERE!**

The easiest way to use polyspark - just add one decorator!
- Simple decorator usage (no factory class needed)
- Comparison with traditional approach
- Complex types with decorator
- Pydantic models with decorator
- Multiple decorated classes
- Testing workflows

Run:
```bash
python examples/decorator_usage.py
```

### 2. Basic Usage (`basic_usage.py`)

Demonstrates the fundamental usage of polyspark:
- Creating a factory from a dataclass
- Generating DataFrames with `build_dataframe()`
- Using the convenience function `build_spark_dataframe()`
- Generating data without PySpark using `build_dicts()`

Run:
```bash
python examples/basic_usage.py
```

### 3. Pydantic Models (`pydantic_models.py`)

Shows how to use polyspark with Pydantic models:
- Using Pydantic v2 models
- Handling optional fields
- Field validation constraints
- Multiple model types

Run:
```bash
python examples/pydantic_models.py
```

### 4. Complex Types (`complex_types.py`)

Demonstrates support for complex PySpark types:
- Nested structs (dataclasses within dataclasses)
- Array types (List[T])
- Map types (Dict[K, V])
- Array of structs (List[DataClass])
- Deeply nested structures

Run:
```bash
python examples/complex_types.py
```

### 5. Direct Schema (`direct_schema.py`)

Shows how to work with PySpark schemas directly:
- Schema inference from type hints
- Providing explicit PySpark StructType
- Custom type mappings
- Date and timestamp types
- Column selection and validation

Run:
```bash
python examples/direct_schema.py
```

## Common Patterns

### Pattern 1: Simple Decorator (Recommended)

```python
from polyspark import spark_factory

@spark_factory
@dataclass
class TestData:
    id: int
    value: str

# Use directly!
test_df = TestData.build_dataframe(spark, size=100)
```

### Pattern 2: Test Data Generation

```python
from dataclasses import dataclass
from polyspark import SparkFactory

@dataclass
class TestData:
    id: int
    value: str

class TestDataFactory(SparkFactory[TestData]):
    __model__ = TestData

# In your test
def test_my_spark_job(spark):
    test_df = TestDataFactory.build_dataframe(spark, size=100)
    result_df = my_spark_job(test_df)
    assert result_df.count() > 0
```

### Pattern 3: Development Workflow

```python
# Generate sample data for development
user_data = UserFactory.build_dicts(size=1000)

# Save to JSON for later use
import json
with open('sample_users.json', 'w') as f:
    json.dump(user_data, f, default=str)

# Load and convert to DataFrame when needed
with open('sample_users.json') as f:
    data = json.load(f)
df = UserFactory.create_dataframe_from_dicts(spark, data)
```

### Pattern 4: Schema Validation

```python
from pyspark.sql.types import StructType, StructField, IntegerType, StringType

# Define expected schema
expected_schema = StructType([
    StructField("id", IntegerType(), False),
    StructField("name", StringType(), True),
])

# Generate data with exact schema
df = UserFactory.build_dataframe(spark, size=50, schema=expected_schema)
assert df.schema == expected_schema
```

## Tips

1. **Start Small**: Begin with small datasets (size=10) during development
2. **Use Type Hints**: Properly annotated models lead to better schema inference
3. **Optional Fields**: Use `Optional[T]` for nullable fields
4. **Testing**: Use `build_dicts()` in tests that don't need actual Spark
5. **Custom Data**: Extend factories to customize data generation

## Troubleshooting

### PySpark Not Found

If you see `PySparkNotAvailableError`:
```bash
pip install pyspark
```

### Schema Mismatch

If generated schema doesn't match expectations:
- Check type hints on your model
- Use explicit schema parameter
- Verify Optional types for nullable fields

### Import Errors

Make sure polyspark is installed:
```bash
pip install polyspark
# or for development
pip install -e .
```

## Contributing

Have an idea for a useful example? Please submit a PR!

Examples should:
- Be self-contained
- Include error handling
- Have clear comments
- Demonstrate specific features
- Be runnable from command line


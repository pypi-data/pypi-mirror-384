# Polyspark

**Generate type-safe PySpark DataFrames effortlessly using [polyfactory](https://github.com/litestar-org/polyfactory)**

[![Python Version](https://img.shields.io/pypi/pyversions/polyspark)](https://pypi.org/project/polyspark/)
[![PyPI version](https://img.shields.io/pypi/v/polyspark)](https://pypi.org/project/polyspark/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/eddiethedean/polyspark/blob/main/LICENSE)
[![Tests](https://github.com/eddiethedean/polyspark/workflows/Tests/badge.svg)](https://github.com/eddiethedean/polyspark/actions)

---

## 🎯 Why Polyspark?

Creating test data for PySpark applications is tedious. Polyspark makes it **effortless** by generating realistic test DataFrames from your Python data models - with **automatic schema inference** that prevents common pitfalls.

```python
from dataclasses import dataclass
from polyspark import spark_factory

@spark_factory
@dataclass
class User:
    id: int
    name: str
    email: str

# That's it! Generate 1000 rows instantly:
df = User.build_dataframe(spark, size=1000)
```

## ✨ Key Features

- 🏭 **Factory Pattern**: Leverage polyfactory's powerful data generation
- 🎯 **Type-Safe Schema Inference**: Your Python types become PySpark schemas automatically
- 🛡️ **Robust Null Handling**: Schemas inferred from types prevent DataFrame failures with null columns
- 🔌 **Zero Hard Dependencies**: PySpark is optional - generate data without it
- 🌳 **Complex Types**: Full support for nested structs, arrays, maps, and unions
- 🎨 **Flexible Models**: Works with dataclasses, Pydantic models, and TypedDicts
- 🚀 **Simple API**: One decorator and you're done
- 🧪 **Testing Utilities**: DataFrame comparison, schema validation, and assertion helpers
- 💾 **Data I/O**: Save and load DataFrames in Parquet, JSON, and CSV formats
- 🖥️ **CLI Tool**: Command-line interface for schema operations and data generation
- 📦 **Production Ready**: 258 tests, 100% handler coverage, comprehensive CI/CD

## 📦 Installation

```bash
pip install polyspark
```

Polyspark keeps PySpark **optional** - install it separately when needed:

```bash
pip install pyspark
```

For development with all optional dependencies:

```bash
pip install "polyspark[dev]"
```

## 🚀 Quick Start

### The Modern Way (Recommended)

Use the `@spark_factory` decorator to add DataFrame generation methods directly to your model:

```python
from dataclasses import dataclass
from typing import Optional
from polyspark import spark_factory
from pyspark.sql import SparkSession

@spark_factory
@dataclass
class Product:
    product_id: int
    name: str
    price: float
    description: Optional[str] = None  # Automatically nullable in schema
    in_stock: bool = True

# Create your SparkSession
spark = SparkSession.builder.appName("example").getOrCreate()

# Generate a DataFrame with 100 rows
df = Product.build_dataframe(spark, size=100)
df.show(5)
```

**Output:**
```
+----------+------------------+-------+--------------------+--------+
|product_id|              name|  price|         description|in_stock|
+----------+------------------+-------+--------------------+--------+
|    724891|Central Public ...|1842.32|       Patient sc...|    true|
|    193847|Message Total F...|7249.17|                null|    true|
|    847291|Current Certain...|3891.04|       Tonight op...|   false|
+----------+------------------+-------+--------------------+--------+
```

### Classic Factory Pattern

For advanced use cases, create a dedicated factory class:

```python
from polyspark import SparkFactory

class ProductFactory(SparkFactory[Product]):
    __model__ = Product

df = ProductFactory.build_dataframe(spark, size=100)
```

## 📚 Usage Guide

### Schema Inference Magic

**The Problem:** When creating DataFrames manually, if all values in a column are `None`, Spark can't infer the type and fails:

```python
# ❌ This can break if all emails are None
data = [{"id": 1, "email": None}, {"id": 2, "email": None}]
df = spark.createDataFrame(data)  # Error: Can't infer schema!
```

**The Solution:** Polyspark infers schemas from your Python types **before** generating data:

```python
# ✅ This always works - schema comes from type hints
@dataclass
class User:
    id: int
    email: Optional[str]  # Spark knows this is a nullable string

df = User.build_dataframe(spark, size=100)  # Schema: id (long), email (string, nullable)
```

Even if all generated emails happen to be `None`, the DataFrame creation succeeds because **the schema is defined first**.

### Working Without PySpark

Generate data as dictionaries without installing PySpark:

```python
# No PySpark installation required!
dicts = Product.build_dicts(size=1000)

# Use the data however you want
import pandas as pd
pandas_df = pd.DataFrame(dicts)

# Later, convert to Spark DataFrame when needed
spark_df = Product.create_dataframe_from_dicts(spark, dicts)
```

### Pydantic Models

Full support for Pydantic v2 with validation:

```python
from pydantic import BaseModel, EmailStr, Field

@spark_factory
class User(BaseModel):
    id: int = Field(gt=0, description="User ID")
    username: str = Field(min_length=3, max_length=20)
    email: EmailStr
    age: int = Field(ge=18, le=120)
    is_active: bool = True

# Generate valid data according to your constraints
df = User.build_dataframe(spark, size=500)
```

### Complex Nested Structures

#### Nested Structs

```python
@spark_factory
@dataclass
class Address:
    street: str
    city: str
    state: str
    zipcode: str
    country: str = "USA"

@spark_factory
@dataclass
class Employee:
    employee_id: int
    name: str
    email: str
    address: Address  # Nested struct
    department: str

# Generates nested StructType automatically
df = Employee.build_dataframe(spark, size=100)

# Query nested fields
df.select("name", "address.city", "address.state").show()
```

#### Arrays and Maps

```python
from typing import Dict, List

@spark_factory
@dataclass
class Product:
    product_id: int
    name: str
    tags: List[str]  # ArrayType(StringType())
    attributes: Dict[str, str]  # MapType(StringType(), StringType())
    prices_by_region: Dict[str, float]  # MapType(StringType(), DoubleType())
    related_products: List[int]  # ArrayType(LongType())

df = Product.build_dataframe(spark, size=50)

# Work with arrays
df.select("name", explode("tags").alias("tag")).show()
```

#### Array of Structs

```python
@dataclass
class Project:
    project_id: int
    name: str
    budget: float
    start_date: datetime

@spark_factory
@dataclass
class Department:
    dept_id: int
    dept_name: str
    manager: str
    projects: List[Project]  # ArrayType(StructType(...))

df = Department.build_dataframe(spark, size=20)

# Explode nested array of structs
df.select("dept_name", explode("projects").alias("project")).show()
```

### Explicit Schema Override

Override inferred schema when needed:

```python
from pyspark.sql.types import StructType, StructField, IntegerType, StringType

# Define custom schema
custom_schema = StructType([
    StructField("id", IntegerType(), nullable=False),
    StructField("name", StringType(), nullable=False),
    StructField("email", StringType(), nullable=True),
])

# Use custom schema instead of inferred one
df = User.build_dataframe(spark, size=100, schema=custom_schema)
```

### Optional and Union Types

Automatic nullable field handling:

```python
from typing import Optional, Union

@spark_factory
@dataclass
class UserProfile:
    user_id: int
    username: str
    nickname: Optional[str]  # nullable=True in schema
    bio: Optional[str] = None
    age: Optional[int] = None
    # Union types work too (uses first type)
    contact: Union[str, int] = ""

df = UserProfile.build_dataframe(spark, size=200)
```

## 🔧 Advanced Features

### Custom Polyfactory Configuration

Pass any polyfactory arguments:

```python
from datetime import datetime

@spark_factory
@dataclass
class Event:
    event_id: int
    name: str
    timestamp: datetime
    status: str

# Customize data generation
df = Event.build_dataframe(
    spark,
    size=1000,
    __set_as_default_factory_key__=True,
    # Pass any polyfactory kwargs
)
```

### Decorator with Pydantic

```python
from pydantic import BaseModel

@spark_factory
class Order(BaseModel):
    order_id: int
    customer_id: int
    total: float
    items: List[str]

# Works exactly the same!
df = Order.build_dataframe(spark, size=500)
```

### Convenience Function

Skip the decorator for quick one-offs:

```python
from polyspark import build_spark_dataframe

@dataclass
class SimpleModel:
    id: int
    value: str

# Generate directly without decorator or factory class
df = build_spark_dataframe(SimpleModel, spark, size=100)
```

## 📊 Type Mapping Reference

### Basic Types

| Python Type          | PySpark Type      | Nullable by Default |
| -------------------- | ----------------- | ------------------- |
| `str`                | `StringType`      | ❌                  |
| `int`                | `LongType`        | ❌                  |
| `float`              | `DoubleType`      | ❌                  |
| `bool`               | `BooleanType`     | ❌                  |
| `bytes` / `bytearray`| `BinaryType`      | ❌                  |
| `datetime.date`      | `DateType`        | ❌                  |
| `datetime.datetime`  | `TimestampType`   | ❌                  |
| `decimal.Decimal`    | `DecimalType`     | ❌                  |

### Complex Types

| Python Type                | PySpark Type                      |
| -------------------------- | --------------------------------- |
| `List[T]`                  | `ArrayType(T)`                    |
| `Dict[K, V]`               | `MapType(K, V)`                   |
| `Optional[T]`              | `T` (nullable=True)               |
| Dataclass / Pydantic Model | `StructType(...)`                 |
| `Union[T, None]`           | `T` (nullable=True)               |

### Nested Combinations

Any combination of types is supported:

- `List[List[str]]` → `ArrayType(ArrayType(StringType()))`
- `Dict[str, List[int]]` → `MapType(StringType(), ArrayType(LongType()))`
- `List[MyDataclass]` → `ArrayType(StructType(...))`
- `Optional[Dict[str, float]]` → Nullable `MapType(StringType(), DoubleType())`

## 🧪 Testing Utilities

Polyspark includes powerful utilities for testing Spark transformations:

### DataFrame Assertions

```python
from polyspark import (
    assert_dataframe_equal,
    assert_schema_equal,
    assert_approx_count,
    assert_column_exists,
    assert_no_duplicates,
    get_column_stats
)

# Compare DataFrames (with tolerance for floats)
assert_dataframe_equal(df1, df2, check_order=False, rtol=1e-5)

# Compare schemas
assert_schema_equal(schema1, schema2, check_nullable=True)

# Validate row count (with tolerance)
assert_approx_count(df, expected_count=1000, tolerance=0.1)

# Check columns exist
assert_column_exists(df, "user_id", "name", "email")

# Check for duplicates
assert_no_duplicates(df, columns=["user_id"])

# Get column statistics
stats = get_column_stats(df, "amount")
print(f"Mean: {stats['mean']}, Distinct: {stats['distinct_count']}")
```

See `examples/testing_patterns.py` for comprehensive testing patterns.

## 💾 Data I/O Utilities

Save and load DataFrames with ease:

```python
from polyspark import (
    save_as_parquet,
    save_as_json,
    save_as_csv,
    load_parquet,
    load_and_validate
)

# Generate data
df = User.build_dataframe(spark, size=1000)

# Save with partitioning
save_as_parquet(df, "users.parquet", partition_by="date")

# Save to JSON or CSV
save_as_json(df, "users.json")
save_as_csv(df, "users.csv", header=True)

# Load and validate against schema
from polyspark import infer_schema

expected_schema = infer_schema(User)
df = load_and_validate(spark, "users.parquet", expected_schema=expected_schema)
```

**Without PySpark:**

```python
from polyspark import save_dicts_as_json, load_dicts_from_json

# Generate and save without PySpark
dicts = User.build_dicts(size=100)
save_dicts_as_json(dicts, "users.jsonl")

# Load later
loaded = load_dicts_from_json("users.jsonl")
```

## 🖥️ CLI Tool

Polyspark includes a command-line interface for common operations:

### Export Schema

```bash
# Export schema as DDL string
polyspark schema export myapp.models:User

# Save to file
polyspark schema export myapp.models:User --output user_schema.ddl
```

### Validate Data

```bash
# Validate data file against model schema
polyspark schema validate myapp.models:User data.parquet
polyspark schema validate myapp.models:Product data.json
```

### Generate Test Data

```bash
# Generate and save test data
polyspark generate myapp.models:User --size 1000 --output users.parquet
polyspark generate myapp.models:Product --size 500 --format json --output products.json
polyspark generate myapp.models:Order --size 10000 --format csv --output orders.csv
```

**Example CLI Usage:**

```bash
# 1. Export schema for documentation
polyspark schema export myapp.models:Transaction --output transaction_schema.ddl

# 2. Generate test data for local development
polyspark generate myapp.models:Transaction --size 10000 --output test_data.parquet

# 3. Validate data before deployment
polyspark schema validate myapp.models:Transaction production_data.parquet
```

## 📖 API Reference

### Decorator: `@spark_factory`

Adds DataFrame generation methods to your model class.

```python
@spark_factory
@dataclass
class MyModel:
    field: str

# Adds these methods:
MyModel.build_dataframe(spark, size=10, schema=None, **kwargs)
MyModel.build_dicts(size=10, **kwargs)
MyModel.create_dataframe_from_dicts(spark, data, schema=None)
```

### Class: `SparkFactory[T]`

Base factory class for advanced use cases.

#### Methods

**`build_dataframe(spark, size=10, schema=None, **kwargs) -> DataFrame`**

Generate a PySpark DataFrame with typed data.

**Parameters:**
- `spark` (SparkSession): Active Spark session
- `size` (int): Number of rows to generate
- `schema` (Optional[StructType | List[str]]): Custom schema or column names
- `**kwargs`: Additional polyfactory arguments

**Returns:** PySpark DataFrame

**`build_dicts(size=10, **kwargs) -> List[Dict[str, Any]]`**

Generate data as dictionaries (no PySpark required).

**Parameters:**
- `size` (int): Number of records
- `**kwargs`: Additional polyfactory arguments

**Returns:** List of dictionaries

**`create_dataframe_from_dicts(spark, data, schema=None) -> DataFrame`**

Convert dictionaries to DataFrame with inferred schema.

**Parameters:**
- `spark` (SparkSession): Active Spark session
- `data` (List[Dict]): Data to convert
- `schema` (Optional[StructType]): Optional custom schema

**Returns:** PySpark DataFrame

### Function: `build_spark_dataframe`

```python
build_spark_dataframe(model, spark, size=10, schema=None, **kwargs) -> DataFrame
```

Convenience function to generate DataFrame without decorator or factory class.

### Schema Utilities

#### `infer_schema(model, schema=None) -> StructType`

Infer PySpark schema from model type.

#### `python_type_to_spark_type(python_type, nullable=True) -> DataType`

Convert Python type to PySpark DataType.

#### `dataclass_to_struct_type(dataclass_type) -> StructType`

Convert dataclass to StructType.

#### `pydantic_to_struct_type(model_type) -> StructType`

Convert Pydantic model to StructType.

### Runtime Utilities

#### `is_pyspark_available() -> bool`

Check if PySpark is installed and available.

## 🧪 Testing

Run the test suite:

```bash
# Install dev dependencies
pip install "polyspark[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=polyspark --cov-report=html

# Run specific test file
pytest tests/test_factory.py -v
```

## 💡 Examples

Explore complete examples in the [`examples/`](https://github.com/eddiethedean/polyspark/tree/main/examples) directory:

### Core Examples
- **[basic_usage.py](https://github.com/eddiethedean/polyspark/blob/main/examples/basic_usage.py)** - Getting started with dataclasses
- **[decorator_usage.py](https://github.com/eddiethedean/polyspark/blob/main/examples/decorator_usage.py)** - Using the `@spark_factory` decorator
- **[pydantic_models.py](https://github.com/eddiethedean/polyspark/blob/main/examples/pydantic_models.py)** - Pydantic model integration
- **[complex_types.py](https://github.com/eddiethedean/polyspark/blob/main/examples/complex_types.py)** - Arrays, maps, and nested structures
- **[direct_schema.py](https://github.com/eddiethedean/polyspark/blob/main/examples/direct_schema.py)** - Explicit PySpark schema usage

### Advanced Examples
- **[testing_patterns.py](https://github.com/eddiethedean/polyspark/blob/main/examples/testing_patterns.py)** ⭐ NEW - Unit testing, integration testing, and test fixtures
- **[custom_providers.py](https://github.com/eddiethedean/polyspark/blob/main/examples/custom_providers.py)** ⭐ NEW - Custom data generation for realistic test data
- **[production_usage.py](https://github.com/eddiethedean/polyspark/blob/main/examples/production_usage.py)** ⭐ NEW - Large-scale generation, partitioning, and performance optimization

## 🐛 Troubleshooting

### "PySpark not available" Error

```python
# Make sure PySpark is installed
pip install pyspark

# Or use build_dicts() which doesn't need PySpark
dicts = MyModel.build_dicts(size=100)
```

### Schema Inference Issues

If schema inference fails, provide an explicit schema:

```python
from pyspark.sql.types import StructType, StructField, StringType

schema = StructType([StructField("field", StringType(), True)])
df = MyModel.build_dataframe(spark, size=100, schema=schema)
```

### Type Not Supported

If you encounter `UnsupportedTypeError`, the type may not have a direct PySpark equivalent. Use a supported type or provide an explicit schema.

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Run linting (`ruff check . && black --check .`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

See [CONTRIBUTING.md](https://github.com/eddiethedean/polyspark/blob/main/CONTRIBUTING.md) for detailed guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[polyfactory](https://github.com/litestar-org/polyfactory)** - The powerful factory library that powers Polyspark's data generation
- **[PySpark](https://spark.apache.org/docs/latest/api/python/)** - The Python API for Apache Spark
- **[Faker](https://github.com/joke2k/faker)** - Realistic fake data generation (used by polyfactory)

## 🔗 Related Projects

- [polyfactory](https://github.com/litestar-org/polyfactory) - Factory library for mock data
- [PySpark](https://spark.apache.org/docs/latest/api/python/) - Python API for Apache Spark  
- [Pydantic](https://docs.pydantic.dev/) - Data validation using Python type annotations
- [pytest](https://docs.pytest.org/) - Testing framework

## 📞 Support

- 🐛 **Bug Reports**: [Open an issue](https://github.com/eddiethedean/polyspark/issues)
- 💡 **Feature Requests**: [Start a discussion](https://github.com/eddiethedean/polyspark/discussions)
- 📖 **Documentation**: [Read the guide](https://github.com/eddiethedean/polyspark#readme)
- ⭐ **Star us on GitHub** if you find Polyspark helpful!

---

<p align="center">
  <i>Built with ❤️ for the PySpark community</i>
</p>

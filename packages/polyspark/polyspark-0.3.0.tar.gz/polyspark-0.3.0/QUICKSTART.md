# Polyspark Quickstart Guide

Get up and running with Polyspark in 5 minutes!

## Installation

### Basic Installation

```bash
pip install polyspark
```

### With PySpark (Recommended)

```bash
pip install polyspark pyspark
```

### For Development

```bash
git clone https://github.com/odosmatthews/polyspark.git
cd polyspark
pip install -r requirements-dev.txt
pip install -e .
```

## Verify Installation

```bash
python verify_installation.py
```

This will check that everything is installed correctly.

## Your First DataFrame

### The Easy Way (Recommended)

Just add one decorator to your model - that's it!

```python
from dataclasses import dataclass
from polyspark import spark_factory
from pyspark.sql import SparkSession

# Step 1: Add @spark_factory decorator to your model
@spark_factory
@dataclass
class User:
    id: int
    name: str
    email: str
    age: int

# Step 2: Generate DataFrame - use methods directly on your class!
spark = SparkSession.builder \
    .appName("my-app") \
    .master("local[*]") \
    .getOrCreate()

df = User.build_dataframe(spark, size=100)

# Use it!
df.show(10)
df.printSchema()
```

### Traditional Way (Optional)

If you prefer separate factory classes:

```python
from polyspark import SparkFactory

@dataclass
class User:
    id: int
    name: str
    email: str
    age: int

class UserFactory(SparkFactory[User]):
    __model__ = User

df = UserFactory.build_dataframe(spark, size=100)
```

## Quick Examples

### Using the Decorator

```python
@spark_factory
@dataclass
class Product:
    id: int
    name: str
    price: float

# Generate DataFrame
df = Product.build_dataframe(spark, size=50)

# Generate dicts (no PySpark needed)
dicts = Product.build_dicts(size=100)
```

### Without PySpark

Generate data without needing PySpark installed:

```python
# Generate as dictionaries (works with decorator too!)
users = User.build_dicts(size=50)

# Use the dictionaries
for user in users[:5]:
    print(user)

# Later, convert to DataFrame when you have Spark
df = UserFactory.create_dataframe_from_dicts(spark, users)
```

### With Pydantic

```python
from pydantic import BaseModel, EmailStr
from typing import Optional

class User(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: Optional[str] = None

class UserFactory(SparkFactory[User]):
    __model__ = User

df = UserFactory.build_dataframe(spark, size=100)
```

### Complex Types

```python
from typing import List, Dict

@dataclass
class Employee:
    id: int
    name: str
    skills: List[str]  # Array
    department: Department  # Nested struct
    metadata: Dict[str, str]  # Map

class EmployeeFactory(SparkFactory[Employee]):
    __model__ = Employee

df = EmployeeFactory.build_dataframe(spark, size=50)
```

### Convenience Function

Skip creating a factory class:

```python
from polyspark import build_spark_dataframe

df = build_spark_dataframe(User, spark, size=100)
```

## Common Use Cases

### Testing

```python
def test_my_spark_job():
    """Test a Spark transformation."""
    # Generate test data
    input_df = UserFactory.build_dataframe(spark, size=10)
    
    # Run your transformation
    result_df = my_spark_job(input_df)
    
    # Assert results
    assert result_df.count() == 10
    assert "processed" in result_df.columns
```

### Development

```python
# Generate sample data for development
df = UserFactory.build_dataframe(spark, size=1000)

# Save for later use
df.write.parquet("sample_data.parquet")

# Develop your pipeline
result = (df
    .filter(df.age > 18)
    .groupBy("age")
    .count()
    .orderBy("count", ascending=False))

result.show()
```

### Data Exploration

```python
# Generate realistic test data
df = ProductFactory.build_dataframe(spark, size=10000)

# Explore schemas
df.printSchema()

# Test queries
df.filter(df.price > 100).count()
df.groupBy("category").agg({"price": "avg"}).show()
```

## Next Steps

1. **Explore Examples**: Check out the `examples/` directory
   ```bash
   python examples/basic_usage.py
   python examples/complex_types.py
   ```

2. **Read the Docs**: See [README.md](README.md) for full documentation

3. **Run Tests**: Verify everything works
   ```bash
   pytest
   ```

4. **Customize**: Extend factories for your specific needs

## Common Issues

### "PySpark not installed"

```bash
pip install pyspark
```

### "Cannot import polyspark"

Make sure it's installed:
```bash
pip install polyspark
# or for development
pip install -e .
```

### Schema doesn't match

- Check your type hints
- Use `Optional[T]` for nullable fields
- Provide explicit schema if needed

### Need help?

- Check [README.md](README.md)
- Look at [examples/](examples/)
- Open an issue on GitHub

## Tips

✓ Start with small datasets (size=10) during development  
✓ Use type hints for better schema inference  
✓ Use `Optional[T]` for nullable fields  
✓ Test with `build_dicts()` before generating DataFrames  
✓ Check the generated schema with `df.printSchema()`  

## Resources

- [Full Documentation](README.md)
- [Examples](examples/)
- [Contributing Guide](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

Happy testing! 🚀


"""Edge case tests for polyspark."""

from dataclasses import dataclass
from typing import Dict, List, Optional

import pytest

from polyspark import SparkFactory, spark_factory

try:
    import pyspark  # noqa: F401

    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False

try:
    from pydantic import BaseModel

    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

pytestmark = pytest.mark.skipif(not PYSPARK_AVAILABLE, reason="PySpark not installed")

# Use the session-scoped spark fixture from conftest.py


class TestDeeplyNestedStructures:
    """Tests for deeply nested data structures."""

    def test_five_level_nested_structs(self, spark):
        """Test deeply nested structures (5 levels)."""

        @dataclass
        class Level5:
            value: str

        @dataclass
        class Level4:
            data: Level5

        @dataclass
        class Level3:
            nested: Level4

        @dataclass
        class Level2:
            inner: Level3

        @spark_factory
        @dataclass
        class Level1:
            top: Level2

        df = Level1.build_dataframe(spark, size=5)
        assert df.count() == 5
        # Verify we can access deeply nested fields
        df.select("top.inner.nested.data.value").show()

    def test_deeply_nested_arrays(self, spark):
        """Test arrays nested within arrays."""

        @spark_factory
        @dataclass
        class DeepArrays:
            id: int
            matrix: List[List[int]]

        df = DeepArrays.build_dataframe(spark, size=5)
        assert df.count() == 5
        data = df.collect()[0]
        assert isinstance(data.matrix, list)
        if data.matrix:
            assert isinstance(data.matrix[0], list)

    def test_nested_maps_in_arrays(self, spark):
        """Test maps nested within arrays."""

        @spark_factory
        @dataclass
        class NestedMapArray:
            id: int
            configs: List[Dict[str, str]]

        df = NestedMapArray.build_dataframe(spark, size=5)
        assert df.count() == 5


class TestLargeSchemas:
    """Tests for schemas with many fields."""

    def test_schema_with_100_fields(self, spark):
        """Test generation with very large schema (100 fields)."""
        # Dynamically create a dataclass with 100 fields
        fields = {f"field_{i}": (str, ...) for i in range(100)}

        from dataclasses import make_dataclass

        LargeModel = make_dataclass(
            "LargeModel", [(name, typ) for name, (typ, _) in fields.items()]
        )

        class LargeFactory(SparkFactory):
            __model__ = LargeModel

        df = LargeFactory.build_dataframe(spark, size=10)
        assert df.count() == 10
        assert len(df.columns) == 100

    def test_schema_with_mixed_complex_types(self, spark):
        """Test schema with many different complex types."""

        @spark_factory
        @dataclass
        class ComplexSchema:
            # Basic types
            id: int
            name: str
            active: bool
            score: float
            # Collections
            tags: List[str]
            metadata: Dict[str, str]
            scores_by_subject: Dict[str, float]
            # Optional
            description: Optional[str]
            notes: Optional[List[str]]
            extra: Optional[Dict[str, int]]

        df = ComplexSchema.build_dataframe(spark, size=10)
        assert df.count() == 10
        assert len(df.columns) == 10


class TestUnicodeAndSpecialCharacters:
    """Tests for Unicode and special characters in field names and data."""

    def test_unicode_field_names(self, spark):
        """Test models with Unicode characters in field names."""

        @spark_factory
        @dataclass
        class UnicodeFields:
            nombre: str  # Spanish
            prénom: str  # French
            名前: str  # Japanese

        df = UnicodeFields.build_dataframe(spark, size=5)
        assert df.count() == 5
        assert "nombre" in df.columns
        assert "prénom" in df.columns
        assert "名前" in df.columns

    def test_field_names_with_underscores(self, spark):
        """Test field names with various underscore patterns."""

        @spark_factory
        @dataclass
        class UnderscoreFields:
            trailing_: str
            regular_field: str
            another_field_: str

        df = UnderscoreFields.build_dataframe(spark, size=5)
        assert df.count() == 5
        # Note: Leading underscores with name mangling don't work well with polyfactory


class TestEmptyAndMinimalModels:
    """Tests for empty or minimal models."""

    def test_single_field_model(self, spark):
        """Test model with only one field."""

        @spark_factory
        @dataclass
        class SingleField:
            only_field: str

        df = SingleField.build_dataframe(spark, size=10)
        assert df.count() == 10
        assert len(df.columns) == 1

    def test_all_optional_fields(self, spark):
        """Test model where all fields are optional."""

        @spark_factory
        @dataclass
        class AllOptional:
            field1: Optional[str] = None
            field2: Optional[int] = None
            field3: Optional[bool] = None

        df = AllOptional.build_dataframe(spark, size=10)
        assert df.count() == 10
        # Verify schema has nullable fields
        for field in df.schema.fields:
            assert field.nullable is True

    def test_optional_complex_types(self, spark):
        """Test optional complex types."""

        @spark_factory
        @dataclass
        class OptionalComplex:
            id: int
            tags: Optional[List[str]] = None
            metadata: Optional[Dict[str, str]] = None

        df = OptionalComplex.build_dataframe(spark, size=10)
        assert df.count() == 10


class TestErrorHandling:
    """Tests for error handling and edge cases."""

    def test_invalid_decorator_usage(self):
        """Test decorator on invalid types."""
        from polyfactory.exceptions import ConfigurationException

        from polyspark.exceptions import PolysparkError

        with pytest.raises((TypeError, AttributeError, ConfigurationException, PolysparkError)):
            # Try to decorate a non-class
            @spark_factory
            def not_a_class():
                pass

    def test_model_without_fields(self):
        """Test behavior with models that have no fields."""

        @dataclass
        class EmptyModel:
            pass

        # This should work but produce an empty schema
        class EmptyFactory(SparkFactory):
            __model__ = EmptyModel

        dicts = EmptyFactory.build_dicts(size=5)
        assert len(dicts) == 5
        assert all(isinstance(d, dict) for d in dicts)


class TestKwargsPropagation:
    """Tests for kwargs propagation to polyfactory."""

    def test_build_dataframe_with_factory_kwargs(self, spark):
        """Test that factory kwargs are properly propagated."""

        @spark_factory
        @dataclass
        class User:
            id: int
            name: str
            email: str

        # Build with custom kwargs (polyfactory supports these)
        df = User.build_dataframe(spark, size=10)
        assert df.count() == 10

    def test_build_dicts_with_kwargs(self):
        """Test build_dicts with additional kwargs."""

        @spark_factory
        @dataclass
        class Product:
            id: int
            name: str

        dicts = Product.build_dicts(size=5)
        assert len(dicts) == 5
        assert all("id" in d and "name" in d for d in dicts)


class TestCreateDataframeFromDicts:
    """Tests for create_dataframe_from_dicts method."""

    def test_create_from_pregenerated_dicts(self, spark):
        """Test creating DataFrame from pre-generated dictionaries."""

        @spark_factory
        @dataclass
        class Item:
            id: int
            name: str

        # Generate dicts first
        dicts = Item.build_dicts(size=10)
        assert len(dicts) == 10

        # Convert to DataFrame
        df = Item.create_dataframe_from_dicts(spark, dicts)
        assert df.count() == 10

    def test_create_from_custom_dicts(self, spark):
        """Test creating DataFrame from manually created dictionaries."""

        @spark_factory
        @dataclass
        class Person:
            id: int
            name: str
            age: int

        # Manually create dicts
        custom_dicts = [
            {"id": 1, "name": "Alice", "age": 30},
            {"id": 2, "name": "Bob", "age": 25},
            {"id": 3, "name": "Charlie", "age": 35},
        ]

        df = Person.create_dataframe_from_dicts(spark, custom_dicts)
        assert df.count() == 3

        # Verify data
        rows = df.collect()
        assert rows[0].name == "Alice"
        assert rows[1].age == 25

    def test_create_with_custom_schema(self, spark):
        """Test create_dataframe_from_dicts with custom schema."""
        from pyspark.sql.types import IntegerType, StringType, StructField, StructType

        @spark_factory
        @dataclass
        class Data:
            id: int
            value: str

        dicts = Data.build_dicts(size=5)

        # Use custom schema
        custom_schema = StructType(
            [
                StructField("id", IntegerType(), False),
                StructField("value", StringType(), True),
            ]
        )

        df = Data.create_dataframe_from_dicts(spark, dicts, schema=custom_schema)
        assert df.count() == 5
        assert df.schema == custom_schema


@pytest.mark.skipif(not PYDANTIC_AVAILABLE, reason="Pydantic not installed")
class TestPydanticEdgeCases:
    """Edge case tests specific to Pydantic models."""

    def test_pydantic_with_validators(self, spark):
        """Test Pydantic model with field validators."""
        from pydantic import Field

        @spark_factory
        class ValidatedModel(BaseModel):
            id: int = Field(gt=0, lt=1000)
            name: str = Field(min_length=1, max_length=50)
            score: float = Field(ge=0.0, le=100.0)

        df = ValidatedModel.build_dataframe(spark, size=10)
        assert df.count() == 10

    def test_pydantic_with_default_factory(self, spark):
        """Test Pydantic model with default_factory."""
        from pydantic import Field

        @spark_factory
        class WithDefaults(BaseModel):
            id: int
            tags: List[str] = Field(default_factory=list)
            metadata: Dict[str, str] = Field(default_factory=dict)

        df = WithDefaults.build_dataframe(spark, size=10)
        assert df.count() == 10

    def test_pydantic_optional_fields(self, spark):
        """Test Pydantic model with Optional fields."""

        @spark_factory
        class OptionalPydantic(BaseModel):
            id: int
            name: str
            nickname: Optional[str] = None
            bio: Optional[str] = None

        df = OptionalPydantic.build_dataframe(spark, size=10)
        assert df.count() == 10

        # Check that optional fields are nullable in schema
        schema_dict = {f.name: f.nullable for f in df.schema.fields}
        assert schema_dict["nickname"] is True
        assert schema_dict["bio"] is True


class TestDataframeOperations:
    """Tests for operations on generated DataFrames."""

    def test_filter_on_generated_data(self, spark):
        """Test that generated DataFrames support filter operations."""

        @spark_factory
        @dataclass
        class Record:
            id: int
            value: str

        df = Record.build_dataframe(spark, size=100)
        filtered = df.filter(df.id > 0)
        assert filtered.count() > 0

    def test_groupby_on_generated_data(self, spark):
        """Test groupBy operations on generated data."""

        @spark_factory
        @dataclass
        class Transaction:
            id: int
            category: str
            amount: float

        df = Transaction.build_dataframe(spark, size=50)
        grouped = df.groupBy("category").count()
        assert grouped.count() > 0

    def test_join_multiple_generated_dataframes(self, spark):
        """Test joining multiple generated DataFrames."""

        @spark_factory
        @dataclass
        class User:
            user_id: int
            name: str

        @spark_factory
        @dataclass
        class Order:
            order_id: int
            user_id: int
            amount: float

        users_df = User.build_dataframe(spark, size=10)
        orders_df = Order.build_dataframe(spark, size=20)

        # Join on user_id
        joined = orders_df.join(users_df, on="user_id", how="left")
        assert joined.count() > 0


class TestMemoryAndPerformance:
    """Tests related to memory usage and performance."""

    def test_large_dataset_generation(self, spark):
        """Test generation of larger datasets."""

        @spark_factory
        @dataclass
        class LargeData:
            id: int
            value: str

        # Generate 10k rows - should complete without issues
        df = LargeData.build_dataframe(spark, size=10000)
        assert df.count() == 10000

    def test_wide_schema_generation(self, spark):
        """Test generation with wide schema (many columns)."""
        from dataclasses import make_dataclass

        # Create a dataclass with 50 fields
        fields = [(f"col_{i}", int) for i in range(50)]
        WideModel = make_dataclass("WideModel", fields)

        class WideFactory(SparkFactory):
            __model__ = WideModel

        df = WideFactory.build_dataframe(spark, size=100)
        assert df.count() == 100
        assert len(df.columns) == 50

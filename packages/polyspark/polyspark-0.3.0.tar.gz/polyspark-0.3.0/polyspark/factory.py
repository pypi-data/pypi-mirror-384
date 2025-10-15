"""SparkFactory class for generating PySpark DataFrames."""

import functools
from abc import ABC
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

from polyfactory.factories import DataclassFactory

try:
    from pydantic import BaseModel
except ImportError:
    BaseModel = None

from polyspark.exceptions import PySparkNotAvailableError
from polyspark.protocols import (
    DataFrameProtocol,
    SparkSessionProtocol,
    StructTypeProtocol,
    is_pyspark_available,
)
from polyspark.schema import infer_schema

T = TypeVar("T")


class SparkFactory(DataclassFactory[T], ABC):
    """Factory for generating PySpark DataFrames from models.

    This factory extends polyfactory's DataclassFactory to support generating
    PySpark DataFrames instead of model instances. It works with dataclasses,
    Pydantic models, and TypedDicts.

    Example:
        ```python
        from dataclasses import dataclass
        from polyspark import SparkFactory
        from pyspark.sql import SparkSession

        @dataclass
        class User:
            id: int
            name: str
            email: str

        class UserFactory(SparkFactory[User]):
            __model__ = User

        spark = SparkSession.builder.getOrCreate()
        df = UserFactory.build_dataframe(spark, size=100)
        df.show()
        ```
    """

    __is_base_factory__ = True

    @classmethod
    def build_dataframe(
        cls,
        spark: SparkSessionProtocol,
        size: int = 10,
        schema: Optional[Union[StructTypeProtocol, List[str]]] = None,
        **kwargs: Any,
    ) -> DataFrameProtocol:
        """Build a PySpark DataFrame with generated data.

        Args:
            spark: SparkSession instance to create the DataFrame.
            size: Number of rows to generate.
            schema: Optional explicit schema. Can be:
                   - PySpark StructType: Used as-is
                   - List[str]: Column names to include (infers types from model)
                   - None: Infers full schema from model
            **kwargs: Additional keyword arguments passed to the factory.

        Returns:
            A PySpark DataFrame with generated data.

        Raises:
            PySparkNotAvailableError: If PySpark is not installed and schema is a StructType.
        """
        # Infer schema first (before generating data, so error is raised early)
        inferred_schema = infer_schema(cls.__model__, schema)

        # If schema is a StructType but PySpark is not available, raise error
        # (This means user explicitly provided a StructType but PySpark isn't installed)
        if not is_pyspark_available() and not isinstance(inferred_schema, str):
            raise PySparkNotAvailableError(
                "PySpark is required when using StructType schemas. "
                "Install it with: pip install pyspark\n"
                "Or use build_dicts() to generate data without PySpark."
            )

        # Generate data as list of dictionaries
        data = cls.build_dicts(size=size, **kwargs)

        # Create DataFrame
        # Note: If PySpark is not available, inferred_schema will be a DDL string
        # which works with mock-spark and other PySpark-compatible libraries
        df = spark.createDataFrame(data, schema=inferred_schema)
        return df

    @classmethod
    def build_dicts(
        cls,
        size: int = 10,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Build a list of dictionaries with generated data.

        This method doesn't require PySpark and can be used to generate
        data that can be converted to a DataFrame later.

        Args:
            size: Number of records to generate.
            **kwargs: Additional keyword arguments passed to the factory.

        Returns:
            A list of dictionaries with generated data.
        """
        instances = cls.batch(size=size, **kwargs)

        # Convert instances to dictionaries
        dicts = []
        for instance in instances:
            if is_dataclass(instance):
                dicts.append(asdict(instance))  # type: ignore[arg-type]
            elif BaseModel is not None and isinstance(instance, BaseModel):
                dicts.append(instance.model_dump())
            elif isinstance(instance, dict):
                dicts.append(instance)
            else:
                # Try to convert to dict
                try:
                    dicts.append(dict(instance))  # type: ignore[call-overload]
                except (TypeError, ValueError):
                    dicts.append(instance.__dict__)

        return dicts

    @classmethod
    def create_dataframe_from_dicts(
        cls,
        spark: SparkSessionProtocol,
        data: List[Dict[str, Any]],
        schema: Optional[Union[StructTypeProtocol, List[str]]] = None,
    ) -> DataFrameProtocol:
        """Convert pre-generated dictionary data to a PySpark DataFrame.

        Useful when you've generated data with build_dicts() and want to
        convert it to a DataFrame later.

        Args:
            spark: SparkSession instance to create the DataFrame.
            data: List of dictionaries to convert.
            schema: Optional explicit schema.

        Returns:
            A PySpark DataFrame.

        Raises:
            PySparkNotAvailableError: If PySpark is not installed and schema is a StructType.
        """
        inferred_schema = infer_schema(cls.__model__, schema)

        # If schema is a StructType but PySpark is not available, raise error
        if not is_pyspark_available() and not isinstance(inferred_schema, str):
            raise PySparkNotAvailableError(
                "PySpark is required when using StructType schemas. "
                "Install it with: pip install pyspark\n"
                "Or use build_dicts() to generate data without PySpark."
            )

        return spark.createDataFrame(data, schema=inferred_schema)


def build_spark_dataframe(
    model: Type[T],
    spark: SparkSessionProtocol,
    size: int = 10,
    schema: Optional[Union[StructTypeProtocol, List[str]]] = None,
    **kwargs: Any,
) -> Any:
    """Convenience function to build a DataFrame without creating a factory class.

    Args:
        model: The model type (dataclass, Pydantic, TypedDict).
        spark: SparkSession instance.
        size: Number of rows to generate.
        schema: Optional explicit schema.
        **kwargs: Additional keyword arguments for data generation.

    Returns:
        A PySpark DataFrame with generated data.

    Example:
        ```python
        from dataclasses import dataclass
        from polyspark import build_spark_dataframe
        from pyspark.sql import SparkSession

        @dataclass
        class Product:
            id: int
            name: str
            price: float

        spark = SparkSession.builder.getOrCreate()
        df = build_spark_dataframe(Product, spark, size=50)
        df.show()
        ```
    """
    # Create a dynamic factory class
    factory_class = type(f"{model.__name__}Factory", (SparkFactory,), {"__model__": model})

    return factory_class.build_dataframe(spark, size=size, schema=schema, **kwargs)  # type: ignore[attr-defined]


def spark_factory(cls: Type[T]) -> Type[T]:
    """Decorator to add factory methods directly to a model class.

    This decorator eliminates the need to create a separate factory class.
    It adds classmethods to the decorated class for generating DataFrames
    and dictionaries.

    Args:
        cls: The model class (dataclass, Pydantic model, or TypedDict).

    Returns:
        The same class with added factory methods.

    Example:
        ```python
        from dataclasses import dataclass
        from polyspark import spark_factory
        from pyspark.sql import SparkSession

        @spark_factory
        @dataclass
        class User:
            id: int
            name: str
            email: str

        # Use directly on the class!
        spark = SparkSession.builder.getOrCreate()
        df = User.build_dataframe(spark, size=100)
        dicts = User.build_dicts(size=50)
        ```
    """
    # Determine the appropriate base factory and create a custom factory
    if BaseModel is not None and isinstance(cls, type) and issubclass(cls, BaseModel):
        # Pydantic model - we need to create a special factory that inherits from both
        try:
            from polyfactory.factories.pydantic_factory import ModelFactory as PydanticModelFactory

            # Create a hybrid factory that combines PydanticModelFactory with our methods
            class _PydanticSparkFactory(PydanticModelFactory):
                __is_base_factory__ = True  # Mark as base to skip validation

                # Add our custom methods - note: these are already classmethods
                # We need to extract the actual function and rewrap it
                @classmethod
                def build_dataframe(cls, *args: Any, **kwargs: Any) -> Any:
                    return SparkFactory.build_dataframe.__func__(cls, *args, **kwargs)  # type: ignore[attr-defined]

                @classmethod
                def build_dicts(cls, *args: Any, **kwargs: Any) -> Any:
                    return SparkFactory.build_dicts.__func__(cls, *args, **kwargs)  # type: ignore[attr-defined]

                @classmethod
                def create_dataframe_from_dicts(cls, *args: Any, **kwargs: Any) -> Any:
                    return SparkFactory.create_dataframe_from_dicts.__func__(cls, *args, **kwargs)  # type: ignore[attr-defined]

            factory_class = type(
                f"_{cls.__name__}Factory",
                (_PydanticSparkFactory,),
                {"__model__": cls, "__is_base_factory__": False},
            )
        except ImportError:
            # Fallback to SparkFactory if Pydantic not available
            factory_class = type(
                f"_{cls.__name__}Factory",
                (SparkFactory,),
                {"__model__": cls, "__is_base_factory__": False},
            )
    else:
        # Dataclass or other - use SparkFactory directly
        factory_class = type(
            f"_{cls.__name__}Factory",
            (SparkFactory,),
            {"__model__": cls, "__is_base_factory__": False},
        )

    # Define the classmethod wrappers that delegate to the factory
    @classmethod  # type: ignore[misc]
    @functools.wraps(SparkFactory.build_dataframe)
    def build_dataframe(
        model_cls: Type[T],
        spark: SparkSessionProtocol,
        size: int = 10,
        schema: Optional[Union[StructTypeProtocol, List[str]]] = None,
        **kwargs: Any,
    ) -> Any:
        """Build a PySpark DataFrame with generated data.

        Args:
            spark: SparkSession instance to create the DataFrame.
            size: Number of rows to generate.
            schema: Optional explicit schema. Can be:
                   - PySpark StructType: Used as-is
                   - List[str]: Column names to include (infers types from model)
                   - None: Infers full schema from model
            **kwargs: Additional keyword arguments passed to the factory.

        Returns:
            A PySpark DataFrame with generated data.

        Raises:
            PySparkNotAvailableError: If PySpark is not installed.
        """
        return factory_class.build_dataframe(spark, size=size, schema=schema, **kwargs)  # type: ignore[attr-defined]

    @classmethod  # type: ignore[misc]
    @functools.wraps(SparkFactory.build_dicts)
    def build_dicts(
        model_cls: Type[T],
        size: int = 10,
        **kwargs: Any,
    ) -> Any:
        """Build a list of dictionaries with generated data.

        This method doesn't require PySpark and can be used to generate
        data that can be converted to a DataFrame later.

        Args:
            size: Number of records to generate.
            **kwargs: Additional keyword arguments passed to the factory.

        Returns:
            A list of dictionaries with generated data.
        """
        return factory_class.build_dicts(size=size, **kwargs)  # type: ignore[attr-defined]

    @classmethod  # type: ignore[misc]
    @functools.wraps(SparkFactory.create_dataframe_from_dicts)
    def create_dataframe_from_dicts(
        model_cls: Type[T],
        spark: SparkSessionProtocol,
        data: List[Dict[str, Any]],
        schema: Optional[Union[StructTypeProtocol, List[str]]] = None,
    ) -> Any:
        """Convert pre-generated dictionary data to a PySpark DataFrame.

        Useful when you've generated data with build_dicts() and want to
        convert it to a DataFrame later.

        Args:
            spark: SparkSession instance to create the DataFrame.
            data: List of dictionaries to convert.
            schema: Optional explicit schema.

        Returns:
            A PySpark DataFrame.

        Raises:
            PySparkNotAvailableError: If PySpark is not installed.
        """
        return factory_class.create_dataframe_from_dicts(spark, data, schema=schema)  # type: ignore[attr-defined]

    # Add the methods to the class
    cls.build_dataframe = build_dataframe  # type: ignore[attr-defined]
    cls.build_dicts = build_dicts  # type: ignore[attr-defined]
    cls.create_dataframe_from_dicts = create_dataframe_from_dicts  # type: ignore[attr-defined]

    # Store reference to the factory class for advanced use cases
    cls._polyspark_factory = factory_class  # type: ignore[attr-defined]

    return cls

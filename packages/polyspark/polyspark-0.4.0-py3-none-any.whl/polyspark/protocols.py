"""Protocol definitions for PySpark types to avoid hard dependency."""

from typing import Any, Dict, List, Optional, Protocol, Union, runtime_checkable

from typing_extensions import Self


@runtime_checkable
class DataTypeProtocol(Protocol):
    """Protocol matching PySpark DataType interface."""

    def jsonValue(self) -> Dict[str, Any]:
        """Return JSON representation."""
        ...

    def simpleString(self) -> str:
        """Return simple string representation."""
        ...


@runtime_checkable
class StructFieldProtocol(Protocol):
    """Protocol matching PySpark StructField interface."""

    name: str
    dataType: DataTypeProtocol
    nullable: bool
    metadata: Dict[str, Any]

    def jsonValue(self) -> Dict[str, Any]:
        """Return JSON representation."""
        ...


@runtime_checkable
class StructTypeProtocol(Protocol):
    """Protocol matching PySpark StructType interface."""

    fields: List[StructFieldProtocol]

    def add(
        self,
        field: Union[str, StructFieldProtocol],
        data_type: Optional[DataTypeProtocol] = None,
        nullable: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Self:
        """Add field to struct."""
        ...

    def jsonValue(self) -> Dict[str, Any]:
        """Return JSON representation."""
        ...


@runtime_checkable
class RowProtocol(Protocol):
    """Protocol matching PySpark Row interface."""

    def asDict(self, recursive: bool = False) -> Dict[str, Any]:
        """Convert row to dictionary."""
        ...

    def __getitem__(self, key: Union[int, str]) -> Any:
        """Get item by index or key."""
        ...


@runtime_checkable
class DataFrameProtocol(Protocol):
    """Protocol matching PySpark DataFrame interface."""

    schema: StructTypeProtocol
    columns: List[str]
    dtypes: List[Any]

    def show(self, n: int = 20, truncate: Union[bool, int] = True, vertical: bool = False) -> None:
        """Display the DataFrame."""
        ...

    def collect(self) -> List[RowProtocol]:
        """Return all rows."""
        ...

    def count(self) -> int:
        """Return the number of rows."""
        ...

    def take(self, num: int) -> List[RowProtocol]:
        """Return first n rows."""
        ...

    def toPandas(self) -> Any:
        """Convert to pandas DataFrame."""
        ...

    def select(self, *cols: Any) -> Self:
        """Select columns."""
        ...

    def filter(self, condition: Any) -> Self:
        """Filter rows."""
        ...

    def orderBy(self, *cols: Any, **kwargs: Any) -> Self:
        """Order by columns."""
        ...

    def distinct(self) -> Self:
        """Return distinct rows."""
        ...

    def dropDuplicates(self, subset: Optional[List[str]] = None) -> Self:
        """Drop duplicate rows."""
        ...

    def describe(self, *cols: Any) -> Self:
        """Generate descriptive statistics."""
        ...

    @property
    def write(self) -> Any:
        """DataFrameWriter for saving."""
        ...


@runtime_checkable
class SparkSessionProtocol(Protocol):
    """Protocol matching PySpark SparkSession interface."""

    def createDataFrame(
        self,
        data: Union[List[Any], List[Dict[str, Any]]],
        schema: Optional[Union[StructTypeProtocol, List[str]]] = None,
    ) -> DataFrameProtocol:
        """Create a DataFrame from data."""
        ...

    @property
    def read(self) -> Any:
        """DataFrameReader for loading data."""
        ...


def is_pyspark_available() -> bool:
    """Check if PySpark is available at runtime.

    Returns:
        bool: True if pyspark can be imported, False otherwise.
    """
    try:
        import pyspark  # noqa: F401

        return True
    except ImportError:
        return False


def get_pyspark_types() -> Optional[Any]:
    """Get pyspark.sql.types module if available.

    Returns:
        The pyspark.sql.types module if available, None otherwise.
    """
    if is_pyspark_available():
        from pyspark.sql import types as pyspark_types

        return pyspark_types
    return None


def get_spark_session() -> Optional[Any]:
    """Get SparkSession class if available.

    Returns:
        The SparkSession class if available, None otherwise.
    """
    if is_pyspark_available():
        from pyspark.sql import SparkSession

        return SparkSession
    return None

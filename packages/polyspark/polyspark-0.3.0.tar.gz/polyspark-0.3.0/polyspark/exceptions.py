"""Custom exceptions for polyspark."""


class PolysparkError(Exception):
    """Base exception for polyspark."""

    pass


class PySparkNotAvailableError(PolysparkError):
    """Raised when PySpark is required but not installed."""

    def __init__(
        self, message: str = "PySpark is not installed. Install it with: pip install pyspark"
    ):
        super().__init__(message)


class SchemaInferenceError(PolysparkError):
    """Raised when schema cannot be inferred from a type."""

    pass


class UnsupportedTypeError(PolysparkError):
    """Raised when a type is not supported for conversion."""

    pass

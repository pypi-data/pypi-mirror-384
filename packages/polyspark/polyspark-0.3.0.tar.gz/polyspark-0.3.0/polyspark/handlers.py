"""Custom type handlers for PySpark-specific types."""

import random
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional


def handle_array_type(
    element_handler: Callable[[], Any], min_items: int = 0, max_items: int = 5
) -> List[Any]:
    """Generate a list for PySpark ArrayType.

    Args:
        element_handler: Function to generate a single element.
        min_items: Minimum number of items.
        max_items: Maximum number of items.

    Returns:
        A list of generated elements.
    """
    size = random.randint(min_items, max_items)
    return [element_handler() for _ in range(size)]


def handle_map_type(
    key_handler: Callable[[], Any],
    value_handler: Callable[[], Any],
    min_items: int = 0,
    max_items: int = 5,
) -> Dict[Any, Any]:
    """Generate a dictionary for PySpark MapType.

    Args:
        key_handler: Function to generate a key.
        value_handler: Function to generate a value.
        min_items: Minimum number of items.
        max_items: Maximum number of items.

    Returns:
        A dictionary of generated key-value pairs.
    """
    size = random.randint(min_items, max_items)
    result = {}
    for _ in range(size):
        key = key_handler()
        # Ensure unique keys
        attempt = 0
        while key in result and attempt < 100:
            key = key_handler()
            attempt += 1
        result[key] = value_handler()
    return result


def handle_decimal_type(precision: int = 10, scale: int = 2) -> Decimal:
    """Generate a Decimal for PySpark DecimalType.

    Args:
        precision: Total number of digits.
        scale: Number of digits after decimal point.

    Returns:
        A Decimal value.
    """
    max_value = 10 ** (precision - scale) - 1
    integer_part = random.randint(-max_value, max_value)

    if scale > 0:
        fractional_part = random.randint(0, 10**scale - 1)
        value = f"{integer_part}.{str(fractional_part).zfill(scale)}"
    else:
        value = str(integer_part)

    return Decimal(value)


def handle_binary_type(min_length: int = 0, max_length: int = 32) -> bytes:
    """Generate bytes for PySpark BinaryType.

    Args:
        min_length: Minimum number of bytes.
        max_length: Maximum number of bytes.

    Returns:
        Random bytes.
    """
    length = random.randint(min_length, max_length)
    return bytes(random.randint(0, 255) for _ in range(length))


def handle_date_type(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> date:
    """Generate a date for PySpark DateType.

    Args:
        start_date: Minimum date (default: 2000-01-01).
        end_date: Maximum date (default: today).

    Returns:
        A random date.
    """
    if start_date is None:
        start_date = date(2000, 1, 1)
    if end_date is None:
        end_date = date.today()

    days_between = (end_date - start_date).days
    random_days = random.randint(0, days_between)
    return start_date + timedelta(days=random_days)


def handle_timestamp_type(
    start_datetime: Optional[datetime] = None,
    end_datetime: Optional[datetime] = None,
) -> datetime:
    """Generate a datetime for PySpark TimestampType.

    Args:
        start_datetime: Minimum datetime (default: 2000-01-01 00:00:00).
        end_datetime: Maximum datetime (default: now).

    Returns:
        A random datetime.
    """
    if start_datetime is None:
        start_datetime = datetime(2000, 1, 1, 0, 0, 0)
    if end_datetime is None:
        end_datetime = datetime.now()

    seconds_between = int((end_datetime - start_datetime).total_seconds())
    random_seconds = random.randint(0, seconds_between)
    return start_datetime + timedelta(seconds=random_seconds)


def handle_struct_type(field_handlers: Dict[str, Callable[[], Any]]) -> Dict[str, Any]:
    """Generate a dictionary for nested PySpark StructType.

    Args:
        field_handlers: Dictionary mapping field names to their generator functions.

    Returns:
        A dictionary with generated values for each field.
    """
    return {field_name: handler() for field_name, handler in field_handlers.items()}

"""Comprehensive tests for polyspark handlers module."""

import random
from datetime import date, datetime, timedelta
from decimal import Decimal

from polyspark.handlers import (
    handle_array_type,
    handle_binary_type,
    handle_date_type,
    handle_decimal_type,
    handle_map_type,
    handle_struct_type,
    handle_timestamp_type,
)


class TestHandleArrayType:
    """Tests for handle_array_type function."""

    def test_basic_array_generation(self):
        """Test basic array generation with default parameters."""
        result = handle_array_type(lambda: "test", min_items=2, max_items=5)
        assert isinstance(result, list)
        assert 2 <= len(result) <= 5
        assert all(item == "test" for item in result)

    def test_empty_array(self):
        """Test generation of empty arrays."""
        result = handle_array_type(lambda: 42, min_items=0, max_items=0)
        assert result == []

    def test_array_with_varying_elements(self):
        """Test array generation with varying elements."""
        counter = {"value": 0}

        def increment():
            counter["value"] += 1
            return counter["value"]

        result = handle_array_type(increment, min_items=5, max_items=5)
        assert len(result) == 5
        assert result == [1, 2, 3, 4, 5]

    def test_array_with_complex_elements(self):
        """Test array generation with complex element types."""
        result = handle_array_type(lambda: {"key": "value"}, min_items=3, max_items=3)
        assert len(result) == 3
        assert all(item == {"key": "value"} for item in result)

    def test_array_size_randomness(self):
        """Test that array size varies within the specified range."""
        random.seed(42)
        sizes = [len(handle_array_type(lambda: 1, min_items=1, max_items=10)) for _ in range(20)]
        # Should have some variation
        assert len(set(sizes)) > 1
        assert all(1 <= size <= 10 for size in sizes)


class TestHandleMapType:
    """Tests for handle_map_type function."""

    def test_basic_map_generation(self):
        """Test basic map generation with default parameters."""
        key_counter = {"value": 0}

        def key_gen():
            key_counter["value"] += 1
            return f"key_{key_counter['value']}"

        result = handle_map_type(key_gen, lambda: "value", min_items=2, max_items=5)
        assert isinstance(result, dict)
        assert 2 <= len(result) <= 5
        assert all(key.startswith("key_") for key in result.keys())
        assert all(val == "value" for val in result.values())

    def test_empty_map(self):
        """Test generation of empty maps."""
        result = handle_map_type(lambda: "key", lambda: "value", min_items=0, max_items=0)
        assert result == {}

    def test_map_with_varying_values(self):
        """Test map generation with varying values."""
        key_counter = {"value": 0}
        val_counter = {"value": 100}

        def key_gen():
            key_counter["value"] += 1
            return key_counter["value"]

        def val_gen():
            val_counter["value"] += 1
            return val_counter["value"]

        result = handle_map_type(key_gen, val_gen, min_items=3, max_items=3)
        assert len(result) == 3
        assert all(isinstance(k, int) for k in result.keys())
        assert all(isinstance(v, int) for v in result.values())

    def test_map_unique_keys(self):
        """Test that map maintains unique keys even with collisions."""
        # This tests the collision handling in handle_map_type
        result = handle_map_type(lambda: "same_key", lambda: "value", min_items=5, max_items=5)
        # Due to collision handling, it should try to generate unique keys
        # but if they all collide, we'll get fewer items
        assert len(result) >= 1  # At least one item should be added

    def test_map_size_randomness(self):
        """Test that map size varies within the specified range."""
        random.seed(42)
        key_counter = {"value": 0}

        def unique_key_gen():
            key_counter["value"] += 1
            return f"key_{key_counter['value']}"

        sizes = []
        for _ in range(20):
            result = handle_map_type(unique_key_gen, lambda: 1, min_items=1, max_items=10)
            sizes.append(len(result))

        # Should have some variation
        assert len(set(sizes)) > 1
        assert all(1 <= size <= 10 for size in sizes)


class TestHandleDecimalType:
    """Tests for handle_decimal_type function."""

    def test_default_decimal_generation(self):
        """Test decimal generation with default parameters."""
        result = handle_decimal_type()
        assert isinstance(result, Decimal)
        # Default is precision=10, scale=2
        str_repr = str(abs(result))
        # Check it's a valid decimal
        assert "." in str_repr or len(str_repr) <= 10

    def test_decimal_with_custom_precision_and_scale(self):
        """Test decimal with custom precision and scale."""
        result = handle_decimal_type(precision=5, scale=2)
        assert isinstance(result, Decimal)
        # Value should be within bounds: -999.99 to 999.99
        assert abs(result) < 1000

    def test_decimal_with_zero_scale(self):
        """Test decimal with zero scale (integer)."""
        result = handle_decimal_type(precision=5, scale=0)
        assert isinstance(result, Decimal)
        # Should be an integer value
        assert result == result.to_integral_value()
        assert abs(result) <= 99999

    def test_decimal_with_large_scale(self):
        """Test decimal with large scale."""
        result = handle_decimal_type(precision=10, scale=8)
        assert isinstance(result, Decimal)
        # Should have fractional part
        str_repr = str(result)
        if "." in str_repr:
            fractional = str_repr.split(".")[1]
            assert len(fractional) <= 8

    def test_decimal_range(self):
        """Test that decimals are within expected range."""
        random.seed(42)
        for _ in range(10):
            result = handle_decimal_type(precision=4, scale=1)
            # Max value should be 999.9
            assert abs(result) < 1000

    def test_decimal_negative_values(self):
        """Test that negative decimals can be generated."""
        random.seed(42)
        values = [handle_decimal_type() for _ in range(50)]
        # Should have some negative values
        assert any(v < 0 for v in values)


class TestHandleBinaryType:
    """Tests for handle_binary_type function."""

    def test_basic_binary_generation(self):
        """Test basic binary generation."""
        result = handle_binary_type()
        assert isinstance(result, bytes)
        assert 0 <= len(result) <= 32

    def test_empty_binary(self):
        """Test generation of empty binary."""
        result = handle_binary_type(min_length=0, max_length=0)
        assert result == b""

    def test_fixed_length_binary(self):
        """Test fixed length binary generation."""
        result = handle_binary_type(min_length=10, max_length=10)
        assert len(result) == 10
        assert isinstance(result, bytes)

    def test_binary_length_range(self):
        """Test binary length within specified range."""
        random.seed(42)
        for _ in range(10):
            result = handle_binary_type(min_length=5, max_length=15)
            assert 5 <= len(result) <= 15

    def test_binary_content_is_random(self):
        """Test that binary content varies."""
        random.seed(42)
        results = [handle_binary_type(min_length=10, max_length=10) for _ in range(5)]
        # At least some should be different
        assert len(set(results)) > 1

    def test_binary_byte_values(self):
        """Test that all bytes are in valid range."""
        result = handle_binary_type(min_length=100, max_length=100)
        assert all(0 <= byte <= 255 for byte in result)


class TestHandleDateType:
    """Tests for handle_date_type function."""

    def test_default_date_generation(self):
        """Test date generation with default parameters."""
        result = handle_date_type()
        assert isinstance(result, date)
        # Default range is 2000-01-01 to today
        assert date(2000, 1, 1) <= result <= date.today()

    def test_date_with_custom_range(self):
        """Test date generation with custom range."""
        start = date(2020, 1, 1)
        end = date(2020, 12, 31)
        result = handle_date_type(start_date=start, end_date=end)
        assert start <= result <= end

    def test_same_start_and_end_date(self):
        """Test date generation with same start and end."""
        target = date(2021, 6, 15)
        result = handle_date_type(start_date=target, end_date=target)
        assert result == target

    def test_date_distribution(self):
        """Test that dates are distributed across the range."""
        random.seed(42)
        start = date(2020, 1, 1)
        end = date(2020, 12, 31)
        dates = [handle_date_type(start_date=start, end_date=end) for _ in range(50)]
        # Should have some variation
        assert len(set(dates)) > 10

    def test_recent_dates(self):
        """Test generation of recent dates."""
        start = date.today() - timedelta(days=7)
        end = date.today()
        result = handle_date_type(start_date=start, end_date=end)
        assert start <= result <= end


class TestHandleTimestampType:
    """Tests for handle_timestamp_type function."""

    def test_default_timestamp_generation(self):
        """Test timestamp generation with default parameters."""
        result = handle_timestamp_type()
        assert isinstance(result, datetime)
        # Default range is 2000-01-01 00:00:00 to now
        assert datetime(2000, 1, 1, 0, 0, 0) <= result <= datetime.now()

    def test_timestamp_with_custom_range(self):
        """Test timestamp generation with custom range."""
        start = datetime(2020, 1, 1, 12, 0, 0)
        end = datetime(2020, 1, 2, 12, 0, 0)
        result = handle_timestamp_type(start_datetime=start, end_datetime=end)
        assert start <= result <= end

    def test_same_start_and_end_timestamp(self):
        """Test timestamp generation with same start and end."""
        target = datetime(2021, 6, 15, 10, 30, 45)
        result = handle_timestamp_type(start_datetime=target, end_datetime=target)
        assert result == target

    def test_timestamp_distribution(self):
        """Test that timestamps are distributed across the range."""
        random.seed(42)
        start = datetime(2020, 1, 1, 0, 0, 0)
        end = datetime(2020, 12, 31, 23, 59, 59)
        timestamps = [
            handle_timestamp_type(start_datetime=start, end_datetime=end) for _ in range(50)
        ]
        # Should have some variation
        assert len(set(timestamps)) > 10

    def test_timestamp_with_microseconds(self):
        """Test that timestamps include time components."""
        start = datetime(2020, 1, 1, 0, 0, 0)
        end = datetime(2020, 1, 1, 23, 59, 59)
        result = handle_timestamp_type(start_datetime=start, end_datetime=end)
        # Should be a datetime with potentially different hours/minutes/seconds
        assert isinstance(result, datetime)
        assert result.year == 2020
        assert result.month == 1
        assert result.day == 1

    def test_recent_timestamps(self):
        """Test generation of recent timestamps."""
        start = datetime.now() - timedelta(hours=1)
        end = datetime.now()
        result = handle_timestamp_type(start_datetime=start, end_datetime=end)
        assert start <= result <= end


class TestHandleStructType:
    """Tests for handle_struct_type function."""

    def test_basic_struct_generation(self):
        """Test basic struct generation."""
        field_handlers = {"name": lambda: "John", "age": lambda: 25, "active": lambda: True}
        result = handle_struct_type(field_handlers)
        assert isinstance(result, dict)
        assert result == {"name": "John", "age": 25, "active": True}

    def test_empty_struct(self):
        """Test generation of empty struct."""
        result = handle_struct_type({})
        assert result == {}

    def test_struct_with_varying_fields(self):
        """Test struct generation with varying field values."""
        counter = {"value": 0}

        def increment():
            counter["value"] += 1
            return counter["value"]

        field_handlers = {"field1": increment, "field2": increment, "field3": increment}
        result = handle_struct_type(field_handlers)
        assert result == {"field1": 1, "field2": 2, "field3": 3}

    def test_struct_with_complex_fields(self):
        """Test struct with complex field types."""
        field_handlers = {
            "list_field": lambda: [1, 2, 3],
            "dict_field": lambda: {"key": "value"},
            "nested_struct": lambda: {"inner": "data"},
        }
        result = handle_struct_type(field_handlers)
        assert result["list_field"] == [1, 2, 3]
        assert result["dict_field"] == {"key": "value"}
        assert result["nested_struct"] == {"inner": "data"}

    def test_struct_with_none_values(self):
        """Test struct with None values."""
        field_handlers = {"optional_field": lambda: None, "required_field": lambda: "value"}
        result = handle_struct_type(field_handlers)
        assert result["optional_field"] is None
        assert result["required_field"] == "value"

    def test_struct_field_order(self):
        """Test that struct maintains field order."""
        field_handlers = {
            "field_a": lambda: "a",
            "field_b": lambda: "b",
            "field_c": lambda: "c",
        }
        result = handle_struct_type(field_handlers)
        assert list(result.keys()) == ["field_a", "field_b", "field_c"]


class TestHandlersIntegration:
    """Integration tests combining multiple handlers."""

    def test_nested_structures(self):
        """Test handlers with nested structures."""

        # Create an array of structs
        def create_struct():
            return handle_struct_type(
                {"id": lambda: random.randint(1, 100), "name": lambda: "test"}
            )

        result = handle_array_type(create_struct, min_items=3, max_items=3)
        assert len(result) == 3
        assert all(isinstance(item, dict) for item in result)
        assert all("id" in item and "name" in item for item in result)

    def test_map_of_arrays(self):
        """Test map containing arrays."""

        def create_array():
            return handle_array_type(lambda: random.randint(1, 10), min_items=2, max_items=5)

        key_counter = {"value": 0}

        def key_gen():
            key_counter["value"] += 1
            return f"key_{key_counter['value']}"

        result = handle_map_type(key_gen, create_array, min_items=2, max_items=3)
        assert 2 <= len(result) <= 3
        assert all(isinstance(v, list) for v in result.values())

    def test_struct_with_all_types(self):
        """Test struct containing all handler types."""
        field_handlers = {
            "array_field": lambda: handle_array_type(lambda: 1, min_items=2, max_items=2),
            "map_field": lambda: handle_map_type(
                lambda: "k", lambda: "v", min_items=1, max_items=1
            ),
            "decimal_field": lambda: handle_decimal_type(precision=5, scale=2),
            "binary_field": lambda: handle_binary_type(min_length=5, max_length=5),
            "date_field": lambda: handle_date_type(
                start_date=date(2020, 1, 1), end_date=date(2020, 12, 31)
            ),
            "timestamp_field": lambda: handle_timestamp_type(
                start_datetime=datetime(2020, 1, 1), end_datetime=datetime(2020, 12, 31)
            ),
        }
        result = handle_struct_type(field_handlers)

        assert isinstance(result["array_field"], list)
        assert isinstance(result["map_field"], dict)
        assert isinstance(result["decimal_field"], Decimal)
        assert isinstance(result["binary_field"], bytes)
        assert isinstance(result["date_field"], date)
        assert isinstance(result["timestamp_field"], datetime)

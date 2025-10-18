"""Tests for type handlers."""

from datetime import date, datetime
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


class TestHandlers:
    """Test custom type handlers."""

    def test_handle_array_type(self):
        result = handle_array_type(lambda: "test", min_items=2, max_items=5)

        assert isinstance(result, list)
        assert 2 <= len(result) <= 5
        assert all(item == "test" for item in result)

    def test_handle_array_type_integers(self):
        result = handle_array_type(lambda: 42, min_items=3, max_items=3)

        assert len(result) == 3
        assert all(item == 42 for item in result)

    def test_handle_map_type(self):
        result = handle_map_type(lambda: "key", lambda: 100, min_items=1, max_items=3)

        assert isinstance(result, dict)
        assert 1 <= len(result) <= 3

    def test_handle_map_type_unique_keys(self):
        counter = {"value": 0}

        def key_gen():
            counter["value"] += 1
            return f"key_{counter['value']}"

        result = handle_map_type(key_gen, lambda: "value", min_items=5, max_items=5)

        assert len(result) == 5
        assert all(k.startswith("key_") for k in result.keys())

    def test_handle_decimal_type(self):
        result = handle_decimal_type(precision=10, scale=2)

        assert isinstance(result, Decimal)

        # Check that decimal has correct scale
        str_value = str(result)
        if "." in str_value:
            _, fractional = str_value.split(".")
            assert len(fractional) == 2

    def test_handle_decimal_type_no_scale(self):
        result = handle_decimal_type(precision=5, scale=0)

        assert isinstance(result, Decimal)
        assert "." not in str(result) or str(result).endswith(".0")

    def test_handle_binary_type(self):
        result = handle_binary_type(min_length=5, max_length=10)

        assert isinstance(result, bytes)
        assert 5 <= len(result) <= 10

    def test_handle_binary_type_fixed_length(self):
        result = handle_binary_type(min_length=8, max_length=8)

        assert len(result) == 8

    def test_handle_date_type(self):
        result = handle_date_type()

        assert isinstance(result, date)
        assert date(2000, 1, 1) <= result <= date.today()

    def test_handle_date_type_custom_range(self):
        start = date(2020, 1, 1)
        end = date(2020, 12, 31)

        result = handle_date_type(start_date=start, end_date=end)

        assert start <= result <= end

    def test_handle_timestamp_type(self):
        result = handle_timestamp_type()

        assert isinstance(result, datetime)
        assert datetime(2000, 1, 1) <= result <= datetime.now()

    def test_handle_timestamp_type_custom_range(self):
        start = datetime(2020, 1, 1, 0, 0, 0)
        end = datetime(2020, 1, 31, 23, 59, 59)

        result = handle_timestamp_type(start_datetime=start, end_datetime=end)

        assert start <= result <= end

    def test_handle_struct_type(self):
        handlers = {
            "name": lambda: "John",
            "age": lambda: 30,
            "active": lambda: True,
        }

        result = handle_struct_type(handlers)

        assert isinstance(result, dict)
        assert result == {"name": "John", "age": 30, "active": True}

    def test_handle_struct_type_empty(self):
        result = handle_struct_type({})

        assert result == {}

#
# tests/test_tdd_stdlib_functions.py
#

import pytest

# Functions to be tested
from pyvider.components.functions.collection_functions import contains, length, lookup
from pyvider.components.functions.string_manipulation import format_str, join
from pyvider.components.functions.type_conversion_functions import tostring
from pyvider.exceptions import FunctionError


class TestStdlibFunctions:
    """
    TDD: Verifies the contracts for standard library functions.
    """

    # --- collection_functions ---
    def test_length_of_list(self):
        assert length(["a", "b", "c"]) == 3

    def test_length_of_map(self):
        assert length({"a": 1, "b": 2}) == 2

    def test_length_of_string(self):
        assert length("hello") == 5

    def test_length_of_null_is_null(self):
        assert length(None) is None

    def test_contains_in_list_true(self):
        assert contains(["a", "b", "c"], "b") is True

    def test_contains_in_list_false(self):
        assert contains(["a", "b", "c"], "d") is False

    def test_contains_with_null_list_is_null(self):
        assert contains(None, "a") is None

    def test_lookup_success(self):
        assert lookup({"a": "found"}, "a", "default") == "found"

    def test_lookup_fallback_to_default(self):
        assert lookup({"a": "found"}, "b", "default") == "default"

    def test_lookup_raises_error_without_default(self):
        with pytest.raises(FunctionError, match="Invalid key for map lookup"):
            lookup({"a": "found"}, "b", None)

    def test_lookup_with_null_map_returns_null(self):
        assert lookup(None, "a", "default") is None

    # --- type_conversion_functions ---
    def test_tostring_on_string(self):
        assert tostring("hello") == "hello"

    def test_tostring_on_number(self):
        assert tostring(123) == "123"
        assert tostring(123.45) == "123.45"

    def test_tostring_on_bool(self):
        assert tostring(True) == "true"
        assert tostring(False) == "false"

    def test_tostring_on_null_is_null(self):
        assert tostring(None) is None

    # --- string_manipulation functions (for boolean conversion) ---
    def test_format_with_boolean_uses_lowercase(self):
        """Verifies that format() converts booleans to lowercase 'true'/'false'."""
        result = format_str("The value is {0}", [True])
        assert result == "The value is true"

    def test_join_with_boolean_uses_lowercase(self):
        """Verifies that join() converts booleans to lowercase 'true'/'false'."""
        result = join(", ", ["a", True, 123, False])
        assert result == "a, true, 123, false"


# 🧪🎯📦

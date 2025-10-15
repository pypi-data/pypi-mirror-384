"""Comprehensive test suite for TypyTypy's exceptions.py module.

This module tests all custom exception classes and their functionality,
ensuring complete code coverage and proper error handling behavior.
"""

import pytest

from src.typytypy.exceptions import (
    ConfigurationError,
    InvalidTimingError,
    PrintingPressError,
    ProfileError,
)


class TestPrintingPressError:
    """Test cases for the base PrintingPressError exception."""

    def test_basic_initialization(self):
        """Test basic initialization with message only."""
        message = "Something went wrong"
        error = PrintingPressError(message)

        assert error.message == message
        assert error.context == {}
        assert str(error) == message

    def test_initialization_with_context(self):
        """Test initialization with message and context."""
        message = "Configuration failed"
        context: dict[str, str | int | float | bool | None] = {
            "config_file": "settings.ini",
            "line": 42,
        }
        error = PrintingPressError(message, context)

        assert error.message == message
        assert error.context == context

    def test_initialization_with_none_context(self):
        """Test initialization with explicitly None context."""
        message = "Error occurred"
        error = PrintingPressError(message, None)

        assert error.message == message
        assert error.context == {}

    def test_str_representation_without_context(self):
        """Test string representation when no context is provided."""
        message = "Simple error"
        error = PrintingPressError(message)

        assert str(error) == message

    def test_str_representation_with_context(self):
        """Test string representation when context is provided."""
        message = "Complex error"
        context: dict[str, str | int | float | bool | None] = {
            "key1": "value1",
            "key2": 123,
        }
        error = PrintingPressError(message, context)

        result = str(error)
        assert result.startswith(message)
        assert "Context:" in result
        assert "key1=value1" in result
        assert "key2=123" in result

    def test_str_representation_with_empty_context(self):
        """Test string representation with empty context dict."""
        message = "Error with empty context"
        context: dict[str, str | int | float | bool | None] = {}
        error = PrintingPressError(message, context)

        assert str(error) == message

    def test_inheritance_from_exception(self):
        """Test that PrintingPressError inherits from Exception."""
        error = PrintingPressError("test")
        assert isinstance(error, Exception)


class TestInvalidTimingError:
    """Test cases for InvalidTimingError exception."""

    def test_minimal_initialization(self):
        """Test initialization with message only."""
        message = "Invalid timing parameter"
        error = InvalidTimingError(message)

        assert error.message == message
        assert error.parameter_name is None
        assert error.parameter_value is None
        assert error.valid_range is None
        assert str(error) == message

    def test_full_initialization(self):
        """Test initialization with all parameters."""
        message = "Delay out of range"
        param_name = "base_delay"
        param_value = -1.5
        valid_range = (0.0, 10.0)

        error = InvalidTimingError(
            message,
            parameter_name=param_name,
            parameter_value=param_value,
            valid_range=valid_range,
        )

        assert error.message == message
        assert error.parameter_name == param_name
        assert error.parameter_value == param_value
        assert error.valid_range == valid_range

    def test_partial_initialization_parameter_name_only(self):
        """Test initialization with parameter name only."""
        message = "Invalid parameter"
        param_name = "delay_range"

        error = InvalidTimingError(message, parameter_name=param_name)

        assert error.parameter_name == param_name
        assert error.parameter_value is None
        assert error.valid_range is None

    def test_partial_initialization_parameter_value_only(self):
        """Test initialization with parameter value only."""
        message = "Invalid value"
        param_value = 15.0

        error = InvalidTimingError(message, parameter_value=param_value)

        assert error.parameter_name is None
        assert error.parameter_value == param_value
        assert error.valid_range is None

    def test_partial_initialization_valid_range_only(self):
        """Test initialization with valid range only."""
        message = "Range error"
        valid_range = (0.1, 5.0)

        error = InvalidTimingError(message, valid_range=valid_range)

        assert error.parameter_name is None
        assert error.parameter_value is None
        assert error.valid_range == valid_range

    def test_context_building_all_parameters(self):
        """Test context dictionary building with all parameters."""
        error = InvalidTimingError(
            "test",
            parameter_name="test_param",
            parameter_value=99.9,
            valid_range=(1.0, 100.0),
        )

        result = str(error)
        assert "parameter=test_param" in result
        assert "value=99.9" in result
        assert "valid_range=1.0 to 100.0" in result

    def test_inheritance_from_printing_press_error(self):
        """Test that InvalidTimingError inherits from PrintingPressError."""
        error = InvalidTimingError("test")
        assert isinstance(error, PrintingPressError)
        assert isinstance(error, Exception)


class TestProfileError:
    """Test cases for ProfileError exception."""

    def test_minimal_initialization(self):
        """Test initialization with message only."""
        message = "Profile operation failed"
        error = ProfileError(message)

        assert error.message == message
        assert error.profile_name is None
        assert error.operation is None
        assert error.word_count is None
        assert str(error) == message

    def test_full_initialization(self):
        """Test initialization with all parameters."""
        message = "Cannot add words to profile"
        profile_name = "test_profile"
        operation = "add_words"
        word_count = 25

        error = ProfileError(
            message,
            profile_name=profile_name,
            operation=operation,
            word_count=word_count,
        )

        assert error.message == message
        assert error.profile_name == profile_name
        assert error.operation == operation
        assert error.word_count == word_count

    def test_partial_initialization_profile_name_only(self):
        """Test initialization with profile name only."""
        message = "Profile error"
        profile_name = "my_profile"

        error = ProfileError(message, profile_name=profile_name)

        assert error.profile_name == profile_name
        assert error.operation is None
        assert error.word_count is None

    def test_partial_initialization_operation_only(self):
        """Test initialization with operation only."""
        message = "Operation failed"
        operation = "remove"

        error = ProfileError(message, operation=operation)

        assert error.profile_name is None
        assert error.operation == operation
        assert error.word_count is None

    def test_partial_initialization_word_count_only(self):
        """Test initialization with word count only."""
        message = "Word count error"
        word_count = 10

        error = ProfileError(message, word_count=word_count)

        assert error.profile_name is None
        assert error.operation is None
        assert error.word_count == word_count

    def test_context_building_all_parameters(self):
        """Test context dictionary building with all parameters."""
        error = ProfileError(
            "test",
            profile_name="test_profile",
            operation="create",
            word_count=50,
        )

        result = str(error)
        assert "profile_name=test_profile" in result
        assert "operation=create" in result
        assert "word_count=50" in result

    def test_inheritance_from_printing_press_error(self):
        """Test that ProfileError inherits from PrintingPressError."""
        error = ProfileError("test")
        assert isinstance(error, PrintingPressError)
        assert isinstance(error, Exception)


class TestConfigurationError:
    """Test cases for ConfigurationError exception."""

    def test_minimal_initialization(self):
        """Test initialization with message only."""
        message = "Configuration is invalid"
        error = ConfigurationError(message)

        assert error.message == message
        assert error.setting_name is None
        assert error.setting_value is None
        assert error.expected_type is None
        assert str(error) == message

    def test_full_initialization(self):
        """Test initialization with all parameters."""
        message = "Wrong type for setting"
        setting_name = "case_sensitivity"
        setting_value = "invalid_string"
        expected_type = bool

        error = ConfigurationError(
            message,
            setting_name=setting_name,
            setting_value=setting_value,
            expected_type=expected_type,
        )

        assert error.message == message
        assert error.setting_name == setting_name
        assert error.setting_value == setting_value
        assert error.expected_type == expected_type

    def test_partial_initialization_setting_name_only(self):
        """Test initialization with setting name only."""
        message = "Setting error"
        setting_name = "timeout"

        error = ConfigurationError(message, setting_name=setting_name)

        assert error.setting_name == setting_name
        assert error.setting_value is None
        assert error.expected_type is None

    def test_partial_initialization_setting_value_only(self):
        """Test initialization with setting value only."""
        message = "Value error"
        setting_value = 42

        error = ConfigurationError(message, setting_value=setting_value)

        assert error.setting_name is None
        assert error.setting_value == setting_value
        assert error.expected_type is None

    def test_partial_initialization_expected_type_only(self):
        """Test initialization with expected type only."""
        message = "Type error"
        expected_type = str

        error = ConfigurationError(message, expected_type=expected_type)

        assert error.setting_name is None
        assert error.setting_value is None
        assert error.expected_type == expected_type

    def test_context_building_all_parameters(self):
        """Test context dictionary building with all parameters."""
        error = ConfigurationError(
            "test",
            setting_name="debug_mode",
            setting_value=123,
            expected_type=bool,
        )

        result = str(error)
        assert "setting=debug_mode" in result
        assert "value=123" in result
        assert "expected_type=bool" in result

    def test_setting_value_none_handling(self):
        """Test handling of None setting value."""
        error = ConfigurationError(
            "test",
            setting_name="optional_setting",
            setting_value=None,
            expected_type=str,
        )

        result = str(error)
        assert "setting=optional_setting" in result
        assert "expected_type=str" in result
        assert "value=None" not in result
        assert "value=" not in result

    def test_setting_value_explicit_none_vs_omitted(self):
        """Test that explicitly passing None is handled same as omitting parameter."""
        error1 = ConfigurationError("test", setting_name="test")
        error2 = ConfigurationError("test", setting_name="test", setting_value=None)

        assert str(error1) == str(error2)

    def test_setting_value_conversion_to_string(self):
        """Test that setting values are properly converted to strings."""
        test_values: list[int | float | bool | str] = [42, 3.14, True, False, "string"]

        for value in test_values:
            error = ConfigurationError("test", setting_value=value)
            result = str(error)
            assert f"value={str(value)}" in result

    def test_inheritance_from_printing_press_error(self):
        """Test that ConfigurationError inherits from PrintingPressError."""
        error = ConfigurationError("test")
        assert isinstance(error, PrintingPressError)
        assert isinstance(error, Exception)


class TestExceptionInteraction:
    """Test cases for exception interactions and edge cases."""

    def test_exception_chaining(self):
        """Test that exceptions can be properly chained."""
        try:
            raise ValueError("Original error")
        except ValueError as e:
            new_error = PrintingPressError("Wrapped error")
            new_error.__cause__ = e
            assert new_error.__cause__ is e

    def test_empty_context_string_representation(self):
        """Test string representation with various empty contexts."""
        error1 = PrintingPressError("test", {})
        error2 = PrintingPressError("test", None)

        assert str(error1) == "test"
        assert str(error2) == "test"

    def test_context_with_complex_values(self):
        """Test context handling with complex data types."""
        complex_context: dict[str, str | int | float | bool | None] = {
            "string": "text_value",
            "integer": 42,
            "float": 3.14,
            "none": None,
            "bool": True,
        }

        error = PrintingPressError("test", complex_context)
        result = str(error)

        for key, value in complex_context.items():
            assert f"{key}={value}" in result

    def test_all_exceptions_are_catchable_by_base(self):
        """Test that all specific exceptions can be caught by base exception."""
        exceptions = [
            InvalidTimingError("timing error"),
            ProfileError("profile error"),
            ConfigurationError("config error"),
        ]

        for exc in exceptions:
            try:
                raise exc
            except PrintingPressError:
                pass  # Successfully caught
            else:
                pytest.fail(
                    f"{type(exc).__name__} was not caught by PrintingPressError"
                )

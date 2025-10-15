"""Custom exception classes for TypyTypy.

This module defines all TypyTypy-specific exceptions, providing clear error categories
for precise handling and debugging across the library.

Classes:
    PrintingPressError: Base exception for all TypyTypy errors.
    InvalidTimingError: Raised when timing parameters are invalid.
    ProfileError: Raised when timing profile operations fail.
    ConfigurationError: Raised when configuration values are invalid.

Examples:
    Basic exception handling:
        >>> try:
        ...     printer = PrintingPress(base_delay=-1.0)
        ... except InvalidTimingError as e:
        ...     print(f"Invalid timing: {e}")

Metadata:
    Author: KitscherEins,
    Version: 0.1.0,
    License: Apache-2.0
"""

# Type alias for valid configuration values
ConfigValue = str | int | float | bool | None


class PrintingPressError(Exception):
    """Base exception for all TypyTypy-specific errors.

    All custom exceptions in the TypyTypy library inherit from this class.
    Catching 'PrintingPressError' will also catch any more TypyTypy-specific exceptions.

    Attributes:
        message (str): Human-readable error description.
        context (dict[str, ConfigValue] | None): Optional dictionary containing
                                                 additional error context (e.g.,
                                                 parameter name, invalid value, etc.).

    Examples:
        Catch any TypyTypy-related exception:
            >>> try:
            ...     # Some TypyTypy operation
            ...     pass
            ... except PrintingPressError as e:
            ...     print(f"PrintingPress error occurred: {e}")
    """

    def __init__(
        self, message: str, context: dict[str, ConfigValue] | None = None
    ) -> None:
        """Initialize a new PrintingPress exception.

        Stores the human-readable message and any optional context that provides
        additional diagnostic information. Context entries are stringified and
        incorporated into the string representation of the exception.

        Args:
            message (str): Human-readable error description.
            context (dict[str, ConfigValue] | None): Optional dictionary containing
                                                     additional error context (e.g.,
                                                     parameter name, invalid value,
                                                     etc.).

        Returns:
            None.
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}

    def __str__(self) -> str:
        """Return a formatted string representation of the exception.

        If additional context is available, it is appended in parentheses after the main
        message.

        Returns:
            str: The formatted message including context if present.
        """
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} (Context: {context_str})"
        return self.message


class InvalidTimingError(PrintingPressError):
    """Raised when timing parameters are invalid or out of acceptable range.

    This exception is thrown when 'base_delay' or 'delay_range' values do not meet the
    validation criteria for safe and reasonable typing simulation.

    Attributes:
        message (str): Human-readable error description.
        parameter_name (str | None): Name of the invalid parameter.
        parameter_value (float | None): The invalid value that was provided.
        valid_range (tuple[float, float] | None): Minimum and maximum acceptable values
                                                  for the parameter.

    Examples:
        Negative delay:
            >>> try:
            ...     printer = PrintingPress(base_delay=-0.5)
            ... except InvalidTimingError as e:
            ...     print(f"Timing error: {e}")
    """

    def __init__(
        self,
        message: str,
        parameter_name: str | None = None,
        parameter_value: float | None = None,
        valid_range: tuple[float, float] | None = None,
    ) -> None:
        """Initialize a new InvalidTimingError exception.

        Constructs the error with details about the invalid parameter, including its
        name, value, and expected range. These values are also recorded as context for
        debugging.

        Args:
            message (str): Human-readable error description.
            parameter_name (str | None): Name of the invalid parameter.
            parameter_value (float | None): The invalid value that was provided.
            valid_range (tuple[float, float] | None): Minimum and maximum acceptable
                                                      values for the parameter.

        Returns:
            None.
        """
        context: dict[str, ConfigValue] = {}
        if parameter_name is not None:
            context["parameter"] = parameter_name
        if parameter_value is not None:
            context["value"] = str(parameter_value)
        if valid_range is not None:
            context["valid_range"] = f"{valid_range[0]} to {valid_range[1]}"

        super().__init__(message, context)
        self.parameter_name = parameter_name
        self.parameter_value = parameter_value
        self.valid_range = valid_range


class ProfileError(PrintingPressError):
    """Raised when timing profile operations fail or encounter invalid states.

    This exception covers errors in timing profile management, including attempts to
    operate on non-existent profiles, invalid word formats, or conflicting profile
    operations.

    Attributes:
        message (str): Human-readable error description.
        profile_name (str | None): Name of the timing profile involved, or None if not
                                   applicable.
        operation (str | None): The operation that failed (add, remove, create, etc.).
        word_count (int | None): Number of words involved in the operation, or None.

    Examples:
        Adding a word to a missing profile:
            >>> printer = PrintingPress()
            >>> try:
            ...     printer.add_words_to_profile("missing_profile", "word")
            ... except ProfileError as e:
            ...     print(f"Profile error: {e}")
    """

    def __init__(
        self,
        message: str,
        profile_name: str | None = None,
        operation: str | None = None,
        word_count: int | None = None,
    ) -> None:
        """Initialize a new ProfileError exception.

        Used when a timing profile operation fails, such as attempting to use a
        non-existent profile, performing an invalid operation, or violating duplicate
        rules. Relevant details are stored for context.

        Args:
            message (str): Human-readable error description.
            profile_name (str | None): Name of the timing profile involved, or None if
                                       not applicable.
            operation (str | None): The operation that failed (add, remove, create,
                                    etc.).
            word_count (int | None): Number of words involved in the operation, or None.

        Returns:
            None.
        """
        context: dict[str, ConfigValue] = {}
        if profile_name is not None:
            context["profile_name"] = profile_name
        if operation is not None:
            context["operation"] = operation
        if word_count is not None:
            context["word_count"] = str(word_count)

        super().__init__(message, context)
        self.profile_name = profile_name
        self.operation = operation
        self.word_count = word_count


class ConfigurationError(PrintingPressError):
    """Raised when configuration values are invalid or incompatible.

    This exception is thrown when configuration settings are malformed, contain invalid
    combinations, or fail validation checks.

    Attributes:
        message (str): Human-readable error description.
        setting_name (str | None): Name of the configuration setting that failed.
        setting_value (ConfigValue | None): The invalid value that was provided.
        expected_type (type | None): Expected type for the configuration setting, or
                                     None if not type-constrained.

    Examples:
        Setting case-sensitivity with the wrong type:
            >>> try:
            ...     printer = PrintingPress()
            ...     printer.set_profile_case_sensitivity("invalid")
            ... except ConfigurationError as e:
            ...     print(f"Configuration error: {e}")
    """

    def __init__(
        self,
        message: str,
        setting_name: str | None = None,
        setting_value: ConfigValue | None = None,
        expected_type: type | None = None,
    ) -> None:
        """Initialize a new ConfigurationError exception.

        Represents invalid or incompatible configuration settings. Stores the failed
        setting name, its value, and the expected type (if known), for inclusion in
        error reports and debugging context.

        Args:
            message (str): Human-readable error description.
            setting_name (str | None): Name of the configuration setting that failed.
            setting_value (ConfigValue | None): The invalid value that was provided.
            expected_type (type | None): Expected type for the configuration setting, or
                                         None if not type-constrained.

        Returns:
            None.
        """
        context: dict[str, ConfigValue] = {}
        if setting_name is not None:
            context["setting"] = setting_name
        if setting_value is not None:
            context["value"] = str(setting_value)
        if expected_type is not None:
            context["expected_type"] = expected_type.__name__

        super().__init__(message, context)
        self.setting_name = setting_name
        self.setting_value = setting_value
        self.expected_type = expected_type


# Export all exception classes
__all__ = [
    "PrintingPressError",
    "InvalidTimingError",
    "ProfileError",
    "ConfigurationError",
]

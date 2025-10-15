"""TypyTypy — A Bespoke Character-by-Character Text Printer.

A utility Python library which provides for a realistic, "real-time typing" simulation
with highly configurable implementations. It features a flexible API for both simple and
advanced use, quick-use "character personality" presets, and granular timing control for
creating custom text presentations with authentic temporal dynamics.

Born of the KitschCode philosophy of applying meticulous craftsmanship to humble
functionality.

Classes:
    PrintingPress: Main character-by-character text printer class.

Examples:
    Basic usage:
        >>> import typytypy
        ...
        >>> typytypy.type_out("Hello, World!")

    Using "character personality" presets:
        >>> nervous = typytypy.use_preset('nervous')
        ...
        >>> nervous.type_out("Um, hello there...")

    Advanced instance management (full functionality; recommended approach):
        >>> printer = typytypy.PrintingPress()
        ...
        >>> printer.create_profile("highlight", 0.1, 0.05, "IMPORTANT")
        ...
        >>> printer.type_out("This is IMPORTANT information!")

Metadata:
    Author: KitscherEins,
    Version: 0.1.0,
    License: Apache-2.0
"""

# Import core functionality
from .core import PrintingPress

# Package metadata
__version__ = "0.1.0"
__author__ = "KitscherEins"
__license__ = "Apache-2.0"
__description__ = "A Bespoke Character-by-Character Text Printer."

# Package URLs for distribution
__homepage__ = "https://github.com/VDundDB/typytypy-py"
__documentation__ = "https://VDundDB.github.io/typytypy-py"
__repository__ = "https://github.com/VDundDB/typytypy-py"
__pypi__ = "https://pypi.org/project/typytypy"
__issues__ = "https://github.com/VDundDB/typytypy-py/issues"
__changelog__ = "https://github.com/VDundDB/typytypy-py/blob/main/CHANGELOG.md"

# Create a default global instance for direct module-level usage
_default_printer = PrintingPress()


# Timing preset constants for user convenience
class _TimingPresets:
    """Collection of predefined timing presets for "character personalities".

    These presets provide ready-to-use timing configurations that users can access
    through the 'use_preset()' function. Each preset is a tuple of (base_delay,
    delay_range) in seconds and can be used to create a limited preset printer.

    Attributes:
        DEFAULT (tuple[float, float]): Standard typing speed.
        EMPHASIS (tuple[float, float]): Moderate typing speed.
        SLOW (tuple[float, float]): Deliberate, careful typing.
        CONTEMPLATIVE (tuple[float, float]): Thoughtful, reflective typing.
        NERVOUS (tuple[float, float]): Anxious, hesitant typing.
        AVERAGE (tuple[float, float]): Approximate researched average typing speed.
        CONFIDENT (tuple[float, float]): Steady, professional typing.
        ROBOTIC (tuple[float, float]): Mechanical, consistent typing.
        CHAOTIC (tuple[float, float]): Distracted, erratic typing.
    """

    # Standard presets
    DEFAULT = (PrintingPress.DEFAULT_BASE_DELAY, PrintingPress.DEFAULT_DELAY_RANGE)
    EMPHASIS = (PrintingPress.EMPHASIS_BASE_DELAY, PrintingPress.EMPHASIS_DELAY_RANGE)

    # Character personality presets
    SLOW = (0.30, 0.30)  # Slow, -ly
    CONTEMPLATIVE = (0.15, 0.30)
    NERVOUS = (0.10, 0.40)
    AVERAGE = (0.12, 0.24)  # Researched human average
    CONFIDENT = (0.08, 0.16)
    ROBOTIC = (0.10, 0.05)
    CHAOTIC = (0.007, 0.993)


class _PresetCollection(dict[str, str]):
    """Custom dictionary subclass with formatted string representation for presets.

    This specialized class provides all standard dictionary functionality while
    offering a formatted, user-friendly string representation, in list view, of
    predefined timing presets when printed.

    Inherits from dict, maintaining full dictionary compatibility for membership
    testing, iteration, etc.
    """

    def __init__(self, preset_data: dict[str, tuple[str, tuple[float, float]]]) -> None:
        """Initialize with preset data containing both formatted and raw values.

        For INTERNAL USE.

        Args:
            preset_data (dict): Dictionary where values are tuples of
                                (formatted_string, (base_delay, delay_range))

        Returns:
            None.
        """
        # Store only formatted strings in the main dict for display
        formatted_preset_data = {name: data[0] for name, data in preset_data.items()}
        super().__init__(formatted_preset_data)
        # Store raw timing values separately for internal use
        self._raw_timings = {name: data[1] for name, data in preset_data.items()}

    def _get_raw_timing(self, preset_name: str) -> tuple[float, float]:
        """Get raw timing values for a preset.

        For INTERNAL USE.

        Args:
            preset_name (str): Name of the timing preset.

        Returns:
            tuple[float, float]: Base delay and delay range values.
        """
        return self._raw_timings[preset_name.lower()]

    def __str__(self) -> str:
        """Return formatted string representation of predefined timing presets.

        For INTERNAL USE.

        Returns:
            str: Formatted list of timing presets with timing information.
        """
        result = "Available presets:\n"
        for name, timing in self.items():
            result += f" - {name}: {timing}\n"
        return result.rstrip()  # Remove trailing newline


class _PresetPrinter:
    """Limited printer instance bound to a predefined timing preset.

    This lightweight wrapper only provides 'type_out()' functionality, preventing access
    to advanced features like profile management. It allows users to create multiple
    independent printers for different timing presets without managing full
    'PrintingPress' instances.

    Attributes:
        _preset_printer (PrintingPress): The underlying printer configured with the
                                         chosen preset timings.
    """

    def __init__(self, base_delay: float, delay_range: float) -> None:
        """Initialize a PrintingPress instance with fixed timing configuration.

        For INTERNAL USE.

        Args:
            base_delay (float): Base delay per character, in seconds, for this session.
            delay_range (float): Random delay range, in seconds, for this session.

        Returns:
            None.
        """
        self._preset_printer = PrintingPress(
            base_delay=base_delay, delay_range=delay_range
        )

    def type_out(self, text: str) -> None:
        """Print text to stdout one character at a time, simulating real-time typing.

        Renders the given text in real time, inserting preset-configured calculated
        delays between printed characters. Stdout is flushed after printing each
        character for immediate display.

        All original formatting (spacing, punctuation, and line breaks) is preserved.

        Args:
            text (str): The text to print.

        Returns:
            None.
        """
        self._preset_printer.type_out(text)


# Direct module-level functions that delegate to the default instance
def type_out(
    text: str, base_delay: float | None = None, delay_range: float | None = None
) -> None:
    """Print text to stdout one character at a time, simulating real-time typing.

    Renders the given text in real time, inserting calculated delays between printed
    characters. Stdout is flushed after printing each character for immediate display.

    All original formatting (spacing, punctuation, and line breaks) is preserved.

    Provides direct access to TypyTypy's core functionality without requiring class
    instantiation.

    Args:
        text (str): The text to print.
        base_delay (float | None): Overide (optional) for the session minimum delay per
                                   character, in seconds.
        delay_range (float | None): Override (optional) for the session delay range, in
                                    seconds.

    Returns:
        None.

    Raises:
        InvalidTimingError: If invalid timing values are provided.

    Examples:
        General use:
            >>> typytypy.type_out("Hello, World!")

        With custom timings:
            >>> typytypy.type_out("HeLlO, WoRlD!",
            ...                   base_delay=0.05, delay_range=0.50)
    """
    _default_printer.type_out(text, base_delay, delay_range)


def get_available_presets() -> _PresetCollection:
    """List all predefined timing presets with their configuration details.

    This function retrieves all predefined timing presets and returns them in a
    formatted collection. Each preset includes both 'base_delay' and 'delay_range'
    values, visually formatted for human readability.

    The returned collection maintains full dictionary compatibility, allowing users to
    check preset availability using standard membership testing (e.g. 'in', 'for', etc.)
    while providing clean, formatted output, in list format, when printed.

    Returns:
        _PresetCollection: A formatted dictionary of preset names and their timing
                           configurations, with lowercase preset names as keys.

    Examples:
        Displaying all presets:
            >>> print(typytypy.get_available_presets())
            Available presets:
             - default: (base_delay: 0.015s, delay_range: 0.042s)
             - emphasis: (base_delay: 0.031s, delay_range: 0.099s)
             ...

        Extending use-case of preset availablity:
            >>> presets = typytypy.get_available_presets()
            >>> if 'nervous' in presets:
            ...     print("I can use this to do something more... maybe?")
    """

    def _format_preset(name: str) -> tuple[str, tuple[float, float]]:
        """Format preset timing values and return both formatted and raw data.

        For INTERNAL USE.

        Args:
            name (str): The uppercase preset name from '_TimingPresets'.

        Returns:
            tuple: (formatted_string, (base_delay, delay_range))
        """
        preset_base_delay, preset_delay_range = getattr(_TimingPresets, name)
        formatted = (
            f"(base_delay: {preset_base_delay:.3f}s,"
            f" delay_range: {preset_delay_range:.3f}s)"
        )

        return formatted, (preset_base_delay, preset_delay_range)

    # Extract all preset names dynamically from _TimingPresets class
    preset_names = [
        name
        for name in vars(_TimingPresets)
        if name.isupper() and not name.startswith("__")
    ]

    presets_data = {}
    for name in preset_names:
        presets_data[name.lower()] = _format_preset(name)

    return _PresetCollection(presets_data)


def use_preset(preset_name: str) -> _PresetPrinter:
    """Create a limited PresetPrinter instance using a predefined timing configuration.

    This function returns a '_PresetPrinter' instance that only exposes the 'type_out()'
    functionality. It facilitates the quick application of preconfigured "character
    personality" styles without need for managing full 'PrintingPress' instances.

    Args:
        preset_name (str): Name of the timing preset to use. Case-insensitive.
                           To check valid options, use 'get_available_presets()'.

    Returns:
        _PresetPrinter: A printer instance configured with the specified preset.

    Raises:
        ValueError: If preset_name is not recognized.

    Examples:
        Using multiple typing presets:
            >>> nervous = typytypy.use_preset('nervous')
            >>> confident = typytypy.use_preset('confident')
            ...
            >>> nervous.type_out("Um, hello there...")
            >>> confident.type_out("Good morning, team!")
    """
    # Get available presets for both validation and timing values
    available_presets = get_available_presets()

    if preset_name.lower() not in available_presets:
        available_preset_names = ", ".join(available_presets.keys())
        raise ValueError(
            f"Unknown preset '{preset_name}'."
            f" Available presets: {available_preset_names}"
        )

    # Extract raw timing values using the new method
    base_delay, delay_range = available_presets._get_raw_timing(preset_name)
    return _PresetPrinter(base_delay=base_delay, delay_range=delay_range)


# Export what users need (also what gets exported via "from typytypy import *")
__all__ = [
    # Core functionality
    "type_out",
    "use_preset",
    # Utility function for discovering presets
    "get_available_presets",
    # Advanced class (for users who need multiple instances)
    "PrintingPress",
    # Package metadata
    "__version__",
    "__author__",
    "__license__",
    "__description__",
    "__homepage__",
    "__documentation__",
    "__repository__",
    "__pypi__",
    "__issues__",
    "__changelog__",
]

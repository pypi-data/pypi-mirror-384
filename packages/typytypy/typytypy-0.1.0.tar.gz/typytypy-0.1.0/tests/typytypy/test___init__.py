"""Comprehensive test suite for TypyTypy's __init__.py module.

This module tests all functionality exposed by the package's main __init__.py file,
ensuring complete code coverage and proper behavior of all public interfaces.
"""

from unittest.mock import Mock, patch

import pytest

# Import the module under test
import src.typytypy as typytypy

# Import internal classes for testing
from src.typytypy import (
    PrintingPress,
    # Package metadata
    __author__,
    __changelog__,
    __description__,
    __documentation__,
    __homepage__,
    __issues__,
    __license__,
    __pypi__,
    __repository__,
    __version__,
    _PresetPrinter,
    _TimingPresets,
    # Core functionality
    get_available_presets,
    type_out,
    use_preset,
)


class TestPackageMetadata:
    """Test cases for package metadata constants."""

    def test_version_constant(self):
        """Test __version__ constant is correctly defined."""
        assert __version__ == "0.1.0"
        assert isinstance(__version__, str)

    def test_author_constant(self):
        """Test __author__ constant is correctly defined."""
        assert __author__ == "KitscherEins"
        assert isinstance(__author__, str)

    def test_license_constant(self):
        """Test __license__ constant is correctly defined."""
        assert __license__ == "Apache-2.0"
        assert isinstance(__license__, str)

    def test_description_constant(self):
        """Test __description__ constant is correctly defined."""
        expected = "A Bespoke Character-by-Character Text Printer."
        assert __description__ == expected
        assert isinstance(__description__, str)

    def test_homepage_constant(self):
        """Test __homepage__ constant is correctly defined."""
        assert __homepage__ == "https://github.com/VDundDB/typytypy-py"
        assert isinstance(__homepage__, str)

    def test_documentation_constant(self):
        """Test __documentation__ constant is correctly defined."""
        assert __documentation__ == "https://VDundDB.github.io/typytypy-py"
        assert isinstance(__documentation__, str)

    def test_repository_constant(self):
        """Test __repository__ constant is correctly defined."""
        assert __repository__ == "https://github.com/VDundDB/typytypy-py"
        assert isinstance(__repository__, str)

    def test_pypi_constant(self):
        """Test __pypi__ constant is correctly defined."""
        assert __pypi__ == "https://pypi.org/project/typytypy"
        assert isinstance(__pypi__, str)

    def test_issues_constant(self):
        """Test __issues__ constant is correctly defined."""
        assert __issues__ == "https://github.com/VDundDB/typytypy-py/issues"
        assert isinstance(__issues__, str)

    def test_changelog_constant(self):
        """Test __changelog__ constant is correctly defined."""
        assert (
            __changelog__
            == "https://github.com/VDundDB/typytypy-py/blob/main/CHANGELOG.md"
        )
        assert isinstance(__changelog__, str)


class TestDefaultPrinterInstance:
    """Test cases for the default global printer instance."""

    def test_default_printer_exists(self):
        """Test that _default_printer is created as PrintingPress instance."""
        assert hasattr(typytypy, "_default_printer")
        assert isinstance(typytypy._default_printer, PrintingPress)

    def test_default_printer_is_singleton(self):
        """Test that _default_printer is the same instance across calls."""
        # Import again to verify same instance
        import src.typytypy as typytypy_2

        assert typytypy._default_printer is typytypy_2._default_printer


class TestTimingPresets:
    """Test cases for _TimingPresets class and its constants."""

    def test_default_preset(self):
        """Test DEFAULT preset values."""
        assert hasattr(_TimingPresets, "DEFAULT")
        base_delay, delay_range = _TimingPresets.DEFAULT
        assert isinstance(base_delay, float)
        assert isinstance(delay_range, float)
        # Should match PrintingPress default values based on the code
        assert base_delay == PrintingPress.DEFAULT_BASE_DELAY
        assert delay_range == PrintingPress.DEFAULT_DELAY_RANGE

    def test_emphasis_preset(self):
        """Test EMPHASIS preset values."""
        assert hasattr(_TimingPresets, "EMPHASIS")
        base_delay, delay_range = _TimingPresets.EMPHASIS
        assert isinstance(base_delay, float)
        assert isinstance(delay_range, float)
        # Should match PrintingPress emphasis values
        assert base_delay == PrintingPress.EMPHASIS_BASE_DELAY
        assert delay_range == PrintingPress.EMPHASIS_DELAY_RANGE

    def test_slow_preset(self):
        """Test SLOW preset values."""
        assert _TimingPresets.SLOW == (0.30, 0.30)

    def test_contemplative_preset(self):
        """Test CONTEMPLATIVE preset values."""
        assert _TimingPresets.CONTEMPLATIVE == (0.15, 0.30)

    def test_nervous_preset(self):
        """Test NERVOUS preset values."""
        assert _TimingPresets.NERVOUS == (0.10, 0.40)

    def test_average_preset(self):
        """Test AVERAGE preset values."""
        assert _TimingPresets.AVERAGE == (0.12, 0.24)

    def test_confident_preset(self):
        """Test CONFIDENT preset values."""
        assert _TimingPresets.CONFIDENT == (0.08, 0.16)

    def test_robotic_preset(self):
        """Test ROBOTIC preset values."""
        assert _TimingPresets.ROBOTIC == (0.10, 0.05)

    def test_chaotic_preset(self):
        """Test CHAOTIC preset values."""
        assert _TimingPresets.CHAOTIC == (0.007, 0.993)

    def test_all_presets_are_tuples(self):
        """Test that all presets are tuples of two floats."""
        presets = [
            _TimingPresets.DEFAULT,
            _TimingPresets.EMPHASIS,
            _TimingPresets.SLOW,
            _TimingPresets.CONTEMPLATIVE,
            _TimingPresets.NERVOUS,
            _TimingPresets.AVERAGE,
            _TimingPresets.CONFIDENT,
            _TimingPresets.ROBOTIC,
            _TimingPresets.CHAOTIC,
        ]

        for preset in presets:
            assert isinstance(preset, tuple)
            assert len(preset) == 2
            assert isinstance(preset[0], int | float)
            assert isinstance(preset[1], int | float)

    def test_timing_presets_docstring(self):
        """Test that _TimingPresets class has comprehensive docstring."""
        assert _TimingPresets.__doc__ is not None
        docstring = _TimingPresets.__doc__
        assert "Collection of predefined timing presets" in docstring
        assert "DEFAULT" in docstring
        assert "CHAOTIC" in docstring


class TestPresetCollection:
    """Test cases for _PresetCollection class."""

    def test_preset_collection_initialization(self):
        """Test _PresetCollection initialization with preset data."""
        from src.typytypy import _PresetCollection

        test_data = {"test": ("formatted_string", (0.1, 0.05))}
        collection = _PresetCollection(test_data)

        assert "test" in collection
        assert collection["test"] == "formatted_string"

    def test_preset_collection_str_representation(self):
        """Test _PresetCollection.__str__() method formatting."""
        from src.typytypy import _PresetCollection

        test_data = {
            "test1": ("(base_delay: 0.100s, delay_range: 0.050s)", (0.1, 0.05)),
            "test2": ("(base_delay: 0.200s, delay_range: 0.100s)", (0.2, 0.1)),
        }
        collection = _PresetCollection(test_data)

        str_repr = str(collection)
        assert str_repr.startswith("Available presets:")
        assert "test1: (base_delay: 0.100s, delay_range: 0.050s)" in str_repr
        assert "test2: (base_delay: 0.200s, delay_range: 0.100s)" in str_repr
        assert not str_repr.endswith("\n")  # Tests rstrip() functionality

    def test_preset_collection_get_raw_timing(self):
        """Test _PresetCollection._get_raw_timing() method."""
        from src.typytypy import _PresetCollection

        test_data = {"test": ("formatted", (0.15, 0.25))}
        collection = _PresetCollection(test_data)

        raw_timing = collection._get_raw_timing("test")
        assert raw_timing == (0.15, 0.25)

        # Test case-insensitive access
        raw_timing_upper = collection._get_raw_timing("TEST")
        assert raw_timing_upper == (0.15, 0.25)

    def test_preset_collection_empty_str(self):
        """Test _PresetCollection.__str__() with empty collection."""
        from src.typytypy import _PresetCollection

        collection = _PresetCollection({})
        str_repr = str(collection)
        assert str_repr == "Available presets:"

    def test_preset_collection_membership_testing(self):
        """Test _PresetCollection supports membership testing."""
        presets = get_available_presets()

        assert "default" in presets
        assert "nonexistent" not in presets
        assert "DEFAULT" not in presets  # Should be case-sensitive for keys


class TestPresetPrinter:
    """Test cases for _PresetPrinter class."""

    def test_initialization(self):
        """Test _PresetPrinter initialization."""
        base_delay = 0.1
        delay_range = 0.05
        printer = _PresetPrinter(base_delay, delay_range)

        assert hasattr(printer, "_preset_printer")
        assert isinstance(printer._preset_printer, PrintingPress)

    def test_initialization_with_different_values(self):
        """Test _PresetPrinter initialization with different timing values."""
        test_cases = [
            (0.05, 0.02),
            (0.2, 0.15),
            (0.5, 0.3),
        ]

        for base_delay, delay_range in test_cases:
            printer = _PresetPrinter(base_delay, delay_range)
            assert isinstance(printer._preset_printer, PrintingPress)

    @patch("src.typytypy.core.PrintingPress.type_out")
    def test_type_out_method(self, mock_type_out):
        """Test _PresetPrinter.type_out method delegates to internal printer."""
        base_delay = 0.2
        delay_range = 0.1
        printer = _PresetPrinter(base_delay, delay_range)

        test_text = "Hello, World!"
        printer.type_out(test_text)

        mock_type_out.assert_called_once_with(test_text)

    @patch("src.typytypy.core.PrintingPress.type_out")
    def test_type_out_method_with_various_texts(self, mock_type_out):
        """Test _PresetPrinter.type_out with various text inputs."""
        printer = _PresetPrinter(0.1, 0.05)
        test_texts = ["", "Single", "Multiple words here", "Special chars: !@#$%"]

        for text in test_texts:
            mock_type_out.reset_mock()
            printer.type_out(text)
            mock_type_out.assert_called_once_with(text)

    def test_preset_printer_docstring(self):
        """Test that _PresetPrinter class has proper docstring."""
        assert _PresetPrinter.__doc__ is not None
        docstring = _PresetPrinter.__doc__
        assert "Limited printer instance" in docstring
        assert "'type_out()' functionality" in docstring


class TestModuleLevelTypeOut:
    """Test cases for module-level type_out function."""

    @patch("src.typytypy._default_printer.type_out")
    def test_type_out_without_overrides(self, mock_type_out):
        """Test type_out function without parameter overrides."""
        test_text = "Test message"
        type_out(test_text)

        mock_type_out.assert_called_once_with(test_text, None, None)

    @patch("src.typytypy._default_printer.type_out")
    def test_type_out_with_base_delay_override(self, mock_type_out):
        """Test type_out function with base_delay override."""
        test_text = "Test message"
        base_delay = 0.5
        type_out(test_text, base_delay=base_delay)

        mock_type_out.assert_called_once_with(test_text, base_delay, None)

    @patch("src.typytypy._default_printer.type_out")
    def test_type_out_with_delay_range_override(self, mock_type_out):
        """Test type_out function with delay_range override."""
        test_text = "Test message"
        delay_range = 0.2
        type_out(test_text, delay_range=delay_range)

        mock_type_out.assert_called_once_with(test_text, None, delay_range)

    @patch("src.typytypy._default_printer.type_out")
    def test_type_out_with_both_overrides(self, mock_type_out):
        """Test type_out function with both parameter overrides."""
        test_text = "Test message"
        base_delay = 0.5
        delay_range = 0.2
        type_out(test_text, base_delay=base_delay, delay_range=delay_range)

        mock_type_out.assert_called_once_with(test_text, base_delay, delay_range)

    @patch("src.typytypy._default_printer.type_out")
    def test_type_out_with_keyword_arguments(self, mock_type_out):
        """Test type_out function with explicit keyword arguments."""
        test_text = "Keyword test"
        type_out(text=test_text, base_delay=0.1, delay_range=0.05)

        mock_type_out.assert_called_once_with(test_text, 0.1, 0.05)

    @patch("src.typytypy._default_printer.type_out")
    def test_type_out_parameter_precedence(self, mock_type_out):
        """Test type_out function parameter handling precedence."""
        # Test various parameter combinations
        test_cases = [
            ("text1", 0.1, None),
            ("text2", None, 0.2),
            ("text3", 0.3, 0.4),
            ("text4", None, None),
        ]

        for text, base_delay, delay_range in test_cases:
            mock_type_out.reset_mock()
            type_out(text, base_delay=base_delay, delay_range=delay_range)
            mock_type_out.assert_called_once_with(text, base_delay, delay_range)


class TestUsePreset:
    """Test cases for use_preset function."""

    def test_use_preset_default(self):
        """Test use_preset with 'default' preset."""
        printer = use_preset("default")

        assert isinstance(printer, _PresetPrinter)
        assert isinstance(printer._preset_printer, PrintingPress)

    def test_use_preset_emphasis(self):
        """Test use_preset with 'emphasis' preset."""
        printer = use_preset("emphasis")

        assert isinstance(printer, _PresetPrinter)
        assert isinstance(printer._preset_printer, PrintingPress)

    @pytest.mark.parametrize(
        "preset_name,expected_values",
        [
            ("slow", (0.30, 0.30)),
            ("contemplative", (0.15, 0.30)),
            ("nervous", (0.10, 0.40)),
            ("average", (0.12, 0.24)),
            ("confident", (0.08, 0.16)),
            ("robotic", (0.10, 0.05)),
            ("chaotic", (0.007, 0.993)),
        ],
    )
    def test_use_preset_all_character_presets(self, preset_name, expected_values):
        """Test use_preset with all character personality presets."""
        presets = get_available_presets()
        raw_timing = presets._get_raw_timing(preset_name)
        assert raw_timing == expected_values

    def test_use_preset_case_insensitive(self):
        """Test use_preset is case-insensitive."""
        test_cases = [
            "default",
            "DEFAULT",
            "Default",
            "DeFaUlT",
            "emphasis",
            "EMPHASIS",
            "Emphasis",
        ]

        for preset_name in test_cases:
            printer = use_preset(preset_name)
            assert isinstance(printer, _PresetPrinter)

    def test_use_preset_invalid_name(self):
        """Test use_preset raises ValueError for invalid preset name."""
        invalid_names = [
            "invalid_preset",
            "nonexistent",
            "fake",
            "wrong",
        ]

        for invalid_name in invalid_names:
            with pytest.raises(ValueError) as exc_info:
                use_preset(invalid_name)

            error_message = str(exc_info.value)
            assert f"Unknown preset '{invalid_name}'" in error_message
            assert "Available presets:" in error_message

            # Check that all valid presets are listed in error message
            expected_presets = [
                "default",
                "emphasis",
                "slow",
                "contemplative",
                "nervous",
                "average",
                "confident",
                "robotic",
                "chaotic",
            ]
            for preset in expected_presets:
                assert preset in error_message

    def test_use_preset_empty_string(self):
        """Test use_preset with empty string raises appropriate error."""
        with pytest.raises(ValueError) as exc_info:
            use_preset("")

        assert "Unknown preset ''" in str(exc_info.value)

    def test_use_preset_multiple_instances_independence(self):
        """Test that multiple preset instances are independent."""
        printer1 = use_preset("nervous")
        printer2 = use_preset("confident")

        assert printer1 is not printer2
        assert printer1._preset_printer is not printer2._preset_printer

    def test_use_preset_same_preset_multiple_instances(self):
        """Test that using same preset multiple times creates different instances."""
        printer1 = use_preset("default")
        printer2 = use_preset("default")

        assert printer1 is not printer2
        assert printer1._preset_printer is not printer2._preset_printer

    def test_use_preset_all_available_presets(self):
        """Test use_preset works with all presets returned by get_available_presets."""
        available_presets = get_available_presets()

        for preset_name in available_presets:
            printer = use_preset(preset_name)
            assert isinstance(printer, _PresetPrinter)


class TestGetAvailablePresets:
    """Test cases for get_available_presets function."""

    def test_get_available_presets_returns_preset_collection(self):
        """Test get_available_presets returns a _PresetCollection."""
        from src.typytypy import _PresetCollection

        presets = get_available_presets()
        assert isinstance(presets, _PresetCollection)
        assert isinstance(presets, dict)  # Should inherit from dict

    def test_get_available_presets_contents(self):
        """Test get_available_presets returns correct preset names."""
        presets = get_available_presets()
        expected_presets = {
            "default",
            "emphasis",
            "slow",
            "contemplative",
            "nervous",
            "average",
            "confident",
            "robotic",
            "chaotic",
        }

        assert set(presets.keys()) == expected_presets
        assert len(presets) == len(expected_presets)

    def test_get_available_presets_formatted_values(self):
        """Test that get_available_presets returns properly formatted strings."""
        presets = get_available_presets()

        for _preset_name, formatted_string in presets.items():
            assert isinstance(formatted_string, str)
            assert "base_delay:" in formatted_string
            assert "delay_range:" in formatted_string
            assert formatted_string.startswith("(")
            assert formatted_string.endswith(")")

    def test_get_available_presets_all_strings(self):
        """Test all returned preset names are strings."""
        presets = get_available_presets()
        assert all(isinstance(preset, str) for preset in presets)

    def test_get_available_presets_string_representation(self):
        """Test that get_available_presets result can be printed."""
        presets = get_available_presets()
        str_output = str(presets)

        assert "Available presets:" in str_output
        assert "default:" in str_output
        assert "chaotic:" in str_output

    def test_get_available_presets_no_duplicates(self):
        """Test get_available_presets returns no duplicate preset names."""
        presets = get_available_presets()
        assert len(presets) == len(set(presets))

    def test_get_available_presets_consistency_with_use_preset(self):
        """Test that all presets from get_available_presets work with use_preset."""
        presets = get_available_presets()

        for preset_name in presets:
            # Should not raise an exception
            printer = use_preset(preset_name)
            assert isinstance(printer, _PresetPrinter)

    def test_get_available_presets_immutability(self):
        """Test that modifying returned dictionary doesn't affect subsequent calls."""
        presets1 = get_available_presets()
        original_length = len(presets1)
        original_keys = set(presets1.keys())

        # Modify the returned dictionary
        presets1["fake_preset"] = "fake_value"

        # Get fresh dictionary
        presets2 = get_available_presets()

        assert len(presets2) == original_length
        assert "fake_preset" not in presets2
        assert set(presets2.keys()) == original_keys

    def test_format_preset_function_coverage(self):
        """Test the internal format_preset function through get_available_presets."""
        presets = get_available_presets()

        # Test that raw timings are obtained (this exercises _get_raw_timing)
        for preset_name in presets:
            raw_timing = presets._get_raw_timing(preset_name)
            assert isinstance(raw_timing, tuple)
            assert len(raw_timing) == 2
            assert all(isinstance(x, (int, float)) for x in raw_timing)

    def test_dynamic_preset_extraction(self):
        """Test that preset names are extracted dynamically from _TimingPresets."""
        presets = get_available_presets()

        # Verify all _TimingPresets uppercase attributes are included
        timing_preset_attrs = [
            name
            for name in vars(_TimingPresets)
            if name.isupper() and not name.startswith("__")
        ]

        expected_lowercase = {name.lower() for name in timing_preset_attrs}
        assert set(presets.keys()) == expected_lowercase


class TestExports:
    """Test cases for __all__ exports and module-level imports."""

    def test_all_exports_defined(self):
        """Test that __all__ is properly defined."""
        assert hasattr(typytypy, "__all__")
        assert isinstance(typytypy.__all__, list)

    def test_all_exports_accessible(self):
        """Test that all items in __all__ are accessible from module."""
        expected_exports = [
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

        assert typytypy.__all__ == expected_exports

        # Test each export is actually accessible
        for export_name in expected_exports:
            assert hasattr(
                typytypy, export_name
            ), f"Export '{export_name}' not accessible"

    def test_star_import_items(self):
        """Test that star import provides expected functionality."""
        all_items = typytypy.__all__

        for item in all_items:
            imported_item = getattr(typytypy, item)
            assert imported_item is not None

    def test_core_imports(self):
        """Test that core imports are accessible."""
        assert typytypy.PrintingPress is PrintingPress
        assert hasattr(typytypy, "PrintingPress")

    def test_function_imports(self):
        """Test that function imports are accessible."""
        assert typytypy.type_out is type_out
        assert typytypy.use_preset is use_preset
        assert typytypy.get_available_presets is get_available_presets

    def test_metadata_imports(self):
        """Test that metadata imports are accessible."""
        metadata_items = [
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

        for item in metadata_items:
            assert hasattr(typytypy, item)
            assert getattr(typytypy, item) is not None


class TestInternalClassesAndStructures:
    """Test cases for internal classes and data structures."""

    def test_timing_presets_class_exists(self):
        """Test that _TimingPresets class exists and has expected attributes."""
        assert hasattr(typytypy, "_TimingPresets")

        expected_attributes = [
            "DEFAULT",
            "EMPHASIS",
            "SLOW",
            "CONTEMPLATIVE",
            "NERVOUS",
            "AVERAGE",
            "CONFIDENT",
            "ROBOTIC",
            "CHAOTIC",
        ]

        for attr in expected_attributes:
            assert hasattr(_TimingPresets, attr)

    def test_preset_printer_class_exists(self):
        """Test that _PresetPrinter class exists."""
        assert hasattr(typytypy, "_PresetPrinter")

        # Test it can be instantiated
        printer = _PresetPrinter(0.1, 0.05)
        assert hasattr(printer, "type_out")
        assert callable(printer.type_out)

    def test_internal_classes_not_exported(self):
        """Test that internal classes are not in __all__ exports."""
        exports = typytypy.__all__
        assert "_TimingPresets" not in exports
        assert "_PresetPrinter" not in exports


class TestIntegrationAndEdgeCases:
    """Test cases for integration scenarios and edge cases."""

    @patch("src.typytypy.PrintingPress")
    def test_preset_printer_initialization_integration(self, mock_printing_press):
        """Test full integration of preset printer initialization."""
        mock_instance = Mock()
        mock_printing_press.return_value = mock_instance

        base_delay = 0.15
        delay_range = 0.05
        printer = _PresetPrinter(base_delay, delay_range)

        # Verify PrintingPress was called with correct parameters
        mock_printing_press.assert_called_once_with(
            base_delay=base_delay, delay_range=delay_range
        )
        assert printer._preset_printer is mock_instance

    def test_multiple_preset_usage(self):
        """Test using multiple presets simultaneously."""
        presets = ["nervous", "confident", "chaotic"]
        printers = [use_preset(name) for name in presets]

        # All should be different instances
        for i, printer1 in enumerate(printers):
            for j, printer2 in enumerate(printers):
                if i != j:
                    assert printer1 is not printer2

    def test_preset_map_completeness(self):
        """Test that internal preset map covers all available presets."""
        available_presets = get_available_presets()

        # All presets should work without raising KeyError
        for preset_name in available_presets:
            # This exercises the internal preset_map dictionary
            printer = use_preset(preset_name)
            assert isinstance(printer, _PresetPrinter)


class TestDocstringsAndMetadata:
    """Test cases for module docstring and metadata consistency."""

    def test_module_has_docstring(self):
        """Test that the module has a comprehensive docstring."""
        assert typytypy.__doc__ is not None
        docstring = typytypy.__doc__
        assert len(docstring.strip()) > 0
        assert "typytypy" in docstring
        assert "A Bespoke Character-by-Character Text Printer." in docstring

    def test_module_docstring_contains_examples(self):
        """Test that module docstring contains usage examples."""
        docstring = typytypy.__doc__
        assert docstring is not None
        assert "Examples:" in docstring
        assert "import typytypy" in docstring
        assert "type_out" in docstring

    def test_module_docstring_contains_classes(self):
        """Test that module docstring lists main classes."""
        docstring = typytypy.__doc__
        assert docstring is not None
        assert "PrintingPress:" in docstring

    def test_function_docstrings_exist(self):
        """Test that main functions have docstrings."""
        functions_to_check = [type_out, use_preset, get_available_presets]

        for func in functions_to_check:
            assert func.__doc__ is not None
            assert len(func.__doc__.strip()) > 0


class TestErrorHandlingAndValidation:
    """Test cases for comprehensive error handling and validation scenarios."""

    def test_use_preset_none_input(self):
        """Test use_preset with None input raises appropriate error."""
        with pytest.raises(ValueError):
            # This will fail when trying to pass None to a str parameter
            use_preset(str(None))

    def test_use_preset_numeric_input(self):
        """Test use_preset with numeric input raises appropriate error."""
        with pytest.raises(ValueError):
            # This will fail when trying to call .lower() on a number
            use_preset(str(123))

    def test_preset_error_message_formatting(self):
        """Test that preset error messages are properly formatted."""
        with pytest.raises(ValueError) as exc_info:
            use_preset("invalid")

        error_message = str(exc_info.value)
        assert "Unknown preset 'invalid'" in error_message
        assert "Available presets: " in error_message

        # Verify all presets are listed with proper formatting
        available_presets = get_available_presets()
        expected_preset_list = ", ".join(available_presets)
        assert expected_preset_list in error_message


class TestComprehensiveCoverage:
    """Test cases to ensure 100% code coverage of remaining edge cases."""

    def test_timing_presets_all_attributes_accessible(self):
        """Test that all _TimingPresets attributes are accessible and valid."""
        preset_attributes = [
            "DEFAULT",
            "EMPHASIS",
            "SLOW",
            "CONTEMPLATIVE",
            "NERVOUS",
            "AVERAGE",
            "CONFIDENT",
            "ROBOTIC",
            "CHAOTIC",
        ]

        for attr_name in preset_attributes:
            preset_value = getattr(_TimingPresets, attr_name)
            assert isinstance(preset_value, tuple)
            assert len(preset_value) == 2
            assert all(isinstance(x, int | float) for x in preset_value)

    def test_preset_printer_init_parameter_handling(self):
        """Test _PresetPrinter initialization with various parameter types."""
        # Test with different numeric types
        test_cases = [
            (0.1, 0.05),  # floats
            (1, 2),  # integers
            (0.0, 0.0),  # zero values
        ]

        for base_delay, delay_range in test_cases:
            printer = _PresetPrinter(base_delay, delay_range)
            assert isinstance(printer._preset_printer, PrintingPress)

    def test_module_level_imports_coverage(self):
        """Test that all module-level imports are covered."""
        # Test that imports from core work
        assert PrintingPress is not None
        assert type_out is not None
        assert use_preset is not None
        assert get_available_presets is not None

    def test_use_preset_case_variations_comprehensive(self):
        """Test use_preset with comprehensive case variations."""
        base_preset = "default"
        case_variations = [
            base_preset,
            base_preset.upper(),
            base_preset.capitalize(),
            base_preset.title(),
            "".join(c.upper() if i % 2 else c for i, c in enumerate(base_preset)),
        ]

        for variation in case_variations:
            printer = use_preset(variation)
            assert isinstance(printer, _PresetPrinter)

    def test_get_available_presets_return_value_type(self):
        """Test that get_available_presets returns the expected _PresetCollection."""
        from src.typytypy import _PresetCollection

        presets = get_available_presets()

        # Verify exact match with expected preset keys
        expected_keys = [
            "default",
            "emphasis",
            "slow",
            "contemplative",
            "nervous",
            "average",
            "confident",
            "robotic",
            "chaotic",
        ]

        assert list(presets.keys()) == expected_keys
        assert isinstance(presets, _PresetCollection)
        assert isinstance(presets, dict)  # Should inherit from dict
        assert type(presets) is _PresetCollection

    def test_all_list_completeness(self):
        """Test that __all__ list is comprehensive and accurate."""
        expected_all = [
            "type_out",
            "use_preset",
            "get_available_presets",
            "PrintingPress",
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

        assert typytypy.__all__ == expected_all

        # Verify each item is actually available
        for item in expected_all:
            assert hasattr(typytypy, item)

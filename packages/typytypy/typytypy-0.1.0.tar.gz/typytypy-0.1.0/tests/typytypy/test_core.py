"""Comprehensive test suite for TypyTypy's core.py module.

This module tests the PrintingPress class and all its functionality,
ensuring complete code coverage and proper behavior validation.
"""

from typing import Any
from unittest.mock import call, patch

import pytest

from src.typytypy.core import (
    TIMING_MAX_VALUE,
    TIMING_MIN_VALUE,
    PrintingPress,
    _ProfileData,
)
from src.typytypy.exceptions import (
    ConfigurationError,
    InvalidTimingError,
    ProfileError,
)


class TestPrintingPressInitialization:
    """Test cases for PrintingPress initialization."""

    def test_default_initialization(self):
        """Test initialization with default parameters."""
        printer = PrintingPress()
        assert printer.base_delay == PrintingPress.DEFAULT_BASE_DELAY
        assert printer.delay_range == PrintingPress.DEFAULT_DELAY_RANGE
        assert printer.profiles == {}
        assert printer.word_to_profile == {}
        assert printer.normalized_to_original == {}
        assert printer.case_sensitive_setting is True

    def test_custom_initialization(self):
        """Test initialization with custom parameters."""
        base_delay = 0.05
        delay_range = 0.03
        printer = PrintingPress(base_delay=base_delay, delay_range=delay_range)
        assert printer.base_delay == base_delay
        assert printer.delay_range == delay_range

    def test_partial_custom_initialization_base_delay_only(self):
        """Test initialization with only base_delay specified."""
        base_delay = 0.08
        printer = PrintingPress(base_delay=base_delay)
        assert printer.base_delay == base_delay
        assert printer.delay_range == PrintingPress.DEFAULT_DELAY_RANGE

    def test_partial_custom_initialization_delay_range_only(self):
        """Test initialization with only delay_range specified."""
        delay_range = 0.06
        printer = PrintingPress(delay_range=delay_range)
        assert printer.base_delay == PrintingPress.DEFAULT_BASE_DELAY
        assert printer.delay_range == delay_range

    def test_initialization_with_invalid_base_delay_too_low(self):
        """Test initialization with base_delay below minimum."""
        with pytest.raises(InvalidTimingError) as exc_info:
            PrintingPress(base_delay=-0.1)
        assert "base_delay must be non-negative" in str(exc_info.value)
        assert exc_info.value.parameter_name == "base_delay"
        assert exc_info.value.parameter_value == -0.1

    def test_initialization_with_invalid_base_delay_too_high(self):
        """Test initialization with base_delay above maximum."""
        with pytest.raises(InvalidTimingError) as exc_info:
            PrintingPress(base_delay=15.0)
        assert f"base_delay exceeds reasonable maximum ({TIMING_MAX_VALUE}s)" in str(
            exc_info.value
        )

    def test_initialization_with_invalid_delay_range_too_low(self):
        """Test initialization with delay_range below minimum."""
        with pytest.raises(InvalidTimingError) as exc_info:
            PrintingPress(delay_range=-0.5)
        assert "delay_range must be non-negative" in str(exc_info.value)

    def test_initialization_with_invalid_delay_range_too_high(self):
        """Test initialization with delay_range above maximum."""
        with pytest.raises(InvalidTimingError) as exc_info:
            PrintingPress(delay_range=12.0)
        assert f"delay_range exceeds reasonable maximum ({TIMING_MAX_VALUE}s)" in str(
            exc_info.value
        )


class TestTimingValidation:
    """Test cases for timing validation methods."""

    def test_validate_timing_valid_values(self):
        """Test validation with valid timing values."""
        printer = PrintingPress()
        printer._validate_timing(0.0, "test_param")
        printer._validate_timing(5.0, "test_param")
        printer._validate_timing(TIMING_MAX_VALUE, "test_param")

    def test_validate_timing_minimum_boundary(self):
        """Test validation at minimum boundary."""
        printer = PrintingPress()
        printer._validate_timing(TIMING_MIN_VALUE, "test_param")

    def test_validate_timing_maximum_boundary(self):
        """Test validation at maximum boundary."""
        printer = PrintingPress()
        printer._validate_timing(TIMING_MAX_VALUE, "test_param")

    def test_validate_timing_below_minimum(self):
        """Test validation below minimum value."""
        printer = PrintingPress()
        with pytest.raises(InvalidTimingError) as exc_info:
            printer._validate_timing(-0.1, "test_param")
        assert "test_param must be non-negative" in str(exc_info.value)

    def test_validate_timing_above_maximum(self):
        """Test validation above maximum value."""
        printer = PrintingPress()
        with pytest.raises(InvalidTimingError) as exc_info:
            printer._validate_timing(11.0, "test_param")
        assert f"test_param exceeds reasonable maximum ({TIMING_MAX_VALUE}s)" in str(
            exc_info.value
        )


class TestWordNormalization:
    """Test cases for word normalization methods."""

    def test_normalize_word_case_sensitive(self):
        """Test word normalization with case-sensitivity enabled."""
        printer = PrintingPress()
        printer.case_sensitive_setting = True
        assert printer._normalize_word("Hello") == "Hello"
        assert printer._normalize_word("WORLD") == "WORLD"
        assert printer._normalize_word("test") == "test"

    def test_normalize_word_case_insensitive(self):
        """Test word normalization with case-sensitivity disabled."""
        printer = PrintingPress()
        printer.case_sensitive_setting = False
        assert printer._normalize_word("Hello") == "hello"
        assert printer._normalize_word("WoRlD") == "world"
        assert printer._normalize_word("Test") == "test"


class TestProfileCreation:
    """Test cases for profile creation."""

    def test_create_profile_basic(self):
        """Test creating a basic profile without words."""
        printer = PrintingPress()
        result = printer.create_profile("test_profile", 0.1, 0.05)
        assert result is True
        assert "test_profile" in printer.profiles
        assert printer.profiles["test_profile"]["base_delay"] == 0.1
        assert printer.profiles["test_profile"]["delay_range"] == 0.05
        assert printer.profiles["test_profile"]["words"] == set()

    def test_create_profile_with_single_word(self):
        """Test creating a profile with a single word."""
        printer = PrintingPress()
        result = printer.create_profile("test_profile", 0.1, 0.05, "hello")
        assert result is True
        assert "hello" in printer.profiles["test_profile"]["words"]
        assert printer.word_to_profile["hello"] == "test_profile"
        assert printer.normalized_to_original["hello"] == "hello"

    def test_create_profile_with_word_list(self):
        """Test creating a profile with a list of words."""
        printer = PrintingPress()
        words = ["hello", "world", "test"]
        result = printer.create_profile("test_profile", 0.1, 0.05, words)
        assert result is True
        for word in words:
            assert word in printer.profiles["test_profile"]["words"]
            assert printer.word_to_profile[word] == "test_profile"
            assert printer.normalized_to_original[word] == word

    def test_create_profile_duplicate_name(self):
        """Test creating a profile with duplicate name."""
        printer = PrintingPress()
        printer.create_profile("duplicate", 0.1, 0.05)
        result = printer.create_profile("duplicate", 0.2, 0.1)
        assert result is False
        # Original profile should remain unchanged
        assert printer.profiles["duplicate"]["base_delay"] == 0.1
        assert printer.profiles["duplicate"]["delay_range"] == 0.05

    def test_create_profile_invalid_base_delay(self):
        """Test creating a profile with invalid base_delay."""
        printer = PrintingPress()
        with pytest.raises(InvalidTimingError):
            printer.create_profile("test", -0.1, 0.05)

    def test_create_profile_invalid_delay_range(self):
        """Test creating a profile with invalid delay_range."""
        printer = PrintingPress()
        with pytest.raises(InvalidTimingError):
            printer.create_profile("test", 0.1, -0.05)


class TestInputDuplicateDetection:
    """Test cases for input duplicate detection."""

    def test_detect_input_duplicates_case_sensitive_no_duplicates(self):
        """Test duplicate detection with case-sensitivity and no duplicates."""
        printer = PrintingPress()
        printer.case_sensitive_setting = True
        words = ["Hello", "hello", "HELLO"]  # Different cases, no duplicates
        result = printer._detect_input_duplicates(words)
        assert result == []

    def test_detect_input_duplicates_case_sensitive_with_duplicates(self):
        """Test duplicate detection with case-sensitivity and duplicates."""
        printer = PrintingPress()
        printer.case_sensitive_setting = True
        words = ["Hello", "World", "Hello"]  # Exact duplicate
        result = printer._detect_input_duplicates(words)
        assert "Hello" in result

    def test_detect_input_duplicates_case_sensitive_exact_triple_occurrence(self):
        """Test duplicate detection with case-sensitivity and 3x duplicates."""
        printer = PrintingPress()
        printer.case_sensitive_setting = True
        words = ["Hello", "World", "Hello", "Test", "Hello"]  # Exact duplicate x3
        result = printer._detect_input_duplicates(words)

        # Should return the duplicate word only once
        assert result == ["Hello"]
        assert result.count("Hello") == 1

    def test_detect_input_duplicates_case_insensitive_with_duplicates(self):
        """Test duplicate detection without case-sensitivity and duplicates."""
        printer = PrintingPress()
        printer.case_sensitive_setting = False
        words = ["Hello", "hello", "HELLO"]  # Case-insensitive duplicates
        result = printer._detect_input_duplicates(words)
        assert len(result) == 1  # "Hello" and "HELLO" are duplicates of "hello"

    def test_detect_input_duplicates_case_insensitive_no_duplicates(self):
        """Test duplicate detection without case-sensitivity and no duplicates."""
        printer = PrintingPress()
        printer.case_sensitive_setting = False
        words = ["Hello", "World", "Test"]
        result = printer._detect_input_duplicates(words)
        assert result == []


class TestProfileModification:
    """Test cases for profile modification methods."""

    def test_modify_profile_add_words(self):
        """Test adding words to a profile."""
        printer = PrintingPress()
        printer.create_profile("test", 0.1, 0.05)
        result = printer._modify_profile("test", ["word1", "word2"], "add")
        assert result == 2
        assert "word1" in printer.profiles["test"]["words"]
        assert "word2" in printer.profiles["test"]["words"]

    def test_modify_profile_add_with_duplicates_case_sensitive(self):
        """Test adding words with duplicates in case-sensitive mode."""
        printer = PrintingPress()
        printer.case_sensitive_setting = True
        printer.create_profile("test", 0.1, 0.05)

        with pytest.raises(ProfileError) as exc_info:
            printer._modify_profile("test", ["Word", "other", "Word"], "add")
        assert "case-sensitive duplicates" in str(exc_info.value)

    def test_modify_profile_add_with_duplicates_case_insensitive(self):
        """Test adding words with duplicates in case-insensitive mode."""
        printer = PrintingPress()
        printer.case_sensitive_setting = False
        printer.create_profile("test", 0.1, 0.05)

        with pytest.raises(ProfileError) as exc_info:
            printer._modify_profile("test", ["Word", "other", "word"], "add")
        assert "case-insensitive duplicates" in str(exc_info.value)

    def test_modify_profile_remove_words(self):
        """Test removing words from a profile."""
        printer = PrintingPress()
        printer.create_profile("test", 0.1, 0.05, ["word1", "word2", "word3"])
        result = printer._modify_profile("test", ["word1", "word2"], "remove")
        assert result == 2
        assert "word1" not in printer.profiles["test"]["words"]
        assert "word2" not in printer.profiles["test"]["words"]
        assert "word3" in printer.profiles["test"]["words"]

    def test_modify_profile_nonexistent_profile(self):
        """Test modifying a nonexistent profile."""
        printer = PrintingPress()
        with pytest.raises(ProfileError) as exc_info:
            printer._modify_profile("nonexistent", ["word"], "add")
        assert "Profile 'nonexistent' does not exist" in str(exc_info.value)

    def test_modify_profile_invalid_action(self):
        """Test modifying a profile with invalid action."""
        printer = PrintingPress()
        printer.create_profile("test", 0.1, 0.05)
        with pytest.raises(ProfileError) as exc_info:
            printer._modify_profile("test", ["word"], "invalid_action")
        assert "Action must be 'add' or 'remove'" in str(exc_info.value)

    def test_modify_profile_auto_transfer(self):
        """Test auto-transfer when adding word that exists in another profile."""
        printer = PrintingPress()
        printer.create_profile("profile1", 0.1, 0.05, ["shared_word"])
        printer.create_profile("profile2", 0.2, 0.1)

        result = printer._modify_profile("profile2", ["shared_word"], "add")
        assert result == 1
        assert "shared_word" not in printer.profiles["profile1"]["words"]
        assert "shared_word" in printer.profiles["profile2"]["words"]
        assert printer.word_to_profile["shared_word"] == "profile2"
        assert printer.normalized_to_original["shared_word"] == "shared_word"

    def test_modify_profile_auto_transfer_validation_failure(self):
        """Test auto-transfer validation failure with realistic corruption."""
        printer = PrintingPress()
        printer.create_profile("profile1", 0.1, 0.05, ["shared_word"])
        printer.create_profile("profile2", 0.2, 0.1)
        printer.create_profile("profile3", 0.3, 0.2)

        result = printer._modify_profile("profile2", ["shared_word"], "add")
        assert result == 1

        # Manually corrupt state AFTER successful auto-transfer
        # Put the word back in profile1 to create validation failure
        printer.profiles["profile1"]["words"].add("shared_word")

        # Add the word - auto-transfer will occur but validation will
        # fail because the word already exists in a profile
        with pytest.raises(ProfileError) as exc_info:
            printer._modify_profile("profile3", ["shared_word"], "add")
        assert "Auto-transfer validation failed" in str(exc_info.value)
        assert "still exists in old profile 'profile1'" in str(exc_info.value)

    def test_add_words_to_profile(self):
        """Test add_words_to_profile wrapper method."""
        printer = PrintingPress()
        printer.create_profile("test", 0.1, 0.05)
        result = printer.add_words_to_profile("test", ["word1", "word2"])
        assert result == 2

    def test_remove_words_from_profile(self):
        """Test remove_words_from_profile wrapper method."""
        printer = PrintingPress()
        printer.create_profile("test", 0.1, 0.05, ["word1", "word2"])
        result = printer.remove_words_from_profile("test", ["word1"])
        assert result == 1

    def test_remove_words_from_profile_nonexistent_word(self):
        """Test removing nonexistent words from profile."""
        printer = PrintingPress()
        printer.create_profile("test", 0.1, 0.05, ["word1"])
        result = printer.remove_words_from_profile("test", ["nonexistent"])
        assert result == 0

    def test_remove_words_missing_word_to_profile_mapping(self):
        """Test removing word in profile but missing from word_to_profile."""
        printer = PrintingPress()
        printer.create_profile("test", 0.1, 0.05, ["test_word"])

        # Manually corrupt state: remove from word_to_profile
        del printer.word_to_profile["test_word"]

        # Remove the word - should handle missing mapping gracefully
        result = printer.remove_words_from_profile("test", ["test_word"])
        assert result == 1
        assert "test_word" not in printer.profiles["test"]["words"]
        assert "test_word" not in printer.normalized_to_original

    def test_remove_words_missing_normalized_to_original_mapping(self):
        """Test removing word in profile but missing from normalized_to_original."""
        printer = PrintingPress()
        printer.create_profile("test", 0.1, 0.05, ["test_word"])

        # Manually corrupt state: remove from normalized_to_original
        del printer.normalized_to_original["test_word"]

        # Remove the word - should handle missing mapping gracefully
        result = printer.remove_words_from_profile("test", ["test_word"])
        assert result == 1
        assert "test_word" not in printer.profiles["test"]["words"]
        assert "test_word" not in printer.word_to_profile

    def test_remove_words_missing_both_mappings(self):
        """Test removing word that exists in profile but missing from both mappings."""
        printer = PrintingPress()
        printer.create_profile("test", 0.1, 0.05, ["test_word"])

        # Manually corrupt state: remove from both mappings
        del printer.word_to_profile["test_word"]
        del printer.normalized_to_original["test_word"]

        # Remove the word - should handle missing mappings gracefully
        result = printer.remove_words_from_profile("test", ["test_word"])
        assert result == 1
        assert "test_word" not in printer.profiles["test"]["words"]
        # Both mappings should remain empty
        assert "test_word" not in printer.word_to_profile
        assert "test_word" not in printer.normalized_to_original


class TestAutoTransferValidation:
    """Test cases for auto-transfer validation."""

    def test_validate_auto_transfer_success(self):
        """Test successful auto-transfer validation."""
        printer = PrintingPress()
        printer.create_profile("test", 0.1, 0.05)
        printer.add_words_to_profile("test", ["word"])

        success, message = printer._validate_auto_transfer("word", "test")
        assert success is True
        assert "Auto-transfer validation successful" in message

    def test_validate_auto_transfer_missing_normalized_mapping(self):
        """Test auto-transfer validation with missing normalized mapping."""
        printer = PrintingPress()
        printer.create_profile("test", 0.1, 0.05)

        # Manually break the mapping
        printer.profiles["test"]["words"].add("word")

        success, message = printer._validate_auto_transfer("word", "test")
        assert success is False
        assert "not found in word_to_profile mapping" in message

    def test_validate_auto_transfer_wrong_profile_mapping(self):
        """Test auto-transfer validation with wrong profile mapping."""
        printer = PrintingPress()
        printer.create_profile("test1", 0.1, 0.05)
        printer.create_profile("test2", 0.1, 0.05)
        printer.add_words_to_profile("test1", ["word"])

        success, message = printer._validate_auto_transfer("word", "test2")
        assert success is False
        assert "mapped to 'test1' instead of 'test2'" in message

    def test_validate_auto_transfer_missing_from_target_profile(self):
        """Test auto-transfer validation with word missing from target profile."""
        printer = PrintingPress()
        printer.create_profile("test", 0.1, 0.05)

        # Manually add mapping but not to profile
        printer.word_to_profile["word"] = "test"

        success, message = printer._validate_auto_transfer("word", "test")
        assert success is False
        assert "not found in target profile" in message

    def test_validate_auto_transfer_word_in_old_profile(self):
        """Test auto-transfer validation with word still in old profile."""
        printer = PrintingPress()
        printer.create_profile("old", 0.1, 0.05)
        printer.create_profile("new", 0.1, 0.05)

        # Manually create a broken state
        printer.profiles["old"]["words"].add("word")
        printer.profiles["new"]["words"].add("word")
        printer.word_to_profile["word"] = "new"

        success, message = printer._validate_auto_transfer("word", "new")
        assert success is False
        assert "still exists in old profile 'old'" in message


class TestProfileManagement:
    """Test cases for profile management methods."""

    def test_delete_profile_success(self):
        """Test successful profile deletion."""
        printer = PrintingPress()
        printer.create_profile("to_delete", 0.1, 0.05, ["word1", "word2"])
        result = printer.delete_profile("to_delete")
        assert result is True
        assert "to_delete" not in printer.profiles
        assert "word1" not in printer.word_to_profile
        assert "word2" not in printer.word_to_profile
        assert "word1" not in printer.normalized_to_original
        assert "word2" not in printer.normalized_to_original

    def test_delete_profile_nonexistent(self):
        """Test deleting nonexistent profile."""
        printer = PrintingPress()
        result = printer.delete_profile("nonexistent")
        assert result is False

    def test_delete_profile_missing_word_to_profile_mapping(self):
        """Test deleting profile when word in profile but not word_to_profile."""
        printer = PrintingPress()
        printer.create_profile("test", 0.1, 0.05, ["test_word"])

        # Manually corrupt state: remove from word_to_profile
        del printer.word_to_profile["test_word"]

        # Delete profile - should handle missing mapping gracefully
        result = printer.delete_profile("test")
        assert result is True
        assert "test" not in printer.profiles
        assert "test_word" not in printer.normalized_to_original

    def test_delete_profile_missing_normalized_to_original_mapping(self):
        """Test deleting profile when word in profile but not normalized_to_original."""
        printer = PrintingPress()
        printer.create_profile("test", 0.1, 0.05, ["test_word"])

        # Manually corrupt state: remove from normalized_to_original
        del printer.normalized_to_original["test_word"]

        # Delete profile - should handle missing mapping gracefully
        result = printer.delete_profile("test")
        assert result is True
        assert "test" not in printer.profiles
        assert "test_word" not in printer.word_to_profile

    def test_delete_profile_missing_both_mappings(self):
        """Test deleting profile when word in profile but not both mappings."""
        printer = PrintingPress()
        printer.create_profile("test", 0.1, 0.05, ["test_word"])

        # Manually corrupt state: remove from both mappings
        del printer.word_to_profile["test_word"]
        del printer.normalized_to_original["test_word"]

        # Delete profile - should handle missing mappings gracefully
        result = printer.delete_profile("test")
        assert result is True
        assert "test" not in printer.profiles
        # Both mappings should remain empty
        assert "test_word" not in printer.word_to_profile
        assert "test_word" not in printer.normalized_to_original

    def test_list_profiles_empty(self):
        """Test listing profiles when none exist."""
        printer = PrintingPress()
        result = printer.list_profiles()
        assert result == []

    def test_list_profiles_with_profiles(self):
        """Test listing profiles when some exist."""
        printer = PrintingPress()
        printer.create_profile("profile1", 0.1, 0.05)
        printer.create_profile("profile2", 0.2, 0.1)
        result = printer.list_profiles()
        assert set(result) == {"profile1", "profile2"}

    def test_get_profile_info_existing(self):
        """Test getting info for existing profile."""
        printer = PrintingPress()
        printer.create_profile("test", 0.1, 0.05, ["word1", "word2"])
        result = printer.get_profile_info("test")
        assert result is not None
        assert result["base_delay"] == 0.1
        assert result["delay_range"] == 0.05
        assert set(result["words"] if isinstance(result["words"], list) else []) == {
            "word1",
            "word2",
        }
        assert result["word_count"] == 2

    def test_get_profile_info_nonexistent(self):
        """Test getting info for nonexistent profile."""
        printer = PrintingPress()
        result = printer.get_profile_info("nonexistent")
        assert result is None

    def test_update_profile_timing_success(self):
        """Test successful profile timing update."""
        printer = PrintingPress()
        printer.create_profile("test", 0.1, 0.05)
        result = printer.update_profile_timing("test", 0.2, 0.1)
        assert result is True
        assert printer.profiles["test"]["base_delay"] == 0.2
        assert printer.profiles["test"]["delay_range"] == 0.1

    def test_update_profile_timing_nonexistent(self):
        """Test updating timing for nonexistent profile."""
        printer = PrintingPress()
        result = printer.update_profile_timing("nonexistent", 0.1, 0.05)
        assert result is False

    def test_update_profile_timing_invalid_values(self):
        """Test updating profile timing with invalid values."""
        printer = PrintingPress()
        printer.create_profile("test", 0.1, 0.05)
        with pytest.raises(InvalidTimingError):
            printer.update_profile_timing("test", -0.1, 0.05)


class TestCaseSensitivityCollisionDetection:
    """Test cases for case-sensitivity collision detection."""

    def test_detect_case_sensitivity_collisions_no_collisions(self):
        """Test collision detection when no collisions exist."""
        printer = PrintingPress()
        printer.case_sensitive_setting = True
        printer.create_profile("test1", 0.1, 0.05, ["Hello"])
        printer.create_profile("test2", 0.1, 0.05, ["World"])

        collisions = printer._detect_case_sensitivity_collisions()
        assert collisions == {}

    def test_detect_case_sensitivity_collisions_with_collisions(self):
        """Test collision detection when collisions exist."""
        printer = PrintingPress()
        printer.case_sensitive_setting = True
        printer.create_profile("test1", 0.1, 0.05, ["Hello"])
        printer.create_profile("test2", 0.1, 0.05, ["hello"])

        collisions = printer._detect_case_sensitivity_collisions()
        assert "hello" in collisions
        assert len(collisions["hello"]) == 2
        word_profile_pairs = collisions["hello"]
        assert ("Hello", "test1") in word_profile_pairs
        assert ("hello", "test2") in word_profile_pairs

    def test_detect_case_sensitivity_collisions_already_case_insensitive(self):
        """Test collision detection when already case-insensitive."""
        printer = PrintingPress()
        printer.case_sensitive_setting = False
        printer.create_profile("test1", 0.1, 0.05, ["hello"])
        printer.create_profile("test2", 0.1, 0.05, ["world"])

        collisions = printer._detect_case_sensitivity_collisions()
        assert collisions == {}

    def test_detect_case_sensitivity_collisions_multiple_collisions(self):
        """Test collision detection with multiple collision groups."""
        printer = PrintingPress()
        printer.case_sensitive_setting = True
        printer.create_profile("test1", 0.1, 0.05, ["Hello", "World"])
        printer.create_profile("test2", 0.1, 0.05, ["hello", "WORLD"])

        collisions = printer._detect_case_sensitivity_collisions()
        assert len(collisions) == 2
        assert "hello" in collisions
        assert "world" in collisions


class TestCaseSensitivitySwitchAnalysis:
    """Test cases for case-sensitivity switch analysis."""

    def test_analyze_case_sensitivity_switch_safe_to_insensitive(self):
        """Test analysis of safe switch to case-insensitive."""
        printer = PrintingPress()
        printer.case_sensitive_setting = True
        printer.create_profile("test", 0.1, 0.05, ["Hello", "World"])

        analysis = printer._analyze_case_sensitivity_switch(False)
        assert analysis["switch_safe"] is True
        assert analysis["current_mode"] == "case-sensitive"
        assert analysis["target_mode"] == "case-insensitive"
        assert analysis["collision_count"] == 0

    def test_analyze_case_sensitivity_switch_unsafe_to_insensitive_inter(self):
        """Test analysis of unsafe (inter) switch to case-insensitive."""
        printer = PrintingPress()
        printer.case_sensitive_setting = True
        printer.create_profile("test1", 0.1, 0.05, ["Hello"])
        printer.create_profile("test2", 0.1, 0.05, ["hello"])

        analysis = printer._analyze_case_sensitivity_switch(False)
        assert analysis["switch_safe"] is False
        assert analysis["collision_count"] == 1
        assert "hello" in analysis["collisions"]
        assert "test1" in analysis["affected_profiles"]
        assert "test2" in analysis["affected_profiles"]

    def test_analyze_case_sensitivity_switch_unsafe_to_insensitive_intra(self):
        """Test analysis of unsafe (intra) switch to case-insensitive."""
        printer = PrintingPress()
        printer.case_sensitive_setting = True
        printer.create_profile("test", 0.1, 0.05, ["Hello", "HeLLo"])

        analysis = printer._analyze_case_sensitivity_switch(False)
        assert analysis["switch_safe"] is False
        assert analysis["collision_count"] == 1
        assert "hello" in analysis["collisions"]
        assert "test" in analysis["affected_profiles"]

    def test_analyze_case_sensitivity_switch_to_sensitive(self):
        """Test analysis of switch to case-sensitive."""
        printer = PrintingPress()
        printer.case_sensitive_setting = False
        printer.create_profile("test", 0.1, 0.05, ["hello"])

        analysis = printer._analyze_case_sensitivity_switch(True)
        assert analysis["switch_safe"] is True
        assert analysis["current_mode"] == "case-insensitive"
        assert analysis["target_mode"] == "case-sensitive"

    def test_analyze_case_sensitivity_switch_no_change(self):
        """Test analysis when no change is needed."""
        printer = PrintingPress()
        printer.case_sensitive_setting = True

        analysis = printer._analyze_case_sensitivity_switch(True)
        assert analysis["switch_safe"] is True
        assert "Already in case-sensitive mode" in analysis["recommendations"][0]


class TestCaseSensitivity:
    """Test cases for case-sensitivity configuration."""

    def test_set_profile_case_sensitivity_valid_true(self):
        """Test setting case-sensitivity to True."""
        printer = PrintingPress()
        printer.case_sensitive_setting = False
        printer.create_profile("test", 0.1, 0.05, ["hello"])

        printer.set_profile_case_sensitivity(True)
        assert printer.case_sensitive_setting is True

    def test_set_profile_case_sensitivity_valid_false_safe(self):
        """Test setting case-sensitivity to False when safe."""
        printer = PrintingPress()
        printer.case_sensitive_setting = True
        printer.create_profile("test", 0.1, 0.05, ["Hello", "World"])

        printer.set_profile_case_sensitivity(False)
        assert printer.case_sensitive_setting is False

    def test_set_profile_case_sensitivity_valid_false_unsafe(self):
        """Test setting case-sensitivity to False when unsafe."""
        printer = PrintingPress()
        printer.case_sensitive_setting = True
        printer.create_profile("test1", 0.1, 0.05, ["Hello"])
        printer.create_profile("test2", 0.1, 0.05, ["hello"])

        with pytest.raises(ConfigurationError) as exc_info:
            printer.set_profile_case_sensitivity(False)
        assert "Cannot switch to case-insensitive mode" in str(exc_info.value)
        assert "word collision(s) detected" in str(exc_info.value)

    def test_set_profile_case_sensitivity_no_change(self):
        """Test setting case-sensitivity to same value."""
        printer = PrintingPress()
        original_setting = printer.case_sensitive_setting
        printer.set_profile_case_sensitivity(True)  # Same as default
        assert printer.case_sensitive_setting == original_setting

    def test_set_profile_case_sensitivity_invalid_type(self):
        """Test setting case-sensitivity with invalid type."""
        printer = PrintingPress()
        invalid_value: Any = "invalid"
        with pytest.raises(ConfigurationError) as exc_info:
            printer.set_profile_case_sensitivity(invalid_value)
        assert "Case-sensitivity setting must be a boolean value" in str(exc_info.value)
        assert exc_info.value.setting_name == "case_sensitive"
        assert exc_info.value.setting_value == "invalid"
        assert exc_info.value.expected_type is bool


class TestMappingRebuild:
    """Test cases for mapping rebuild after sensitivity changes."""

    def test_rebuild_mappings_after_sensitivity_change(self):
        """Test rebuilding mappings when case-sensitivity changes."""
        printer = PrintingPress()
        printer.case_sensitive_setting = True
        # Create profiles with mixed case words
        printer.create_profile("test1", 0.1, 0.05, ["Hello", "WORLD"])
        printer.create_profile("test2", 0.2, 0.1, ["Test"])

        # Verify initial mappings
        assert printer.word_to_profile["Hello"] == "test1"
        assert printer.word_to_profile["WORLD"] == "test1"
        assert printer.word_to_profile["Test"] == "test2"

        # Change to case-insensitive (safe change)
        printer.case_sensitive_setting = False
        printer._rebuild_mappings_after_sensitivity_change()

        # Check that mappings use lowercase keys
        assert printer.word_to_profile["hello"] == "test1"
        assert printer.word_to_profile["world"] == "test1"
        assert printer.word_to_profile["test"] == "test2"

        # Check reverse mappings
        assert printer.normalized_to_original["hello"] == "Hello"
        assert printer.normalized_to_original["world"] == "WORLD"
        assert printer.normalized_to_original["test"] == "Test"

        # Original words should remain in profiles
        assert "Hello" in printer.profiles["test1"]["words"]
        assert "WORLD" in printer.profiles["test1"]["words"]
        assert "Test" in printer.profiles["test2"]["words"]


class TestWordTiming:
    """Test cases for word timing retrieval."""

    def test_get_word_timing_default(self):
        """Test getting timing for word not in any profile."""
        printer = PrintingPress(base_delay=0.1, delay_range=0.05)
        result = printer._get_word_timing("unknown_word", 0.1, 0.05)
        assert result == (0.1, 0.05)

    def test_get_word_timing_profile_word(self):
        """Test getting timing for word in a profile."""
        printer = PrintingPress()
        printer.create_profile("test", 0.2, 0.1, ["special", "two"])
        result = printer._get_word_timing("special", 0.05, 0.02)
        assert result == (0.2, 0.1)

    def test_get_word_timing_case_sensitive(self):
        """Test word timing with case-sensitivity."""
        printer = PrintingPress()
        printer.case_sensitive_setting = True
        printer.create_profile("test", 0.2, 0.1, ["Word"])

        # Exact match should find profile
        result1 = printer._get_word_timing("Word", 0.05, 0.02)
        assert result1 == (0.2, 0.1)

        # Different case should use fallback
        result2 = printer._get_word_timing("word", 0.05, 0.02)
        assert result2 == (0.05, 0.02)

    def test_get_word_timing_case_insensitive(self):
        """Test word timing without case-sensitivity."""
        printer = PrintingPress()
        printer.case_sensitive_setting = False
        printer.create_profile("test", 0.2, 0.1, ["Word"])

        # Both should find profile
        result1 = printer._get_word_timing("Word", 0.05, 0.02)
        assert result1 == (0.2, 0.1)
        result2 = printer._get_word_timing("word", 0.05, 0.02)
        assert result2 == (0.2, 0.1)


class TestTypeOut:
    """Test cases for the type_out method."""

    @patch("time.sleep")
    @patch("sys.stdout.write")
    @patch("sys.stdout.flush")
    def test_type_out_basic(self, mock_flush, mock_write, mock_sleep):
        """Test basic type_out functionality."""
        printer = PrintingPress(base_delay=0.1, delay_range=0.05)
        printer.type_out("Hi")

        # Should write each character
        expected_writes = [call("H"), call("i")]
        mock_write.assert_has_calls(expected_writes)

        # Should flush after each character
        assert mock_flush.call_count == 2

        # Should sleep after each character
        assert mock_sleep.call_count == 2

    @patch("sys.stdout.write")
    def test_type_out_with_spaces(self, mock_write):
        """Test type_out with spaces."""
        printer = PrintingPress()
        printer.type_out("Hi World")

        expected_writes = [
            call("H"),
            call("i"),
            call(" "),
            call("W"),
            call("o"),
            call("r"),
            call("l"),
            call("d"),
        ]
        mock_write.assert_has_calls(expected_writes)

    @patch("sys.stdout.write")
    def test_type_out_with_profile_word(self, mock_write):
        """Test type_out with word in timing profile."""
        printer = PrintingPress()
        printer.create_profile("test", 0.5, 0.2, ["special"])
        printer.type_out("special")

        # Should still write each character
        expected_writes = [
            call("s"),
            call("p"),
            call("e"),
            call("c"),
            call("i"),
            call("a"),
            call("l"),
        ]
        mock_write.assert_has_calls(expected_writes)

    @patch("sys.stdout.write")
    def test_type_out_with_override_timing(self, mock_write):
        """Test type_out with timing overrides."""
        printer = PrintingPress()
        printer.type_out("test", base_delay=0.2, delay_range=0.1)

        # Should still work normally
        expected_writes = [call("t"), call("e"), call("s"), call("t")]
        mock_write.assert_has_calls(expected_writes)

    def test_type_out_invalid_override_base_delay(self):
        """Test type_out with invalid override base_delay."""
        printer = PrintingPress()
        with pytest.raises(InvalidTimingError):
            printer.type_out("test", base_delay=-0.1)

    def test_type_out_invalid_override_delay_range(self):
        """Test type_out with invalid override delay_range."""
        printer = PrintingPress()
        with pytest.raises(InvalidTimingError):
            printer.type_out("test", delay_range=-0.1)

    @patch("time.sleep")
    @patch("sys.stdout.write")
    @patch("sys.stdout.flush")
    def test_type_out_empty_string(self, mock_flush, mock_write, mock_sleep):
        """Test type_out with empty string."""
        printer = PrintingPress()
        printer.type_out("")

        mock_write.assert_not_called()
        mock_flush.assert_not_called()
        mock_sleep.assert_not_called()

    @patch("sys.stdout.write")
    def test_type_out_whitespace_only(self, mock_write):
        """Test type_out with whitespace only."""
        printer = PrintingPress()
        printer.type_out("   ")

        expected_writes = [call(" "), call(" "), call(" ")]
        mock_write.assert_has_calls(expected_writes)

    @patch("sys.stdout.write")
    def test_type_out_ends_with_whitespace(self, mock_write):
        """Test type_out with text ending in whitespace."""
        printer = PrintingPress()
        printer.type_out("word ")

        expected_writes = [call("w"), call("o"), call("r"), call("d"), call(" ")]
        mock_write.assert_has_calls(expected_writes)

    @patch("sys.stdout.write")
    def test_type_out_multiple_words_with_profiles(self, mock_write):
        """Test type_out with multiple words, some in profiles."""
        printer = PrintingPress()
        printer.create_profile("special", 0.2, 0.1, ["important"])
        printer.type_out("This is important text")

        # Should write all characters
        text = "This is important text"
        expected_writes = [call(char) for char in text]
        mock_write.assert_has_calls(expected_writes)


class TestTimingConfiguration:
    """Test cases for timing configuration methods."""

    def test_set_timing_valid(self):
        """Test setting valid timing parameters."""
        printer = PrintingPress()
        printer.set_timing(0.2, 0.1)
        assert printer.base_delay == 0.2
        assert printer.delay_range == 0.1

    def test_set_timing_invalid_base_delay(self):
        """Test setting invalid base_delay."""
        printer = PrintingPress()
        with pytest.raises(InvalidTimingError):
            printer.set_timing(-0.1, 0.05)

    def test_set_timing_invalid_delay_range(self):
        """Test setting invalid delay_range."""
        printer = PrintingPress()
        with pytest.raises(InvalidTimingError):
            printer.set_timing(0.1, -0.05)

    @patch.object(PrintingPress, "type_out")
    def test_print_default(self, mock_type_out):
        """Test print_default method."""
        printer = PrintingPress()
        printer._print_default("test text")

        mock_type_out.assert_called_once_with(
            "test text",
            PrintingPress.DEFAULT_BASE_DELAY,
            PrintingPress.DEFAULT_DELAY_RANGE,
        )

    @patch.object(PrintingPress, "type_out")
    def test_print_emphasis(self, mock_type_out):
        """Test print_emphasis method."""
        printer = PrintingPress()
        printer._print_emphasis("important text")

        mock_type_out.assert_called_once_with(
            "important text",
            PrintingPress.EMPHASIS_BASE_DELAY,
            PrintingPress.EMPHASIS_DELAY_RANGE,
        )


class TestConstants:
    """Test cases for module and class constants."""

    def test_timing_min_value(self):
        """Test TIMING_MIN_VALUE module constant."""
        assert TIMING_MIN_VALUE == 0.0
        assert isinstance(TIMING_MIN_VALUE, float)

    def test_timing_max_value(self):
        """Test TIMING_MAX_VALUE module constant."""
        assert TIMING_MAX_VALUE == 10.0
        assert isinstance(TIMING_MAX_VALUE, float)

    def test_default_constants(self):
        """Test that default constants are properly defined."""
        assert hasattr(PrintingPress, "DEFAULT_BASE_DELAY")
        assert hasattr(PrintingPress, "DEFAULT_DELAY_RANGE")
        assert hasattr(PrintingPress, "EMPHASIS_BASE_DELAY")
        assert hasattr(PrintingPress, "EMPHASIS_DELAY_RANGE")

        assert isinstance(PrintingPress.DEFAULT_BASE_DELAY, float)
        assert isinstance(PrintingPress.DEFAULT_DELAY_RANGE, float)
        assert isinstance(PrintingPress.EMPHASIS_BASE_DELAY, float)
        assert isinstance(PrintingPress.EMPHASIS_DELAY_RANGE, float)


class TestProfileDataType:
    """Test cases for _ProfileData TypedDict."""

    def test_profile_data_structure(self):
        """Test that _ProfileData has correct structure."""
        # Create a valid profile data structure
        profile_data: _ProfileData = {
            "words": {"hello", "world"},
            "base_delay": 0.1,
            "delay_range": 0.05,
        }

        assert isinstance(profile_data["words"], set)
        assert isinstance(profile_data["base_delay"], float)
        assert isinstance(profile_data["delay_range"], float)


class TestMainFunction:
    """Test cases for the main function."""

    @patch.object(PrintingPress, "_print_default")
    @patch.object(PrintingPress, "_print_emphasis")
    def test_main_function(self, mock_print_emphasis, mock_print_default):
        """Test the _main function."""
        from src.typytypy.core import _main

        _main()

        # Should call print_default twice and print_emphasis once
        assert mock_print_default.call_count == 2
        assert mock_print_emphasis.call_count == 1

    @patch("src.typytypy.core.__name__", "__main__")
    @patch.object(PrintingPress, "_print_default")
    @patch.object(PrintingPress, "_print_emphasis")
    def test_init_function_main_block(self, mock_print_emphasis, mock_print_default):
        """Test the _init function executes _main when __name__ is __main__."""
        from src.typytypy.core import _init

        _init()

        # Should call print_default twice and print_emphasis once
        assert mock_print_default.call_count == 2
        assert mock_print_emphasis.call_count == 1


class TestComplexScenarios:
    """Test cases for complex scenarios and edge cases."""

    def test_multiple_profile_operations(self):
        """Test complex sequence of profile operations."""
        printer = PrintingPress()

        # Create multiple profiles
        printer.create_profile("fast", 0.01, 0.005, ["quick", "rapid"])
        printer.create_profile("slow", 0.1, 0.05, ["careful", "deliberate"])

        # Move word between profiles (auto-transfer)
        printer.add_words_to_profile("slow", ["quick"])

        assert "quick" in printer.profiles["slow"]["words"]
        assert "quick" not in printer.profiles["fast"]["words"]
        assert printer.word_to_profile["quick"] == "slow"

    def test_case_sensitivity_with_existing_profiles_safe_switch(self):
        """Test safely changing case-sensitivity with existing profiles."""
        printer = PrintingPress()
        printer.create_profile("test", 0.1, 0.05, ["Hello", "WORLD"])

        # This should be safe as there are no collisions
        printer.set_profile_case_sensitivity(False)

        # Check that lookups work with both cases
        timing1 = printer._get_word_timing("hello", 0.05, 0.02)
        timing2 = printer._get_word_timing("HELLO", 0.05, 0.02)
        timing3 = printer._get_word_timing("world", 0.05, 0.02)

        assert timing1 == (0.1, 0.05)
        assert timing2 == (0.1, 0.05)
        assert timing3 == (0.1, 0.05)

    def test_profile_deletion_with_word_cleanup(self):
        """Test that profile deletion properly cleans up word mappings."""
        printer = PrintingPress()
        printer.create_profile("to_delete", 0.1, 0.05, ["word1", "word2"])

        # Verify mappings exist
        assert "word1" in printer.word_to_profile
        assert "word2" in printer.word_to_profile
        assert "word1" in printer.normalized_to_original
        assert "word2" in printer.normalized_to_original

        # Delete profile
        printer.delete_profile("to_delete")

        # Verify cleanup
        assert "word1" not in printer.word_to_profile
        assert "word2" not in printer.word_to_profile
        assert "word1" not in printer.normalized_to_original
        assert "word2" not in printer.normalized_to_original

    @patch("random.uniform")
    @patch("time.sleep")
    def test_type_out_timing_calculation(self, mock_sleep, mock_random):
        """Test that type_out correctly calculates timing with random component."""
        mock_random.return_value = 0.02  # Fixed random value for testing

        printer = PrintingPress(base_delay=0.1, delay_range=0.05)
        printer.type_out("a")

        # Should sleep with base_delay + random value
        mock_sleep.assert_called_with(0.1 + 0.02)
        mock_random.assert_called_with(0, 0.05)

    def test_empty_profile_operations(self):
        """Test operations on empty profiles."""
        printer = PrintingPress()
        printer.create_profile("empty", 0.1, 0.05)

        # Remove from empty profile
        result = printer.remove_words_from_profile("empty", ["nonexistent"])
        assert result == 0

        # Get info from empty profile
        info = printer.get_profile_info("empty")
        assert info is not None
        assert info["word_count"] == 0
        assert info["words"] == []

    def test_case_sensitivity_switch_with_collision_details(self):
        """Test case-sensitivity switch error message details."""
        printer = PrintingPress()
        printer.case_sensitive_setting = True
        printer.create_profile("profile1", 0.1, 0.05, ["Apple"])
        printer.create_profile("profile2", 0.1, 0.05, ["apple", "APPLE"])

        with pytest.raises(ConfigurationError) as exc_info:
            printer.set_profile_case_sensitivity(False)

        error_message = str(exc_info.value)
        assert "Cannot switch to case-insensitive mode" in error_message
        assert "word collision(s) detected" in error_message
        assert "'apple'" in error_message  # The normalized conflicting word

    @patch("sys.stdout.write")
    def test_type_out_with_mixed_profile_and_non_profile_words(self, mock_write):
        """Test type_out with text containing both profile and non-profile words."""
        printer = PrintingPress()
        printer.create_profile("important", 0.2, 0.1, ["URGENT"])

        # Text with both profile word and regular words
        printer.type_out("This URGENT message")

        # Should process all characters
        expected_writes = []
        for char in "This URGENT message":
            expected_writes.append(call(char))

        mock_write.assert_has_calls(expected_writes)

    def test_word_timing_with_fallback_parameters(self):
        """Test word timing method with explicit fallback parameters."""
        printer = PrintingPress(base_delay=0.01, delay_range=0.005)

        # Test with different fallback parameters
        result = printer._get_word_timing("unknown", 0.1, 0.05)
        assert result == (0.1, 0.05)  # Should use fallback, not instance defaults

"""Core functionality for TypyTypy.

This module defines the 'PrintingPress' class, which implements the library's main
character-by-character text rendering engine. It provides configurable timing control,
word-level profiles, and case-sensitivity options, serving as the beating heart of
TypyTypy.

Classes:
    PrintingPress: Main character-by-character text printer class.

Examples:
    Basic usage:
        >>> import typytypy
        ...
        >>> printer = typytypy.PrintingPress()
        ...
        >>> printer.type_out("Hello, World!")

    With timing profiles:
        >>> printer.create_profile("highlight", 0.1, 0.05, "IMPORTANT")
        ...
        >>> printer.type_out("This is IMPORTANT information!")

Metadata:
    Author: KitscherEins,
    Version: 0.1.0,
    License: Apache-2.0
"""

import random
import sys
import time
from typing import TypedDict

from .exceptions import (
    ConfigurationError,
    InvalidTimingError,
    ProfileError,
)

# Constants for common validation ranges
TIMING_MIN_VALUE = 0.0
TIMING_MAX_VALUE = 10.0


class _ProfileData(TypedDict):
    """Type definition for timing profile data structure.

    Attributes:
        words (set[str]): Set of words that trigger custom timing.
        base_delay (float): Minimum delay per character, in seconds, for words in a
                            profile.
        delay_range (float): Random delay range, in seconds, for words in a profile.
    """

    words: set[str]
    base_delay: float
    delay_range: float


class _CaseSensitivityAnalysis(TypedDict):
    """Type definition for case-sensitivity switch analysis results.

    Attributes:
        current_mode (str): The current case-sensitivity mode in use.
        target_mode (str): The desired case-sensitivity mode to switch to.
        switch_safe (bool): Whether switching to the target mode is safe.
        collision_count (int): Total number of detected name collisions.
        collisions (dict[str, list[tuple[str, str]]]): Mapping of entities with name
                                                       collisions, where each list
                                                       contains tuples of conflicting
                                                       names.
        affected_profiles (set[str]): Set of profiles impacted by the collisions.
        recommendations (list[str]): List of recommended actions to resolve or avoid
                                     collisions.
    """

    current_mode: str
    target_mode: str
    switch_safe: bool
    collision_count: int
    collisions: dict[str, list[tuple[str, str]]]
    affected_profiles: set[str]
    recommendations: list[str]


class PrintingPress:
    """Character-by-character text printer engine with custom timing profile support.

    This class prints text to stdout character-by-character, simulating real-time
    typing. It supports configurable timing parameters and custom timing profiles that
    override default timings for specific words or phrases.

    Attributes:
        base_delay (float): Default minimum delay per character, in seconds.
        delay_range (float): Default random delay range, in seconds.
        profiles (dict[str, _ProfileData]): Mapping of profile names to profile data.
        word_to_profile (dict[str, str]): Mapping of normalized words to their assigned
                                          profile name.
        normalized_to_original (dict[str, str]): Mapping of normalized words to their
                                                 original form for case-sensitivity
                                                 restoration.
        case_sensitive_setting (bool): True if profile word matching is case-sensitive.

    Examples:
        Basic initialization:
            >>> printer = PrintingPress()
            ...
            >>> printer.type_out("Hello, World!")

        Custom timing:
            >>> printer = PrintingPress(base_delay=0.1, delay_range=0.2)
            ...
            >>> printer.type_out("Slow typing...")

        Timing profiles:
            >>> printer.create_profile("fast", 0.01, 0.005, "URGENT")
            ...
            >>> printer.type_out("This is URGENT!")
    """

    # Default timing constants for different use cases
    DEFAULT_BASE_DELAY = 0.015
    DEFAULT_DELAY_RANGE = 0.042
    EMPHASIS_BASE_DELAY = 0.0314
    EMPHASIS_DELAY_RANGE = 0.0985

    def __init__(
        self, base_delay: float | None = None, delay_range: float | None = None
    ) -> None:
        """Initialize a 'PrintingPress' instance with timing configuration (optional).

        Args:
            base_delay (float | None): Minimum delay per character, in seconds.
                                       Defaults to 'DEFAULT_BASE_DELAY' if None.
            delay_range (float | None): Random delay range, in seconds.
                                        Defaults to 'DEFAULT_DELAY_RANGE' if None.

        Raises:
            InvalidTimingError: If invalid timing values are provided.

        Examples:
            Default timing:
                >>> printer = PrintingPress()

            Custom timing:
                >>> printer = PrintingPress(base_delay=0.05, delay_range=0.02)
        """
        # Validate and set timing parameters
        if base_delay is not None:
            self._validate_timing(base_delay, "base_delay")
        if delay_range is not None:
            self._validate_timing(delay_range, "delay_range")

        self.base_delay = base_delay or self.DEFAULT_BASE_DELAY
        self.delay_range = delay_range or self.DEFAULT_DELAY_RANGE

        # Timing profiles management with precise typing
        self.profiles: dict[str, _ProfileData] = {}

        # Word-to-profile mapping for efficient lookup
        self.word_to_profile: dict[str, str] = {}

        # Reverse mapping for efficient auto-transfer
        self.normalized_to_original: dict[str, str] = {}

        # Configuration settings (default: sensitive)
        self.case_sensitive_setting = True

    def _validate_timing(self, value: float, param_name: str) -> None:
        """Validate a timing parameter value against configured limits.

        This method ensures that timing values fall within the globally defined
        minimum and maximum limits.

        For INTERNAL USE.

        Args:
            value (float): Timing value to validate, in seconds.
            param_name (str): Name of the parameter being validated (used in error
                              messages).

        Raises:
            InvalidTimingError: If the value is less than 'TIMING_MIN_VALUE' or greater
                                than 'TIMING_MAX_VALUE'.
        """
        if value < TIMING_MIN_VALUE:
            raise InvalidTimingError(
                f"{param_name} must be non-negative",
                parameter_name=param_name,
                parameter_value=value,
                valid_range=(TIMING_MIN_VALUE, TIMING_MAX_VALUE),
            )
        if value > TIMING_MAX_VALUE:
            raise InvalidTimingError(
                f"{param_name} exceeds reasonable maximum ({TIMING_MAX_VALUE}s)",
                parameter_name=param_name,
                parameter_value=value,
                valid_range=(TIMING_MIN_VALUE, TIMING_MAX_VALUE),
            )

    def _normalize_word(self, word: str) -> str:
        """Normalize a word for internal profile lookups.

        Converts the word to lowercase if the printer's case-sensitivity setting is
        set to False; otherwise leaves it unchanged. This ensures consistent key
        matching in timing profile mappings.

        For INTERNAL USE.

        Args:
            word (str): The word to normalize.

        Returns:
            str: The normalized word (lowercase if case-insensitive, unchanged if
                 case-sensitive).
        """
        return word if self.case_sensitive_setting else word.lower()

    def create_profile(
        self,
        profile_name: str,
        base_delay: float,
        delay_range: float,
        words: str | list[str] | None = None,
    ) -> bool:
        """Create a new custom timing profile with the specified parameters.

        A custom timing profile defines a base_delay and delay_range that override the
        printer's defaults for a specific set of words. If initial words are provided,
        they are added to the profile immediately after creation.

        Args:
            profile_name (str): Unique name for the custom timing profile. If a profile
                                with the same name already exists, creation fails.
            base_delay (float): Minimum delay per character, in seconds, for words in
                                this profile.
            delay_range (float): Random delay range, in seconds, for words in
                                 this profile.
            words (str | list[str] | None): Initial word(s) to add to the profile
                                            (optional). Can be a single word string,
                                            list of words, or None.

        Returns:
            bool: True if the profile was created successfully, False if a profile with
                  the given name already exists.

        Raises:
            InvalidTimingError: If invalid timing values are provided.

        Examples:
            Create empty profile:
                >>> printer.create_profile("emotions", 0.08, 0.12)
                True

            Create profile with initial word:
                >>> printer.create_profile("calm", 0.1, 0.015, "holistic")
                True

            Create profile with multiple initial words:
                >>> printer.create_profile("fast", 0.01, 0.005, ["CLEAR", "UNDERSTAND"])
                True
        """
        # Validate timing parameters
        self._validate_timing(base_delay, "base_delay")
        self._validate_timing(delay_range, "delay_range")

        if profile_name in self.profiles:
            return False

        self.profiles[profile_name] = {
            "base_delay": base_delay,
            "delay_range": delay_range,
            "words": set(),
        }

        # Add initial words if provided
        if words is not None:
            self.add_words_to_profile(profile_name, words)

        return True

    def _modify_profile(
        self, profile_name: str, words: str | list[str], action: str
    ) -> int:
        """Modify the word list of a custom timing profile.

        Depending on the specified action, this method adds words to or removes words
        from the given profile. When adding, it validates against case-sensitive or
        case-insensitive duplicates based on the active setting, and automatically
        transfers a word from its existing profile if needed. When removing, it cleans
        up associated lookup mappings.

        For INTERNAL USE.

        Args:
            profile_name (str): Name of the custom timing profile to modify.
            words (str | list[str]): Word(s) to process (single string or list).
            action (str): Either "add" or "remove".

        Returns:
            int: The number of words successfully processed.

        Raises:
            ProfileError: If the profile does not exist, if the action is invalid, or if
                          adding words would violate duplicate rules under the current
                          case-sensitivity configuration.
        """
        if profile_name not in self.profiles:
            raise ProfileError(
                f"Profile '{profile_name}' does not exist",
                profile_name=profile_name,
                operation=action,
            )

        if action not in ["add", "remove"]:
            raise ProfileError(
                "Action must be 'add' or 'remove'",
                profile_name=profile_name,
                operation=action,
            )

        # Convert to list but keep original forms
        if isinstance(words, str):
            word_list = [words]
        else:
            word_list = words

        # Check for duplicates within input
        if action == "add":
            duplicates = self._detect_input_duplicates(word_list)
            if duplicates:
                duplicate_type = (
                    "case-sensitive"
                    if self.case_sensitive_setting
                    else "case-insensitive"
                )
                raise ProfileError(
                    f"Input contains {duplicate_type} duplicates: {duplicates}",
                    profile_name=profile_name,
                    operation=action,
                )

        processed_count = 0

        if action == "add":
            for original_word in word_list:
                normalized_word = self._normalize_word(original_word)

                # Track if auto-transfer will happen (for validation)
                auto_transfer_occurs = normalized_word in self.word_to_profile

                # Auto-transfer: remove from previous profile if exists
                if auto_transfer_occurs:
                    previous_profile = self.word_to_profile[normalized_word]
                    old_original_word = self.normalized_to_original[normalized_word]

                    # Remove from previous profile
                    self.profiles[previous_profile]["words"].discard(old_original_word)

                # Add to new profile with both mappings
                self.profiles[profile_name]["words"].add(
                    original_word  # Store original
                )
                self.word_to_profile[normalized_word] = (
                    profile_name  # Normalized → profile
                )
                self.normalized_to_original[normalized_word] = (
                    original_word  # Normalized → original
                )

                # Validate auto-transfer if it occurred
                if auto_transfer_occurs:
                    validation_success, validation_message = (
                        self._validate_auto_transfer(original_word, profile_name)
                    )
                    if not validation_success:
                        raise ProfileError(
                            (
                                f"Auto-transfer validation failed for word "
                                f"'{original_word}': {validation_message}"
                            ),
                            profile_name=profile_name,
                            operation=action,
                        )

                processed_count += 1

        else:  # remove
            for original_word in word_list:
                normalized_word = self._normalize_word(original_word)

                if original_word in self.profiles[profile_name]["words"]:
                    # Remove from profile and clean up mappings
                    self.profiles[profile_name]["words"].remove(original_word)
                    if normalized_word in self.word_to_profile:
                        del self.word_to_profile[normalized_word]
                    if normalized_word in self.normalized_to_original:
                        del self.normalized_to_original[normalized_word]
                    processed_count += 1

        return processed_count

    def _detect_input_duplicates(self, word_list: list[str]) -> list[str]:
        """Detect duplicate words in a given list according to case-sensitivity setting.

        This method checks for duplicates in the input list using the instance's
        'case_sensitive_setting'. In case-sensitive mode, duplicates must match exactly.
        In case-insensitive mode, duplicates are detected by their lowercase normalized
        form.

        For INTERNAL USE.

        Args:
            word_list (list[str]): List of original words strings to check for
                                   duplicates.

        Returns:
            list[str]: A list of duplicates found. In case-sensitive mode, the
                       duplicates are returned in their original form. In
                       case-insensitive mode, duplicates are returned in normalized
                       (lowercase) form.
        """
        seen_normalized = set()
        seen_original = set()
        duplicates = []

        for original_word in word_list:
            normalized_word = self._normalize_word(original_word)

            if self.case_sensitive_setting:
                # Case-sensitive: check for exact original duplicates
                if original_word in seen_original:
                    if original_word not in duplicates:
                        duplicates.append(original_word)
                else:
                    seen_original.add(original_word)
            else:
                # Case-insensitive: check for normalized duplicates
                if normalized_word in seen_normalized:
                    if normalized_word not in duplicates:
                        duplicates.append(normalized_word)
                else:
                    seen_normalized.add(normalized_word)

        return duplicates

    def _validate_auto_transfer(
        self, original_word: str, target_profile: str
    ) -> tuple[bool, str]:
        """Verify that an auto-transfer operation for a word completed successfully.

        This method, used after adding a word that may have been moved automatically
        from a different profile, checks that:

            1. The original word exists in the target profile.
            2. The word's normalized form (case-lowered if case-insensitive) correctly
               maps to the target profile in 'word_to_profile'.
            3. The original word does not remain in any other profile's word set.

        For INTERNAL USE.

        Args:
            original_word (str): The word in its original form that was added.
            target_profile (str): Name of the profile the word should now be in.

        Returns:
            tuple[bool, str]: A '(success, error_message)' tuple where:
                              - 'success' is True if all the validation checks passed,
                                False otherwise
                              - 'error_message' is a description of the first validation
                                failure encountered, or a success confirmation string if
                                valid.
        """
        normalized_word = self._normalize_word(original_word)

        # Check if word is properly mapped to target profile
        if normalized_word not in self.word_to_profile:
            return (
                False,
                (
                    f"Normalized word '{normalized_word}' not found "
                    "in word_to_profile mapping"
                ),
            )

        if self.word_to_profile[normalized_word] != target_profile:
            actual_profile = self.word_to_profile[normalized_word]
            return (
                False,
                f"Word mapped to '{actual_profile}' instead of '{target_profile}'",
            )

        # Check if original word exists in target profile
        if original_word not in self.profiles[target_profile]["words"]:
            return (
                False,
                (
                    f"Original word '{original_word}' not found in "
                    f"target profile '{target_profile}'"
                ),
            )

        # Check that word doesn't exist in any other profile
        for profile_name, profile_data in self.profiles.items():
            if (
                profile_name != target_profile
                and original_word in profile_data["words"]
            ):
                return (
                    False,
                    (
                        f"Word '{original_word}' still exists in old profile "
                        f"'{profile_name}'"
                    ),
                )

        return True, "Auto-transfer validation successful"

    def add_words_to_profile(self, profile_name: str, words: str | list[str]) -> int:
        """Add word(s) to an existing custom timing profile.

        Words are validated according to the active case-sensitivity setting
        (default=True), and duplicates (based on those rules) are not allowed. If a word
        already exists in another profile, it will be automatically transferred to the
        target profile.

        Args:
            profile_name (str): Name of the existing custom timing profile to add words
                                to.
            words (str | list[str]): Word(s) to add (single string or list). Matching is
                                     case-sensitive or case-insensitive based on the
                                     instance's case-sensitivity setting.

        Returns:
            int: The number of words successfully added to the profile.

        Raises:
            ProfileError: If the profile does not exist or if adding the words would
                          violate duplicate rules under the current case-sensitivity
                          setting.

        Examples:
            Add a single word:
                >>> count = printer.add_words_to_profile("emotions", "happy")
                >>> print(count)  # 1

            Add multiple words:
                >>> count = printer.add_words_to_profile("emotions", ["happy", "sad"])
                >>> print(count)  # 2
        """
        return self._modify_profile(profile_name, words, "add")

    def remove_words_from_profile(
        self, profile_name: str, words: str | list[str]
    ) -> int:
        """Remove word(s) from an existing custom timing profile.

        Any specified words that are found in the target profile are removed, and their
        entries are cleaned from the lookup mappings. Words that are not present in the
        profile are ignored.

        Args:
            profile_name (str): Name of the existing custom timing profile to remove
                                words from.
            words (str | list[str]): Word(s) to remove (single string or list). Matching
                                     is case-sensitive or case-insensitive based on the
                                     instance's case-sensitivity setting.

        Returns:
            int: The number of words successfully removed from the profile.

        Raises:
            ProfileError: If the profile does not exist.

        Examples:
            Remove a single word:
                >>> count = printer.remove_words_from_profile("emotions", "guilty")
                >>> print(count)  # 1

            Remove multiple words:
                >>> count = printer.remove_words_from_profile("emotions",
                ...                                           ["angry", "guilty"])
                >>> print(count)  # 2 if both existed
        """
        return self._modify_profile(profile_name, words, "remove")

    def delete_profile(self, profile_name: str) -> bool:
        """Delete an entire custom timing profile and remove all associated mappings.

        Permanently removes the specified profile from the printer instance. It also
        cleans up all associated words from the 'word_to_profile' and
        'normalized_to_original' lookup mappings using the current case-sensitivity
        rules.

        Args:
            profile_name (str): Name of the custom timing profile to delete.

        Returns:
            bool: True if the profile existed and was deleted successfully, False if no
                  such profile exists.

        Examples:
            >>> success = printer.delete_profile("profile_omega")
            >>> print(success)  # True if profile existed, False otherwise
        """
        if profile_name not in self.profiles:
            return False

        # Clean up both mappings using normalized keys
        original_words_to_remove = list(self.profiles[profile_name]["words"])
        for original_word in original_words_to_remove:
            normalized_word = self._normalize_word(original_word)

            # Remove from both mappings using normalized key
            if normalized_word in self.word_to_profile:
                del self.word_to_profile[normalized_word]
            if normalized_word in self.normalized_to_original:
                del self.normalized_to_original[normalized_word]

        # Delete the profile
        del self.profiles[profile_name]
        return True

    def list_profiles(self) -> list[str]:
        """Return the names of all custom timing profiles in this printer instance.

        Profiles are listed in the order they were added to the instance (insertion
        order). Result reflects profiles stored in memory for the current instance.

        Returns:
            list[str]: A list of custom timing profile names, in insertion order.

        Examples:
            >>> profiles = printer.list_profiles()
            >>> print(profiles)  # ['emotions', 'technical', 'emphasis']
        """
        return list(self.profiles.keys())

    def get_profile_info(
        self, profile_name: str
    ) -> dict[str, float | int | list[str]] | None:
        """Return detailed information about a custom timing profile.

        If the profile exists, returns its configuration and current words.
        If no matching profile is found, returns None.

        Args:
            profile_name (str): Name of the custom timing profile.

        Returns:
            dict[str, float | int | list[str]] | None:
                A dictionary containing the following keys, or None if the profile does
                not exist:

                - base_delay (float): Minimum delay per character, in seconds, for
                                      words in this profile.
                - delay_range (float): Random delay range, in seconds, for words in this
                                       profile.
                - word_count (int): Number of words currently assigned to the profile.
                - words (list[str]): All words in the profile, in their original form.

        Examples:
            Retrieve and inspect a profile:
                >>> info = printer.get_profile_info("emotions")
                >>> print(info)  # Full profile record
                >>> print(info['word_count'])  # Number of words in profile
        """
        if profile_name not in self.profiles:
            return None

        profile_data = self.profiles[profile_name]

        # Create a new dict
        return {
            "base_delay": profile_data["base_delay"],
            "delay_range": profile_data["delay_range"],
            "word_count": len(profile_data["words"]),
            "words": list(profile_data["words"]),  # Convert set to list for readability
        }

    def update_profile_timing(
        self, profile_name: str, base_delay: float, delay_range: float
    ) -> bool:
        """Update the timing parameters for an existing custom timing profile.

        Replaces the profile's current 'base_delay' and 'delay_range' values with the
        specified ones, after validating that both are within the allowed limits.

        Args:
            profile_name (str): Name of the custom timing profile to update.
            base_delay (float): New minimum delay per character, in seconds.
            delay_range (float): New random delay range, in seconds.

        Returns:
            bool: True if the profile exists and was updated successfully, False if no
                  profile with the given name exists.

        Raises:
            InvalidTimingError: If invalid timing values are provided.

        Examples:
            Update an existing profile's timings:
                >>> success = printer.update_profile_timing("emotions", 0.1, 0.05)
                >>> print(success)  # True if profile exists
        """
        if profile_name not in self.profiles:
            return False

        # Validate timing parameters
        self._validate_timing(base_delay, "base_delay")
        self._validate_timing(delay_range, "delay_range")

        self.profiles[profile_name]["base_delay"] = base_delay
        self.profiles[profile_name]["delay_range"] = delay_range
        return True

    def set_profile_case_sensitivity(self, sensitive: bool) -> None:
        """Configure the case-sensitivity setting for profile word matching.

        Enables switching the instance's word matching mode between case-sensitive and
        case-insensitive. Before applying a change, it analyzes all existing profiles to
        detect whether the new mode would cause conflicting normalized word mappings
        (e.g., "Apple" and "apple" would collide in case-insensitive mode).

        If a switch is deemed safe, all internal lookup mappings are rebuilt to match
        the new case-sensitivity rules. If the target mode is the same as the current
        mode, no changes are made.

        Args:
            sensitive (bool): True to enable case-sensitive matching, False to enable
                              case-insensitive matching.

        Raises:
            ConfigurationError: If 'sensitive' is not a boolean, or if switching to the
                                new mode would cause collisions in normalized word
                                mappings.

        Examples:
            Safe switch to case-insensitive mode:
                >>> printer.set_profile_case_sensitivity(False)  # No conflicts

            Unsafe switch with conflicts:
                >>> printer.set_profile_case_sensitivity(False)
                Traceback (most recent call last):
                    ...
                ConfigurationError: Cannot switch to case-insensitive mode: 1 word
                collision(s) detected...
        """
        if not isinstance(sensitive, bool):
            raise ConfigurationError(
                "Case-sensitivity setting must be a boolean value",
                setting_name="case_sensitive",
                setting_value=sensitive,
                expected_type=bool,
            )

        if self.case_sensitive_setting == sensitive:
            # No change needed
            return

        # Analyze the proposed switch
        analysis = self._analyze_case_sensitivity_switch(sensitive)

        if not analysis["switch_safe"]:
            # Build detailed error message
            collision_details = []
            for normalized_word, word_profile_pairs in analysis["collisions"].items():
                pairs_str = ", ".join(
                    [f"'{word}' (in {profile})" for word, profile in word_profile_pairs]
                )
                collision_details.append(f"'{normalized_word}' ← {pairs_str}")

            error_message = (
                "Cannot switch to case-insensitive mode: "
                f"{analysis['collision_count']} "
                f"word collision(s) detected. The following words would create "
                f"conflicting mappings: {'; '.join(collision_details)}."
                f"\nPlease resolve these conflicts by removing or renaming words "
                f"before switching."
            )

            raise ConfigurationError(
                error_message,
                setting_name="case_sensitive",
                setting_value=sensitive,
                expected_type=bool,
            )

        # Safe to switch - perform the switch by rebuilding mappings correctly
        self.case_sensitive_setting = sensitive
        self._rebuild_mappings_after_sensitivity_change()

    def _analyze_case_sensitivity_switch(
        self, target_sensitivity: bool
    ) -> _CaseSensitivityAnalysis:
        """Analyze the impact of changing the case-sensitivity mode.

        This method simulates switching the instance's case-sensitivity setting to the
        specified target mode without actually applying it. It checks for word
        collisions that would occur in the new mode.

        If switching from case-sensitive to case-insensitive, this method groups words
        by their lowercase form to detect collisions (e.g., "Apple" and "apple" would
        conflict). If collisions are found, the report marks the switch as unsafe and
        lists affected words and profiles, for taking action.

        For INTERNAL USE.

        Args:
            target_sensitivity (bool): The proposed case-sensitivity mode. True for
                                       case-sensitive, False for case-insensitive.

        Returns:
            _CaseSensitivityAnalysis: TypedDict structured analysis results including
                                      collision details and recommendations.
        """
        current_sensitivity = self.case_sensitive_setting

        analysis: _CaseSensitivityAnalysis = {
            "current_mode": (
                "case-sensitive" if current_sensitivity else "case-insensitive"
            ),
            "target_mode": (
                "case-sensitive" if target_sensitivity else "case-insensitive"
            ),
            "switch_safe": True,
            "collision_count": 0,
            "collisions": {},
            "affected_profiles": set(),
            "recommendations": [],
        }

        if current_sensitivity and not target_sensitivity:
            # Switching from case-sensitive to case-insensitive - check for collisions
            collisions = self._detect_case_sensitivity_collisions()

            if collisions:
                analysis["switch_safe"] = False
                analysis["collision_count"] = len(collisions)
                analysis["collisions"] = collisions

                # Collect affected profiles
                for word_profile_pairs in collisions.values():
                    for _, profile_name in word_profile_pairs:
                        analysis["affected_profiles"].add(profile_name)

                analysis["recommendations"] = [
                    "Remove or rename conflicting words before switching to "
                    "case-insensitive mode",
                    f"Found {len(collisions)} normalized words that would create "
                    "conflicts",
                    "Affected profiles: "
                    f"{', '.join(sorted(analysis['affected_profiles']))}",
                ]

        elif not current_sensitivity and target_sensitivity:
            # Switching from case-insensitive to case-sensitive - should be safe
            analysis["recommendations"] = [
                "Switch should be safe - no conflicts expected "
                "when going to case-sensitive mode"
            ]

        else:
            # No actual switch needed
            analysis["recommendations"] = [
                f"Already in {analysis['current_mode']} mode - no switch needed"
            ]

        return analysis

    def _detect_case_sensitivity_collisions(self) -> dict[str, list[tuple[str, str]]]:
        """Identify word collisions that would occur in case-insensitive mode.

        This method scans all profiles to detect words that would map to the same
        normalized lowercase form if the printer were switched from case-sensitive to
        case-insensitive mode. If the instance is already in case-insensitive mode, or
        if no such conflicts exist, an empty dictionary is returned.

        For INTERNAL USE.

        Returns:
            dict[str, list[tuple[str, str]]]: A mapping of each conflicting normalized
                                              lowercase word to the list of
                                              (original_word, profile_name) tuples that
                                              would collide in case-insensitive mode.
                                              Empty if no collisions.
        """
        if not self.case_sensitive_setting:
            # Already case-insensitive, no collisions possible
            return {}

        # Group all original words by their case-insensitive normalized form
        normalized_groups: dict[str, list[tuple[str, str]]] = {}

        for profile_name, profile_data in self.profiles.items():
            for original_word in profile_data["words"]:
                # Get what the normalized form would be in case-insensitive mode
                case_insensitive_normalized = original_word.lower()

                if case_insensitive_normalized not in normalized_groups:
                    normalized_groups[case_insensitive_normalized] = []

                normalized_groups[case_insensitive_normalized].append(
                    (original_word, profile_name)
                )

        # Filter to only return groups with collisions (more than one entry)
        collisions = {
            normalized: word_profile_pairs
            for normalized, word_profile_pairs in normalized_groups.items()
            if len(word_profile_pairs) > 1
        }

        return collisions

    def _rebuild_mappings_after_sensitivity_change(self) -> None:
        """Rebuild internal word lookup mappings after a case-sensitivity change.

        This method clears and repopulates the 'word_to_profile' and
        'normalized_to_original' dictionaries for all existing profiles to match the new
        case-sensitivity setting. The original words within each profile's word list set
        are preserved.

        This method is only called after a successful case-sensitivity switch
        validation, so collisions are not possible during the rebuild. The operation is
        idempotent and does not alter any profile word sets.

        For INTERNAL USE.

        Returns:
            None.
        """
        # Clear lookup mappings but preserve original words in profiles
        self.word_to_profile.clear()
        self.normalized_to_original.clear()

        # Rebuild mappings with new case-sensitivity
        for profile_name, profile_data in self.profiles.items():
            for original_word in profile_data["words"]:
                normalized_word = self._normalize_word(original_word)

                # These should not conflict - already validated before switching
                self.word_to_profile[normalized_word] = profile_name
                self.normalized_to_original[normalized_word] = original_word

    def _get_word_timing(
        self, word: str, fallback_base_delay: float, fallback_delay_range: float
    ) -> tuple[float, float]:
        """Retrieve the timing parameters for a given word, checking timing profiles.

        This method determines the 'base_delay' and 'delay_range' values to use when
        printing the specified word. The lookup process is:

            1. Normalize the word according to the current case-sensitivity setting.
            2. If the normalized word exists in a timing profile, return that profile's
               configured timing values.
            3. If the word is not in any profile, return the provided fallback values
               (which are typically either override values passed to the calling method
               or the instance's default timings).

        For INTERNAL USE.

        Args:
            word (str): The word to retrieve timing for.
            fallback_base_delay (float | None): Delay, in seconds, to use if the word is
                                                not in a profile. Should already be
                                                resolved to either an override or the
                                                instance default by the caller.
            fallback_delay_range (float | None): Delay range, in seconds, to
                                                 use if the word is not in a profile.
                                                 Should already be resolved to either an
                                                 override or the instance default by the
                                                 caller.

        Returns:
            tuple[float, float]: A '(base_delay, delay_range)' pair, in seconds, to
                                 apply when printing the word.
        """
        normalized_word = self._normalize_word(word)

        if normalized_word in self.word_to_profile:
            # Word is in a profile - use profile timing
            profile_name = self.word_to_profile[normalized_word]
            profile_info = self.profiles[profile_name]
            return (profile_info["base_delay"], profile_info["delay_range"])

        # Word not in profile - use instance fallback timing
        base_delay = fallback_base_delay
        delay_range = fallback_delay_range

        return (base_delay, delay_range)

    def type_out(
        self,
        text: str,
        base_delay: float | None = None,
        delay_range: float | None = None,
    ) -> None:
        """Print text to stdout one character at a time, simulating real-time typing.

        Renders the given text in real time, inserting calculated delays between printed
        characters. Words in custom timing profiles use their configured timing, while
        other words and whitespace use the provided or the instance's default timing
        parameters. Stdout is flushed after printing each character for immediate
        display.

        All original formatting (spacing, punctuation, and line breaks) is preserved.

        Args:
            text (str): The text to print.
            base_delay (float | None): Override (optional) for the instance minimum
                                       delay per character, in seconds, for non-profile
                                       words.
            delay_range (float | None): Override (optional) for the instance random
                                        delay range, in seconds, for non-profile words.

        Returns:
            None.

        Raises:
            InvalidTimingError: If invalid timing values are provided.

        Examples:
            Basic usage:
                >>> printer.type_out("Hello, World!")

            With per-call timing overrides:
                >>> printer.type_out("Fast message",
                                     base_delay=0.01, delay_range=0.005)

            With timing profiles:
                >>> printer.create_profile("emphasis", 0.1, 0.05, "IMPORTANT")
                ...
                >>> printer.type_out("This is IMPORTANT information!")
        """
        # Validate override parameters if provided
        if base_delay is not None:
            self._validate_timing(base_delay, "base_delay")
        if delay_range is not None:
            self._validate_timing(delay_range, "delay_range")

        # Fallback timing for non-profile words and whitespace
        fallback_base_delay = base_delay if base_delay is not None else self.base_delay
        fallback_delay_range = (
            delay_range if delay_range is not None else self.delay_range
        )

        current_word = ""

        for char in text:
            if char.isspace():
                # Process accumulated word if any
                if current_word:
                    word_base_delay, word_delay_range = self._get_word_timing(
                        current_word, fallback_base_delay, fallback_delay_range
                    )

                    # Print the accumulated word per its timing
                    for word_char in current_word:
                        sys.stdout.write(word_char)
                        sys.stdout.flush()
                        time.sleep(
                            word_base_delay + random.uniform(0, word_delay_range)
                        )

                    current_word = ""  # Reset word accumulator

                # Print whitespace character per fallback timing
                sys.stdout.write(char)
                sys.stdout.flush()
                time.sleep(
                    fallback_base_delay + random.uniform(0, fallback_delay_range)
                )
            else:
                # Accumulate non-whitespace characters into current word
                current_word += char

        # Handle final word if text doesn't end with whitespace
        if current_word:
            word_base_delay, word_delay_range = self._get_word_timing(
                current_word, fallback_base_delay, fallback_delay_range
            )

            for word_char in current_word:
                sys.stdout.write(word_char)
                sys.stdout.flush()
                time.sleep(word_base_delay + random.uniform(0, word_delay_range))

    def set_timing(self, base_delay: float, delay_range: float) -> None:
        """Update the default timing parameters for this printer instance.

        Permanently changes the instance's base delay and delay range values for all
        subsequent calls to 'type_out()', unless per-call overrides are provided. Both
        values are validated against the globally defined minimum and maximum timing
        limits.

        Args:
            base_delay (float): New minimum delay per character, in seconds.
            delay_range (float): New random delay range, in seconds.

        Raises:
            InvalidTimingError: If invalid timing values are provided.

        Examples:
            Set slower default typing speed:
                >>> printer_one.set_timing(0.05, 0.02)

            Set faster default typing speed:
                >>> printer_two.set_timing(0.005, 0.01)
        """
        self._validate_timing(base_delay, "base_delay")
        self._validate_timing(delay_range, "delay_range")

        self.base_delay = base_delay
        self.delay_range = delay_range

    def _print_default(self, text: str) -> None:
        """Print text using the class's default timing preset.

        This method calls 'type_out()' with the predefined 'DEFAULT_BASE_DELAY' and
        'DEFAULT_DELAY_RANGE' values for a standard typing speed. It behaves identically
        to calling 'type_out()' directly with those constants.

        Args:
            text (str): The text to print.

        Examples:
            >>> printer.print_default("Normal speed text")
        """
        self.type_out(text, self.DEFAULT_BASE_DELAY, self.DEFAULT_DELAY_RANGE)

    def _print_emphasis(self, text: str) -> None:
        """Print text using the class's emphasis timing preset.

        This method calls 'type_out()' with the predefined 'EMPHASIS_BASE_DELAY' and
        'EMPHASIS_DELAY_RANGE' values for a slower, dramatic effect typing speed. It
        behaves identically to calling 'type_out()' directly with those constants.

        Args:
            text (str): The text to print.

        Examples:
            >>> printer.print_emphasis("This text has dramatic timing...")
        """
        self.type_out(text, self.EMPHASIS_BASE_DELAY, self.EMPHASIS_DELAY_RANGE)


def _main() -> None:
    """Run a live demonstration of the TypyTypy library.

    This internal function creates a 'PrintingPress' instance and prints the module's
    Kitschbotschaft using different timing presets:

        1. Default timing preset ('_print_default')
        2. Emphasis timing preset ('_print_emphasis')
    """
    # Initialize printer with default settings
    printer = PrintingPress()

    # Define demonstration texts
    text_before = """\nThank you for using KitschCode's TypyTypy.
"""

    quote = """\n    „Hear me! For I am such and such a person.
     Above all, do not mistake me for someone else."  
        — Friedrich Wilhelm Nietzsche
"""

    text_after = """\nBleiben Sie inspiriert.

\nIn gratitude,  
KitscherEins\n
"""

    # Demonstrate different printing modes
    printer._print_default(text_before)
    printer._print_emphasis(quote)  # Use emphasis timing
    printer._print_default(text_after)


# Run the demo if this file is executed as a script
def _init() -> None:
    """Initialize when executed as main module."""
    if __name__ == "__main__":
        _main()


_init()

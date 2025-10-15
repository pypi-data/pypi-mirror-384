# Usage Guide

## Basic Usage

The simplest way to use TypyTypy is with the module-level function:

```python
import typytypy

# Basic typewriter effect
typytypy.type_out("Hello, World!")

# ... with custom timing
typytypy.type_out("How are we doing today?",
                  base_delay=0.25, delay_range=0.5)
```

## Using "Character Personality" Presets

Create printers with predefined "character personality" styles:

```python
import typytypy

# Discover available presets
available_presets = typytypy.get_available_presets()
print(available_presets)

# Instantiate desired preset printer(s)
nervous = typytypy.use_preset("nervous")
confident = typytypy.use_preset("confident")

# Use instantiated preset printer(s)
nervous.type_out("Um, hello there...")
confident.type_out("Good morning, team!")
```

```{toctree}
---
maxdepth: 1
caption: Resources:
---

presets
```

## Advanced: Full Instance Management

For maximum control, use the {py:class}`PrintingPress <typytypy.core.PrintingPress>` class directly:

```python
import typytypy

# Create printer instance
printer = typytypy.PrintingPress()

# Adjust printer instance timing defaults
printer.set_timing(0.03, 0.02)

# Configure the instance's case-sensitivity setting for profile word matching
printer.set_profile_case_sensitivity(False)

# Create a custom timing profile for specific words
printer.create_profile("highlight", 0.1, 0.05, "IMPORTANT")

# Print with automatic profile-based timing
printer.type_out("This is IMPORTANT information!")

# Manage profile words
printer.add_words_to_profile("highlight", ["now", "soon", "URGENT"])
printer.remove_words_to_profile("highlight", ["soon", "IMPORTANT"])

# List all custom timing profiles
custom_timing_profiles = printer.list_profiles()
print(custom_timing_profiles)

# Obtain detailed information about a profile
detailed_profile_info = printer.get_profile_info("highlight")
print(detailed_profile_info)

# Update a profile's timings
printer.update_profile_timing("highlight", 0.2, 0.1)

# Delete a custom timing profile
printer.delete_profile("highlight")
```

`````{admonition} A Little Spark (for the curious soul)
:class: seealso dropdown

````{tab-set}
:sync-group: OS

```{tab-item} Linux/macOS
:sync: unix

Run this command in your terminal:

    python3 -m typytypy.core

*It is (probably) safe, I promise.*
```

```{tab-item} Windows
:sync: microsoft

Run this command in your terminal:

    python -m typytypy.core

*It is (probably) safe, I promise.*
```

````

`````

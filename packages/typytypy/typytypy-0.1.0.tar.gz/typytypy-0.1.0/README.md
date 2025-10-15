<img src="assets/images/logo/typytypy-logo-full.svg" alt="TypyTypy logo" role="img" style="display:block; margin:0 auto;"/>

# TypyTypy *(typytypy)*

*— A Bespoke Character-by-Character Text Printer.*

> *[click-clack-clack...]*

A utility Python library which provides for a realistic, "real-time typing" simulation with highly configurable implementations. It features a flexible API for both simple and advanced use, quick-use "character personality" presets, and granular timing control for creating custom text presentations with authentic temporal dynamics.

*Born of the [KitschCode](https://github.com/VDundDB/KitschCode-py) philosophy of applying meticulous craftsmanship to humble functionality.*

> [!NOTE]
> *TypyTypy* is currently still in **BETA** release (but hopefully that changes soon). Notwithstanding, *TypyTypy* has a comprehensive test suite (100% statement and branch coverage with [pytest](https://github.com/pytest-dev/pytest)), is [Ruff](https://github.com/astral-sh/ruff)-linted, [Black](https://github.com/psf/black)-formatted, and [mypy](https://github.com/python/mypy) type-checked.

<div align="center">

[![PyPI - Version](https://img.shields.io/pypi/v/typytypy.svg)](https://pypi.org/project/typytypy)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/typytypy.svg?logo=python&logoColor=gold)](https://devguide.python.org/versions)
[![GitHub License](https://img.shields.io/github/license/VDundDB/typytypy-py?color=%23bc292b)](https://opensource.org/licenses/Apache-2.0)
[![PyPI - Status](https://img.shields.io/pypi/status/typytypy)](https://pypi.org/project/typytypy)

![PyPI - Implementation](https://img.shields.io/pypi/implementation/typytypy)
![PyPI - Types](https://img.shields.io/pypi/types/typytypy)
[![Docs](https://img.shields.io/badge/docs-online-success)](https://VDundDB.github.io/typytypy-py)

[![PyPI - Downloads (pepy)](https://img.shields.io/pepy/dt/typytypy?label=total%20downloads)](https://pepy.tech/projects/typytypy)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/typytypy.svg)](https://pypi.org/project/typytypy)

[![Linting: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Types: mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://github.com/python/mypy)

[![GitHub Actions - Python](https://github.com/VDundDB/typytypy-py/actions/workflows/python-package.yml/badge.svg)](https://github.com/VDundDB/typytypy-py/actions/workflows/python-package.yml)
[![CodeQL](https://github.com/VDundDB/typytypy-py/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/VDundDB/typytypy-py/actions/workflows/github-code-scanning/codeql)

</div>

---

## Features

### > Developer-Focused API

- 🎯 **Simple Direct Usage**: Get started with a single function call: `typytypy.type_out("Hello, World!")`.
- 📊 **Layered Design**: A flexible API offers both module-level convenience functions and advanced, object-oriented instance management.

### > Expressive Typing Engine

- 🎭 **Character Personalities**: Simulate distinct typing styles with built-in presets like `NERVOUS`, `CONFIDENT`, and `ROBOTIC`.
- ⏱️ **Granular Timing Control**: Define custom timing profiles to precisely control typing rhythm for specific keywords.
- 👁️‍🗨️ **High-Fidelity Output**: Renders text as "real-time typing" simulation, perfectly preserving all original formatting, spacing, and line breaks.

### > Professional-Grade Foundation

- ⚡ **Zero Dependencies**: Pure Python implementation for a lightweight and hassle-free integration.
- 🔒 **Robust & Type-Safe**: Comprehensive validation and full type safety ensure predictable, error-free behavior.
- 📦 **Modern Packaging**: Built and packaged using contemporary Python standards for seamless installation and use.

---

## Quick Start

### Installation

```python
pip install typytypy
```

### Basic Usage

```python
import typytypy

# Basic typewriter effect
typytypy.type_out("Hello, World!")

# ... with custom timing
typytypy.type_out("How are we doing today?",
                  base_delay=0.25, delay_range=0.5)
```

### Using "Character Personality" Presets

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

#### Available Presets

| Preset | Base Delay (`base_delay`) | Delay Range (`delay_range`) | Description |
|--------|------------|-------------|-------------|
| `default` | 0.015s | 0.042s | Standard typing speed |
| `emphasis` | ~0.031s | ~0.099s | Moderate typing speed |
| `slow` | 0.300s | 0.300s | Deliberate, careful |
| `contemplative` | 0.150s | 0.300s | Thoughtful, reflective |
| `nervous` | 0.100s | 0.400s | Anxious, hesitant |
| `average` | 0.120s | 0.240s | Researched human average typing speed |
| `confident` | 0.080s | 0.160s | Steady, professional |
| `robotic` | 0.100s | 0.050s | Mechanical, consistent |
| `chaotic` | 0.007s | 0.993s | Distracted, erratic |

---

## API Reference

### Module-Level Functions

#### `typytypy.type_out(text, base_delay=None, delay_range=None)`

- Print text character-by-character using the default printer instance with optional timing overrides.

#### `typytypy.get_available_presets()`

- List all predefined timing presets (Character Presets) with their timing configuration details.

#### `typytypy.use_preset(preset_name)`

- Create a limited printer instance using a predefined timing preset.
  - only the `type_out()` method is available

### Advanced Class

#### `typytypy.PrintingPress(base_delay=None, delay_range=None)`

*Advanced printer with full profile management capabilities.*

**Core Methods:**

- `type_out(text, base_delay=None, delay_range=None)`: Print text character-by-character, applying profile timings for recognized words and fallback timings for others.
- `set_timing(base_delay, delay_range)`: Update the instance's default timing parameters.

**Profile Management:**

- `create_profile(profile_name, base_delay, delay_range, words=None)`: Create a new timing profile with optional initial words.
- `add_words_to_profile(profile_name, words)`: Add words to an existing profile. Accepts a single string or list of strings.
- `remove_words_from_profile(profile_name, words)`: Remove words from a profile. Accepts a single string or list of strings.
- `list_profiles()`: Return list of all profile names in insertion order.
- `get_profile_info(profile_name)`: Return dictionary with profile details: `base_delay`, `delay_range`, `word_count`, and `words` list.
- `update_profile_timing(profile_name, base_delay, delay_range)`: Update timing parameters for an existing profile.
- `delete_profile(profile_name)`: Delete an entire profile and clean up all mappings.

**Configuration:**

- `set_profile_case_sensitivity(sensitive)`: Configure case-sensitivity for word matching.

---

## Development

### Requirements

- Python 3.10+
- No runtime dependencies

### Development Setup

#### Clone repository

```shell
git clone https://github.com/VDundDB/typytypy-py.git

cd typytypy-py
```

#### Install development dependencies

```python
pip install -e ".[dev]"
```

#### Run quality checks

```python
ruff check src/ tests/
black --check src/ tests/
mypy src/ tests/

# Run all tests with coverage
pytest
```

---

## Documentation

Full documentation: <https://VDundDB.github.io/typytypy-py>

---

## License

Apache License 2.0. See [LICENSE](LICENSE) for details.

---

## Contributing

> [!NOTE]
> 🚧 Contributions are welcome... soon.

---

*"In the careful spacing of characters lies the true poetry of a message."*

> *[...clack-click-clack...ting!]*

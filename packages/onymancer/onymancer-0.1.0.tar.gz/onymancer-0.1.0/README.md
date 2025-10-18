# Onymancer

A Python library for procedural generation of fantasy names using pattern-based generation.

## Features

- **Pattern-Based Name Generation**: Generate diverse fantasy names using customizable patterns with tokens for syllables, vowels, consonants, and more.
- **Token System**: Supports various tokens like 's' for syllables, 'v' for vowels, 'c' for consonants, and special tokens for titles, insults, etc.
- **Grouping and Capitalization**: Use angle brackets `<>` for groups, parentheses `()` for literals, and `!` for capitalization.
- **JSON Token Loading**: Load custom token sets from JSON files for extensible name generation.
- **Seeded Random Generation**: Reproducible name generation with seed support.
- **Customizable Parameters**: Fine-tune generation parameters for different name styles.

## Installation

```bash
pip install onymancer
```

For development:

```bash
git clone https://github.com/Galfurian/onymancer.git
cd onymancer
pip install -e ".[dev]"
```

## Quick Start

```python
from onymancer import generate

# Generate a simple name
name = generate("s(dim)", seed=42)
print(name)  # e.g., "randim"

# Generate a fantasy name with capitalization
name = generate("!s!v!c", seed=123)
print(name)  # e.g., "Elira"

# Use groups for variety
name = generate("<s|v>c", seed=456)
print(name)  # e.g., "brin" or "acor"
```

## Command Line Interface

For quick testing and batch generation, use the included CLI tool:

```bash
# Generate 5 fantasy names
python examples/generate.py --preset fantasy --count 5

# Use a custom pattern
python examples/generate.py --pattern "!s<v|l>!c!v" --count 3 --seed 42

# List available presets
python examples/generate.py --list-patterns

# Output as JSON
python examples/generate.py --preset title --count 2 --json
```

## Patterns

The `generate()` function creates names based on input patterns. Patterns consist of various characters representing different types of random replacements. Everything else is emitted literally.

### Tokens

- **s**: Generic syllable
- **v**: Vowel (a, e, i, o, u, y)
- **V**: Vowel or vowel combination
- **c**: Consonant
- **B**: Consonant or combination suitable for word beginnings
- **C**: Consonant or combination suitable anywhere in a word
- **i**: Insult (humorous/derogatory words)
- **m**: Mushy name (cute/affectionate names)
- **M**: Mushy name ending
- **D**: Consonant suited for "stupid" names
- **d**: Syllable suited for "stupid" names
- **t**: Title prefix (Master of, Ruler of, etc.)
- **T**: Title suffix (the Endless, the Sea, etc.)

### Special Characters

- **()**: Literals - characters between parentheses are emitted literally
- **<>**: Groups - random selection between options separated by `|`
- **!**: Capitalization - capitalizes the next component

### Examples

- `"s(dim)"` → random syllable + "(dim)" → "thor(dim)"
- `"<s|v>"` → either syllable or vowel → "brin" or "a"
- `"!s!v!c"` → capitalized syllable + vowel + consonant → "Elira"
- `"<c|v|>"` → consonant, vowel, or nothing

### generate(pattern: str, seed: int) -> str

Main function for generating names.

**Parameters:**

- `pattern` (str): The pattern defining the name structure
- `seed` (int): Seed for random number generation

**Returns:**

- `str`: The generated name

### load_tokens_from_json(filename: str) -> bool

Load token definitions from a JSON file.

**Parameters:**

- `filename` (str): Path to the JSON file

**Returns:**

- `bool`: True if loading was successful

### `set_token(key: str, tokens: list[str]) -> None`

Set the token list for a given key.

**Parameters:**

- `key (str)`: Single character token key
- `tokens (list[str])`: List of possible replacements

### `set_tokens(tokens: dict[str, list[str]]) -> None`

Set multiple token lists at once.

**Parameters:**

- `tokens (dict[str, list[str]])`: Dictionary mapping keys to token lists

## Usage Examples

See the `examples/` directory for more detailed usage examples.

## Development

Run tests:

```bash
pytest
```

Format code:

```bash
black src/onymancer tests
isort src/onymancer tests
```

## License

MIT License. See LICENSE file.

## Inspiration

This project is a Python port of the C++ namegen library, adapted for modern Python with type hints and comprehensive testing.

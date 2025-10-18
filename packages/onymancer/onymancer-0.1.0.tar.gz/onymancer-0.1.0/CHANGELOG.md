# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-10-17

### Added

- Initial release of Onymancer library
- Procedural fantasy name generation using pattern-based tokens
- Support for various tokens: syllables, vowels, consonants, titles, etc.
- Pattern features: literals with (), groups with <>, capitalization with !
- JSON token loading for custom token sets
- Seeded random generation for reproducibility
- Comprehensive test suite
- Example scripts
- Modern Python packaging with pyproject.toml

### Features

- Token system with predefined fantasy name tokens
- Customizable token sets via JSON or API
- Complex pattern support with grouping and capitalization
- Type hints and documentation
- Ported from C++ namegen library to Python

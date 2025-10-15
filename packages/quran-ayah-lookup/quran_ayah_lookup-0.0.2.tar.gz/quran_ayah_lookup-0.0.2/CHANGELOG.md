# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- N/A

### Changed
- N/A

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- N/A

## [0.0.2] - 2025-10-14

### Added
- **CLI Interface**: Complete command-line interface with Click framework
  - `qal` and `quran-ayah-lookup` command entry points
  - Interactive REPL mode with Ctrl+C exit support
  - All package functions mapped to CLI commands:
    - `verse <surah> <ayah>` - Get specific verses with optional text normalization
    - `surah <number>` - Display surah information and verse counts
    - `search <query>` - Exact substring search across all verses
    - `fuzzy <query>` - Fuzzy search with similarity scoring and thresholds
    - `list-verses <surah>` - List all verses in a specific surah
    - `stats` - Display database statistics
- **Comprehensive CLI Documentation**: Updated README with CLI usage examples and REPL mode guide
- **Unit Tests**: 42 comprehensive test cases covering all CLI functionality
- **Dependencies**: Added Click framework for CLI implementation
- **Error Handling**: Meaningful error messages and graceful exit handling

### Changed
- **Package Dependencies**: Added Click >= 8.0.0 to core dependencies
- **README**: Enhanced with CLI usage section and interactive examples
- **Build Configuration**: Added console script entry points in pyproject.toml

### Notes
- CLI provides full access to all package functionality through command line
- Interactive REPL mode allows continuous queries without restarting
- All existing functionality remains unchanged and backward compatible
- Package now supports both programmatic and command-line usage patterns

## [0.0.1] - 2025-10-09

### Added
- Initial package structure
- MIT License
- README with project description
- pyproject.toml configuration
- Development dependencies setup
- Documentation directory structure
- Contributing guidelines
- .gitignore for Python development

### Notes
- This is the initial release with package structure only
- Core functionality implementation is pending
- Package is ready for PyPI publication structure-wise
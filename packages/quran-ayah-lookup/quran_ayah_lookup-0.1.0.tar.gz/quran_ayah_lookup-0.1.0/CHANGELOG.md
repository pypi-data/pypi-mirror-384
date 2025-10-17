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

## [0.1.0] - 2025-10-17

### Added
- **🔄 Sliding Window Search**: Multi-ayah text matching with vectorized fuzzy matching
  - `search_sliding_window()` function for finding text spanning multiple consecutive ayahs
  - Vectorized fuzzy matching using `rapidfuzz.process.cdist` for high performance
  - Dynamic window sizing and stride optimization for long queries
  - Cross-surah matching capability
  - Configurable similarity thresholds (0.0-100.0)
  - CLI command: `qal sliding-window <query> [--threshold 80.0] [--limit N]`
  - REST API endpoint: `GET /sliding-window`
  - Returns `MultiAyahMatch` objects with verse ranges and similarity scores

- **🧠 Smart Search**: Intelligent automatic method selection
  - `smart_search()` function with cascading search strategy
  - Automatic method selection: exact text search → fuzzy search → sliding window search
  - Transparent method reporting and type-safe result handling
  - CLI command: `qal smart-search <query> [--fuzzy-threshold 0.7] [--sliding-threshold 80.0]`
  - REST API endpoint: `GET /smart-search`
  - Returns structured results with method used, results, and count

- **📊 MultiAyahMatch Data Model**: New dataclass for multi-ayah search results
  - Word-level position tracking across verse boundaries
  - `get_reference()` method for formatted verse references (e.g., "55:1-4")
  - Support for cross-surah matches
  - Similarity scoring and verse range information

- **🌐 REST API Server**: Complete HTTP API with FastAPI framework
  - 8 comprehensive endpoints exposing all package functionalities
  - Automatic Swagger/OpenAPI documentation at `/docs`
  - Interactive API documentation at `/redoc`
  - CLI command: `qal serve` to start API server
  - Optional API dependencies: `fastapi>=0.104.0`, `uvicorn[standard]>=0.24.0`

- **🔧 Dependencies**: Added numpy for vectorized operations
  - `numpy>=2.0.0` as core dependency (required by rapidfuzz.cdist)
  - Maintains compatibility with existing rapidfuzz and click dependencies

- **📚 Documentation**: Comprehensive updates for new features
  - Complete API documentation in `docs/api.md` including REST endpoints
  - Practical examples in `docs/quickstart.md`
  - Updated `README.md` with new features and usage examples
  - Implementation documentation organized in `docs/implementation/`
  - REST API endpoint documentation with request/response examples

- **🧪 Testing**: Extensive test coverage for new functionality
  - 18 comprehensive tests for sliding window functionality
  - 22 comprehensive tests for smart search functionality
  - 36 comprehensive API tests for REST endpoints
  - All 152 tests passing (112 existing + 40 new)

### Changed
- **Version Management**: Updated to use dynamic versioning from `importlib.metadata`
- **Package Structure**: Organized implementation documentation in dedicated directory
- **Dependencies**: Added numpy to core dependencies for vectorized operations

### Fixed
- **Version Resolution**: Fixed dynamic version loading from package metadata

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
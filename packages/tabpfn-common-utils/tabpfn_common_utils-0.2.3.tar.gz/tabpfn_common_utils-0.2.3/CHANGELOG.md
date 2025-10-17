# Changelog

All notable changes to this project will be documented in this file.

## [0.2.3] - 2025-10-16

### Changed
- **Telemetry**: Surpress any telemetry logs, e.g. when internet connection not available.

## [0.2.2] - 2025-09-23

### Added
- **Ping Event**: Add frequency to ping events, allowing to send weekly and monthly pings.

## [0.2.1] - 2025-09-23

### Added
- **License**: Define open source licensing, Apache 2.0.

## [0.2.0] - 2025-09-19

### Added
- **Toggle telemeetry**: Control telemetry toggle using a remote configuration file.
- **Extensions**: Allow setting the context for TabPFN extensions.

## [0.1.9] - 2025-09-10

### Added
- **Hierarchical Extension Context**: Implemented context-aware extension tracking using Python's `contextvars`
- **Extension Decorator**: Added `set_extension()` decorator for automatic extension context management
- **Context Preservation**: Extension context is preserved across nested function calls without overriding higher-level contexts

### Enhanced
- **Telemetry Events**: Events now automatically include the current extension name when available
- **Context Management**: Improved extension context handling with proper cleanup and inheritance

## [0.1.7] - 2025-09-09

### Enhanced
- **Interactive Prompts**: Improved user input validation for telemetry consent prompts
- **Input Validation**: Now requires explicit "y" or "n" input instead of accepting empty strings
- **Retry Logic**: Added retry mechanism with up to 3 attempts for invalid input
- **User Experience**: More specific error messages and clearer input requirements

### Changed
- **Prompt Behavior**: Identity prompt now enforces explicit user choice rather than defaulting on empty input
- **Error Handling**: Enhanced input parsing with customizable retry messages
- **Type Safety**: Updated type annotations to support optional outcomes for invalid input

## [0.1.6] - 2025-09-08

### Added
- **Interactive Telemetry Module**: New `telemetry.interactive` package with optional dependencies
- **Runtime Detection**: Automatic detection of IPython, Jupyter, and TTY environments
- **User Prompts**: Interactive consent prompts for telemetry opt-in
- **State Management**: File-based state storage for user preferences
- **Model Tracking**: Decorators for automatic model call tracking
- **Optional Dependencies**: Install with `pip install tabpfn_common_utils[telemetry-interactive]` for interactive features

### Changed
- **Package Structure**: Refactored telemetry into `core/` and `interactive/` modules
- **API Separation**: Core telemetry always available, interactive features behind `[telemetry-interactive]` extra
- **Import Strategy**: Graceful fallback when interactive dependencies are not installed

## [0.1.4] - 2025-09-08

### Changed
- **Dependency Compatibility**: Updated numpy and pandas requirements to be compatible with scipy 1.11.1 and tabpfn ecosystem
- **NumPy Version**: Downgraded numpy requirement from `>=2,<3` to `>=1.21.6,<1.28.0` for scipy compatibility
- **Pandas Version**: Updated pandas requirement to `>=1.4.0,<3` for broader compatibility

## [0.1.2] - 2025-09-05

### Changed
- **NumPy Compatibility**: Updated `scikit-learn` dependency to match `tabpfn` requirements
- **Development Dependencies**: Added pytest as an explicit dev dependency for consistent testing across environments

## [0.1.1] - 2025-09-05

### Added
- **Privacy-First Telemetry System**: New GDPR-compliant telemetry system using PostHog for anonymous, aggregated usage data collection
- **Telemetry Events**: Implemented specific events (`fit_called`, `dataset`, `predict_called`, `PingEvent`) for TabPFN usage tracking
- **ProductTelemetry Class**: Singleton service for capturing and pushing events with opt-out via `TABPFN_DISABLE_TELEMETRY` environment variable
- **Python 3.13 Support**: Added Python 3.13 classifier and CI testing
- **Comprehensive Documentation**: Complete README overhaul with installation guides, quick start examples, and privacy compliance details

### Changed
- **Package Metadata**: Updated `pyproject.toml` with authors, maintainers, keywords, and extended Python version support
- **Dependencies**: Added `posthog~=6.7` as runtime dependency
- **Type Hints**: Enhanced type safety across utility modules with explicit typing imports
- **Version Management**: Dynamic package version retrieval using `importlib.metadata`

### Fixed
- **Type Annotations**: Corrected return type annotations in `get_example_dataset()` function
- **DataFrame Compatibility**: Improved pandas DataFrame column initialization for better type safety
- **Code Quality**: Enhanced type hinting and removed outdated modules

### Removed
- **load_test.py**: Removed outdated module (moved to API repository)
- **Outdated Configuration**: Cleaned up redundant pyright and ruff configuration sections

---

## [0.1.0] - Initial Release

### Added
- Core utility functions for TabPFN
- Regression prediction result handling
- Data processing and serialization utilities
- Basic project structure and testing framework
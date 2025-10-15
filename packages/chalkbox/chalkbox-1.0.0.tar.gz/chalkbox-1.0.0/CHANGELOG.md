# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-10-13

### Added

- **Alert Component**: Added `debug` and `critical` severity levels (expanded from 4 to 6 levels)
  - `Alert.debug()` - For verbose debugging output with "▪" glyph and dim cyan color
  - `Alert.critical()` - For system-critical failures with "‼" glyph and bright red color
- **Alert Component**: Added `title_align` parameter for customizable title positioning
  - Supports "left" (default), "center", and "right" alignment
  - Available in all alert factory methods (`Alert.debug()`, `Alert.info()`, etc.)
- **Alert Component**: Added `padding` parameter for customizable internal spacing
  - Accepts integer for all sides or tuple `(vertical, horizontal)` for asymmetric padding
  - Default remains `(0, 1)` for backward compatibility
- **Section Component**: Added `title_align` and `subtitle_align` parameters
  - Both support "left", "center", and "right" alignment
  - `title_align` defaults to "left", `subtitle_align` defaults to "right"
  - Enables better visual hierarchy and emphasis in sections
- **Table Component**: Added `border_style` parameter for custom table theming
  - Accepts any Rich color string (e.g., "bright_cyan", "red", "dim white")
  - Defaults to theme's primary color for backward compatibility
  - Enables color-coded tables for different data types
- **Spinner Component**: Added `refresh_per_second` parameter for performance tuning
  - Controls animation refresh rate (default: 10 fps)
  - Lower values (4-6 fps) for slow terminals or remote connections
  - Higher values (15-20 fps) for smooth animations on fast terminals

### Changed

- **Theme System**: Updated color tokens to include `debug` (dim cyan) and `critical` (bright red)
- **Theme System**: Updated glyph tokens to include `debug` (▪) and `critical` (‼)
- **Documentation**: Updated `README.md` and `docs/COMPONENTS.md` with examples of all 6 alert levels
- **Demo Scripts**: Updated component demos to showcase all new features (title alignment, border styles, refresh rates)
- **Theme Files**: Updated `demos/theming/theme-dark.toml` and `theme-light.toml` with debug/critical support

## [0.9.0] - 2025-10-12

### Changed

- Project renamed from `Terminal UI Kit` to `ChalkBox`
- Updated Rich package version to 14.2.0
- Converted all interactive demos to auto-run mode for batch execution
- Added explicit Python 3.12+ requirement documentation

### Fixed

- Fixed Spinner component duplicate output when using `transient=False`
- Fixed demo file naming (removed `_demo` suffix from component demos)
- Fixed `interactive_components.py` to use simulated interaction for batch runs

### Added

- Documentation:
- Created CONTRIBUTING.md with comprehensive contribution guidelines
- Added "Why Python 3.12+" section to README explaining modern features
- Added badges to README (PyPI version, downloads, Python version, license, Rich, Poetry, quality tools, community metrics)
- Added Poetry badge to indicate dependency management approach

## [0.8.0] - 2025-07-27

### Added

- **Live & Responsive Components**:

  - LiveComponent: Generic wrapper for making any component live and responsive
  - LiveTable: Pre-configured live table wrapper
  - LiveLayout: Pre-configured live layout wrapper
  - Dashboard: High-level dashboard builder with header/sidebar/main/footer sections
  - Built-in `.live()` methods for Table and MultiPanel components
  - Automatic terminal resize handling for all live components
  - Support for both static (scrolling) and live (updating) output modes

- **Advanced Demos**:

  - Live component demos with auto-updating displays
  - Dashboard builder demonstrations
  - Responsive layout examples showing terminal resize adaptation

### Changed

- Updated Rich package version to 14.1.0

## [0.7.0] - 2025-03-30

### Added

- MultiPanel: Complex layouts component for grids and dashboards with automatic responsiveness
- Advanced live dashboard demos showcasing multi-section layouts
- Nested panel demonstrations showing composition patterns

### Changed

- Updated Rich package version to 14.0.0

## [0.6.0] - 2025-01-22

### Added

- **KeyValue**: Key-value display component with automatic secret masking for passwords, keys, tokens
  - Comprehensive test suite for KeyValue component
  - Secret detection patterns (password, secret, key, token, credential)

## [0.5.0] - 2025-01-10

### Added

- **CodeBlock**: Syntax-highlighted code display component with file reading support
- **Progress**: Multi-task progress bars with ETA and thread-safe updates
- Comprehensive test coverage for new components
- Support for multiple programming languages in CodeBlock

### Changed

- Migrated from Black, isort, and flake8 to Ruff for linting and formatting
- Improved code quality and consistency with unified linting tool

## [0.4.0] - 2025-01-10

### Added

- **Input Components**: Interactive prompt components for user interaction
  - Input: Basic text input with validation
  - IntInput: Integer input with range validation
  - FloatInput: Float input with range validation
  - Select: Choice selection from list
  - Confirm: Yes/no confirmation prompts
- Test suite for input components

### Changed

- Updated Rich package version to 13.9.4

## [0.1.0] - 2025-01-09

### Added

- **Initial Release** of terminal-ui-kit (project later renamed to ChalkBox in 0.9.5)

## Core Components

- **Spinner**: Context manager for async operations with success/fail/warning states
- **Alert**: Debug/info/success/warning/error/critical callouts with optional details
- **Table**: Auto-sizing tables with severity-based row styling and smart truncation
- **Section**: Organized content containers with optional subtitles
- **Divider**: Section dividers with multiple styles (standard, double, heavy, dotted, dashed)
- **Status**: Non-blocking status indicators for background operations
- **ColumnLayout**: Responsive column layouts with equal/custom sizing
- **Stepper**: Multi-step workflow tracking with status indicators
- **Tree**: Hierarchical data visualization with file system support
- **Markdown**: Markdown rendering component
- **JsonView**: JSON data visualization with pretty printing

## Theme System

- Token-based theming with colors, spacing, glyphs, and borders
- Three-tier configuration: defaults → config file → environment variables
- Config file support (`~/.chalkbox/theme.toml`)
- Environment variable overrides (`CHALKBOX_THEME_*`)
- Dot-notation access (e.g., `theme.get("colors.primary")`)
- Severity-based styling (success/warning/error/info)

## Core Features

- **Fail-safe design**: Components never raise exceptions, degrade gracefully
- **Non-TTY support**: Automatic degradation in CI/CD and piped output
- **Thread-safe operations**: Safe concurrent updates for Progress and stateful components
- **Context managers**: All stateful components support `with` statements
- **Factory methods**: Convenience constructors for common patterns
- **Singleton console**: `get_console()` for shared console access
- **Rich compatibility**: All components return Rich renderables for composition

## Logging

- Pre-configured Rich logging via `setup_logging()`
- Console and file handlers with configurable levels
- Rich tracebacks for better error diagnostics

## Development Tools

- Python 3.12+ requirement (uses modern type hints and `type` statement)
- Built on Rich >= 13.7.0
- Poetry for dependency management
- Ruff for linting and formatting
- MyPy for type checking
- Bandit for security analysis
- Pytest for testing with coverage support

## Documentation & Examples

- Component demos in `demos/components/` (individual examples)
- Showcase demos in `demos/showcases/` (multi-component demos)
- Workflow examples in `demos/workflows/` (real-world demos)
- README with quick start and examples
- Fail-safe patterns and best practices documentation

## Developer Experience

- Consistent naming conventions (snake_case for variables, kebab-case for CLI)
- Type hints throughout codebase using Python 3.12 syntax
- Fail-safe error handling patterns in all components
- Zero dependencies beyond Rich

## Version History Summary

- **0.1.0** (2025-01-09) - Initial release as terminal-ui-kit with core components
- **0.4.0** (2025-01-10) - Added interactive input components
- **0.5.0** (2025-01-10) - Added CodeBlock and Progress, migrated to Ruff
- **0.6.0** (2025-01-22) - Added KeyValue with secret masking
- **0.7.0** (2025-03-30) - Added MultiPanel and advanced live demos
- **0.8.0** (2025-07-27) - Added live components and Dashboard builder
- **0.9.0** (2025-10-12) - Renamed to ChalkBox, comprehensive documentation
- **1.0.0** (2025-10-13) - **Stable release**: Enhanced components, production-ready, 100% linting compliance

## Links

- **PyPI**: https://pypi.org/project/chalkbox/
- **GitHub**: https://github.com/bulletinmybeard/chalkbox
- **Issues**: https://github.com/bulletinmybeard/chalkbox/issues
- **Changelog**: https://github.com/bulletinmybeard/chalkbox/blob/main/CHANGELOG.md

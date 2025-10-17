# Changelog

## [0.4.2] - 2025-10-16

- Fixed dictionary assignments with string keys being misclassified as CALL
  - `environ['KEY'] = value` now correctly classified as ASSIGNMENT
  - Prevents incorrect blank lines being added between consecutive dictionary assignments

## [0.4.1] - 2025-10-14

- Updated `--check` mode output to "All checks passed!" when no formatting changes needed (matches ruff style)
- Fixed `async def` being misclassified as CALL instead of DEFINITION
  - This was causing blank lines to be incorrectly added between `async def` and its docstring
  - Now properly recognizes `async def` as a function definition
- Fixed class docstrings always requiring 1 blank line before first method, regardless of `after_docstring` config
  - Class docstrings now always get 1 blank line (PEP 257 requirement)
  - Function/method docstrings respect the `after_docstring` configuration setting
  - Fixed comment handling in blank line calculation to properly use BlockType.COMMENT

## [0.4.0] - 2025-10-14

- Added configurable blank lines after docstrings via `after_docstring` configuration
  - Default: 1 blank line (PEP 257 compliance)
  - Set to 0 for compact style with no blank line after docstrings
  - Configurable via TOML (`after_docstring = 0`) or CLI (`--blank-lines-after-docstring 0`)
- Fixed module-level config imports to use JIT (just-in-time) imports for runtime configuration changes

## [0.3.0] - 2025-10-05

**BREAKING CHANGES**: Full PEP 8 and PEP 257 compliance

- **PEP 8 Definition Spacing**: Scope-aware blank lines between function/class definitions
  - **2 blank lines** between top-level (module level) function/class definitions
  - **1 blank line** between method definitions inside classes (nested levels)
  - Automatically detects indentation level to apply correct spacing

- **PEP 257 Docstring Spacing**: Blank lines after docstrings follow normal block transition rules
  - Blank line required after docstrings before first statement (per PEP 257)
  - Removed special suppression of blank lines after docstrings in function/class bodies
  - Aligns with Ruff's formatting expectations for docstring spacing

## [0.2.1] - 2025-01-26

- Added `--quiet` flag to suppress all output except errors
- Fixed missing Statement import in rules.py

## [0.2.0] - 2025-01-26

- Added configurable indent width detection (default 2 spaces, configurable via `indent_width`)
- Added atomic file operations with temporary files for safer processing
- Added CLI `--dry-run` flag to preview changes without applying them
- Added CLI `--verbose` flag for detailed processing information
- Added specific exception handling for file operations (encoding, permissions, I/O errors)
- Implemented singleton configuration pattern for cleaner code architecture
- Added pre-compiled regex patterns for improved performance
- Added end-of-file newline preservation to maintain existing file formatting
- Renamed `tab_width` to `indent_width` for clarity (breaking change)
- Major code quality improvements and critical issue fixes

## [0.1.3] - 2025-01-09

- Fixed blank lines being incorrectly added after multi-line docstrings in function bodies

## [0.1.2] - 2025-01-09

- Fixed blank lines being removed between consecutive class methods
- Added --version flag to display version from pyproject.toml
- Fixed blank lines after docstrings in function bodies
- Fixed internal blank lines being removed from multi-line docstrings
- Fixed comment block "leave-as-is" behavior for blank line preservation

## [0.1.1] - 2025-01-09

- Initial release
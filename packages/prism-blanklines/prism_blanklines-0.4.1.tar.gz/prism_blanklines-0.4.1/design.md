# Prism - Blank Line Enforcement Tool Design

## Overview

Prism is a Python code formatter that enforces configurable blank line rules, similar to `black` or `ruff`. It processes Python files in-place, applying complex blank line rules while preserving existing multiline formatting and docstring content.

## Architecture

### Core Components

1. **MultilineParser** (`parser.py`): Handles line-by-line reading with bracket and quote tracking for multiline statements
2. **StatementClassifier** (`classifier.py`): Identifies statement types and maintains block classification with pre-compiled regex patterns
3. **BlankLineRuleEngine** (`rules.py`): Applies configurable blank line rules based on block transitions
4. **FileAnalyzer** (`analyzer.py`): Manages parsing and analysis of file structure with configurable tab width
5. **BlankLineConfig** (`config.py`): Singleton configuration system for customizable blank line rules
6. **CLI Interface** (`cli.py`): Command-line tool with file/directory processing, check mode, dry-run, and verbose output
7. **FileProcessor** (`processor.py`): Handles atomic file I/O with end-of-file newline preservation and change detection

### Processing Pipeline

```
Configuration Layer:
├── BlankLineConfig (singleton pattern)
├── TOML parsing with validation (0-3 range)
└── Default configuration (fromDefaults)

Processing Pipeline:
├── Pass 1: FileAnalyzer
│   ├── MultilineParser (bracket/quote tracking, statement completion)
│   └── StatementClassifier (block type identification with pre-compiled regex)
├── Pass 2: BlankLineRuleEngine
│   ├── Configuration-driven rule application
│   ├── Scope-aware processing (nested indentation)
│   └── Special rule handling (consecutive Control/Definition, comments)
└── Pass 3: FileProcessor
    ├── Atomic file operations (tempfile + rename)
    ├── End-of-file newline preservation
    └── Change detection and conditional writing
```

## Key Design Decisions

### 1. Singleton Configuration Pattern
- **Global config instance** eliminates parameter passing throughout codebase
- **setConfig function** allows updating global configuration from CLI
- **Default configuration** provides sensible defaults (1 blank line between different blocks)
- **TOML configuration** allows fine-grained customization via `prism.toml`

### 2. Atomic File Operations
- **Temporary file pattern**: Write to `.prism_temp_<random>` then rename
- **Prevents partial writes**: Original file remains intact if write fails
- **End-of-file newline preservation**: Maintains existing EOF newline or lack thereof
- **Encoding handling**: Explicit UTF-8 encoding with specific error handling

### 3. Pre-compiled Regex Patterns
- **Performance optimization**: Compile regex patterns once at module load
- **COMPILED_PATTERNS dictionary**: Maps pattern types to compiled patterns
- **COMPILED_SECONDARY_CLAUSES**: Pre-compiled for fast secondary clause detection
- **Eliminates redundant compilation**: No per-statement regex compilation overhead

### 4. Multiline Statement Handling
- **Buffer physical lines** until complete logical statement is formed
- **Preserve original formatting** - do not alter line breaks within multiline statements
- **Classify entire statement** once complete (e.g., `x = func(\n  arg\n)` is Assignment)
- **Quote tracking**: Track `inString` state with `stringDelimiter` for proper multiline string handling

### 5. Docstring Preservation (Critical)
**Docstrings are atomic units** - their internal structure must NEVER be modified:

- **Triple-quoted strings** (`"""` or `'''`) are tracked from opening to closing quotes
- **All content within docstrings is preserved exactly**, including:
  - Blank lines
  - Lines starting with `#` (not treated as comments)
  - Indentation patterns
  - Special formatting (markdown, reStructuredText, etc.)

**Implementation Details:**
- `MultilineParser` tracks `inString` state and `stringDelimiter` for proper quote matching
- `FileAnalyzer` checks `parser.inString` before processing blank lines or comments
- When `inString=True`, lines are added to current statement without special handling

**PEP 257 Compliance:**
- Per PEP 257, blank lines after docstrings are configurable via `afterDocstring` (default: 1)
- The default of 1 blank line follows PEP 257 recommendation for visual separation
- Setting `afterDocstring = 0` provides a more compact style
- Docstrings to other docstrings always have 0 blank lines (not configurable)

**PEP 8 Compliance:**
- Per PEP 8, scope-aware definition spacing is applied:
  - **2 blank lines** between consecutive top-level (module level, indent 0) function/class definitions
  - **1 blank line** between consecutive method definitions inside classes (nested levels)
- This is implemented by checking indentation level when applying `consecutiveDefinition` rules
- Configuration override: `consecutiveDefinition` still controls nested definition spacing (default: 1)

### 6. Block Classification Priority
```python
# Classification precedence (highest to lowest):
1. Assignment block (x = foo(), comprehensions, lambdas)
2. Call block (foo(), del, assert, pass, raise, yield, return)
3. Import block (import statements)
4. Control block (if/for/while/try/with complete structures)
5. Definition block (def/class complete structures)
6. Declaration block (global/nonlocal)
7. Comment block (consecutive comment lines)
```

### 7. Nested Control Structure Tracking
- **Independent rule application** at each indentation level
- **Secondary clause handling**: No blank lines before `elif`/`else`/`except`/`finally`
- **Complete structure detection**: Track when control blocks end with/without optional clauses
- **Scope boundary enforcement**: Always 0 blank lines at start/end of scopes (non-configurable)

### 8. Comment Block Behavior - Special "Leave-As-Is" Rules

Comments have **fundamentally different behavior** from other block types and do NOT follow normal block transition rules:

#### 8.1 Consecutive Comments Within a Block
- **No blank lines between consecutive comments** (e.g., copyright headers)
- **Comment break rule**: Only add blank lines before a comment if the previous block was NOT a comment
- **Implementation**: `if prevBlockType != BlockType.COMMENT` check prevents breaking up comment blocks

#### 8.2 Transitions FROM Comment Blocks to Other Blocks
Comments follow a **"leave-as-is"** policy that overrides normal block transition rules:

**Case 1: Existing blank line after comment block**
```python
# Comment block
# More comments

import foo  # <- Preserve existing blank line (leave-as-is)
```
- **Behavior**: Preserve the existing blank line
- **Implementation**: `preserveExistingBlank` logic detects and preserves

**Case 2: No existing blank line after comment block**
```python
# Comment block
import foo  # <- Do NOT add blank line
```
- **Behavior**: Do NOT apply normal block transition rules
- **Implementation**: `if prevBlockType != BlockType.COMMENT` check bypasses normal transition logic

#### 8.3 Key Principle
**Comments are "transparent" to blank line rules** - they don't trigger normal block transitions, they only preserve what already exists.

## Configuration System

### Configuration Structure
```python
@dataclass
class BlankLineConfig:
    defaultBetweenDifferent: int = 1
    transitions: dict = field(default_factory=dict)
    consecutiveControl: int = 1
    consecutiveDefinition: int = 1
    afterDocstring: int = 1
    indentWidth: int = 2

    @classmethod
    def fromToml(cls, configPath: Path) -> 'BlankLineConfig'
    @classmethod
    def fromDefaults(cls) -> 'BlankLineConfig'
    def getBlankLines(self, fromBlock: BlockType, toBlock: BlockType) -> int
```

### Configuration File Format
```toml
# prism.toml - Complete example
[blank_lines]
# Default spacing between different block types (0-3)
default_between_different = 1

# Special consecutive block rules (0-3)
consecutive_control = 1
consecutive_definition = 1

# Blank lines after docstrings (0-3, default: 1 for PEP 257 compliance)
after_docstring = 1

# Indent width for indentation detection (default: 2)
indent_width = 2

# Fine-grained transition overrides (0-3)
# Format: <from_block>_to_<to_block> = <count>
assignment_to_call = 2
call_to_assignment = 2
import_to_assignment = 0
assignment_to_import = 0
control_to_definition = 2
```

### Block Type Names for Configuration
- `assignment` - Variable assignments, comprehensions, lambdas
- `call` - Function calls, del, assert, pass, raise, yield, return
- `import` - Import statements
- `control` - if/for/while/try/with structures
- `definition` - def/class structures
- `declaration` - global/nonlocal statements
- `comment` - Comment lines

## CLI Interface

### Command-Line Options
```bash
# Basic usage
prism file.py              # Format single file
prism src/                 # Format directory recursively

# Check mode (no modifications)
prism --check file.py      # Exit 1 if changes needed, 0 otherwise

# Dry-run mode (show what would change)
prism --dry-run file.py    # Show diff without applying changes

# Verbose mode
prism --verbose file.py    # Show detailed processing information

# Configuration
prism --config custom.toml file.py  # Use custom config file

# Version
prism --version            # Show version information

# Help
prism --help              # Show usage information
```

### Exit Codes
- **0**: Success (no changes needed or changes applied successfully)
- **1**: Changes needed (in `--check` mode) or error occurred

## Critical Edge Cases

1. **Nested control with secondary clauses**:
```python
if condition:
    if nested:
        pass
    else:
        pass
else:
    pass
```

2. **Comment breaks with preserved spacing**:
```python
x = 1

# Comment causes break
y = 2  # This starts new Assignment block
```

3. **Multiline classification**:
```python
result = complexFunction(
    arg1,
    arg2
)  # Entire construct is Assignment block
```

4. **Mixed statement classification**:
```python
x = someCall()  # Assignment block (precedence rule)
```

5. **Docstring with internal formatting**:
```python
def func():
    """
    # This is NOT a comment

    This blank line is preserved
    """
    pass
```

## Error Handling

### Specific Exception Handling
- **FileNotFoundError**: File doesn't exist (logged, processing continues)
- **PermissionError**: No permission to read/write file (logged, processing continues)
- **UnicodeDecodeError**: File encoding issues (logged, processing continues)
- **OSError**: General I/O errors (logged, processing continues)
- **TOMLDecodeError**: Invalid TOML configuration (propagated to user)

### Error Handling Strategy
- **CLI level**: Catches and logs errors, continues processing other files
- **Processor level**: Returns `True` for changes made, `False` for no changes or errors
- **Configuration level**: Raises exceptions for invalid configuration (fail fast)

## Performance Optimizations

1. **Pre-compiled regex patterns**: Compile once at module load, not per statement
2. **Singleton configuration**: Load and validate configuration once per execution
3. **Atomic file operations**: Write to temp file, rename only if changes made
4. **Change detection**: Compare line-by-line before writing to avoid unnecessary I/O
5. **Two-pass processing**: Analyze structure once, apply rules in single pass
6. **Efficient bracket tracking**: Simple character scanning without full AST parsing

## Testing Strategy

1. **Unit tests** for each component:
   - `test_parser.py`: MultilineParser bracket/quote tracking
   - `test_classifier.py`: Statement classification and precedence
   - `test_rules.py`: Blank line rule engine logic
   - `test_analyzer.py`: File analysis and indentation detection
   - `test_processor.py`: File I/O and change detection
   - `test_config.py`: Configuration parsing and validation
   - `test_types.py`: Core data structures

2. **Integration tests**:
   - `test_integration.py`: End-to-end file processing scenarios
   - `test_configintegration.py`: Configuration-driven rule application
   - `test_docstrings.py`: Docstring preservation edge cases
   - `test_classmethods.py`: Class method spacing scenarios
   - `test_nestedscopes.py`: Nested control structure handling

3. **Bug regression tests**:
   - `test_bugs.py`: Specific bug scenarios with regression tests

4. **CLI tests**:
   - `test_cli.py`: Command-line interface functionality
   - `test_version.py`: Version detection and reporting

## Outstanding Issues

### Non-Critical Technical Debt

#### MAJOR-003: Excessive Complexity in Rules Engine
**File**: `src/prism/rules.py` (main rule application logic)
**Problem**: The main blank line decision logic contains deeply nested conditionals with multiple boolean flags and complex state tracking.
**Impact**: Maintainability concerns, future modifications may introduce bugs
**Approach**: Consider state machine pattern or extract helper methods for different rule categories
**Priority**: Low - current logic works correctly and has comprehensive test coverage

#### MAJOR-004: Inconsistent Error Handling Strategy
**File**: Multiple files across codebase
**Problem**: Mixed error handling patterns - some functions return `False` on errors, others log and return `False`, configuration raises exceptions
**Impact**: Developer experience could be improved with consistent patterns
**Approach**: Document error handling strategy explicitly; consider whether configuration errors should be handled more gracefully
**Priority**: Low - current patterns work but could be more consistent

## Future Enhancements

### Core Focus: Blank Line Intelligence

Prism's mission is to be **the definitive solution for scope-aware, configurable blank line enforcement**. This is a unique capability that Black, Ruff, and other formatters don't provide comprehensively. Our goal is to become so good at this specific problem that we could be integrated into tools like Ruff.

### ENHANCEMENT-001: Visitor Pattern for Statement Analysis
**Benefit**: Make the code more extensible for future block types
**Approach**: Implement visitor pattern for statement analysis instead of current switch-based classification
**Impact**: Easier to add new block types without modifying core analysis logic
**Priority**: Medium - improves maintainability and extensibility

### ENHANCEMENT-002: Configuration Validation Schema
**Benefit**: Better user feedback on configuration errors
**Approach**: Add configuration validation schema using a library like Pydantic
**Impact**: Clearer error messages and validation, better developer experience
**Priority**: Medium - improves user experience

### ENHANCEMENT-003: Parallel Processing for Multiple Files
**Benefit**: Improve performance on large codebases
**Approach**: Implement parallel processing when multiple files are specified
**Impact**: Significant performance improvement for batch operations
**Priority**: High - essential for large codebases

### ENHANCEMENT-004: Comprehensive Logging Framework
**Benefit**: Aid debugging and provide insights into processing decisions
**Approach**: Add structured logging to show rule decisions, block classifications, etc.
**Impact**: Better troubleshooting and understanding of tool behavior
**Priority**: Medium - aids debugging and transparency

### ENHANCEMENT-005: Support for Additional Languages
**Benefit**: Extend prism beyond Python (JavaScript, TypeScript, Java, etc.)
**Approach**: Abstract language-specific parsing into pluggable modules
**Impact**: Wider applicability of blank line enforcement philosophy
**Priority**: High - dramatically expands prism's usefulness and adoption potential
**Strategic**: Makes prism valuable enough to integrate into multi-language tools like Ruff

### ENHANCEMENT-006: Integration API for Ruff/Other Tools
**Benefit**: Enable prism's blank line intelligence to be used by other formatters
**Approach**: Expose stable API/library interface that other tools can import and use
**Impact**: Prism becomes the de facto blank line engine for Python formatting ecosystem
**Priority**: High - strategic goal for adoption
**Requirements**:
  - Clean, well-documented API
  - Stable interface with semantic versioning
  - Minimal dependencies
  - Fast performance

### Out of Scope

The following are explicitly **NOT** in prism's roadmap as they dilute focus from our core competency:

- **Line length enforcement/wrapping** - Black and Ruff already do this excellently
- **Import sorting** - isort and Ruff already provide this
- **Quote style normalization** - Black and Ruff handle this
- **General code formatting** - Not our mission

These features would make prism "yet another Python formatter" instead of "the best blank line tool."
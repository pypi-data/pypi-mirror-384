# 🍞 mbake

<!-- markdownlint-disable MD033 -->
<div align="center">
    <img src="https://raw.githubusercontent.com/ebodshojaei/bake/main/vscode-mbake-extension/icon.png" alt="mbake logo" width="128" height="128">
    <br/>
    <em>A Makefile formatter and linter. It only took 50 years!</em>
    <br/><br/>
    <a href="https://opensource.org/licenses/MIT">
        <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"/>
    </a>
    <a href="https://www.python.org/downloads/">
        <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python 3.9+"/>
    </a>
    <a href="https://pypi.org/project/mbake/">
        <img src="https://img.shields.io/pypi/v/mbake.svg" alt="PyPI - mbake"/>
    </a>
    <a href="https://github.com/psf/black">
        <img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code style: black"/>
    </a>
    <a href="https://pepy.tech/projects/mbake">
        <img src="https://static.pepy.tech/badge/mbake" alt="PyPI Downloads"/>
    </a>
</div>
<!-- markdownlint-enable MD033 -->

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Migration to v1.3.x](#migration-to-v13x)
- [Usage](#usage)
- [Configuration](#configuration)
- [Examples](#examples-1)
- [Contributing](#contributing)

## Features

- Configurable rules via `~/.bake.toml`
- CI/CD integration with check mode
- Extensible plugin architecture
- Rich terminal output with progress indicators
- Syntax validation before and after formatting
- Smart .PHONY detection with automatic insertion
- Suppress formatting with special comments

---

## Formatting Rules

### Indentation & Spacing

- **Tabs for recipes**: Recipe lines use tabs instead of spaces
- **Assignment operators**: Normalized spacing around `:=`, `=`, `+=`, `?=`
- **Target colons**: Consistent spacing around target dependency colons
- **Trailing whitespace**: Removes unnecessary trailing spaces

### Line Continuations

- **Backslash normalization**: Proper spacing around backslash continuations
- **Smart joining**: Consolidates simple continuations while preserving complex structures

### .PHONY Declarations

- **Grouping**: Consolidates multiple `.PHONY` declarations
- **Auto-insertion**: Automatically detects and inserts `.PHONY` declarations when missing (opt-in)
- **Dynamic enhancement**: Enhances existing `.PHONY` declarations with additional detected phony targets
- **Rule-based analysis**: Uses command analysis to determine if targets are phony
- **Minimal changes**: Only modifies `.PHONY` lines, preserves file structure

---

## Installation

### PyPI (Recommended)

```bash
pip install mbake
```

### VSCode Extension

1. Open VSCode
2. Go to Extensions (Ctrl+Shift+X)
3. Search for "mbake Makefile Formatter"
4. Click Install

### From Source

```bash
git clone https://github.com/ebodshojaei/bake.git
cd mbake
pip install -e .
```

### Development Installation

```bash
git clone https://github.com/ebodshojaei/bake.git
cd mbake
pip install -e ".[dev]"
```

### Package Manager Installation

For system package managers and AUR packagers, mbake supports configurable command names to avoid namespace conflicts.

**For AUR packagers**: The default behavior already avoids conflicts with `ruby-bake` - no additional configuration needed!

---

## Migration to v1.3.x

**⚠️ Breaking Change**: Version 1.3.0 introduces a module rename from `bake` to `mbake` for consistency.

### What Changed

- **Python module**: `bake` → `mbake` (for consistency with command name)
- **Command name**: Still `mbake` (unchanged)
- **Configuration**: Still `~/.bake.toml` (unchanged)

### Migration Steps

1. **Update the package**:

   ```bash
   pip install --upgrade mbake
   ```

2. **If you have shell aliases**, they will continue working:

   ```bash
   # Your existing alias will still work
   alias bake='mbake'
   bake --version  # ✅ Still works
   ```

3. **If you have Python scripts** that import from `bake`, update them:

   ```python
   # Old (v1.2.x)
   from bake.config import Config
   
   # New (v1.3.x)
   from mbake.config import Config
   ```

4. **If you have CI/CD scripts**, update import statements:

   ```bash
   # Old (v1.2.x)
   python -c "from bake.cli import main; main()"
   
   # New (v1.3.x)
   python -c "from mbake.cli import main; main()"
   ```

### Backward Compatibility

- **CLI commands**: All commands work exactly the same
- **Configuration files**: No changes needed
- **Shell aliases**: Continue working without modification
- **Python imports**: Require updating to use `mbake` module

---

## Usage

mbake uses a subcommand-based CLI. All commands support both `bake` and `mbake` aliases.

### Quick Start

```bash
# Check version
mbake --version

# Set up your preferred command name (optional)
mbake setup-command mbake  # or 'bake' (creates alias) or 'both' (creates alias)

# Initialize configuration (optional)
mbake init

# Format a Makefile
mbake format Makefile

# Validate Makefile syntax
mbake validate Makefile
```

### Configuration Management

```bash
# Initialize configuration file with defaults
bake init

# Initialize with custom path or force overwrite
bake init --config /path/to/config.toml --force

# Show current configuration
bake config

# Show configuration file path
bake config --path

# Use custom configuration file
bake config --config /path/to/config.toml
```

### Formatting Files

```bash
# Format a single Makefile
bake format Makefile

# Format multiple files
bake format Makefile src/Makefile tests/*.mk

# Check if files need formatting (CI/CD mode)
bake format --check Makefile

# Show diff of changes without modifying files
bake format --diff Makefile

# Format with verbose output
bake format --verbose Makefile

# Create backup before formatting
bake format --backup Makefile

# Validate syntax after formatting
bake format --validate Makefile

# Use custom configuration
bake format --config /path/to/config.toml Makefile
```

### Syntax Validation

```bash
# Validate single file
bake validate Makefile

# Validate multiple files
bake validate Makefile src/Makefile tests/*.mk

# Validate with verbose output
bake validate --verbose Makefile

# Use custom configuration
bake validate --config /path/to/config.toml Makefile
```

#### **validate vs format --check**

- **`bake validate`**: Checks if Makefile will execute correctly using GNU `make` (syntax validation)
- **`bake format --check`**: Checks if Makefile follows formatting rules (style validation)

Both are useful! Use `validate` for syntax errors, `format --check` for style issues.

### Version Management

```bash
# Check current version and for updates
bake --version

# Check for updates only (without updating)
bake update --check

# Update to latest version
bake update

# Update with confirmation prompt bypass
bake update --yes

# Force update even if already up to date
bake update --force
```

### Shell Completion

```bash
# Install completion for current shell
bake --install-completion

# Show completion script (for manual installation)
bake --show-completion
```

---

## Configuration

mbake works with sensible defaults. Generate a configuration file with:

```bash
bake init
```

### Sample Configuration

```toml
# Global settings
debug = false
verbose = false

# Error message formatting
gnu_error_format = true
wrap_error_messages = false

[formatter]
# Spacing settings - enable proper spacing
space_around_assignment = true
space_before_colon = false
space_after_colon = true

# Line continuation settings
normalize_line_continuations = true
max_line_length = 120

# PHONY settings
group_phony_declarations = false
phony_at_top = false
auto_insert_phony_declarations = false

# General settings - enable proper formatting
remove_trailing_whitespace = true
ensure_final_newline = true
normalize_empty_lines = true
max_consecutive_empty_lines = 2
fix_missing_recipe_tabs = true

# Conditional formatting settings (Default disabled)
indent_nested_conditionals = false
# Indentation settings
tab_width = 2
```

---

## Smart .PHONY Detection

mbake includes intelligent `.PHONY` detection that automatically identifies and manages phony targets.

### How It Works

Detection uses dynamic analysis of recipe commands rather than hardcoded target names:

- **Command Analysis**: Examines what each target's recipe actually does
- **File Creation Detection**: Identifies if commands create files with the target name
- **Pattern Recognition**: Understands compilation patterns, redirections, and common tools

### Examples

#### Docker/Container Targets

```makefile
# These are detected as phony because they manage containers, not files
up:
 docker compose up -d

down:
 docker compose down -v

logs:
 docker compose logs -f
```

#### Build/Development Targets  

```makefile
# These are detected as phony because they don't create files with their names
test:
 npm test

lint:
 eslint src/

deploy:
 ssh user@server 'systemctl restart myapp'
```

#### File vs Phony Target Detection

```makefile
# NOT phony - creates myapp.o file
myapp.o: myapp.c
 gcc -c myapp.c -o myapp.o

# Phony - removes files, doesn't create "clean"
clean:
 rm -f *.o myapp
```

<!-- markdownlint-disable MD024 -->
### Configuration

Enable auto-insertion in your `~/.bake.toml`:

```toml
[formatter]
auto_insert_phony_declarations = true
```

### Behavior Modes

**Default (Conservative)**:

- Groups existing `.PHONY` declarations
- No automatic insertion or enhancement
- Backwards compatible

**Enhanced (auto_insert_phony_declarations = true)**:

- Automatically inserts `.PHONY` when missing
- Enhances existing `.PHONY` with detected targets
- Uses dynamic analysis for accurate detection

### Before and After

**Input** (no `.PHONY`):

```makefile
setup:
 docker compose up -d
 npm install

test:
 npm test

clean:
 docker compose down -v
 rm -rf node_modules
```

**Output** (with auto-insertion enabled):

```makefile
setup:
 docker compose up -d
 npm install

test:
 npm test

clean:
 docker compose down -v
 rm -rf node_modules

```

---

## Examples

### Basic Formatting

**Before:**

```makefile
# Inconsistent spacing and indentation
CC:=gcc
CFLAGS= -Wall -g
SOURCES=main.c \
  utils.c \
    helper.c

.PHONY: clean
all: $(TARGET)
    $(CC) $(CFLAGS) -o $@ $^

.PHONY: install
clean:
    rm -f *.o
```

**After:**

```makefile
# Clean, consistent formatting
CC := gcc
CFLAGS = -Wall -g
SOURCES = main.c \
  utils.c \
  helper.c

.PHONY: clean
all: $(TARGET)
 $(CC) $(CFLAGS) -o $@ $^

.PHONY: install
clean:
 rm -f *.o

```

### Auto-Insertion Example

**Before** (with `auto_insert_phony_declarations = true`):

```makefile
# Docker development workflow
setup:
 docker compose down -v
 docker compose up -d
 @echo "Services ready!"

build:
 docker compose build --no-cache

test:
 docker compose exec app npm test

clean:
 docker compose down -v
 docker system prune -af
```

**After:**

```makefile
# Docker development workflow
.PHONY: clean setup test

setup:
 docker compose down -v
 docker compose up -d
 @echo "Services ready!"

build:
 docker compose build --no-cache

test:
 docker compose exec app npm test

clean:
 docker compose down -v
 docker system prune -af

```

### Disable Formatting Example

Disable formatting within a region using special comments that switch formatting in a delimited range.

Use `# bake-format off` to disable formatting for the lines until the next `#bake-format on`, which re-enables formatting.

```makefile
# bake-format off
NO_FORMAT_1= \
      1 \
  45678 \

#bake-format on

# bake-format off : optional comment
NO_FORMAT_2= \
      1 \
  45678 \

#bake-format on
```

---

## CI/CD Integration

Use mbake in continuous integration:

```yaml
# GitHub Actions example
- name: Check Makefile formatting
  run: |
    pip install mbake
    bake format --check Makefile
```

Exit codes:

- `0` - No formatting needed or formatting successful
- `1` - Files need formatting (--check mode) or validation failed
- `2` - Error occurred

---

## Development

### Setup

```bash
git clone https://github.com/ebodshojaei/bake.git
cd mbake
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=bake --cov-report=html

# Run specific test file
pytest tests/test_formatter.py -v
```

### Code Quality

```bash
# Format code
black bake tests

# Lint code
ruff check bake tests

# Type checking
mypy bake
```

---

## Architecture

mbake follows a modular, plugin-based architecture:

```text
bake/
├── __init__.py                 # Package initialization
├── cli.py                      # Command-line interface with subcommands
├── config.py                   # Configuration management
├── core/
│   ├── formatter.py            # Main formatting engine
│   └── rules/                  # Individual formatting rules
│       ├── tabs.py             # Tab/indentation handling
│       ├── spacing.py          # Spacing normalization
│       ├── continuation.py     # Line continuation formatting
│       └── phony.py            # .PHONY declaration management
└── plugins/
    └── base.py                 # Plugin interface
```

### Adding Custom Rules

Extend the `FormatterPlugin` base class:

```python
from bake.plugins.base import FormatterPlugin, FormatResult

class MyCustomRule(FormatterPlugin):
    def __init__(self):
        super().__init__("my_rule", priority=50)
    
    def format(self, lines: List[str], config: dict) -> FormatResult:
        # Your formatting logic here
        return FormatResult(
            lines=modified_lines,
            changed=True,
            errors=[],
            warnings=[]
        )
```

---

## Contributing

Contributions are welcome! Read the [Contributing Guide](CONTRIBUTING.md) for details on development process, submitting pull requests, and reporting issues.

### Quick Start for Contributors

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run the test suite (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Design Philosophy

- **Minimal changes**: Only modify what needs to be fixed, preserve file structure
- **Predictable behavior**: Consistent formatting rules across all Makefiles
- **Fast execution**: Efficient processing of large Makefiles
- **Reliable validation**: Ensure formatted Makefiles have correct syntax
- **Developer-friendly**: Rich CLI with helpful error messages and progress indicators

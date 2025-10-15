# dep-prune
A tool to analyze your Python project's dependencies and identify unused imports.

1. **Reads pyproject.toml** - Supports multiple formats:
   - Poetry (`tool.poetry.dependencies`)
   - PEP 621 standard (`project.dependencies`)
   - PDM format
   - Handles dev dependencies and optional/group dependencies

2. **Scans all Python files** - Recursively finds all `.py` files in your project
   - Automatically excludes common directories (`.git`, `__pycache__`, `venv`, etc.)
   - Uses AST parsing for accurate import detection

3. **Extracts imports** - Finds all:
   - Regular imports: `import package`
   - From imports: `from package import something`
   - Handles nested modules correctly


## Usage:

```bash
# Basic usage (analyze current directory)
uvx dep-prune

# Analyze specific directory
uvx dep-prune /path/to/project

# Specify custom pyproject.toml location
uvx dep-prune --pyproject /custom/path/pyproject.toml

# Verbose mode for detailed output
uvx dep-prune -v
```

## Installation:

You'll need to install the `toml` package to run this tool:
```bash
pip install toml
```

## Example Output:

```
Analyzing project at: /path/to/project
Reading pyproject.toml from: /path/to/project/pyproject.toml

Found dependency groups:
  main: 15 packages
  dev: 8 packages

Found 127 Python files

============================================================
Analyzing main dependencies:
============================================================

✓ Used packages (12):
  • flask
  • numpy
  • pandas
  • requests

⚠ Potentially unused packages (3):
  • some-unused-lib
  • another-unused-package
  • legacy-dependency

Summary for main:
  Total: 15
  Used: 12
  Potentially unused: 3
```

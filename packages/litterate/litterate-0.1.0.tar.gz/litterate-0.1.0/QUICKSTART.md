# Litterate - Quick Start Guide

## Installation

```bash
# Clone or navigate to the project
cd /Users/james/Packages/Literate

# Install dependencies with pixi
pixi install

# Verify installation
pixi run litterate --help
```

## Basic Usage

### 1. Generate Documentation with Defaults

```bash
pixi run litterate
```

This will process all Python files in `./src/**/*.py` and generate documentation in `./docs/`.

**View your documentation:** Simply open `docs/index.html` in your browser. The generated files use relative paths by default, so navigation and styling work perfectly when viewing locally.

### 2. Using a Configuration File

Create `litterate.config.py`:

```python
name = "My Awesome Project"
description = """
A brief description of your project.
Supports **Markdown** formatting!
"""

files = [
    "./src/**/*.py",
    "./scripts/**/*.py",
]

baseURL = "/"  # Or "/project-name" for GitHub Pages
output_directory = "./docs/"
```

Generate docs:

```bash
pixi run litterate --config litterate.config.py
```

### 3. Command-Line Options

```bash
# Specify project name and output
pixi run litterate -n "My Project" -o ./output/

# Process specific files
pixi run litterate src/main.py src/utils.py

# Verbose mode
pixi run litterate -v --config myconfig.py

# Wrap long lines at 80 characters
pixi run litterate -w 80
```

## Writing Annotated Code

Add literate annotations to your Python code:

```python
#> This function calculates the factorial of a number.
#  It uses a recursive approach for clarity.
#
#  **Example:**
#  ```python
#  factorial(5)  # Returns 120
#  ```

def factorial(n):
    # Regular comments are ignored by litterate
    if n <= 1:
        return 1
    return n * factorial(n - 1)
```

## Annotation Syntax

- `#>` - Start of annotation block (configurable)
- `#` - Continuation of annotation (configurable)
- Regular `#` comments without `>` are ignored
- Annotations support full Markdown syntax

## Publishing to GitHub Pages

1. Configure for GitHub Pages:

```python
# litterate.config.py
baseURL = "/your-repo-name"  # Match your repository name
output_directory = "./docs/"
```

2. Generate documentation:

```bash
pixi run litterate --config litterate.config.py
```

3. Commit and push:

```bash
git add docs/
git commit -m "Add generated documentation"
git push
```

4. Enable GitHub Pages:
   - Go to repository Settings
   - Navigate to Pages
   - Select "Deploy from a branch"
   - Choose `main` branch and `/docs` folder
   - Save

Your documentation will be available at `https://username.github.io/repo-name/`

## Development Tasks

```bash
# Run tests
pixi run test

# Lint code
pixi run lint

# Format code
pixi run fmt

# Generate documentation for this project
pixi run docs
```

## Using with Other Languages

Litterate works with any language that has line comments:

### JavaScript/TypeScript

```python
# litterate.config.py
files = ["./src/**/*.js", "./src/**/*.ts"]
annotation_start_mark = "//>"
annotation_continue_mark = "//"
```

### Ruby

```python
files = ["./lib/**/*.rb"]
annotation_start_mark = "#>"
annotation_continue_mark = "#"
```

### Shell Scripts

```python
files = ["./scripts/**/*.sh"]
annotation_start_mark = "#>"
annotation_continue_mark = "#"
```

## Configuration Options Reference

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `name` | str | "My Project" | Project name |
| `description` | str | ... | Project description (Markdown) |
| `files` | list[str] | `["./src/**/*.py"]` | Glob patterns for files |
| `wrap` | int | 0 | Line wrap length (0 = no wrap) |
| `baseURL` | str | "/" | Base URL for generated site |
| `verbose` | bool | False | Verbose output |
| `output_directory` | str | "./docs/" | Output directory |
| `annotation_start_mark` | str | "#>" | Start marker |
| `annotation_continue_mark` | str | "#" | Continuation marker |

## Troubleshooting

### No files found
```bash
# Check your glob patterns
pixi run litterate -v --config litterate.config.py
```

### Import errors
```bash
# Reinstall dependencies
pixi install
```

### Documentation not updating
```bash
# Clean and regenerate
rm -rf docs/
pixi run docs
```

## Examples

Check out the generated documentation for Litterate itself:

```bash
open docs/index.html
```

Or view specific annotated files:
- `docs/src/litterate/generator.py.html` - Core generator logic
- `docs/src/litterate/cli.py.html` - CLI implementation
- `docs/litterate.config.py.html` - Configuration file

## Next Steps

1. ✅ Install pixi and dependencies
2. ✅ Create your configuration file
3. ✅ Add annotations to your code
4. ✅ Generate documentation
5. ✅ View the results in `docs/index.html`
6. ✅ Publish to GitHub Pages (optional)

Happy documenting! 📝✨

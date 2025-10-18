# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Litterate is a Python CLI tool that generates beautiful literate programming-style documentation from comment annotations in source code. It's a complete Python port of the original JavaScript [litterate](https://github.com/thesephist/litterate) tool, built as a modern Python package managed with [pixi](https://prefix.dev).

## Development Commands

### Environment Setup
```bash
pixi install          # Install dependencies
pixi shell            # Activate the environment
```

### Common Tasks
```bash
pixi run test         # Run pytest test suite (13 tests)
pixi run lint         # Run ruff linting checks
pixi run fmt          # Format code with ruff
pixi run docs         # Generate litterate documentation for this project
pixi run litterate    # Run the CLI tool directly
```

### Running Tests
```bash
# Run all tests
pixi run test

# Run specific test file
pytest tests/test_litterate.py

# Run single test
pytest tests/test_litterate.py::test_encode_html
```

### Running the CLI
```bash
# Display LLM-friendly usage guide
pixi run litterate --llm-txt

# With defaults (processes ./src/**/*.py → ./docs/)
pixi run litterate

# With config file
pixi run litterate --config litterate.config.py

# With CLI options
pixi run litterate -n "Project Name" -v -o ./output/

# Process specific files
pixi run litterate src/file1.py src/file2.py
```

## Code Architecture

### Module Structure

The codebase is organized into three core modules in `src/litterate/`:

1. **`cli.py`** (~160 lines) - Command-line interface
   - Entry point via `main()` function
   - Configuration loading from Python or JSON files
   - Configuration merging: defaults → file → CLI args
   - Glob pattern expansion for file matching
   - Uses Click framework for argument parsing

2. **`generator.py`** (~280 lines) - Core documentation generation
   - `generate_litterate_pages()` - Main entry point called by CLI
   - `lines_to_line_pairs()` - Parser that extracts annotations from source
   - `create_and_save_page()` - Processes individual files into HTML
   - `populate_index_page()` - Generates index.html listing all files
   - Language detection from file extensions
   - Uses Jinja2 for templating (templates loaded at module import time)

3. **`defaults.py`** (~40 lines) - Default configuration
   - `DEFAULTS` dictionary with all configurable options
   - Python-first defaults (`#>` markers, `./src/**/*.py` patterns)

### Templates Directory

`src/litterate/templates/` contains:
- `index.html` - Index page template (Jinja2)
- `source.html` - Source file page template (Jinja2)
- `main.css` - Styles for generated documentation

Templates are loaded once at module import time in `generator.py` for performance.

### Key Architectural Patterns

**Annotation Parsing Flow:**
1. Source file read → split into lines
2. `lines_to_line_pairs()` identifies lines starting with `annotation_start_mark` (default: `#>`)
3. Continuation lines start with `annotation_continue_mark` (default: `#`)
4. Annotations are processed as Markdown
5. Code is HTML-escaped and syntax-highlighted
6. Output as tuples: `(doc_html, code_html, line_number)`

**Configuration System:**
- Three-layer merging: defaults → config file → CLI arguments
- Config files can be Python (`.py`) or JSON (`.json`)
- Python configs are dynamically imported; variables become config keys
- CLI args always have highest priority

**Path Handling:**
- Uses `pathlib.Path` throughout (not string paths)
- Output paths mirror source directory structure
- Supports both local viewing (`baseURL=".//"`) and web deployment (`baseURL="/project-name"`)

## Key Dependencies

- **markdown** ≥3.5 - Markdown to HTML conversion (replaces JS `marked`)
- **jinja2** ≥3.1 - Template engine for HTML generation
- **click** ≥8.1 - CLI framework (replaces JS `minimist`)
- **pytest** ≥7.4 - Testing framework
- **ruff** ≥0.1 - Linting and formatting

## Configuration Files

- `pyproject.toml` - Python package metadata, dependencies, tool config
- `pixi.toml` - Pixi-specific configuration and task definitions
- `litterate.config.py` - Example configuration for self-documentation
- `llm.txt` - LLM-friendly usage guide (displayed via `--llm-txt` flag)

## Annotation Syntax

By default, uses Python-style comments:
- `#>` - Start of annotation block
- `#` - Continuation line (must start with `#` after initial `#>`)
- Regular `#` comments are ignored
- Annotations support full Markdown syntax

For other languages (JS/TS):
```python
# In litterate.config.py
annotation_start_mark = "//>"
annotation_continue_mark = "//"
```

## Output Structure

Generated documentation in `./docs/`:
```
docs/
├── index.html              # Landing page with file list
├── main.css                # Styles
└── src/litterate/          # Mirrors source directory structure
    ├── cli.py.html
    ├── generator.py.html
    └── defaults.py.html
```

## Important Implementation Details

**Template Loading:**
- Templates are loaded at module import time in `generator.py` as global constants
- This avoids repeated disk reads but means template changes require reimporting

**baseURL Handling:**
- `"./"` = relative paths for local file viewing
- `"/"` = absolute paths from web root
- `"/project-name"` = GitHub Pages subdirectory deployment
- The code ensures baseURL ends with `/` for proper path joining

**Line Wrapping:**
- `wrap` config option (default: 0 = no wrapping)
- When set to N, wraps code lines to N characters
- Applied after HTML encoding, before syntax highlighting

**Language Detection:**
- Auto-detected from file extension via `detect_language()`
- Maps to Highlight.js language identifiers
- Can be overridden with `language` config option

## Testing

Test file: `tests/test_litterate.py` (13 tests, all passing)

Tests cover:
- HTML encoding (`test_encode_html`)
- Line wrapping (`test_wrap_line_*`)
- Annotation parsing (`test_lines_to_line_pairs_*`)
- Configuration defaults (`test_defaults_*`)
- Output path generation (`test_get_output_path_*`)

## Common Development Patterns

**Adding a new configuration option:**
1. Add to `DEFAULTS` dict in `defaults.py`
2. Add CLI option in `cli.py` `@click.option()`
3. Add merge logic in `cli.py` `main()` function
4. Use in `generator.py` via `config[key]`

**Adding support for a new language:**
1. Add file extension mapping in `detect_language()` in `generator.py`
2. Language identifier should match Highlight.js naming

**Modifying templates:**
1. Edit files in `src/litterate/templates/`
2. Templates use Jinja2 syntax: `{{ variable }}`, `{% if %}`, etc.
3. Restart Python/reimport module to reload templates

## Publishing

This project generates its own documentation which can be published to GitHub Pages:
1. Run `pixi run docs` to generate
2. Commit `docs/` directory
3. Enable GitHub Pages from `docs/` folder in repo settings

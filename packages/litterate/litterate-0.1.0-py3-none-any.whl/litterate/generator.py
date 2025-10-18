#> ## Generator Module
#
# This module contains the bulk of the logic for generating litterate pages.
# It exports a function that the command-line utility calls with configurations.

import html
from pathlib import Path
from typing import Any

import markdown
from jinja2 import Template

#> This isn't optimal, but for now, we read the three template files into memory
# at module load time, so we can reuse them later without repeatedly reading from disk.

TEMPLATE_DIR = Path(__file__).parent / "templates"
INDEX_TEMPLATE = Template((TEMPLATE_DIR / "index.html").read_text())
STYLES_CSS = (TEMPLATE_DIR / "main.css").read_text()
SOURCE_TEMPLATE = Template((TEMPLATE_DIR / "source.html").read_text())


#> ### Language Detection
#
# Detect the programming language from file extension for syntax highlighting.
# If the user specifies a language in the config, we use that instead of auto-detection.

def detect_language(file_path: Path, config: dict[str, Any]) -> str:
    if "language" in config and config["language"] != "auto":
        return config["language"]

    #> Map common file extensions to Highlight.js language identifiers.
    # This covers most popular programming languages.
    ext_map = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".java": "java",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".cxx": "cpp",
        ".c": "c",
        ".h": "c",
        ".hpp": "cpp",
        ".rs": "rust",
        ".go": "go",
        ".rb": "ruby",
        ".php": "php",
        ".sh": "bash",
        ".bash": "bash",
        ".zsh": "bash",
        ".fish": "bash",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
        ".r": "r",
        ".sql": "sql",
        ".html": "html",
        ".xml": "xml",
        ".css": "css",
        ".scss": "scss",
        ".sass": "sass",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".md": "markdown",
        ".rst": "rst",
        ".tex": "latex",
        ".vim": "vim",
        ".lua": "lua",
        ".pl": "perl",
        ".pm": "perl",
    }

    suffix = file_path.suffix.lower()
    return ext_map.get(suffix, "plaintext")


#> ### Helper Functions
#
# These utility functions help with text processing and path management.

#> **Line Wrapping**: Helper function to wrap a given line of text into multiple lines,
# with `limit` characters per line.

def wrap_line(line: str, limit: int) -> str:
    result = []
    for i in range(0, len(line), limit):
        result.append(line[i:i + limit])
    return "\n".join(result)


#> **HTML Encoding**: Escape characters that won't display in HTML correctly,
# like the very common `>`, `<`, and `&` characters in code.

def encode_html(code: str) -> str:
    return html.escape(code)


#> **Path Mapping**: Function that maps a given source file to the path where
# its annotated version will be saved.

def get_output_path_for_source_path(source_path: Path, config: dict[str, Any]) -> Path:
    output_dir = Path(config["output_directory"])
    return output_dir / f"{source_path}.html"


#> ### Index Page Generation
#
# Function to populate the `index.html` page of the generated site with all
# the source links, project name, description, etc.

def populate_index_page(source_files: list[Path], config: dict[str, Any]) -> str:
    output_dir = Path(config["output_directory"])
    base_url = config["baseURL"]

    #> Generate links for each source file, handling both local and web deployment scenarios.
    files_html = []
    for source_path in source_files:
        output_path = get_output_path_for_source_path(source_path, config)
        relative_path = output_path.relative_to(output_dir)

        if base_url == "./":
            link = str(relative_path)
        else:
            link = f"{base_url}{relative_path}"

        files_html.append(
            f'<p class="sourceLink"><a href="{link}">{source_path}</a></p>'
        )

    #> For CSS link, handle baseURL properly.
    # The template appends "main.css", so just pass the directory path.
    css_base = "" if base_url == "./" else base_url

    return INDEX_TEMPLATE.render(
        title=config["name"],
        description=markdown.markdown(config["description"]),
        sourcesList="\n".join(files_html),
        baseURL=css_base,
    )


#> ### Parsing Source Lines
#
# `lines_to_line_pairs` works by having two arrays -- one of the annotation-lineNumber-source line
# tuples, and one buffer for the annotation text being read.

def lines_to_line_pairs(
    lines: list[str], config: dict[str, Any]
) -> list[tuple[str, str, int]]:
    line_pairs = []
    doc_line = ""
    in_annotation_comment = False

    annotation_start = config["annotation_start_mark"]
    annotation_continue = config["annotation_continue_mark"]
    wrap_limit = config["wrap"]

    def process_code_line(code_line: str) -> str:
        encoded = encode_html(code_line)
        if wrap_limit != 0:
            return wrap_line(encoded, wrap_limit)
        return encoded

    def push_pair(code_line: str, line_number: int) -> None:
        nonlocal doc_line

        if doc_line:
            #> Add spacing between annotation blocks for better readability
            if line_pairs and line_pairs[-1][0]:
                line_pairs.append(("", "", ""))
            line_pairs.append(
                (markdown.markdown(doc_line), process_code_line(code_line), line_number)
            )
        else:
            line_pairs.append(("", process_code_line(code_line), line_number))

        doc_line = ""

    def push_comment(line: str) -> None:
        nonlocal doc_line

        if line.strip().startswith(annotation_start):
            doc_line = line.replace(annotation_start, "", 1).strip()
        else:
            doc_line += "\n" + line.replace(annotation_continue, "", 1).strip()

    #> Main parsing loop: iterate through source lines and identify annotation comments
    # vs regular code lines.
    for idx, line in enumerate(lines):
        stripped = line.strip()

        if stripped.startswith(annotation_start):
            in_annotation_comment = True
            push_comment(line)
        elif stripped.startswith(annotation_continue):
            if in_annotation_comment:
                push_comment(line)
            else:
                push_pair(line, idx + 1)
        else:
            if in_annotation_comment:
                in_annotation_comment = False
            push_pair(line, idx + 1)

    return line_pairs


#> ### Page Creation
#
# This function is called for each source file, to process and save
# the Litterate version of the source file in the correct place.

def create_and_save_page(source_path: Path, config: dict[str, Any]) -> None:
    content = source_path.read_text(encoding="utf-8")

    line_pairs = lines_to_line_pairs(content.split("\n"), config)

    language = detect_language(source_path, config)

    #> Generate HTML for each line, combining documentation and source code
    lines_html = []
    for doc, source, line_number in line_pairs:
        lines_html.append(
            f'<div class="line">'
            f'<div class="doc">{doc}</div>'
            f'<pre class="source language-{language}">'
            f'<strong class="lineNumber">{line_number}</strong>'
            f'<code class="language-{language}">{source}</code>'
            f'</pre>'
            f'</div>'
        )

    #> Calculate relative paths for navigation, handling both local file viewing and web deployment
    output_dir = Path(config["output_directory"])
    output_path = get_output_path_for_source_path(source_path, config)
    base_url = config["baseURL"]

    if base_url == "./":
        depth = len(output_path.relative_to(output_dir).parts) - 1
        base_link = "../" * depth if depth > 0 else "./"
        css_link = base_link + "main.css"
    else:
        base_link = base_url
        css_link = f"{base_url}main.css"

    annotated_page = SOURCE_TEMPLATE.render(
        title=str(source_path),
        lines="\n".join(lines_html),
        baseURL=base_link,
        cssURL=css_link,
    )

    #> Save to output directory, creating parent directories as needed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(annotated_page, encoding="utf-8")


#> ### Main Entry Point
#
# This is the main function called by the CLI to generate literate documentation
# for all specified source files.

def generate_litterate_pages(source_files: list[Path], config: dict[str, Any]) -> None:
    output_directory = Path(config["output_directory"])

    output_directory.mkdir(parents=True, exist_ok=True)

    #> Generate and write the index page listing all source files
    index_html = populate_index_page(source_files, config)
    (output_directory / "index.html").write_text(index_html, encoding="utf-8")

    #> Write the CSS stylesheet
    (output_directory / "main.css").write_text(STYLES_CSS, encoding="utf-8")

    #> Process each source file, generating its annotated page
    for source_file in source_files:
        create_and_save_page(source_file, config)
        print(f"Annotated {source_file}")

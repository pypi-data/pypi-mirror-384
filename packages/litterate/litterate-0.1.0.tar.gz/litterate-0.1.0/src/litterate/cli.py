#!/usr/bin/env python3
#> ## Command-line Interface
#
# This is the entry point for the command-line utility,
# focused on handling and processing CLI arguments and
# figuring out the right options to pass to the docs generator.

import importlib.util
import json
import sys
from glob import glob
from pathlib import Path
from typing import Any

import click

from litterate.defaults import DEFAULTS
from litterate.generator import generate_litterate_pages


#> ### LLM Help Display
#
# Callback function to display the llm.txt file when --llm-txt flag is used.
# This provides LLM-friendly documentation for the tool.

def display_llm_txt(ctx: click.Context, param: click.Parameter, value: bool) -> None:
    if not value or ctx.resilient_parsing:
        return

    # Find llm.txt in project root (parent of src/litterate)
    llm_txt_path = Path(__file__).parent.parent.parent / "llm.txt"

    try:
        llm_content = llm_txt_path.read_text(encoding="utf-8")
        click.echo(llm_content)
    except FileNotFoundError:
        click.echo(f"Error: llm.txt not found at {llm_txt_path}", err=True)
        ctx.exit(1)

    ctx.exit(0)


#> ### Configuration Loading
#
# Load configuration from a Python or JSON file. This allows users to
# specify their Litterate configuration in whichever format is most convenient.

def load_config_file(config_path: str) -> dict[str, Any]:
    path = Path(config_path)

    if path.suffix == ".json":
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    elif path.suffix == ".py":
        #> For Python config files, we dynamically load the module and extract configuration
        spec = importlib.util.spec_from_file_location("config", path)
        if spec is None or spec.loader is None:
            raise ValueError(f"Cannot load config from {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        #> Look for CONFIG or config variable, or extract all non-private module attributes
        if hasattr(module, "CONFIG"):
            return module.CONFIG
        elif hasattr(module, "config"):
            return module.config
        else:
            return {
                k: v
                for k, v in module.__dict__.items()
                if not k.startswith("_") and not callable(v)
            }
    else:
        raise ValueError(f"Unsupported config file type: {path.suffix}. Use .py or .json")


#> ### CLI Command Definition
#
# Using Click to define the command-line interface with various options for customization.

@click.command()
@click.option(
    "--llm-txt",
    is_flag=True,
    is_eager=True,
    expose_value=False,
    callback=display_llm_txt,
    help="Display LLM-friendly usage guide and exit",
)
@click.option(
    "--config",
    type=click.Path(exists=True),
    help="Specify a Python or JSON file for configuration",
)
@click.option("-n", "--name", help="Name of your project, shown in the generated site")
@click.option(
    "-d", "--description", help="Description text for your project, shown in the generated site"
)
@click.option(
    "-w",
    "--wrap",
    type=int,
    help="Wrap long lines to N characters (0 = no wrapping)",
)
@click.option(
    "-b",
    "--base-url",
    help="Base URL for the generated site (e.g., /project-name for GitHub Pages)",
)
@click.option("-v", "--verbose", is_flag=True, help="Verbose output while litterate runs")
@click.option(
    "-o",
    "--output",
    help="Destination directory for generated docs (default: ./docs/)",
)
@click.argument("files", nargs=-1, type=click.Path())
def main(
    config: str | None,
    name: str | None,
    description: str | None,
    wrap: int | None,
    base_url: str | None,
    verbose: bool,
    output: str | None,
    files: tuple[str, ...],
) -> None:
    """Litterate - Generate beautiful literate programming-style code annotations.

    Read the full documentation at https://github.com/thesephist/litterate

    \b
    Basic usage:
        litterate --config your-litterate-config.py
        litterate [options] [files]
        (if no files are specified, litterate runs on src/**/*.py)
    """
    #> Configuration merging: Start with defaults, then layer on config file, then CLI args
    merged_config = DEFAULTS.copy()

    if config:
        user_config = load_config_file(config)
        merged_config.update(user_config)

    #> Command-line arguments have highest priority and override everything else
    if name is not None:
        merged_config["name"] = name
    if description is not None:
        merged_config["description"] = description
    if wrap is not None:
        merged_config["wrap"] = wrap
    if base_url is not None:
        merged_config["baseURL"] = base_url
    if verbose:
        merged_config["verbose"] = True
    if output is not None:
        merged_config["output_directory"] = output
    if files:
        merged_config["files"] = list(files)

    #> Expand glob patterns to actual file paths, filtering out directories
    source_files = []
    for glob_pattern in merged_config["files"]:
        try:
            matches = glob(glob_pattern, recursive=True)
            file_matches = [Path(f) for f in matches if Path(f).is_file()]
            source_files.extend(file_matches)
        except Exception as e:
            click.echo(f"Error while looking for matching source files: {e}", err=True)

    #> Ensure baseURL ends with / for proper path joining
    base_url_value = merged_config["baseURL"]
    if not base_url_value.endswith("/"):
        merged_config["baseURL"] = base_url_value + "/"

    if merged_config["verbose"]:
        click.echo(f"Using configuration: {merged_config}")
        click.echo(f"Found {len(source_files)} source files")

    if not source_files:
        click.echo(
            "Warning: No source files found matching the specified patterns", err=True
        )
        sys.exit(1)

    #> Generate the literate documentation pages
    generate_litterate_pages(source_files, merged_config)


if __name__ == "__main__":
    main()

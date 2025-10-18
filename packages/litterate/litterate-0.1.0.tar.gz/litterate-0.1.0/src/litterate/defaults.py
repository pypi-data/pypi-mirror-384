#> ## Default Configuration
#
# This module contains the default configuration if the user doesn't specify
# a value for any options.

DEFAULTS = {
    #> **Project metadata**: Name and description shown on the index page
    "name": "My Project",
    "description": (
        "Replace this description by setting the `description` option on "
        "`litterate`, or leave it blank"
    ),

    #> **Line wrapping**: If 0, long lines of source code will never be wrapped
    "wrap": 0,

    #> **Base URL**: By default, use relative paths for local file viewing.
    # Set to "/" for web root, or "/project-name" for GitHub Pages.
    "baseURL": "./",

    #> **Verbose output**: Control logging verbosity
    "verbose": False,

    #> **Files to process**: It's reasonable to assume that most projects keep
    # the main source files in ./src/, so that's the default files option.
    "files": [
        "./src/**/*.py",
    ],

    #> **Output directory**: We default to ./docs/ because this is where GitHub Pages pulls from.
    "output_directory": "./docs/",

    #> **Annotation markers**: These identify literate comments in the source code.
    # By default, use Python-style comments (#> to start, # to continue).
    "annotation_start_mark": "#>",
    "annotation_continue_mark": "#",

    #> **Syntax highlighting**: Set to "auto" for automatic detection from file extension,
    # or specify a language like "python", "javascript", "java", etc.
    "language": "auto",
}

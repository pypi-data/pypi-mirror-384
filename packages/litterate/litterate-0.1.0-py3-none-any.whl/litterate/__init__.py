"""Litterate - Generate beautiful literate programming-style documentation.

Litterate is a command-line tool to generate beautiful literate programming-style
description of your code from comment annotations.
"""

__version__ = "0.1.0"
__author__ = "James"

from litterate.generator import generate_litterate_pages

__all__ = ["generate_litterate_pages"]

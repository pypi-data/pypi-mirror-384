"""Test suite for Litterate."""

import tempfile
from pathlib import Path

import pytest

from litterate.defaults import DEFAULTS
from litterate.generator import (
    encode_html,
    get_output_path_for_source_path,
    lines_to_line_pairs,
    wrap_line,
)


class TestWrapLine:
    """Tests for the wrap_line function."""

    def test_wrap_basic(self):
        """Test basic line wrapping."""
        result = wrap_line("hello world", 5)
        assert result == "hello\n worl\nd"

    def test_wrap_exact(self):
        """Test wrapping at exact boundary."""
        result = wrap_line("12345", 5)
        assert result == "12345"

    def test_no_wrap_needed(self):
        """Test when line is shorter than limit."""
        result = wrap_line("hi", 10)
        assert result == "hi"


class TestEncodeHTML:
    """Tests for the encode_html function."""

    def test_encode_basic(self):
        """Test basic HTML encoding."""
        result = encode_html("<div>")
        assert result == "&lt;div&gt;"

    def test_encode_ampersand(self):
        """Test ampersand encoding."""
        result = encode_html("a & b")
        assert result == "a &amp; b"

    def test_encode_quotes(self):
        """Test quote encoding."""
        result = encode_html('"hello"')
        assert result == "&quot;hello&quot;"


class TestGetOutputPath:
    """Tests for get_output_path_for_source_path."""

    def test_basic_path(self):
        """Test basic output path generation."""
        config = {"output_directory": "./docs/"}
        source = Path("src/main.py")
        result = get_output_path_for_source_path(source, config)
        assert result == Path("./docs/src/main.py.html")

    def test_nested_path(self):
        """Test nested path generation."""
        config = {"output_directory": "./output/"}
        source = Path("src/utils/helper.py")
        result = get_output_path_for_source_path(source, config)
        assert result == Path("./output/src/utils/helper.py.html")


class TestLinesToLinePairs:
    """Tests for lines_to_line_pairs function."""

    def test_basic_annotation(self):
        """Test basic annotation parsing."""
        lines = [
            "#> This is a comment",
            "# continued",
            "def hello():",
            '    print("world")',
        ]
        config = DEFAULTS.copy()
        result = lines_to_line_pairs(lines, config)

        # Should have annotation + code pairs
        assert len(result) > 0
        # First pair should have annotation
        assert result[0][0] != ""  # Has annotation HTML

    def test_no_annotation(self):
        """Test code without annotations."""
        lines = ["def hello():", '    print("world")']
        config = DEFAULTS.copy()
        result = lines_to_line_pairs(lines, config)

        # All pairs should have empty annotations
        assert all(pair[0] == "" for pair in result)

    def test_multiple_annotations(self):
        """Test multiple annotation blocks."""
        lines = [
            "#> First comment",
            "x = 1",
            "",
            "#> Second comment",
            "y = 2",
        ]
        config = DEFAULTS.copy()
        result = lines_to_line_pairs(lines, config)

        # Should have 3 items: first annotated line, empty line, second annotated line
        assert len(result) == 3
        # Check that we have two annotation blocks
        assert result[0][0] != ""  # First has annotation
        assert result[2][0] != ""  # Third has annotation


class TestDefaults:
    """Tests for default configuration."""

    def test_defaults_exist(self):
        """Test that all required defaults exist."""
        required_keys = [
            "name",
            "description",
            "wrap",
            "baseURL",
            "verbose",
            "files",
            "output_directory",
            "annotation_start_mark",
            "annotation_continue_mark",
        ]
        for key in required_keys:
            assert key in DEFAULTS

    def test_defaults_types(self):
        """Test that defaults have correct types."""
        assert isinstance(DEFAULTS["name"], str)
        assert isinstance(DEFAULTS["wrap"], int)
        assert isinstance(DEFAULTS["verbose"], bool)
        assert isinstance(DEFAULTS["files"], list)

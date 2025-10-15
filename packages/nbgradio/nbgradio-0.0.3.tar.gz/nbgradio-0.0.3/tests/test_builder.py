"""Tests for the builder module."""

import tempfile
from pathlib import Path

from nbgradio.builder import HTMLBuilder, build_notebooks
from nbgradio.parser import NotebookCell


def test_build_full_page():
    """Test building a full HTML page."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        builder = HTMLBuilder(output_dir, mode="local", port=7860)

        # Create test cells
        cells = [
            NotebookCell("markdown", "# Test Page"),
            NotebookCell("code", "print('hello')"),
        ]

        # Build without Gradio cells
        output_file = builder.build_full_page("Test Title", cells, {})

        assert output_file.exists()
        assert output_file.name == "index.html"

        # Check HTML content
        html = output_file.read_text()
        assert "<!DOCTYPE html>" in html
        assert "<title>Test Title</title>" in html
        assert '<main class="nbgradio-content">' in html
        assert "Test Page" in html
        assert "print" in html

        # Check static files
        css_file = output_dir / "static" / "style.css"
        assert css_file.exists()
        css_content = css_file.read_text()
        assert ".nbgradio-content" in css_content
        assert ".cell-markdown" in css_content


def test_build_fragment():
    """Test building an HTML fragment."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        builder = HTMLBuilder(output_dir, mode="local", port=7860)

        # Create test cells
        cells = [
            NotebookCell("markdown", "# Fragment Test"),
            NotebookCell("code", "x = 42"),
        ]

        # Build fragment
        output_file = builder.build_fragment("test_notebook", cells, {})

        assert output_file.exists()
        assert output_file.parent.name == "fragments"
        assert output_file.name == "test_notebook.html"

        # Check fragment content
        html = output_file.read_text()
        assert '<div class="nbgradio-fragment">' in html
        assert "<!DOCTYPE html>" not in html  # Fragment shouldn't have full HTML
        assert "Fragment Test" in html
        # Check for the code content (accounting for HTML escaping)
        assert "42" in html


def test_build_notebooks_single():
    """Test building a single notebook."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        # Create test notebook data
        cells = [
            NotebookCell("markdown", "# Test"),
            NotebookCell("code", "print('test')"),
        ]

        notebook_data = {"test.ipynb": ("Test Notebook", cells, {})}

        # Build full page
        generated_files, actual_port = build_notebooks(
            notebook_data, output_dir, fragment_only=False, mode="local", port=7861
        )

        assert len(generated_files) == 1
        assert generated_files[0].name == "index.html"
        assert generated_files[0].exists()


def test_build_notebooks_fragment_mode():
    """Test building notebooks in fragment mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        # Create test notebook data
        cells = [NotebookCell("markdown", "# Fragment")]

        notebook_data = {
            "nb1.ipynb": ("Notebook 1", cells, {}),
            "nb2.ipynb": ("Notebook 2", cells, {}),
        }

        # Build fragments
        generated_files = build_notebooks(
            notebook_data, output_dir, fragment_only=True, mode="local", port=7860
        )

        assert len(generated_files) == 2

        # Check fragment files
        fragments_dir = output_dir / "fragments"
        assert fragments_dir.exists()
        assert (fragments_dir / "nb1.html").exists()
        assert (fragments_dir / "nb2.html").exists()



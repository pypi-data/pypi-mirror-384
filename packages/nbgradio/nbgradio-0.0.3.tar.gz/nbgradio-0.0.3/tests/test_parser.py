"""Tests for the notebook parser module."""

import tempfile
from pathlib import Path

import nbformat
import pytest

from nbgradio.parser import NotebookCell, NotebookParser, parse_notebooks


def create_test_notebook(content_cells):
    """Helper to create a test notebook with given cells."""
    nb = nbformat.v4.new_notebook()
    for cell_type, source in content_cells:
        if cell_type == "markdown":
            nb.cells.append(nbformat.v4.new_markdown_cell(source))
        elif cell_type == "code":
            nb.cells.append(nbformat.v4.new_code_cell(source))
    return nb


def test_parse_simple_notebook():
    """Test parsing a simple notebook without Gradio cells."""
    parser = NotebookParser()

    # Create a test notebook
    nb = create_test_notebook(
        [
            ("markdown", "# Title"),
            ("code", "print('hello')"),
            ("markdown", "## Section"),
        ]
    )

    with tempfile.NamedTemporaryFile(suffix=".ipynb", delete=False, mode="w") as f:
        nbformat.write(nb, f)
        f.flush()
        test_path = Path(f.name)

    try:
        title, cells, gradio_cells = parser.parse_notebook(test_path)

        assert title == "Title"
        assert len(cells) == 3
        assert len(gradio_cells) == 0

        assert cells[0].cell_type == "markdown"
        assert cells[1].cell_type == "code"
        assert cells[2].cell_type == "markdown"
    finally:
        test_path.unlink()


def test_parse_gradio_notebook():
    """Test parsing a notebook with Gradio cells."""
    parser = NotebookParser()

    # Create a test notebook with Gradio cells
    nb = create_test_notebook(
        [
            ("markdown", "# Gradio Test"),
            (
                "code",
                '#nbgradio name="app1"\nimport gradio as gr\ndemo = gr.Interface(lambda x: x, "text", "text")',
            ),
            ("code", "print('regular code')"),
            ("code", '#nbgradio name="app2"\nimport gradio as gr'),
        ]
    )

    with tempfile.NamedTemporaryFile(suffix=".ipynb", delete=False, mode="w") as f:
        nbformat.write(nb, f)
        f.flush()
        test_path = Path(f.name)

    try:
        title, cells, gradio_cells = parser.parse_notebook(test_path)

        assert title == "Gradio Test"
        assert len(cells) == 4
        assert len(gradio_cells) == 2

        # Check Gradio cells detection
        assert cells[1].is_gradio is True
        assert cells[1].gradio_name == "app1"
        assert cells[2].is_gradio is False
        assert cells[3].is_gradio is True
        assert cells[3].gradio_name == "app2"

        # Check Gradio cells grouping
        assert "app1" in gradio_cells
        assert "app2" in gradio_cells
        assert len(gradio_cells["app1"]) == 1
        assert len(gradio_cells["app2"]) == 1
    finally:
        test_path.unlink()


def test_parse_multiple_same_name_gradio():
    """Test parsing multiple Gradio cells with the same name."""
    parser = NotebookParser()

    nb = create_test_notebook(
        [
            ("code", '#nbgradio name="app"\nimport gradio as gr'),
            ("code", '#nbgradio name="app"\ndef greet(x): return x'),
            (
                "code",
                '#nbgradio name="app"\ndemo = gr.Interface(greet, "text", "text")',
            ),
        ]
    )

    with tempfile.NamedTemporaryFile(suffix=".ipynb", delete=False, mode="w") as f:
        nbformat.write(nb, f)
        f.flush()
        test_path = Path(f.name)

    try:
        title, cells, gradio_cells = parser.parse_notebook(test_path)

        assert len(gradio_cells) == 1
        assert "app" in gradio_cells
        assert len(gradio_cells["app"]) == 3  # All three cells grouped together
    finally:
        test_path.unlink()


def test_parse_notebooks_multiple():
    """Test parsing multiple notebooks."""
    # Create two test notebooks
    nb1 = create_test_notebook([("markdown", "# Notebook 1")])
    nb2 = create_test_notebook([("markdown", "# Notebook 2")])

    paths = []
    for i, nb in enumerate([nb1, nb2], 1):
        with tempfile.NamedTemporaryFile(
            suffix=f"_nb{i}.ipynb", delete=False, mode="w"
        ) as f:
            nbformat.write(nb, f)
            f.flush()
            paths.append(Path(f.name))

    try:
        results = parse_notebooks(paths)
        assert len(results) == 2

        for path in paths:
            assert str(path) in results
            title, cells, _ = results[str(path)]
            assert title in ["Notebook 1", "Notebook 2"]
    finally:
        for path in paths:
            path.unlink()



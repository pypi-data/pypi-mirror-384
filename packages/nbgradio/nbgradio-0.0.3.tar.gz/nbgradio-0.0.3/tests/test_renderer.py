"""Tests for the renderer module."""

from nbgradio.parser import NotebookCell
from nbgradio.renderer import CellRenderer, render_cells


def test_render_markdown_cell():
    """Test rendering markdown cells."""
    renderer = CellRenderer()
    cell = NotebookCell("markdown", "# Title\n\nSome **bold** text.")

    html = renderer.render_cell(cell)

    assert '<div class="cell cell-markdown">' in html
    assert "<h1>Title</h1>" in html
    assert "<strong>bold</strong>" in html


def test_render_code_cell():
    """Test rendering code cells with syntax highlighting."""
    renderer = CellRenderer()
    cell = NotebookCell("code", "def hello():\n    print('world')")

    html = renderer.render_cell(cell)

    assert '<div class="cell cell-code">' in html
    assert "<pre><code>" in html
    assert "highlight" in html  # Pygments adds highlight class


def test_render_gradio_cell():
    """Test rendering Gradio cells as web components."""
    renderer = CellRenderer()

    html = renderer.render_gradio_cell("my_app", "http://localhost:7860/my_app")

    assert 'class="cell cell-gradio"' in html
    assert "<gradio-app" in html
    assert 'src="http://localhost:7860/my_app"' in html
    assert 'class="gradio-app"' in html


def test_render_cells_mixed():
    """Test rendering a mix of cells."""
    cells = [
        NotebookCell("markdown", "# Title"),
        NotebookCell("code", "print('hello')"),
    ]

    # Add a Gradio cell
    gradio_cell = NotebookCell("code", '#nbgradio name="app"\nimport gradio')
    gradio_cell.is_gradio = True
    gradio_cell.gradio_name = "app"
    cells.append(gradio_cell)

    # Without Gradio apps URLs (Gradio cell should be skipped)
    html = render_cells(cells)
    assert "# Title" not in html  # Markdown is rendered
    assert "print" in html  # Regular code is rendered
    assert "import gradio" not in html  # Gradio code is not rendered

    # With Gradio apps URLs
    gradio_apps = {"app": "http://localhost:7860/app"}
    html = render_cells(cells, gradio_apps)

    assert "<h1>Title</h1>" in html
    assert "print" in html
    assert "<gradio-app" in html
    assert 'src="http://localhost:7860/app"' in html
    assert "import gradio" not in html  # Gradio source code should not appear


def test_skip_gradio_rendering():
    """Test that Gradio cells are properly skipped when not deployed."""
    cells = []

    # Regular cell
    cells.append(NotebookCell("code", "print('regular')"))

    # Gradio cell
    gradio_cell = NotebookCell("code", '#nbgradio name="test"\nimport gradio')
    gradio_cell.is_gradio = True
    gradio_cell.gradio_name = "test"
    cells.append(gradio_cell)

    # Another regular cell
    cells.append(NotebookCell("code", "print('another')"))

    # Render without Gradio apps
    html = render_cells(cells, gradio_apps=None)

    # HTML entities are escaped in the output
    assert "print" in html
    assert "regular" in html
    assert "import gradio" not in html  # Gradio code should not appear
    assert "another" in html

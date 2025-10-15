from pathlib import Path
from typing import Dict, List

from .deployer import deploy_gradio_apps
from .parser import NotebookCell
from .renderer import render_cells


class HTMLBuilder:
    """Builds HTML output from parsed notebooks."""

    def __init__(
        self,
        output_dir: Path,
        mode: str = "local",
        port: int = 7860,
        overwrite: bool = False,
        start_server: bool = True,
    ):
        self.output_dir = output_dir
        self.mode = mode
        self.port = port
        self.overwrite = overwrite
        self.start_server = start_server
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def build_full_page(
        self, title: str, cells: List[NotebookCell], gradio_cells: Dict[str, List[str]]
    ) -> Path:
        """
        Build a full HTML page.

        Args:
            title: Page title
            cells: List of notebook cells
            gradio_cells: Dict mapping gradio names to code strings

        Returns:
            Path to the generated HTML file
        """
        gradio_apps = deploy_gradio_apps(
            gradio_cells,
            mode=self.mode,
            port=self.port,
            output_dir=self.output_dir,
            overwrite=self.overwrite,
            start_server=self.start_server,
        )
        gradio_apps, actual_port = gradio_apps
        self.port = actual_port

        cells_html = render_cells(cells, gradio_apps, self.mode)

        html_content = self._create_full_html(title, cells_html)

        output_file = self.output_dir / "index.html"
        output_file.write_text(html_content, encoding="utf-8")

        self._copy_static_assets()

        return output_file

    def build_fragment(
        self,
        notebook_name: str,
        cells: List[NotebookCell],
        gradio_cells: Dict[str, List[str]],
    ) -> Path:
        """
        Build an HTML fragment.

        Args:
            notebook_name: Name of the notebook
            cells: List of notebook cells
            gradio_cells: Dict mapping gradio names to code strings

        Returns:
            Path to the generated HTML fragment
        """
        gradio_apps = deploy_gradio_apps(
            gradio_cells,
            mode=self.mode,
            port=self.port,
            output_dir=self.output_dir,
            overwrite=self.overwrite,
            start_server=self.start_server,
        )
        gradio_apps, actual_port = gradio_apps
        self.port = actual_port

        cells_html = render_cells(cells, gradio_apps, self.mode)

        fragment_html = self._create_fragment_html(cells_html)

        fragments_dir = self.output_dir / "fragments"
        fragments_dir.mkdir(exist_ok=True)

        output_file = fragments_dir / f"{notebook_name}.html"
        output_file.write_text(fragment_html, encoding="utf-8")

        return output_file

    def _create_full_html(self, title: str, cells_html: str) -> str:
        """Create a full HTML page."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="static/style.css">
    <script
        type="module"
        src="https://gradio.s3-us-west-2.amazonaws.com/5.49.1/gradio.js"
    ></script>
</head>
<body>
    <main class="nbgradio-content">
        {cells_html}
    </main>
</body>
</html>"""

    def _create_fragment_html(self, cells_html: str) -> str:
        """Create an HTML fragment."""
        css_content = self._get_css_content()
        return f"""<style>
{css_content}
</style>
<script
    type="module"
    src="https://gradio.s3-us-west-2.amazonaws.com/5.49.1/gradio.js"
></script>
<div class="nbgradio-fragment">
    {cells_html}
</div>"""

    def _copy_static_assets(self):
        """Copy static assets to output directory."""
        static_dir = self.output_dir / "static"
        static_dir.mkdir(exist_ok=True)

        css_content = self._get_css_content()
        css_file = static_dir / "style.css"
        css_file.write_text(css_content, encoding="utf-8")

    def _get_css_content(self) -> str:
        """Get CSS content for styling."""
        from pygments.formatters import HtmlFormatter

        formatter = HtmlFormatter(style="default")
        pygments_css = formatter.get_style_defs(".highlight")

        formatter_dark = HtmlFormatter(style="monokai")
        pygments_css_dark = formatter_dark.get_style_defs(".highlight")

        base_css = """
/* CSS Custom Properties for theming */
:root {
    --bg-color: #ffffff;
    --text-color: #333333;
    --border-color: #e9ecef;
    --code-bg: #e9ecef;
    --markdown-bg: #f8f9fa;
    --markdown-border: #007acc;
    --cell-bg: #f8f9fa;
}

@media (prefers-color-scheme: dark) {
    :root {
        --bg-color: #1a1a1a;
        --text-color: #e0e0e0;
        --border-color: #404040;
        --code-bg: #0f0f11;
        --markdown-bg: #0f0f11;
        --markdown-border: #4a9eff;
        --cell-bg: #0f0f11;
    }
}

/* nbgradio CSS */
body {
    background-color: var(--bg-color);
    color: var(--text-color);
    transition: background-color 0.3s ease, color 0.3s ease;
}

.nbgradio-content {
    max-width: 1200px;
    margin: 0 auto;
    padding: 10px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6;
}

.nbgradio-fragment {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6;
}

.cell {
    margin-bottom: 10px;
    border-radius: 8px;
    overflow: hidden;
}

.cell:first-child {
    margin-top: 20px;
}

.cell-markdown {
    padding: 12px;
    background: var(--markdown-bg);
    border-left: 4px solid var(--markdown-border);
    transition: background-color 0.3s ease;
}

.cell-markdown h1,
.cell-markdown h2,
.cell-markdown h3,
.cell-markdown h4,
.cell-markdown h5,
.cell-markdown h6 {
    margin-top: 0;
    color: var(--text-color);
}

.cell-markdown p {
    margin-bottom: 16px;
    color: var(--text-color);
}

.cell-markdown code {
    background: var(--code-bg);
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    font-size: 0.9em;
    color: var(--text-color);
}

.cell-markdown pre {
    background: var(--markdown-bg);
    padding: 8px;
    border-radius: 8px;
    overflow-x: auto;
    border: 1px solid var(--border-color);
}

.cell-markdown pre code {
    background: none;
    padding: 0;
}

.notebook-content pre {
    background: rgba(0, 0, 0, 0.3);
    border-radius: 8px;
    padding: 1.5rem;
    overflow-x: auto;
    margin-bottom: 1.5rem;
}

.cell-code {
    background: var(--cell-bg);
    border: 1px solid var(--border-color);
    transition: background-color 0.3s ease, border-color 0.3s ease;
}

.cell-code pre {
    margin: 0;
    padding: 8px 8px 0px 8px;
    overflow-x: auto;
}

.cell-code code {
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    font-size: 14px;
    line-height: 1.5;
    color: var(--text-color);
}

.cell-gradio {
    margin-bottom: 10px;
}

.gradio-app {
    width: 100%;
}

.gradio-loading-container {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 40px;
    margin-bottom: 10px;
    background: var(--cell-bg);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    gap: 12px;
}

.gradio-spinner {
    width: 20px;
    height: 20px;
    border: 3px solid #2c2c2c;
    border-top: 3px solid #ff7c00;
    border-radius: 50%;
    animation: gradio-spin 1s linear infinite;
}

.gradio-loading-text {
    color: var(--text-color);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 14px;
    font-weight: 500;
}

@keyframes gradio-spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

@media (prefers-color-scheme: dark) {
    .gradio-spinner {
        border: 3px solid #404040;
        border-top: 3px solid #ff7c00;
    }
}

/* Responsive design */
@media (max-width: 768px) {
    .nbgradio-content {
        padding: 5px;
    }
    
    .cell-markdown,
    .cell-code {
        padding: 8px;
    }
}
"""
        return f"""/* Pygments syntax highlighting - Light theme */
{pygments_css}

/* Pygments syntax highlighting - Dark theme */
@media (prefers-color-scheme: dark) {{
{pygments_css_dark}
}}

/* Override Pygments background in dark mode to match cell background */
@media (prefers-color-scheme: dark) {{
    .highlight {{
        background: #0f0f11 !important;
    }}
}}

{base_css}"""


def build_notebooks(
    notebook_data: Dict[str, tuple],
    output_dir: Path,
    fragment_only: bool = False,
    mode: str = "local",
    port: int = 7860,
    overwrite: bool = False,
    start_server: bool = True,
) -> tuple[List[Path], int]:
    """
    Build HTML output for multiple notebooks.

    Args:
        notebook_data: Dict mapping notebook paths to parsed data
        output_dir: Output directory
        fragment_only: Whether to build fragments only
        mode: Deployment mode
        port: Port for local deployment

    Returns:
        List of generated file paths
    """
    builder = HTMLBuilder(
        output_dir, mode=mode, port=port, overwrite=overwrite, start_server=start_server
    )
    generated_files = []

    for notebook_path, (title, cells, gradio_cells) in notebook_data.items():
        notebook_name = Path(notebook_path).stem

        if fragment_only:
            fragment_file = builder.build_fragment(notebook_name, cells, gradio_cells)
            generated_files.append(fragment_file)
        else:
            full_file = builder.build_full_page(title, cells, gradio_cells)
            generated_files.append(full_file)

    return generated_files, builder.port

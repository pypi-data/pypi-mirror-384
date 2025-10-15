import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse

import nbformat
import requests


class NotebookCell:
    """Represents a parsed notebook cell."""

    def __init__(self, cell_type: str, source: str, cell_id: Optional[str] = None):
        self.cell_type = cell_type
        self.source = source
        self.cell_id = cell_id
        self.is_gradio = False
        self.gradio_name = None


class NotebookParser:
    """Parses Jupyter notebooks and extracts Gradio cells."""

    def __init__(self):
        self.gradio_pattern = re.compile(
            r'#\s*nbgradio\s+name\s*=\s*["\']([^"\']+)["\']'
        )

    def parse_notebook(
        self, notebook_path: Union[str, Path]
    ) -> Tuple[str, List[NotebookCell], Dict[str, List[str]]]:
        """
        Parse a Jupyter notebook file or URL.

        Args:
            notebook_path: Path to notebook file or URL

        Returns:
            Tuple of (notebook_title, list_of_cells, gradio_cells_by_name)
        """
        # Check if it's a URL
        if isinstance(notebook_path, str) and self._is_url(notebook_path):
            nb = self._load_notebook_from_url(notebook_path)
            notebook_path = Path(notebook_path)
        else:
            notebook_path = Path(notebook_path)
            with open(notebook_path, "r", encoding="utf-8") as f:
                nb = nbformat.read(f, as_version=4)

        title = self._extract_title(nb, notebook_path)

        cells = []
        gradio_cells = {}

        for i, cell in enumerate(nb.cells):
            cell_type = cell.cell_type
            source = cell.source

            if isinstance(source, list):
                source = "".join(source)

            notebook_cell = NotebookCell(cell_type, source, cell_id=f"cell_{i}")

            if cell_type == "code":
                match = self.gradio_pattern.search(source)
                if match:
                    gradio_name = match.group(1)
                    notebook_cell.is_gradio = True
                    notebook_cell.gradio_name = gradio_name

                    if gradio_name not in gradio_cells:
                        gradio_cells[gradio_name] = []
                    gradio_cells[gradio_name].append(source)

            cells.append(notebook_cell)

        return title, cells, gradio_cells

    def _extract_title(self, nb: nbformat.NotebookNode, notebook_path: Path) -> str:
        """Extract title from notebook metadata or filename."""
        if "title" in nb.metadata:
            return nb.metadata["title"]

        for cell in nb.cells:
            if cell.cell_type == "markdown":
                source = cell.source
                if isinstance(source, list):
                    source = "".join(source)

                lines = source.split("\n")
                for line in lines:
                    line = line.strip()
                    if line.startswith("# "):
                        return line[2:].strip()
                break

        return notebook_path.stem.replace("_", " ").replace("-", " ").title()

    def _is_url(self, path: str) -> bool:
        """Check if the path is a URL."""
        try:
            result = urlparse(path)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    def _load_notebook_from_url(self, url: str) -> nbformat.NotebookNode:
        """Load a notebook from a URL."""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Try to parse as JSON (raw notebook)
            try:
                return nbformat.reads(response.text, as_version=4)
            except Exception:
                # If that fails, try to extract from GitHub's raw URL
                if "github.com" in url and "/blob/" in url:
                    raw_url = url.replace("/blob/", "/raw/")
                    response = requests.get(raw_url, timeout=30)
                    response.raise_for_status()
                    return nbformat.reads(response.text, as_version=4)
                else:
                    raise ValueError(f"Could not parse notebook from URL: {url}")

        except requests.RequestException as e:
            raise ValueError(f"Failed to fetch notebook from URL {url}: {e}")


def parse_notebooks(
    notebook_paths: List[Union[str, Path]],
) -> Dict[str, Tuple[str, List[NotebookCell], Dict[str, List[str]]]]:
    """
    Parse multiple notebook files or URLs.

    Args:
        notebook_paths: List of notebook paths or URLs

    Returns:
        Dictionary mapping notebook paths/URLs to parsed data
    """
    parser = NotebookParser()
    results = {}

    for notebook_path in notebook_paths:
        try:
            results[str(notebook_path)] = parser.parse_notebook(notebook_path)
        except FileNotFoundError:
            raise  # Re-raise FileNotFoundError as-is
        except Exception as e:
            raise ValueError(f"Failed to parse notebook {notebook_path}: {e}")

    return results

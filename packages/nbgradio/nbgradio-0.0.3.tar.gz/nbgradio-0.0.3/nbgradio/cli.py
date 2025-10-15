import sys
import webbrowser
from pathlib import Path
from typing import List

import click

from .builder import build_notebooks
from .deployer import find_available_port
from .parser import parse_notebooks


@click.group()
def cli():
    """nbgradio - Convert Jupyter notebooks to static HTML websites with live Gradio apps."""
    pass


@cli.command()
@click.argument("notebooks", nargs=-1, type=str)
@click.option(
    "--spaces", is_flag=True, help="Deploy Gradio apps to Hugging Face Spaces"
)
@click.option(
    "--overwrite", is_flag=True, help="Overwrite existing Spaces (use with caution)"
)
@click.option(
    "--fragment", is_flag=True, help="Output HTML fragments instead of full pages"
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default="site",
    help="Output directory for generated files",
)
@click.option("--port", type=int, default=7860, help="Port for local Gradio apps")
@click.option("--theme", help="Theme for the generated site (not implemented)")
@click.option("--no-browser", is_flag=True, help="Don't open browser automatically")
def build(
    notebooks: List[str],
    spaces: bool,
    overwrite: bool,
    fragment: bool,
    output_dir: Path,
    port: int,
    theme: str,
    no_browser: bool,
):
    """
    Build static HTML websites from Jupyter notebooks with live Gradio apps.

    NOTEBOOKS: One or more Jupyter notebook files (.ipynb) or URLs
    """
    mode = "local"  # Default mode

    if not notebooks:
        click.echo("Error: No notebook files specified", err=True)
        sys.exit(1)

    # Validate notebooks (check if local files exist)
    for notebook in notebooks:
        if not notebook.startswith(("http://", "https://")):
            notebook_path = Path(notebook)
            if not notebook_path.exists():
                click.echo(f"Error: Notebook file not found: {notebook}", err=True)
                sys.exit(1)

    try:
        click.echo(f"Parsing {len(notebooks)} notebook(s)...")
        notebook_data = parse_notebooks(notebooks)

        if spaces:
            mode = "spaces"
            click.echo("Deploying to Hugging Face Spaces...")
            generated_files, actual_port = build_notebooks(
                notebook_data=notebook_data,
                output_dir=output_dir,
                fragment_only=fragment,
                mode="spaces",
                port=port,
                overwrite=overwrite,
                start_server=False,
            )
        else:
            click.echo(f"Building HTML output in {output_dir}...")
            generated_files, actual_port = build_notebooks(
                notebook_data=notebook_data,
                output_dir=output_dir,
                fragment_only=fragment,
                mode=mode,
                port=port,
                start_server=False,
            )

        click.echo(f"Successfully generated {len(generated_files)} file(s):")
        for file_path in generated_files:
            click.echo(f"  - {file_path}")

        if mode == "local":
            click.echo("\n✅ Local build completed!")
            click.echo(f"   📄 View the generated HTML: {output_dir}/index.html")
            click.echo(
                f"   🚀 To serve with live apps, run: nbgradio serve {' '.join(notebooks)}"
            )
        else:
            # Spaces mode - just show the generated HTML file
            click.echo("\n✅ HTML generated for Spaces deployment!")
            click.echo(f"   📄 View the generated HTML: {output_dir}/index.html")
            click.echo("   📝 Note: Gradio apps are configured for Spaces deployment")

    except KeyboardInterrupt:
        click.echo("\n👋 Server stopped. Goodbye!")
        sys.exit(0)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("notebooks", nargs=-1, type=str)
@click.option(
    "--spaces", is_flag=True, help="Serve with Spaces configuration (for testing Spaces deployments)"
)
@click.option(
    "--overwrite", is_flag=True, help="Overwrite existing Spaces (use with caution)"
)
@click.option(
    "--fragment", is_flag=True, help="Output HTML fragments instead of full pages"
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default="site",
    help="Output directory for generated files",
)
@click.option("--port", type=int, default=7860, help="Port for local Gradio apps")
@click.option("--theme", help="Theme for the generated site (not implemented)")
@click.option("--no-browser", is_flag=True, help="Don't open browser automatically")
def serve(
    notebooks: List[str],
    spaces: bool,
    overwrite: bool,
    fragment: bool,
    output_dir: Path,
    port: int,
    theme: str,
    no_browser: bool,
):
    """
    Build and serve notebooks with live Gradio apps locally.

    NOTEBOOKS: One or more Jupyter notebook files (.ipynb) or URLs
    """
    mode = "spaces" if spaces else "local"

    if not notebooks:
        click.echo("Error: No notebook files specified", err=True)
        sys.exit(1)

    # Validate notebooks (check if local files exist)
    for notebook in notebooks:
        if not notebook.startswith(("http://", "https://")):
            notebook_path = Path(notebook)
            if not notebook_path.exists():
                click.echo(f"Error: Notebook file not found: {notebook}", err=True)
                sys.exit(1)

    try:
        click.echo(f"Parsing {len(notebooks)} notebook(s)...")
        notebook_data = parse_notebooks(notebooks)

        if spaces:
            click.echo("Deploying to Hugging Face Spaces...")
            generated_files, actual_port = build_notebooks(
                notebook_data=notebook_data,
                output_dir=output_dir,
                fragment_only=fragment,
                mode="spaces",
                port=port,
                overwrite=overwrite,
                start_server=False,
            )
            
            click.echo(f"Successfully generated {len(generated_files)} file(s):")
            for file_path in generated_files:
                click.echo(f"  - {file_path}")

            click.echo("\n✅ Spaces deployment completed!")
            click.echo(f"   📄 View the generated HTML: {output_dir}/index.html")
            click.echo("   📝 Note: Gradio apps are deployed to Spaces")
            click.echo("\n🚀 Serving locally with deployed Spaces...")
            
            # Start a simple HTTP server for testing
            import http.server
            import socketserver
            import os
            
            os.chdir(output_dir)
            
            # Find available port for HTTP server
            server_port = find_available_port(port)
            
            with socketserver.TCPServer(("", server_port), http.server.SimpleHTTPRequestHandler) as httpd:
                click.echo(f"   📖 View your notebook: http://localhost:{server_port}/")
                click.echo("   ⚡ Gradio apps are live on Hugging Face Spaces")
                click.echo("   Press Ctrl+C to stop the server")
                
                # Open browser automatically
                if not no_browser:
                    try:
                        webbrowser.open(f"http://localhost:{server_port}/")
                        click.echo("   🌐 Opening browser...")
                    except Exception:
                        click.echo("   ⚠️  Could not open browser automatically")
                
                try:
                    httpd.serve_forever()
                except KeyboardInterrupt:
                    click.echo("\n👋 Server stopped. Goodbye!")
                    return
        else:
            click.echo(f"Building HTML output in {output_dir}...")
            generated_files, actual_port = build_notebooks(
                notebook_data=notebook_data,
                output_dir=output_dir,
                fragment_only=fragment,
                mode=mode,
                port=port,
                start_server=True,
            )

            click.echo(f"Successfully generated {len(generated_files)} file(s):")
            for file_path in generated_files:
                click.echo(f"  - {file_path}")

            click.echo("\n🚀 Development server ready!")
            click.echo(f"   📖 View your notebook: http://localhost:{actual_port}/")
            click.echo(
                f"   ⚡ Individual Gradio apps available at: http://localhost:{actual_port}/<app_name>"
            )
            click.echo(
                "\n💡 Tip: The main page shows your full notebook with embedded Gradio apps"
            )
            click.echo("   Press Ctrl+C to stop the server")

            # Open browser automatically
            if not no_browser:
                try:
                    webbrowser.open(f"http://localhost:{actual_port}/")
                    click.echo("   🌐 Opening browser...")
                except Exception:
                    click.echo("   ⚠️  Could not open browser automatically")

            try:
                while True:
                    import time

                    time.sleep(1)
            except KeyboardInterrupt:
                click.echo("\n👋 Server stopped. Goodbye!")
                return

    except KeyboardInterrupt:
        click.echo("\n👋 Server stopped. Goodbye!")
        sys.exit(0)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


def main():
    """Main entry point for the nbgradio CLI."""
    cli()


if __name__ == "__main__":
    main()

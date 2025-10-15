import io
import re
import socket
import threading
from pathlib import Path
from typing import Dict, List

import gradio as gr
import huggingface_hub
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from huggingface_hub.errors import RepositoryNotFoundError
from requests import HTTPError


def find_available_port(start_port: int = 7860) -> int:
    """Find the next available port starting from start_port."""
    port = start_port
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("0.0.0.0", port))
                return port
        except OSError:
            port += 1
            if port > 65535:  # Max port number
                raise RuntimeError("No available ports found")


def get_hf_username() -> str:
    """Get the current user's Hugging Face username."""
    try:
        api = huggingface_hub.HfApi()
        user_info = api.whoami()
        return user_info["name"]
    except Exception as e:
        print(f"Error getting HF username: {e}")
        print("Please make sure you're logged in with `huggingface-cli login`")
        raise


def deploy_gradio_space(app_name: str, code_strings: List[str], username: str, overwrite: bool = False) -> str:
    """Deploy a Gradio app to Hugging Face Spaces."""
    space_id = f"{username}/{app_name}"
    
    try:
        # Check if space already exists
        try:
            huggingface_hub.repo_info(space_id, repo_type="space")
            if not overwrite:
                print(f"Space {space_id} already exists. Use --overwrite to replace it.")
                return space_id
            print(f"Overwriting existing space: {space_id}")
        except RepositoryNotFoundError:
            print(f"Creating new space: {space_id}")
            
        # Create or update the space
        try:
            huggingface_hub.create_repo(
                space_id,
                private=False,
                space_sdk="gradio",
                repo_type="space",
                exist_ok=True,
            )
        except HTTPError as e:
            if e.response.status_code in [401, 403]:  # unauthorized or forbidden
                print("Need 'write' access token to create a Spaces repo.")
                huggingface_hub.login(add_to_git_credential=False)
                huggingface_hub.create_repo(
                    space_id,
                    private=False,
                    space_sdk="gradio",
                    repo_type="space",
                    exist_ok=True,
                )
            else:
                raise ValueError(f"Failed to create Space: {e}")
        
        api = huggingface_hub.HfApi()
        
        # Prepare the app code
        full_code = "\n".join(code_strings)
        
        # Remove #nbgradio comments and .launch() calls
        lines = full_code.split("\n")
        nbgradio_pattern = re.compile(r"#\s*nbgradio")
        lines = [line for line in lines if not nbgradio_pattern.match(line.strip())]
        
        modified_lines = []
        for line in lines:
            if ".launch()" in line:
                # Replace .launch() with .launch() for spaces
                modified_lines.append(line.replace(".launch()", ".launch()"))
            else:
                modified_lines.append(line)
        
        app_code = "\n".join(modified_lines)
        
        # Add the launch call at the end if not present
        if not any(".launch()" in line for line in modified_lines):
            app_code += "\n\nif __name__ == '__main__':\n    demo.launch()"
        
        # Create app.py content
        app_py_content = f"""import gradio as gr

{app_code}
"""
        
        # Upload app.py
        app_py_buffer = io.BytesIO(app_py_content.encode("utf-8"))
        api.upload_file(
            path_or_fileobj=app_py_buffer,
            path_in_repo="app.py",
            repo_id=space_id,
            repo_type="space",
        )
        
        # Create requirements.txt with minimal dependencies
        requirements_content = f"gradio>={gr.__version__}"
        requirements_buffer = io.BytesIO(requirements_content.encode("utf-8"))
        api.upload_file(
            path_or_fileobj=requirements_buffer,
            path_in_repo="requirements.txt",
            repo_id=space_id,
            repo_type="space",
        )
        
        # Create README.md
        readme_content = f"""---
title: {app_name}
emoji: 🧩
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: {gr.__version__}
app_file: app.py
pinned: false
tags:
  - nbgradio
---

# {app_name}

This Gradio app was deployed from a Jupyter notebook using [nbgradio](https://github.com/gradio-app/nbgradio).
"""
        readme_buffer = io.BytesIO(readme_content.encode("utf-8"))
        api.upload_file(
            path_or_fileobj=readme_buffer,
            path_in_repo="README.md",
            repo_id=space_id,
            repo_type="space",
        )
        
        print(f"✅ Successfully deployed to: https://huggingface.co/spaces/{space_id}")
        return space_id
        
    except Exception as e:
        print(f"❌ Failed to deploy {app_name}: {e}")
        raise


class GradioAppManager:
    """Manages Gradio app execution and deployment."""

    def __init__(
        self,
        mode: str = "local",
        port: int = 7860,
        output_dir: Path = None,
        overwrite: bool = False,
    ):
        self.mode = mode
        self.requested_port = port
        self.port = find_available_port(port) if mode == "local" else port
        self.output_dir = output_dir or Path("site")
        self.overwrite = overwrite
        self.apps = {}
        self.fastapi_app = None
        self.server_thread = None
        self.server = None

    def execute_gradio_cells(
        self, gradio_cells: Dict[str, List[str]]
    ) -> Dict[str, str]:
        """Execute Gradio cells and return app URLs."""
        if not gradio_cells:
            return {}

        app_urls = {}

        if self.mode == "spaces":
            # Get username from HF API
            try:
                username = get_hf_username()
            except Exception as e:
                print(f"Failed to get HF username: {e}")
                return {}
            
            # Deploy each app to Spaces
            for app_name, code_strings in gradio_cells.items():
                try:
                    space_id = deploy_gradio_space(app_name, code_strings, username, self.overwrite)
                    app_urls[app_name] = space_id
                except Exception as e:
                    print(f"Failed to deploy {app_name}: {e}")
                    continue
        else:
            # Local mode - execute and serve locally
            for app_name, code_strings in gradio_cells.items():
                try:
                    full_code = "\n".join(code_strings)

                    lines = full_code.split("\n")
                    nbgradio_pattern = re.compile(r"#\s*nbgradio")
                    lines = [
                        line for line in lines if not nbgradio_pattern.match(line.strip())
                    ]

                    modified_lines = []
                    for line in lines:
                        if ".launch()" in line:
                            continue
                        modified_lines.append(line)
                    full_code = "\n".join(modified_lines)

                    namespace = {
                        "__builtins__": __builtins__,
                        "gr": gr,
                        "gradio": gr,
                    }

                    exec(full_code, namespace)

                    gradio_app = None
                    for key, value in namespace.items():
                        if isinstance(value, (gr.Interface, gr.Blocks, gr.ChatInterface)):
                            gradio_app = value
                            break

                    if gradio_app is None:
                        continue

                    if hasattr(gradio_app, "dev_mode"):
                        gradio_app.dev_mode = False

                    self.apps[app_name] = gradio_app
                    app_urls[app_name] = f"http://localhost:{self.port}/{app_name}"

                except Exception:
                    continue

        return app_urls

    def start_local_server(self):
        """Start the local FastAPI server with mounted Gradio apps and main page."""
        self.fastapi_app = FastAPI(title="nbgradio Development Server")

        self.fastapi_app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        static_dir = self.output_dir / "static"
        if static_dir.exists():
            self.fastapi_app.mount(
                "/static", StaticFiles(directory=str(static_dir)), name="static"
            )

        for app_name, gradio_app in self.apps.items():
            gr.mount_gradio_app(self.fastapi_app, gradio_app, path=f"/{app_name}")

        index_file = self.output_dir / "index.html"
        if index_file.exists():

            @self.fastapi_app.get("/")
            async def serve_main_page():
                return FileResponse(str(index_file))

        config = uvicorn.Config(
            self.fastapi_app, host="0.0.0.0", port=self.port, log_level="warning"
        )
        self.server = uvicorn.Server(config)

        self.server_thread = threading.Thread(target=self.server.run, daemon=True)
        self.server_thread.start()

        print("✅ nbgradio development server started!")
        if self.port != self.requested_port:
            print(
                f"   ℹ️  Port {self.requested_port} was in use, using port {self.port} instead"
            )
        print(f"   📖 Main page: http://localhost:{self.port}/")
        for app_name in self.apps:
            print(
                f"   ⚡ Gradio app '{app_name}': http://localhost:{self.port}/{app_name}"
            )

    def stop_local_server(self):
        """Stop the local server."""
        if self.server:
            self.server.should_exit = True


_manager = None


def deploy_gradio_apps(
    gradio_cells: Dict[str, List[str]],
    mode: str = "local",
    port: int = 7860,
    output_dir: Path = None,
    overwrite: bool = False,
    start_server: bool = True,
) -> tuple[Dict[str, str], int]:
    """Deploy Gradio apps and return their URLs and the actual port used."""
    global _manager

    if _manager and _manager.server:
        _manager.stop_local_server()
    _manager = GradioAppManager(
        mode=mode, port=port, output_dir=output_dir, overwrite=overwrite
    )

    app_urls = _manager.execute_gradio_cells(gradio_cells)

    if mode == "local" and start_server:
        _manager.start_local_server()

    return app_urls, _manager.port

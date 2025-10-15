<p align="center">        
    <img width="733" height="370" alt="image" src="https://github.com/user-attachments/assets/2cacf9db-6bd0-427f-a7e9-174c4a297831" />
            
</p>


**`nbgradio`**: convert Jupyter notebooks to static HTML websites with **live, embedded Gradio apps**.

## Installation

```bash
pip install nbgradio
```

## Usage

### Quickstart

Try `nbgradio` instantly by running:

```bash
nbgradio serve https://github.com/gradio-app/nbgradio/blob/main/test_notebook.ipynb
```

This will:
- Download [this example notebook](https://github.com/gradio-app/nbgradio/blob/main/test_notebook.ipynb) from GitHub
- Extract the Gradio apps from any cells that contain the Gradio Cell Syntax (`#nbgradio` comment in the first line)
- Start a local FastAPI server at `http://localhost:7860` and launch each Gradio app on a separate page on that server.
- Generate a static HTML site in a `/site` directory with an `index.html` that is served at the root `http://localhost:7860`.

Open your browser to see the result! The notebook contains a simple greeting app that you can interact with.

### With Your Own Notebooks

Create a Jupyter notebook with Gradio cells marked with the `#nbgradio` comment:

```python
#nbgradio name="greet"
import gradio as gr

def greet(name):
    return f"Hello {name}!"

demo = gr.Interface(
    fn=greet,
    inputs=gr.Textbox(label="Your name"),
    outputs=gr.Textbox(label="Greeting")
)

demo.launch()
```

Then build and serve your notebook with live Gradio apps:

```bash
nbgradio serve notebook.ipynb
```

Or just build the static HTML without starting a server:

```bash
nbgradio build notebook.ipynb
```

### More Usage

#### Multiple Notebooks
```bash
nbgradio serve notebook1.ipynb notebook2.ipynb --output-dir my-site
```

#### Fragment Mode (for embedding into an existing websites)
```bash
nbgradio build notebook.ipynb --fragment --output-dir fragments
```

#### Custom Port
```bash
nbgradio serve notebook.ipynb --port 8080
```

### Deploying to Hugging Face Spaces 🔥

Deploy your Gradio apps directly to Hugging Face Spaces for public hosting with the `--spaces` flag:

```bash
nbgradio build notebook.ipynb --spaces
```

This will:
- Prompt you to login to Hugging Face if not already authenticated
- Create Spaces named `{username}/{app_name}` for each Gradio app extracted from the jupyter notebook
- Deploy each app with proper README and `nbgradio` tag
- Return URLs pointing to your live Spaces

#### Why Deploy to Spaces?

**Perfect for Static Hosting**: This is especially useful if you're deploying your static site to platforms like GitHub Pages or a static Hugging Face Space. These platforms can serve your static HTML, but they can't run Python/Gradio apps. By deploying the interactive components to Spaces, you get:

- **Static HTML** → Hosted on GitHub Pages/Static Hugging Face Space (fast, free, always on)
- **Interactive Apps** → Hosted on Spaces with Python runtime and Gradio support
- **Integration** → Web Components automatically connect the two

### Gradio Cell Syntax

Mark cells with `#nbgradio name="app_name"`:

```python
#nbgradio name="calculator"
import gradio as gr

def calculate(operation, a, b):
    if operation == "add":
        return a + b
    elif operation == "multiply":
        return a * b
    return 0

demo = gr.Interface(
    fn=calculate,
    inputs=[
        gr.Radio(["add", "multiply"], label="Operation"),
        gr.Number(label="First number"),
        gr.Number(label="Second number")
    ],
    outputs=gr.Number(label="Result")
)

demo.launch()
```

**Key Points:**
- Multiple cells with the same `name` are concatenated together 
- The `demo.launch()` call is automatically removed

## 📁 Output Structure

```
site/
├── index.html              # Main HTML page
├── fragments/              # HTML fragments (with --fragment)
│   └── notebook_name.html
└── static/
    └── style.css           # CSS with syntax highlighting
```

## 🎨 HTML Output

Generated HTML includes:

- **Markdown cells** → Rendered HTML with styling
- **Code cells** → Syntax-highlighted code blocks
- **Gradio cells** → Live `<gradio-app>` Web Components

```html
<gradio-app src="http://localhost:7860/greet" class="gradio-app"></gradio-app>
```

## ⚙️ CLI Reference

### `nbgradio serve` - Build and serve with live Gradio apps

```bash
nbgradio serve [OPTIONS] NOTEBOOKS...
```

**NOTEBOOKS:** One or more Jupyter notebook files (.ipynb) or URLs

**Options:**
- `--spaces` - Serve with Spaces configuration (for testing Spaces deployments)
- `--overwrite` - Overwrite existing Spaces (use with caution)
- `--output-dir PATH` - Output directory (default: site)
- `--port INTEGER` - Port for local Gradio apps (default: 7860)
- `--fragment` - Output HTML fragments instead of full pages
- `--no-browser` - Don't open browser automatically

### `nbgradio build` - Build static HTML only

```bash
nbgradio build [OPTIONS] NOTEBOOKS...
```

**NOTEBOOKS:** One or more Jupyter notebook files (.ipynb) or URLs

**Options:**
- `--spaces` - Deploy Gradio apps to Hugging Face Spaces
- `--overwrite` - Overwrite existing Spaces (use with caution)
- `--fragment` - Output HTML fragments instead of full pages
- `--output-dir PATH` - Output directory (default: site)
- `--port INTEGER` - Port for local Gradio apps (default: 7860)

## 📄 Requirements

- Python ≥ 3.10
- Jupyter notebooks with nbformat ≥ 5.0
- Gradio ≥ 5.0

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🔗 Links

- [GitHub Repository](https://github.com/gradio-app/nbgradio)
- [PyPI Package](https://pypi.org/project/nbgradio/)
- [Gradio Documentation](https://gradio.app/docs/)
- The excellent [nbconvert](https://nbconvert.readthedocs.io/en/latest/) and [nbdev](https://nbdev.fast.ai/) projects, which provided inspiration for `nbgradio`!

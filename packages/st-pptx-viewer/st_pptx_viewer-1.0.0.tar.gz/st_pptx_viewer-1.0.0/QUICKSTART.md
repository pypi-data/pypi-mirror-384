# Quick Start Guide

Get started with `st_pptx_viewer` in 5 minutes!

## Prerequisites

- Python 3.8 or higher
- Streamlit installed (`pip install streamlit`)
- Internet connection (for CDN)

**Note:** No build step required! The module uses CDN-hosted PptxViewJS.

## Step 1: Install the Module

### Option A: Development Install (Recommended for testing)
```bash
pip install -e ./st_pptx_viewer
```

### Option B: Copy to your project
```bash
cp -r st_pptx_viewer /path/to/your/project/
```

## Step 2: Create Your First App

Create a file called `my_viewer.py`:

```python
import streamlit as st
from st_pptx_viewer import pptx_viewer

st.set_page_config(page_title="My PPTX Viewer", layout="wide")
st.title("📊 My PPTX Viewer")

uploaded = st.file_uploader("Upload a PPTX file", type=["pptx"])
if uploaded:
    pptx_viewer(uploaded)
```

## Step 3: Run It!

```bash
streamlit run my_viewer.py
```

Your browser will open automatically. Upload a .pptx file and see it render!

## Next Steps

### Add Configuration

Customize the viewer with more options:

```python
from st_pptx_viewer import pptx_viewer, PptxViewerConfig

config = PptxViewerConfig(
    width=1200,
    show_toolbar=True,
    enable_keyboard=True,
    enable_fullscreen=True,
)

pptx_viewer(uploaded, config=config)
```

### Try the Examples

Explore pre-built examples:

```bash
# Basic example
streamlit run st_pptx_viewer/examples/basic_example.py

# Advanced configuration
streamlit run st_pptx_viewer/examples/advanced_example.py

# Side-by-side comparison
streamlit run st_pptx_viewer/examples/compare_presentations.py

# Custom styling and themes
streamlit run st_pptx_viewer/examples/custom_styling.py
```

### Load from File Path

Instead of uploading, load directly from a file:

```python
from pathlib import Path
from st_pptx_viewer import pptx_viewer

pptx_path = Path("./presentations/my_presentation.pptx")
pptx_viewer(pptx_path)
```

## Common Issues

### ❌ "Module not found"
**Solution**: Install the module with `pip install -e ./st_pptx_viewer`

### ❌ "Failed to load PptxViewJS from CDN"
**Solution**: Check your internet connection. The module loads from CDN by default.

### ❌ Want to use a local bundle?
**Solution**: Specify `pptxviewjs_path` in configuration:
```python
config = PptxViewerConfig(
    pptxviewjs_path="/path/to/PptxViewJS.min.js"
)
```

### ❌ Presentation won't render
**Solution**: Check the browser console for errors. Ensure the PPTX file is valid.

## Configuration Cheat Sheet

```python
PptxViewerConfig(
    width=960,                    # Canvas width in pixels
    height=None,                  # Auto-calculated if None
    show_toolbar=True,            # Show prev/next buttons
    show_slide_counter=True,      # Show "Slide X / Y"
    initial_slide=0,              # Starting slide (0-based)
    enable_keyboard=True,         # Arrow key navigation
    toolbar_position='top',       # 'top' or 'bottom'
    enable_fullscreen=False,      # Fullscreen button
    canvas_border='1px solid #ddd',  # CSS border
    canvas_background='#fff',     # Background color
    canvas_border_radius=4,       # Border radius in px
    custom_css='',                # Additional CSS
)
```

## More Help

- [Full README](README.md) - Complete documentation
- [Examples](examples/README.md) - More example apps
- [GitHub Issues](https://github.com/yourusername/js-slide-viewer/issues) - Report bugs

## Minimal Complete Example

Here's everything you need in one file:

```python
import streamlit as st
from st_pptx_viewer import pptx_viewer, PptxViewerConfig

st.title("PPTX Viewer")

# Sidebar configuration
width = st.sidebar.slider("Width", 600, 1600, 960)
show_toolbar = st.sidebar.checkbox("Show toolbar", True)

# File upload
uploaded = st.file_uploader("Upload PPTX", type=["pptx"])

# Render
if uploaded:
    config = PptxViewerConfig(width=width, show_toolbar=show_toolbar)
    pptx_viewer(uploaded, config=config)
```

That's it! You're ready to build amazing presentation viewers with Streamlit! 🚀


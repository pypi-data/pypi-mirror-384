# st_pptx_viewer

A powerful and configurable Streamlit component for rendering PowerPoint presentations using the PptxViewJS library.

## Features

- 🎨 **Fully Customizable**: Control canvas size, toolbar position, colors, and more
- ⌨️ **Keyboard Navigation**: Arrow keys and Page Up/Down support
- 📱 **Responsive Design**: Automatically adapts to slide aspect ratios
- 🎯 **Easy Integration**: Simple API with sensible defaults
- 🔧 **Flexible Configuration**: Dataclass-based configuration for type safety
- ⛶ **Fullscreen Mode**: Optional fullscreen viewing
- 🎭 **Custom Styling**: Add your own CSS for complete control
- 🚀 **No Build Required**: Uses CDN-hosted PptxViewJS

## Quick Start (5 Minutes!)

### Prerequisites

- Python 3.8 or higher
- Streamlit installed (`pip install streamlit`)
- Internet connection (for CDN)

### Step 1: Install

```bash
pip install -e ./st_pptx_viewer
```

Or use the automated installer:
```bash
cd st_pptx_viewer
./install.sh
```

### Step 2: Create Your First App

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

### Step 3: Run It!

```bash
streamlit run my_viewer.py
```

Your browser will open automatically. Upload a .pptx file and see it render!

## Installation

### Quick Install (Recommended)
```bash
cd /path/to/st_pptx_viewer
./install.sh
```

### Manual Install
```bash
# 1. Install dependencies
pip install streamlit

# 2. Install module
pip install -e ./st_pptx_viewer
```

### From PyPI (when published)
```bash
pip install st-pptx-viewer
```

**Note:** No build step required! The module uses CDN-hosted PptxViewJS.

## Basic Usage

### Minimal Example (3 lines!)

```python
import streamlit as st
from st_pptx_viewer import pptx_viewer

uploaded = st.file_uploader("Upload PPTX", type=["pptx"])
if uploaded:
    pptx_viewer(uploaded)
```

### With Configuration

```python
import streamlit as st
from st_pptx_viewer import pptx_viewer, PptxViewerConfig

# Create custom configuration
config = PptxViewerConfig(
    width=1700,              # Recommended for wide layouts
    show_toolbar=True,
    show_slide_counter=True,
    enable_keyboard=True,
    toolbar_position='bottom',
    enable_fullscreen=True,
    canvas_border='2px solid #0066cc',
    canvas_background='#f5f5f5',
)

uploaded_file = st.file_uploader("Upload a PPTX file", type=["pptx"])
if uploaded_file:
    pptx_viewer(uploaded_file, config=config)
```

### From File Path

```python
from pathlib import Path
from st_pptx_viewer import pptx_viewer

# Load from file path
pptx_path = Path("./presentations/demo.pptx")
pptx_viewer(pptx_path)
```

## Configuration Options

The `PptxViewerConfig` dataclass provides comprehensive configuration options:

### Display Options
```python
PptxViewerConfig(
    width=1200,               # Canvas width in pixels (default: 1200)
    height=None,              # Auto-calculated if None
    component_height=None,    # Total iframe height
)
```

**Recommended widths:**
- Normal layout: 1200px (default)
- Wide layout (`st.set_page_config(layout="wide")`): 1600-1800px

### Toolbar Options
```python
PptxViewerConfig(
    show_toolbar=True,        # Show navigation toolbar
    show_slide_counter=True,  # Show "Slide X / Y"
    toolbar_position='top',   # 'top' or 'bottom'
    toolbar_style={           # Custom CSS styles
        'background': '#f8f9fa',
        'padding': '12px',
    },
)
```

### Navigation Options
```python
PptxViewerConfig(
    initial_slide=0,          # Starting slide (0-based)
    enable_keyboard=True,     # Arrow key navigation
    enable_fullscreen=False,  # Fullscreen button
)
```

### Styling Options
```python
PptxViewerConfig(
    canvas_border='1px solid #ddd',    # CSS border
    canvas_background='#fff',           # Background color
    canvas_border_radius=4,             # Border radius in px
    custom_css="""                      # Additional CSS
        .toolbar button {
            background: blue !important;
        }
    """,
)
```

### Advanced Options
```python
PptxViewerConfig(
    pptxviewjs_path=None,     # Custom path to bundle (uses CDN if None)
)
```

### All Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `width` | int | 1200 | Canvas width in pixels |
| `height` | int\|None | None | Canvas height (auto-calculated from aspect ratio if None) |
| `show_toolbar` | bool | True | Show navigation toolbar |
| `show_slide_counter` | bool | True | Show "Slide X / Y" counter |
| `initial_slide` | int | 0 | Initial slide index (0-based) |
| `enable_keyboard` | bool | True | Enable keyboard navigation |
| `toolbar_position` | str | 'top' | Toolbar position: 'top' or 'bottom' |
| `canvas_border` | str | '1px solid #ddd' | CSS border style for canvas |
| `canvas_background` | str | '#fff' | Background color for canvas |
| `canvas_border_radius` | int | 4 | Border radius in pixels |
| `component_height` | int\|None | None | Total component height (auto-calculated if None) |
| `custom_css` | str | '' | Additional custom CSS styles |
| `pptxviewjs_path` | str\|Path\|None | None | Custom path to PptxViewJS.min.js (uses CDN if None) |
| `enable_fullscreen` | bool | False | Show fullscreen button |
| `toolbar_style` | dict | {} | Custom CSS styles for toolbar |

## Common Usage Patterns

### Pattern 1: File Upload
```python
import streamlit as st
from st_pptx_viewer import pptx_viewer

uploaded = st.file_uploader("Upload PPTX", type=["pptx"])
if uploaded:
    pptx_viewer(uploaded)
```

### Pattern 2: From File Path
```python
from pathlib import Path
from st_pptx_viewer import pptx_viewer

pptx_path = Path("./presentations/demo.pptx")
pptx_viewer(pptx_path)
```

### Pattern 3: Multiple Viewers (Side-by-Side)
```python
col1, col2 = st.columns(2)

with col1:
    st.subheader("Presentation A")
    pptx_viewer(file_a, key="viewer_a")

with col2:
    st.subheader("Presentation B")
    pptx_viewer(file_b, key="viewer_b")
```

### Pattern 4: Dynamic Configuration
```python
# Sidebar controls
width = st.sidebar.slider("Width", 600, 1800, 1200)
show_toolbar = st.sidebar.checkbox("Toolbar", True)

config = PptxViewerConfig(width=width, show_toolbar=show_toolbar)
pptx_viewer(uploaded, config=config)
```

### Pattern 5: Start at Specific Slide
```python
slide_number = st.number_input("Start at slide", min_value=1, value=1)
config = PptxViewerConfig(initial_slide=slide_number - 1)  # 0-based
pptx_viewer(uploaded, config=config)
```

### Pattern 6: Minimal Viewer (No UI)
```python
config = PptxViewerConfig(
    show_toolbar=False,
    canvas_border='none',
)
pptx_viewer(uploaded, config=config)
```

### Pattern 7: With Session State
```python
if 'current_config' not in st.session_state:
    st.session_state.current_config = PptxViewerConfig(width=1200)

# User can modify config
width = st.slider("Width", 600, 1800, st.session_state.current_config.width)
st.session_state.current_config.width = width

pptx_viewer(uploaded, config=st.session_state.current_config)
```

### Pattern 8: Multiple Presentations in Tabs
```python
# Use tabs to avoid rendering all at once
tab1, tab2, tab3 = st.tabs(["Deck 1", "Deck 2", "Deck 3"])

with tab1:
    pptx_viewer(file1, key="deck1")
with tab2:
    pptx_viewer(file2, key="deck2")
with tab3:
    pptx_viewer(file3, key="deck3")
```

## Input Formats

The `pptx_viewer()` function accepts multiple input formats:

### 1. UploadedFile (from st.file_uploader)
```python
uploaded = st.file_uploader("Upload", type=["pptx"])
pptx_viewer(uploaded)
```

### 2. Bytes
```python
with open("presentation.pptx", "rb") as f:
    data = f.read()
pptx_viewer(data)
```

### 3. File Path (str or Path)
```python
# String path
pptx_viewer("./presentations/demo.pptx")

# Path object
from pathlib import Path
pptx_viewer(Path("demo.pptx"))
```

### 4. File-like Object
```python
with open("presentation.pptx", "rb") as f:
    pptx_viewer(f)
```

## Keyboard Shortcuts

When `enable_keyboard=True` (default), the following shortcuts are available:

| Key | Action |
|-----|--------|
| Arrow Left | Previous slide |
| Arrow Right | Next slide |
| Page Up | Previous slide |
| Page Down | Next slide |
| Space | Next slide |

## Custom Styling Examples

### Basic Border Customization
```python
config = PptxViewerConfig(
    width=1200,
    canvas_border='2px solid #0066cc',
    canvas_border_radius=8,
)
pptx_viewer(uploaded, config=config)
```

### Toolbar Styling
```python
config = PptxViewerConfig(
    toolbar_style={
        'background': 'linear-gradient(to right, #667eea, #764ba2)',
        'padding': '12px',
        'border-radius': '8px',
    },
)
pptx_viewer(uploaded, config=config)
```

### Button Styling with Custom CSS
```python
config = PptxViewerConfig(
    custom_css="""
        .toolbar button {
            background: #0066cc !important;
            color: white !important;
            border: none !important;
            border-radius: 6px;
            font-weight: 600;
            padding: 8px 16px;
        }
        .toolbar button:hover {
            background: #0052a3 !important;
            transform: translateY(-1px);
        }
        .toolbar button:disabled {
            opacity: 0.5 !important;
        }
    """,
)
pptx_viewer(uploaded, config=config)
```

### Dark Theme Example
```python
DARK_THEME = PptxViewerConfig(
    width=1200,
    canvas_background='#1e1e1e',
    canvas_border='1px solid #444',
    toolbar_style={
        'background': '#2d2d2d',
        'border-bottom': '1px solid #444',
    },
    custom_css="""
        .toolbar button {
            background: #3d3d3d !important;
            color: #e0e0e0 !important;
            border: 1px solid #555 !important;
        }
        .toolbar button:hover {
            background: #4d4d4d !important;
        }
        .status {
            color: #aaa !important;
        }
    """,
)

pptx_viewer(uploaded, config=DARK_THEME)
```

### Corporate Theme Example
```python
CORPORATE_THEME = PptxViewerConfig(
    width=1200,
    canvas_border='3px solid #0066cc',
    canvas_border_radius=12,
    toolbar_style={
        'background': '#0066cc',
        'color': 'white',
    },
    custom_css="""
        .toolbar button {
            background: white !important;
            color: #0066cc !important;
            font-weight: bold;
        }
        .toolbar button:hover {
            background: #f0f0f0 !important;
        }
    """,
)

pptx_viewer(uploaded, config=CORPORATE_THEME)
```

## Advanced Examples

### Complete Interactive Example

```python
import streamlit as st
from st_pptx_viewer import pptx_viewer, PptxViewerConfig

st.set_page_config(page_title="PPTX Viewer", layout="wide")
st.title("📊 Interactive PPTX Viewer")

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Settings")
    width = st.slider("Canvas Width", 600, 1800, 1200)
    show_toolbar = st.checkbox("Show Toolbar", True)
    show_counter = st.checkbox("Show Slide Counter", True)
    enable_keyboard = st.checkbox("Keyboard Navigation", True)
    enable_fullscreen = st.checkbox("Fullscreen Button", False)
    
    toolbar_pos = st.selectbox("Toolbar Position", ["top", "bottom"])
    
    st.subheader("Styling")
    border_color = st.color_picker("Border Color", "#dddddd")
    bg_color = st.color_picker("Background Color", "#ffffff")

# File upload
uploaded = st.file_uploader("Upload a PPTX file", type=["pptx"])

# Render with configuration
if uploaded:
    config = PptxViewerConfig(
        width=width,
        show_toolbar=show_toolbar,
        show_slide_counter=show_counter,
        enable_keyboard=enable_keyboard,
        enable_fullscreen=enable_fullscreen,
        toolbar_position=toolbar_pos,
        canvas_border=f"2px solid {border_color}",
        canvas_background=bg_color,
    )
    pptx_viewer(uploaded, config=config)
else:
    st.info("👆 Upload a .pptx file to get started")
```

### Loading Indicator for Large Files

```python
import streamlit as st
from st_pptx_viewer import pptx_viewer, PptxViewerConfig

uploaded = st.file_uploader("Upload PPTX", type=["pptx"])

if uploaded:
    with st.spinner("Loading presentation..."):
        config = PptxViewerConfig(width=1200)
        pptx_viewer(uploaded, config=config)
```

## API Reference

### `pptx_viewer(pptx_file, config=None, key=None)`

Main function to render a PPTX file in Streamlit.

**Parameters:**
- `pptx_file` (bytes | BinaryIO | str | Path): PPTX file as bytes, file-like object, or path
- `config` (PptxViewerConfig | None): Configuration options (default: None, uses defaults)
- `key` (str | None): Unique component key for Streamlit (default: None)

**Returns:** None

**Example:**
```python
pptx_viewer(file, config=PptxViewerConfig(width=1200), key="my_viewer")
```

### `PptxViewerConfig`

Dataclass for viewer configuration. See Configuration Options section above for all parameters.

**Example:**
```python
config = PptxViewerConfig(
    width=1200,
    show_toolbar=True,
    enable_keyboard=True,
    custom_css=".toolbar { background: blue; }"
)
```

## Troubleshooting

### Installation Issues

**Problem: "Module not found"**

**Solution:**
```bash
pip install -e ./st_pptx_viewer
```

### CDN Loading Issues

**Problem: "Failed to load PptxViewJS from CDN"**

**Solutions:**
1. Check your internet connection
2. Verify CDN is accessible: https://cdn.jsdelivr.net/npm/pptxviewjs/dist/PptxViewJS.min.js
3. Use a local bundle instead:

```python
config = PptxViewerConfig(
    pptxviewjs_path="/path/to/PptxViewJS.min.js"
)
pptx_viewer(uploaded, config=config)
```

### Presentation Not Rendering

**Checklist:**
1. Ensure the PPTX file is valid and not corrupted
2. Check browser console (F12) for JavaScript errors
3. Try with a simpler presentation first
4. Verify file is actually a .pptx format

**Solution for debugging:**
```python
# Check file details
if uploaded:
    st.write(f"File name: {uploaded.name}")
    st.write(f"File size: {uploaded.size} bytes")
    st.write(f"File type: {uploaded.type}")
```

### Layout Issues

**Problem: Slides appear cut off or content is missing**

**Solution:** Increase the width parameter, especially when using `layout="wide"`:

```python
# For wide layouts, use 1600-1800px
st.set_page_config(layout="wide")
config = PptxViewerConfig(width=1700)
pptx_viewer(uploaded, config=config)
```

**Other layout adjustments:**
- Adjust `width` and `height` in configuration
- Use `component_height` to control total iframe height
- Add custom CSS via `custom_css` parameter

### Styling Not Applying

**Solutions:**
1. Use `!important` in CSS:
   ```python
   custom_css=".toolbar button { background: red !important; }"
   ```
2. Check CSS syntax is valid
3. Inspect in browser dev tools (F12)
4. Verify CSS is in `custom_css` parameter

### Multiple Viewers Conflicting

**Problem:** Two viewers interfering with each other

**Solution:** Use unique keys:
```python
pptx_viewer(file1, key="viewer1")
pptx_viewer(file2, key="viewer2")
```

### Keyboard Shortcuts Not Working

**Solution:** Ensure keyboard navigation is enabled:
```python
config = PptxViewerConfig(enable_keyboard=True)
pptx_viewer(file, config=config)
```

### Viewer Too Small/Large

**Solution:** Adjust width and height:
```python
config = PptxViewerConfig(
    width=1200,      # Adjust canvas width
    height=675,      # Or None for auto
)
pptx_viewer(uploaded, config=config)
```

## Performance Tips

### For Large Files
```python
# Show loading message
with st.spinner("Loading presentation..."):
    pptx_viewer(large_file)
```

### Cache Configuration
```python
@st.cache_resource
def get_viewer_config():
    return PptxViewerConfig(width=1200, enable_keyboard=True)

config = get_viewer_config()
pptx_viewer(uploaded, config=config)
```

### For Multiple Viewers
Use tabs to avoid rendering all at once:
```python
tab1, tab2, tab3 = st.tabs(["Deck 1", "Deck 2", "Deck 3"])
with tab1:
    pptx_viewer(file1, key="deck1")
with tab2:
    pptx_viewer(file2, key="deck2")
with tab3:
    pptx_viewer(file3, key="deck3")
```

## Examples

The package includes several example applications in the `examples/` directory:

```bash
# Basic example - minimal usage
streamlit run st_pptx_viewer/examples/basic_example.py

# Advanced example - all configuration options
streamlit run st_pptx_viewer/examples/advanced_example.py

# Compare example - side-by-side comparison
streamlit run st_pptx_viewer/examples/compare_presentations.py

# Styling example - theme gallery
streamlit run st_pptx_viewer/examples/custom_styling.py
```

## Requirements

- Python >= 3.8
- Streamlit >= 1.0.0
- Internet connection (for CDN-hosted PptxViewJS)

## Contributing

Contributions are welcome! Please see the main project repository for contribution guidelines.

## Related Projects

- [PptxViewJS](https://github.com/gptsci/js-slide-viewer) - The underlying JavaScript library
- [Streamlit](https://streamlit.io) - The web framework this component is built for

## Support

For issues and questions:
- GitHub Issues: [Report a bug](https://github.com/gptsci/js-slide-viewer/issues)
- Documentation: See examples in the `examples/` directory

---

**That's it! You're ready to build amazing presentation viewers with Streamlit!** 🚀

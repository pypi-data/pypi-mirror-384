# st_pptx_viewer Usage Guide

## Installation

### Quick Install (Recommended)
```bash
cd /path/to/js-slide-viewer/st_pptx_viewer
./install.sh
```

### Manual Install
```bash
# 1. Install dependencies
pip install streamlit

# 2. Install module
pip install -e ./st_pptx_viewer
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
from st_pptx_viewer import pptx_viewer, PptxViewerConfig

config = PptxViewerConfig(
    width=1200,
    show_toolbar=True,
    enable_keyboard=True,
)

pptx_viewer(uploaded_file, config=config)
```

## Configuration Options Reference

### Display Options
```python
PptxViewerConfig(
    width=960,                # Canvas width in pixels
    height=None,              # Auto-calculated if None
    component_height=None,    # Total iframe height
)
```

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
    pptxviewjs_path=None,     # Custom path to bundle
)
```

## Common Patterns

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

### Pattern 3: Multiple Viewers
```python
col1, col2 = st.columns(2)

with col1:
    pptx_viewer(file_a, key="viewer_a")

with col2:
    pptx_viewer(file_b, key="viewer_b")
```

### Pattern 4: Dynamic Configuration
```python
width = st.sidebar.slider("Width", 600, 1600, 960)
show_toolbar = st.sidebar.checkbox("Toolbar", True)

config = PptxViewerConfig(width=width, show_toolbar=show_toolbar)
pptx_viewer(uploaded, config=config)
```

### Pattern 5: Custom Theme
```python
CORPORATE_THEME = PptxViewerConfig(
    width=1000,
    canvas_border='3px solid #0066cc',
    toolbar_style={
        'background': '#0066cc',
        'color': 'white',
    },
    custom_css="""
        .toolbar button {
            background: white !important;
            color: #0066cc !important;
        }
    """,
)

pptx_viewer(uploaded, config=CORPORATE_THEME)
```

### Pattern 6: Start at Specific Slide
```python
slide_number = st.number_input("Start at slide", min_value=1, value=1)
config = PptxViewerConfig(initial_slide=slide_number - 1)  # 0-based
pptx_viewer(uploaded, config=config)
```

### Pattern 7: Minimal Viewer (No UI)
```python
config = PptxViewerConfig(
    show_toolbar=False,
    canvas_border='none',
)
pptx_viewer(uploaded, config=config)
```

### Pattern 8: With Session State
```python
if 'current_config' not in st.session_state:
    st.session_state.current_config = PptxViewerConfig(width=960)

# User can modify config
width = st.slider("Width", 600, 1600, st.session_state.current_config.width)
st.session_state.current_config.width = width

pptx_viewer(uploaded, config=st.session_state.current_config)
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

When `enable_keyboard=True` (default):

| Key | Action |
|-----|--------|
| Arrow Left | Previous slide |
| Arrow Right | Next slide |
| Page Up | Previous slide |
| Page Down | Next slide |
| Space | Next slide |

## Styling Guide

### Basic Border Customization
```python
config = PptxViewerConfig(
    canvas_border='2px solid #0066cc',
    canvas_border_radius=8,
)
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
```

### Dark Theme Example
```python
DARK_THEME = PptxViewerConfig(
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
```

## Troubleshooting

### Problem: "Module not found"
**Solution:**
```bash
pip install -e ./st_pptx_viewer
```

### Problem: "Failed to load from CDN"
**Solution:**
Check internet connection. The module loads PptxViewJS from CDN by default.

To use a local bundle instead:
```python
config = PptxViewerConfig(
    pptxviewjs_path="/path/to/PptxViewJS.min.js"
)
```

### Problem: Presentation not rendering
**Checklist:**
1. Check if file is valid .pptx
2. Open browser console (F12) for errors
3. Try with a simpler presentation
4. Verify bundle exists: `ls dist/PptxViewJS.min.js`

### Problem: Styling not applying
**Solutions:**
1. Use `!important` in CSS:
   ```css
   .toolbar button { background: red !important; }
   ```
2. Check CSS syntax
3. Inspect in browser dev tools
4. Verify CSS is in `custom_css` parameter

### Problem: Multiple viewers conflicting
**Solution:** Use unique keys:
```python
pptx_viewer(file1, key="viewer1")
pptx_viewer(file2, key="viewer2")
```

### Problem: Keyboard shortcuts not working
**Solution:**
```python
config = PptxViewerConfig(enable_keyboard=True)
pptx_viewer(file, config=config)
```

### Problem: Viewer too small/large
**Solution:** Adjust width and height:
```python
config = PptxViewerConfig(
    width=1200,
    height=675,  # Or None for auto
)
```

### Problem: Want to use local PptxViewJS bundle
**Solution:** Specify path in configuration:
```python
config = PptxViewerConfig(
    pptxviewjs_path="/path/to/PptxViewJS.min.js"
)
pptx_viewer(file, config=config)
```

## Performance Tips

### For Large Files
```python
# Show loading message
with st.spinner("Loading presentation..."):
    pptx_viewer(large_file)
```

### For Multiple Viewers
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

### Cache Configuration
```python
@st.cache_resource
def get_viewer_config():
    return PptxViewerConfig(width=1200, enable_keyboard=True)

config = get_viewer_config()
pptx_viewer(uploaded, config=config)
```

## API Reference

### `pptx_viewer(pptx_file, config=None, key=None)`

Render a PPTX file in Streamlit.

**Parameters:**
- `pptx_file` (bytes | BinaryIO | str | Path): PPTX file
- `config` (PptxViewerConfig | None): Configuration options
- `key` (str | None): Unique key for component

**Returns:** None

**Example:**
```python
pptx_viewer(file, config=PptxViewerConfig(width=1000), key="my_viewer")
```

### `PptxViewerConfig`

Dataclass for viewer configuration.

**All Parameters:**
- `width` (int): Canvas width in pixels (default: 960)
- `height` (int | None): Canvas height (default: None)
- `show_toolbar` (bool): Show toolbar (default: True)
- `show_slide_counter` (bool): Show counter (default: True)
- `initial_slide` (int): Starting slide (default: 0)
- `enable_keyboard` (bool): Keyboard nav (default: True)
- `toolbar_position` (str): 'top' or 'bottom' (default: 'top')
- `canvas_border` (str): CSS border (default: '1px solid #ddd')
- `canvas_background` (str): Background color (default: '#fff')
- `canvas_border_radius` (int): Border radius (default: 4)
- `component_height` (int | None): Total height (default: None)
- `custom_css` (str): Additional CSS (default: '')
- `pptxviewjs_path` (str | Path | None): Bundle path (default: None)
- `enable_fullscreen` (bool): Fullscreen button (default: False)
- `toolbar_style` (dict): Toolbar CSS (default: {})

## Examples

Run the included examples:

```bash
# Minimal usage
streamlit run st_pptx_viewer/examples/basic_example.py

# All configuration options
streamlit run st_pptx_viewer/examples/advanced_example.py

# Side-by-side comparison
streamlit run st_pptx_viewer/examples/compare_presentations.py

# Theme gallery
streamlit run st_pptx_viewer/examples/custom_styling.py
```

## Further Reading

- [README.md](README.md) - Complete documentation
- [QUICKSTART.md](QUICKSTART.md) - 5-minute guide
- [MODULE_OVERVIEW.md](MODULE_OVERVIEW.md) - Architecture
- [PACKAGE_SUMMARY.md](PACKAGE_SUMMARY.md) - What was created
- [examples/README.md](examples/README.md) - Example documentation


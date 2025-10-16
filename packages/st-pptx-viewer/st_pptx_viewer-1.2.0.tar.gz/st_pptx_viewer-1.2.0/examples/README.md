# st_pptx_viewer Examples

This directory contains example applications demonstrating various features and use cases of the `st_pptx_viewer` module.

## Running the Examples

To run any of these examples, make sure you have:

1. Installed Streamlit:
```bash
pip install streamlit
```

2. Installed the module:
```bash
pip install -e ./st_pptx_viewer
```

3. Run the example:
```bash
streamlit run st_pptx_viewer/examples/basic_example.py
```

## Available Examples

### 1. basic_example.py
**The simplest possible implementation**

Demonstrates:
- Minimal setup with default configuration
- File upload functionality
- Basic rendering

Perfect for: Getting started quickly, understanding the core API

### 2. advanced_example.py
**Comprehensive configuration showcase**

Demonstrates:
- All configuration options
- Interactive sidebar controls
- Dynamic configuration changes
- Custom CSS styling

Perfect for: Exploring all features, understanding configuration options

### 3. compare_presentations.py
**Side-by-side presentation comparison**

Demonstrates:
- Multiple viewer instances
- Unique keys for component management
- Layout with columns
- Independent navigation

Perfect for: Version comparison, design reviews, A/B testing

### 4. custom_styling.py
**Theme gallery and styling examples**

Demonstrates:
- Pre-built themes (Dark Mode, Ocean Blue, Sunset, etc.)
- Custom CSS injection
- Toolbar styling
- Canvas customization

Perfect for: Creating branded viewers, matching your app's design system

## Example Code Snippets

### Minimal Setup
```python
from st_pptx_viewer import pptx_viewer

pptx_viewer(uploaded_file)
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

### Custom Theme
```python
config = PptxViewerConfig(
    width=1000,
    canvas_border='3px solid #0066cc',
    toolbar_style={'background': '#0066cc'},
    custom_css="""
        .toolbar button {
            background: white !important;
            color: #0066cc !important;
        }
    """,
)
pptx_viewer(uploaded_file, config=config)
```

## Tips for Using Examples

1. **Test with your own presentations**: All examples support file upload
2. **Modify and experiment**: These are templates - customize them for your needs
3. **Check the sidebar**: Most examples have interactive controls in the sidebar
4. **View source**: Each file is heavily commented to explain the code

## Common Use Cases

### Presentation Gallery App
Use `basic_example.py` as a starting point, add file selection from a directory.

### Design Review Tool
Use `compare_presentations.py` to compare before/after versions.

### Branded Viewer
Use `custom_styling.py` to match your company's design system.

### Presentation Library
Combine multiple viewers with tabs or expanders for a presentation library.

## Troubleshooting

### Import Error
```
ModuleNotFoundError: No module named 'st_pptx_viewer'
```
**Solution**: Install the module:
```bash
cd /path/to/js-slide-viewer
pip install -e ./st_pptx_viewer
```

### CDN Loading Issues
**Solution**: The module uses CDN-hosted PptxViewJS by default. Check your internet connection.

To use a local bundle instead:
```python
config = PptxViewerConfig(pptxviewjs_path="/path/to/PptxViewJS.min.js")
```

### Styling Not Applying
Make sure your custom CSS uses `!important` to override default styles:
```css
.toolbar button {
    background: red !important;  /* Note the !important */
}
```

## Contributing

Found a bug or have an idea for a new example? Please open an issue or pull request in the main repository.

## Further Reading

- [Main README](../README.md) - Full API documentation
- [PptxViewJS Documentation](../../README.md) - Underlying library documentation
- [Streamlit Documentation](https://docs.streamlit.io) - Streamlit framework docs


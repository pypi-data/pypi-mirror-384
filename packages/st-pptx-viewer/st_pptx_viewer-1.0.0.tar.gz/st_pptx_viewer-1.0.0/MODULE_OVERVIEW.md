# st_pptx_viewer Module Overview

## Architecture

```
st_pptx_viewer/
├── __init__.py              # Public API exports
├── viewer.py                # Core viewer component and configuration
├── setup.py                 # Package installation (setuptools)
├── pyproject.toml           # Modern package metadata (PEP 621)
├── MANIFEST.in              # Include additional files in distribution
├── README.md                # Full documentation
├── QUICKSTART.md            # 5-minute getting started guide
├── MODULE_OVERVIEW.md       # This file - architecture documentation
├── install.sh               # Automated installation script
├── .gitignore               # Git ignore patterns
└── examples/
    ├── README.md            # Examples documentation
    ├── basic_example.py     # Minimal usage
    ├── advanced_example.py  # All configuration options
    ├── compare_presentations.py  # Side-by-side comparison
    └── custom_styling.py    # Theming and styling
```

## Design Philosophy

### 1. Ease of Use
- **Minimal API**: Single function `pptx_viewer()` with sensible defaults
- **No configuration required**: Works out of the box
- **Progressive disclosure**: Advanced features available when needed

### 2. Type Safety
- **Dataclass-based config**: PptxViewerConfig with type hints
- **Clear parameter types**: Union types for flexible input (bytes, BinaryIO, str, Path)
- **IDE-friendly**: Full autocomplete and type checking support

### 3. Flexibility
- **Full customization**: Every visual aspect can be customized
- **Custom CSS injection**: Complete styling control
- **Multiple instances**: Support multiple viewers with unique keys
- **Dynamic configuration**: Change settings at runtime

### 4. Streamlit Integration
- **Native component**: Uses `streamlit.components.v1.html`
- **Frame height management**: Automatic height calculation and adjustment
- **State management**: Proper key-based state handling
- **Responsive**: Adapts to container width

## Core Components

### viewer.py

#### `PptxViewerConfig` (dataclass)
Configuration object with 18+ parameters:
- **Display**: width, height, component_height
- **UI Elements**: show_toolbar, show_slide_counter, enable_fullscreen
- **Navigation**: enable_keyboard, initial_slide, toolbar_position
- **Styling**: canvas_border, canvas_background, canvas_border_radius, toolbar_style, custom_css
- **Paths**: pptxviewjs_path

Benefits:
- Type checking at development time
- Default values for all parameters
- Easy to extend with new options
- Self-documenting code

#### `pptx_viewer()` (function)
Main entry point that:
1. Accepts multiple input formats (bytes, file object, path)
2. Loads PptxViewJS bundle
3. Generates HTML with embedded viewer
4. Handles iframe communication
5. Manages viewer lifecycle

Key features:
- **Base64 embedding**: Bundle and PPTX encoded inline (no external dependencies)
- **Dynamic HTML generation**: Template-based HTML with format strings
- **Event handling**: Keyboard shortcuts, button clicks, fullscreen
- **Height management**: Auto-calculates iframe height, posts messages to parent

## Data Flow

```
User Input (File)
    ↓
pptx_viewer() Function
    ↓
Input Processing (bytes, file, path → bytes)
    ↓
Base64 Encoding (PPTX + JS Bundle)
    ↓
HTML Generation (Template + Config)
    ↓
streamlit.components.v1.html()
    ↓
Browser Iframe
    ↓
PptxViewJS Initialization
    ↓
Presentation Rendering
```

## JavaScript Integration

The module embeds a complete viewer environment:

1. **Dependencies**: Chart.js and JSZip loaded from CDN
2. **Bundle loading**: PptxViewJS loaded from base64
3. **Initialization**: PPTXViewer instance created
4. **File loading**: PPTX loaded from base64
5. **Rendering**: Canvas rendering with aspect ratio
6. **Event handlers**: Navigation, keyboard, fullscreen

## Configuration Patterns

### Pattern 1: Default (Zero Config)
```python
pptx_viewer(file)
```

### Pattern 2: Simple Config
```python
config = PptxViewerConfig(width=1200)
pptx_viewer(file, config=config)
```

### Pattern 3: Full Control
```python
config = PptxViewerConfig(
    width=1000,
    show_toolbar=True,
    enable_keyboard=True,
    toolbar_style={'background': '#0066cc'},
    custom_css=".toolbar { ... }",
)
pptx_viewer(file, config=config)
```

### Pattern 4: Theme-based
```python
DARK_THEME = PptxViewerConfig(
    canvas_background='#1e1e1e',
    toolbar_style={'background': '#2d2d2d'},
    custom_css="...",
)
pptx_viewer(file, config=DARK_THEME)
```

## Extension Points

### Adding New Configuration Options

1. Add parameter to `PptxViewerConfig`:
```python
@dataclass
class PptxViewerConfig:
    # ... existing params ...
    new_option: bool = False
```

2. Use in HTML template:
```python
html = f"""
    ... 
    const newOption = {str(config.new_option).lower()};
    ...
"""
```

### Adding New Themes

Create theme configurations:
```python
THEMES = {
    'dark': PptxViewerConfig(...),
    'light': PptxViewerConfig(...),
    'custom': PptxViewerConfig(...),
}
```

### Custom CSS Utilities

Create helper functions:
```python
def create_gradient_theme(start_color, end_color):
    return PptxViewerConfig(
        toolbar_style={
            'background': f'linear-gradient(to right, {start_color}, {end_color})'
        }
    )
```

## State Management

### Component Keys
Each viewer needs a unique key when using multiple instances:
```python
pptx_viewer(file_a, key="viewer_1")
pptx_viewer(file_b, key="viewer_2")
```

### Streamlit Session State
The viewer doesn't directly use session state, but you can:
```python
if 'current_slide' not in st.session_state:
    st.session_state.current_slide = 0

config = PptxViewerConfig(initial_slide=st.session_state.current_slide)
pptx_viewer(file, config=config)
```

## Performance Considerations

### Base64 Encoding
- Bundle: ~100-500KB (one-time load)
- PPTX: Varies by file size
- Impact: Initial load time increases with file size

### Optimization Strategies
1. **Bundle caching**: Load once, reuse across pages
2. **File size limits**: Warn users about large files
3. **Lazy loading**: Load viewer only when needed
4. **CDN dependencies**: Chart.js and JSZip from CDN (cached)

### Browser Compatibility
- Modern browsers (Chrome, Firefox, Safari, Edge)
- Canvas 2D rendering support required
- ES6+ JavaScript features used

## Testing Strategy

### Manual Testing
1. Run examples: `streamlit run examples/basic_example.py`
2. Upload various PPTX files
3. Test configuration options
4. Verify keyboard shortcuts
5. Check responsive behavior

### Automated Testing (Future)
- Unit tests for config validation
- Integration tests with sample files
- Visual regression tests
- Performance benchmarks

## Deployment

### Local Development
```bash
pip install -e ./st_pptx_viewer
streamlit run your_app.py
```

### Production
```bash
pip install st-pptx-viewer  # When published to PyPI
streamlit run your_app.py
```

### Cloud Platforms
- **Streamlit Cloud**: Works out of the box
- **Heroku**: Include buildpacks for Node.js (for building)
- **AWS/GCP**: Standard Streamlit deployment

## Dependencies

### Python
- streamlit >= 1.0.0
- Python >= 3.8

### JavaScript (CDN)
- Chart.js 4.4.1
- JSZip 3.10.1

### Build-time
- Node.js >= 18 (for building PptxViewJS)
- npm

## Security Considerations

### Input Validation
- File type checking (must be .pptx)
- File size limits (optional, add in application)
- Base64 encoding prevents code injection

### Sandboxing
- Viewer runs in iframe (isolated)
- No direct DOM access to parent
- PostMessage for safe communication

### User Data
- Files processed in-memory (not stored)
- No external API calls (except CDN)
- No telemetry or tracking

## Future Enhancements

### Planned Features
1. Slide thumbnails navigation
2. Search within presentation
3. Annotations and markup
4. Export individual slides
5. Presentation metadata display
6. Speaker notes panel
7. Slide transitions
8. Animation support

### API Improvements
1. Callbacks for slide changes
2. Return current slide index
3. Programmatic slide navigation
4. Export API for saving rendered slides

### Performance
1. Lazy slide rendering
2. Virtual scrolling for large decks
3. WebWorker for processing
4. Caching strategies

## Contributing

### Adding Features
1. Update `PptxViewerConfig` dataclass
2. Modify HTML template in `pptx_viewer()`
3. Update README with examples
4. Add example to `examples/`
5. Test with various PPTX files

### Code Style
- Follow PEP 8
- Type hints for all functions
- Docstrings in Google style
- Comments for complex logic

### Documentation
- Update README.md for user-facing changes
- Update MODULE_OVERVIEW.md for architecture changes
- Add examples for new features
- Keep QUICKSTART.md simple

## Troubleshooting

### Common Issues

**Module not found**
- Solution: `pip install -e ./st_pptx_viewer`

**Bundle not found**
- Solution: `npm run build:min` in parent directory

**Rendering issues**
- Check browser console
- Verify PPTX file validity
- Test with simpler presentation

**Styling not applying**
- Use `!important` in custom CSS
- Check browser dev tools
- Verify CSS syntax

## License

This module is part of the PptxViewJS project. See the main project LICENSE file.

## Support

- GitHub Issues: Bug reports and feature requests
- Examples: Working code in `examples/` directory
- Documentation: README.md and QUICKSTART.md


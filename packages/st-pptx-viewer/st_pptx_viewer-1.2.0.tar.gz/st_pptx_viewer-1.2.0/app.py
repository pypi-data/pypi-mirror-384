"""
Main application to run all st_pptx_viewer examples.

This app provides a unified interface to explore all example demonstrations
of the st_pptx_viewer component.
"""

import streamlit as st
from st_pptx_viewer import pptx_viewer, PptxViewerConfig

# Configure page
st.set_page_config(
    page_title="st_pptx_viewer Examples",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar navigation
st.sidebar.title("📊 st_pptx_viewer")
st.sidebar.markdown("### Navigation")

page = st.sidebar.radio(
    "Choose an example:",
    [
        "🏠 Home",
        "📄 Basic Example",
        "🎨 Advanced Configuration",
        "🔀 Compare Presentations",
        "🎭 Custom Styling"
    ]
)

st.sidebar.divider()
st.sidebar.markdown("""
### About
**st_pptx_viewer** is a Streamlit component for viewing PowerPoint presentations in your web apps.

[GitHub](https://github.com/gptsci/st_pptx_viewer) | [PyPI](https://pypi.org/project/st-pptx-viewer/)
""")


# ============================================================================
# HOME PAGE
# ============================================================================
if page == "🏠 Home":
    st.title("📊 st_pptx_viewer Examples")
    st.markdown("""
    Welcome! This app showcases all the features and capabilities of the **st_pptx_viewer** component.
    
    ### 🚀 What is st_pptx_viewer?
    
    `st_pptx_viewer` is a Streamlit component that allows you to display PowerPoint presentations
    (.pptx files) directly in your Streamlit applications with full navigation and customization options.
    
    ### 📚 Available Examples
    
    Use the sidebar to navigate through different examples:
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📄 Basic Example")
        st.markdown("""
        The simplest way to use the viewer:
        - Upload a PPTX file
        - View with default settings
        - Perfect for getting started
        """)
        
        st.subheader("🔀 Compare Presentations")
        st.markdown("""
        Side-by-side comparison:
        - View two presentations at once
        - Independent navigation
        - Great for version comparison
        """)
    
    with col2:
        st.subheader("🎨 Advanced Configuration")
        st.markdown("""
        Explore all configuration options:
        - Customize dimensions
        - Configure toolbar
        - Adjust navigation settings
        - Apply custom styling
        """)
        
        st.subheader("🎭 Custom Styling")
        st.markdown("""
        Beautiful themed viewers:
        - Pre-built themes
        - Custom CSS styling
        - Professional designs
        - Dark mode and more
        """)
    
    st.divider()
    
    st.subheader("🎯 Quick Start")
    st.code("""
import streamlit as st
from st_pptx_viewer import pptx_viewer, PptxViewerConfig

# Upload file
uploaded_file = st.file_uploader("Choose a PPTX file", type=["pptx"])

if uploaded_file:
    # Configure viewer
    config = PptxViewerConfig(width=1200)
    
    # Display presentation
    pptx_viewer(uploaded_file, config=config)
    """, language="python")
    
    st.divider()
    
    st.subheader("📦 Installation")
    st.code("pip install st-pptx-viewer", language="bash")
    
    st.info("👈 Select an example from the sidebar to get started!")


# ============================================================================
# BASIC EXAMPLE
# ============================================================================
elif page == "📄 Basic Example":
    st.title("📊 Basic PPTX Viewer Example")
    st.markdown("""
    This is the simplest way to use the st_pptx_viewer component.
    Upload a PowerPoint file and it will be rendered with default settings.
    """)
    
    uploaded_file = st.file_uploader("Choose a PPTX file", type=["pptx"], key="basic")
    
    if uploaded_file is not None:
        st.divider()
        # Configure viewer to use wider canvas (1400px fits better in wide layout)
        config = PptxViewerConfig(width=1400)
        pptx_viewer(uploaded_file, config=config)
    else:
        st.info("👆 Upload a .pptx file to get started")


# ============================================================================
# ADVANCED CONFIGURATION
# ============================================================================
elif page == "🎨 Advanced Configuration":
    st.title("🎨 Advanced PPTX Viewer Configuration")
    st.markdown("""
    This example demonstrates all the configuration options available in st_pptx_viewer.
    Customize the settings in the sidebar and upload a presentation to see the changes.
    """)
    
    # Sidebar configuration
    st.sidebar.header("⚙️ Configuration")
    
    st.sidebar.subheader("Canvas Settings")
    width = st.sidebar.slider("Canvas Width (px)", 400, 1600, 960, 10)
    use_custom_height = st.sidebar.checkbox("Custom Height", False)
    height = None
    if use_custom_height:
        height = st.sidebar.slider("Canvas Height (px)", 300, 1200, 540, 10)
    
    st.sidebar.subheader("Toolbar Settings")
    show_toolbar = st.sidebar.checkbox("Show Toolbar", True)
    show_slide_counter = st.sidebar.checkbox("Show Slide Counter", True)
    toolbar_position = st.sidebar.selectbox("Toolbar Position", ["top", "bottom"])
    enable_fullscreen = st.sidebar.checkbox("Enable Fullscreen", True)
    
    st.sidebar.subheader("Navigation Settings")
    enable_keyboard = st.sidebar.checkbox("Keyboard Navigation", True)
    initial_slide = st.sidebar.number_input("Initial Slide (0-based)", min_value=0, value=0)
    
    st.sidebar.subheader("Styling")
    canvas_background = st.sidebar.color_picker("Canvas Background", "#ffffff")
    border_color = st.sidebar.color_picker("Border Color", "#dddddd")
    border_width = st.sidebar.slider("Border Width (px)", 0, 5, 1)
    border_radius = st.sidebar.slider("Border Radius (px)", 0, 20, 4)
    
    st.sidebar.subheader("Custom CSS")
    use_custom_css = st.sidebar.checkbox("Add Custom CSS", False)
    custom_css = ""
    if use_custom_css:
        custom_css = st.sidebar.text_area(
            "Custom CSS",
            """
.toolbar button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    border: none !important;
}
            """.strip()
        )
    
    # File upload
    uploaded_file = st.file_uploader("Choose a PPTX file", type=["pptx"], key="advanced")
    
    if uploaded_file is not None:
        st.divider()
        
        # Create configuration
        config = PptxViewerConfig(
            width=width,
            height=height,
            show_toolbar=show_toolbar,
            show_slide_counter=show_slide_counter,
            initial_slide=int(initial_slide),
            enable_keyboard=enable_keyboard,
            toolbar_position=toolbar_position,
            canvas_border=f'{border_width}px solid {border_color}',
            canvas_background=canvas_background,
            canvas_border_radius=border_radius,
            custom_css=custom_css,
            enable_fullscreen=enable_fullscreen,
        )
        
        # Display configuration details
        with st.expander("📋 Current Configuration"):
            st.json({
                "width": config.width,
                "height": config.height,
                "show_toolbar": config.show_toolbar,
                "show_slide_counter": config.show_slide_counter,
                "initial_slide": config.initial_slide,
                "enable_keyboard": config.enable_keyboard,
                "toolbar_position": config.toolbar_position,
                "canvas_border": config.canvas_border,
                "canvas_background": config.canvas_background,
                "canvas_border_radius": config.canvas_border_radius,
                "enable_fullscreen": config.enable_fullscreen,
            })
        
        # Render viewer
        pptx_viewer(uploaded_file, config=config)
    else:
        st.info("👆 Upload a .pptx file to get started")
        
        # Show example configuration
        st.divider()
        st.subheader("📖 Example Configuration Code")
        st.code("""
from st_pptx_viewer import pptx_viewer, PptxViewerConfig

config = PptxViewerConfig(
    width=1200,
    show_toolbar=True,
    show_slide_counter=True,
    enable_keyboard=True,
    toolbar_position='bottom',
    enable_fullscreen=True,
    canvas_border='2px solid #0066cc',
    canvas_background='#f5f5f5',
    canvas_border_radius=8,
)

pptx_viewer(uploaded_file, config=config)
        """, language="python")


# ============================================================================
# COMPARE PRESENTATIONS
# ============================================================================
elif page == "🔀 Compare Presentations":
    st.title("🔀 Compare Two Presentations")
    st.markdown("""
    Upload two PowerPoint presentations to view them side by side.
    This is useful for comparing versions or different designs.
    """)
    
    # Configuration options
    st.sidebar.header("⚙️ Settings")
    viewer_width = st.sidebar.slider("Viewer Width (px)", 400, 800, 600, 10)
    show_toolbar = st.sidebar.checkbox("Show Toolbar", True, key="compare_toolbar")
    enable_keyboard = st.sidebar.checkbox("Keyboard Navigation", False)  # Disabled by default to avoid conflicts
    
    # Create columns for side-by-side comparison
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📄 Presentation A")
        file_a = st.file_uploader("Upload Presentation A", type=["pptx"], key="upload_a")
        
        if file_a is not None:
            config = PptxViewerConfig(
                width=viewer_width,
                show_toolbar=show_toolbar,
                enable_keyboard=enable_keyboard,
                toolbar_position='top',
            )
            pptx_viewer(file_a, config=config, key="viewer_a")
        else:
            st.info("Upload a presentation to display it here")
    
    with col2:
        st.subheader("📄 Presentation B")
        file_b = st.file_uploader("Upload Presentation B", type=["pptx"], key="upload_b")
        
        if file_b is not None:
            config = PptxViewerConfig(
                width=viewer_width,
                show_toolbar=show_toolbar,
                enable_keyboard=enable_keyboard,
                toolbar_position='top',
            )
            pptx_viewer(file_b, config=config, key="viewer_b")
        else:
            st.info("Upload a presentation to display it here")
    
    # Tips section
    st.divider()
    st.subheader("💡 Tips")
    st.markdown("""
    - **Navigate independently**: Each viewer has its own navigation controls
    - **Keyboard shortcuts**: Disabled by default in compare mode to prevent conflicts
    - **Adjust width**: Use the sidebar slider to make viewers larger or smaller
    - **Same presentation**: You can load the same file in both viewers to compare different slides
    """)


# ============================================================================
# CUSTOM STYLING
# ============================================================================
elif page == "🎭 Custom Styling":
    st.title("🎨 Custom Styling & Theming")
    st.markdown("""
    This example shows how to create beautifully styled PPTX viewers with custom themes.
    Choose a theme below or upload your own presentation.
    """)
    
    # Theme selection
    theme = st.selectbox(
        "Choose a Theme",
        ["Default", "Dark Mode", "Ocean Blue", "Sunset", "Minimal", "Professional"]
    )
    
    # Define theme configurations
    themes = {
        "Default": PptxViewerConfig(
            width=1000,
            show_toolbar=True,
            enable_fullscreen=True,
        ),
        "Dark Mode": PptxViewerConfig(
            width=1000,
            show_toolbar=True,
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
            enable_fullscreen=True,
        ),
        "Ocean Blue": PptxViewerConfig(
            width=1000,
            show_toolbar=True,
            canvas_border='3px solid #0077be',
            canvas_border_radius=12,
            canvas_background='#f0f8ff',
            toolbar_style={
                'background': 'linear-gradient(to right, #0077be, #00a8e8)',
                'color': 'white',
                'padding': '12px',
            },
            custom_css="""
                .toolbar button {
                    background: white !important;
                    color: #0077be !important;
                    border: none !important;
                    border-radius: 6px;
                    font-weight: 600;
                    padding: 8px 16px;
                }
                .toolbar button:hover {
                    background: #e6f3ff !important;
                }
                .status {
                    color: white !important;
                    font-weight: 500;
                }
            """,
            enable_fullscreen=True,
        ),
        "Sunset": PptxViewerConfig(
            width=1000,
            show_toolbar=True,
            canvas_border='3px solid #ff6b6b',
            canvas_border_radius=15,
            toolbar_style={
                'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)',
                'padding': '12px',
            },
            custom_css="""
                .toolbar button {
                    background: rgba(255, 255, 255, 0.9) !important;
                    color: #764ba2 !important;
                    border: none !important;
                    border-radius: 8px;
                    font-weight: 600;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .toolbar button:hover {
                    background: white !important;
                    transform: translateY(-1px);
                    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
                }
                .status {
                    color: white !important;
                    font-weight: 500;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
                }
            """,
            enable_fullscreen=True,
        ),
        "Minimal": PptxViewerConfig(
            width=1000,
            show_toolbar=True,
            canvas_border='none',
            canvas_border_radius=0,
            canvas_background='#ffffff',
            toolbar_style={
                'background': 'transparent',
                'border': 'none',
                'padding': '8px 0',
            },
            custom_css="""
                .toolbar button {
                    background: transparent !important;
                    color: #666 !important;
                    border: 1px solid #ddd !important;
                    border-radius: 4px;
                    padding: 6px 12px;
                }
                .toolbar button:hover {
                    background: #f5f5f5 !important;
                    color: #333 !important;
                }
                .status {
                    color: #999 !important;
                }
            """,
            enable_fullscreen=True,
        ),
        "Professional": PptxViewerConfig(
            width=1000,
            show_toolbar=True,
            canvas_border='2px solid #2c3e50',
            canvas_border_radius=8,
            canvas_background='#ffffff',
            toolbar_style={
                'background': '#34495e',
                'padding': '10px',
                'border-radius': '6px 6px 0 0',
            },
            custom_css="""
                .toolbar button {
                    background: #2c3e50 !important;
                    color: #ecf0f1 !important;
                    border: 1px solid #1a252f !important;
                    border-radius: 4px;
                    font-weight: 500;
                    padding: 7px 14px;
                }
                .toolbar button:hover {
                    background: #1a252f !important;
                }
                .toolbar button:disabled {
                    opacity: 0.4 !important;
                }
                .status {
                    color: #bdc3c7 !important;
                    font-family: 'Courier New', monospace;
                }
                .wrap {
                    background: #ecf0f1;
                    padding: 20px;
                }
            """,
            enable_fullscreen=True,
        ),
    }
    
    # File upload
    uploaded_file = st.file_uploader("Choose a PPTX file", type=["pptx"], key="styling")
    
    if uploaded_file is not None:
        st.divider()
        
        # Show theme info
        with st.expander("ℹ️ About This Theme"):
            config = themes[theme]
            st.write(f"**Theme**: {theme}")
            st.write(f"**Width**: {config.width}px")
            st.write(f"**Border**: {config.canvas_border}")
            st.write(f"**Background**: {config.canvas_background}")
            if config.custom_css:
                st.code(config.custom_css, language="css")
        
        # Render with selected theme
        pptx_viewer(uploaded_file, config=themes[theme])
    else:
        st.info("👆 Upload a .pptx file to see the themed viewer")
        
        # Preview section
        st.divider()
        st.subheader("🎭 Theme Previews")
        st.markdown("""
        Each theme includes:
        - Custom color schemes
        - Styled navigation buttons
        - Themed borders and backgrounds
        - Professional typography
        """)
        
        # Show code example
        st.subheader("📝 Creating Your Own Theme")
        st.code("""
from st_pptx_viewer import pptx_viewer, PptxViewerConfig

custom_config = PptxViewerConfig(
    width=1000,
    canvas_border='3px solid #your-color',
    canvas_border_radius=12,
    toolbar_style={
        'background': 'your-gradient-or-color',
        'padding': '12px',
    },
    custom_css=\"\"\"
        .toolbar button {
            background: white !important;
            color: #your-color !important;
        }
    \"\"\",
)

pptx_viewer(your_file, config=custom_config)
        """, language="python")


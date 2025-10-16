"""
Advanced example demonstrating all configuration options.

This shows how to customize the PPTX viewer with various settings.
"""

import streamlit as st
from st_pptx_viewer import pptx_viewer, PptxViewerConfig

st.set_page_config(page_title="Advanced PPTX Viewer", layout="wide")

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
uploaded_file = st.file_uploader("Choose a PPTX file", type=["pptx"])

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


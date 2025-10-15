"""
Example showing side-by-side comparison of two presentations.

This demonstrates using multiple viewer instances with unique keys.
"""

import streamlit as st
from st_pptx_viewer import pptx_viewer, PptxViewerConfig

st.set_page_config(page_title="Compare Presentations", layout="wide")

st.title("🔀 Compare Two Presentations")
st.markdown("""
Upload two PowerPoint presentations to view them side by side.
This is useful for comparing versions or different designs.
""")

# Configuration options
st.sidebar.header("⚙️ Settings")
viewer_width = st.sidebar.slider("Viewer Width (px)", 400, 800, 600, 10)
show_toolbar = st.sidebar.checkbox("Show Toolbar", True)
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


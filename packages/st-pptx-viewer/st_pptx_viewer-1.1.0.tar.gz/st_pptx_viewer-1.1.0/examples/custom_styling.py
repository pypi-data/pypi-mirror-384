"""
Example demonstrating custom styling and theming.

This shows how to apply custom CSS and create themed viewers.
"""

import streamlit as st
from st_pptx_viewer import pptx_viewer, PptxViewerConfig

st.set_page_config(page_title="Custom Styling Example", layout="wide")

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
uploaded_file = st.file_uploader("Choose a PPTX file", type=["pptx"])

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


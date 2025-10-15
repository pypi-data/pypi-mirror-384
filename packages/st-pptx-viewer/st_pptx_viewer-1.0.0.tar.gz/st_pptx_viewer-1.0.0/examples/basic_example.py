"""
Basic example of using st_pptx_viewer module.

This demonstrates the simplest way to use the PPTX viewer component.
"""

import streamlit as st
from st_pptx_viewer import pptx_viewer

st.set_page_config(page_title="Basic PPTX Viewer", layout="wide")

st.title("📊 Basic PPTX Viewer Example")
st.markdown("""
This is the simplest way to use the st_pptx_viewer component.
Upload a PowerPoint file and it will be rendered with default settings.
""")

uploaded_file = st.file_uploader("Choose a PPTX file", type=["pptx"])

if uploaded_file is not None:
    st.divider()
    pptx_viewer(uploaded_file)
else:
    st.info("👆 Upload a .pptx file to get started")


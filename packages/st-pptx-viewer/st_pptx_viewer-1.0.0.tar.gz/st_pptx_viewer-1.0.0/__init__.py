"""
st_pptx_viewer - A Streamlit component for rendering PPTX files using PptxViewJS

This module provides a reusable Streamlit component that displays PowerPoint presentations
in a web browser with interactive controls.
"""

from .viewer import pptx_viewer, PptxViewerConfig

__version__ = "1.0.0"
__all__ = ["pptx_viewer", "PptxViewerConfig"]


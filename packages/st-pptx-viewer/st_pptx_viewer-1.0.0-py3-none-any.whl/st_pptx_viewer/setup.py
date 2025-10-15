"""
Setup configuration for st_pptx_viewer package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README for long description
this_directory = Path(__file__).parent
long_description = ""
readme_path = this_directory / "README.md"
if readme_path.exists():
    long_description = readme_path.read_text(encoding='utf-8')

setup(
    name="st-pptx-viewer",
    version="1.0.0",
    author="PptxViewJS Contributors",
    description="A Streamlit component for rendering PowerPoint presentations using PptxViewJS",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sdafa123/js-slide-viewer",
    packages=["st_pptx_viewer"],
    package_dir={"st_pptx_viewer": "."},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "streamlit>=1.0.0",
    ],
    keywords="streamlit pptx powerpoint viewer presentation component",
    project_urls={
        "Bug Reports": "https://github.com/sdafa123/js-slide-viewer/issues",
        "Source": "https://github.com/sdafa123/js-slide-viewer",
    },
    include_package_data=True,
)


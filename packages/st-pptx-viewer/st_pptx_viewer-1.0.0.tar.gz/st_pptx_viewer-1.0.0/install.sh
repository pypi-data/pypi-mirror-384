#!/bin/bash
# Installation script for st_pptx_viewer module

set -e  # Exit on error

echo "========================================="
echo "Installing st_pptx_viewer module"
echo "========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "setup.py" ]; then
    echo "Error: setup.py not found. Please run this script from the st_pptx_viewer directory."
    exit 1
fi

# Step 1: Check Python version
echo "Step 1: Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oP '(?<=Python )\d+\.\d+')
major_version=$(echo $python_version | cut -d. -f1)
minor_version=$(echo $python_version | cut -d. -f2)

if [ "$major_version" -lt 3 ] || ([ "$major_version" -eq 3 ] && [ "$minor_version" -lt 8 ]); then
    echo "Error: Python 3.8 or higher is required. Found Python $python_version"
    exit 1
fi
echo "✓ Python $python_version found"
echo ""

# Step 2: Note about PptxViewJS
echo "Step 2: PptxViewJS library..."
echo "✓ Using CDN-hosted PptxViewJS (no build required)"
echo "  The module will load PptxViewJS from:"
echo "  https://cdn.jsdelivr.net/npm/pptxviewjs/dist/PptxViewJS.min.js"
echo ""

# Step 3: Install Python dependencies
echo "Step 3: Installing Python dependencies..."
pip3 install streamlit

echo "✓ Dependencies installed"
echo ""

# Step 4: Install the module
echo "Step 4: Installing st_pptx_viewer module..."
pip3 install -e .

echo "✓ Module installed"
echo ""

# Step 5: Verify installation
echo "Step 5: Verifying installation..."
python3 -c "from st_pptx_viewer import pptx_viewer, PptxViewerConfig; print('✓ Module imports successfully')"
echo ""

echo "========================================="
echo "Installation complete! 🎉"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Try the examples:"
echo "     streamlit run examples/basic_example.py"
echo ""
echo "  2. Read the documentation:"
echo "     cat README.md"
echo ""
echo "  3. Start building your own app!"
echo ""


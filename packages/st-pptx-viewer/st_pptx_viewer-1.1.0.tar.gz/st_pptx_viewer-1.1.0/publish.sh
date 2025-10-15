#!/bin/bash
# Publishing script for st-pptx-viewer package

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}====================================${NC}"
echo -e "${BLUE}  PyPI Publishing Script${NC}"
echo -e "${BLUE}====================================${NC}"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command_exists python3; then
    echo -e "${RED}Error: python3 is not installed${NC}"
    exit 1
fi

if ! command_exists pip; then
    echo -e "${RED}Error: pip is not installed${NC}"
    exit 1
fi

# Check/install build tools
if ! python3 -c "import build" 2>/dev/null; then
    echo -e "${YELLOW}Installing build package...${NC}"
    pip install --upgrade build
fi

if ! command_exists twine; then
    echo -e "${YELLOW}Installing twine...${NC}"
    pip install --upgrade twine
fi

echo -e "${GREEN}✓ Prerequisites checked${NC}"
echo ""

# Show menu
echo "Select publishing target:"
echo "  1) TestPyPI (recommended for testing)"
echo "  2) PyPI (production)"
echo "  3) Build only (no upload)"
echo "  4) Exit"
echo ""
read -p "Enter choice [1-4]: " choice

case $choice in
    1)
        TARGET="testpypi"
        REPO_FLAG="--repository testpypi"
        ;;
    2)
        TARGET="pypi"
        REPO_FLAG=""
        echo -e "${YELLOW}⚠️  WARNING: Publishing to PRODUCTION PyPI${NC}"
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            echo "Cancelled."
            exit 0
        fi
        ;;
    3)
        TARGET="build-only"
        ;;
    4)
        echo "Exiting."
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

# Clean previous builds
echo ""
echo -e "${YELLOW}Cleaning previous builds...${NC}"
rm -rf dist/ build/ *.egg-info/
echo -e "${GREEN}✓ Cleaned${NC}"

# Build package
echo ""
echo -e "${YELLOW}Building package...${NC}"
python3 -m build

if [ $? -ne 0 ]; then
    echo -e "${RED}Build failed!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Package built successfully${NC}"
echo ""
echo "Created files:"
ls -lh dist/

# Upload if not build-only
if [ "$TARGET" != "build-only" ]; then
    echo ""
    echo -e "${YELLOW}Uploading to $TARGET...${NC}"
    python3 -m twine upload $REPO_FLAG dist/*
    
    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✓ Successfully published to $TARGET!${NC}"
        echo ""
        
        if [ "$TARGET" = "testpypi" ]; then
            echo "To test installation:"
            echo "  pip install --index-url https://test.pypi.org/simple/ st-pptx-viewer"
        else
            echo "To install:"
            echo "  pip install st-pptx-viewer"
            echo ""
            echo "View on PyPI:"
            echo "  https://pypi.org/project/st-pptx-viewer/"
        fi
    else
        echo -e "${RED}Upload failed!${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}Done!${NC}"


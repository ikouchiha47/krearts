#!/bin/bash
# Publish generated graphic novel to landing page
# Usage: ./scripts/publish_to_landing.sh <workflow_id>

set -e

WORKFLOW_ID=$1

if [ -z "$WORKFLOW_ID" ]; then
    echo "Usage: $0 <workflow_id>"
    echo "Example: $0 43e21caa"
    exit 1
fi

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

PDF_SOURCE="output/book_${WORKFLOW_ID}/graphic_novel/graphic_novel.pdf"
PDF_DEST="landing/releases/noir/full_novel.pdf"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Publishing to Landing Page${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Check if PDF exists
if [ ! -f "$PDF_SOURCE" ]; then
    echo -e "${RED}Error: PDF not found: $PDF_SOURCE${NC}"
    echo "Run: ./scripts/create_graphic_novel.sh $WORKFLOW_ID"
    exit 1
fi

# Create destination directory
mkdir -p "landing/releases/noir"

# Copy PDF
echo "Copying PDF..."
cp "$PDF_SOURCE" "$PDF_DEST"

# Copy novel.md
NOVEL_SOURCE="output/book_${WORKFLOW_ID}/novel.md"
NOVEL_DEST="landing/releases/noir/novel.md"

if [ -f "$NOVEL_SOURCE" ]; then
    echo "Copying novel.md..."
    cp "$NOVEL_SOURCE" "$NOVEL_DEST"
else
    echo "Warning: novel.md not found at $NOVEL_SOURCE"
fi

# Get file sizes
PDF_SIZE=$(du -h "$PDF_DEST" | cut -f1)
NOVEL_SIZE=$(du -h "$NOVEL_DEST" 2>/dev/null | cut -f1 || echo "N/A")

echo -e "${GREEN}✓ PDF published${NC}"
echo ""
echo "Details:"
echo "  PDF: $PDF_DEST ($PDF_SIZE)"
echo "  Novel: $NOVEL_DEST ($NOVEL_SIZE)"
echo ""
echo "Landing page links:"
echo "  Viewer: https://yourdomain.com/novel-viewer.html"
echo "  PDF: https://yourdomain.com/releases/noir/full_novel.pdf"
echo "  Novel: https://yourdomain.com/releases/noir/novel.md"
echo ""
echo "To deploy to GitHub Pages:"
echo "  make webpage"
echo ""

#!/bin/bash
# Create a graphic novel PDF from generated pages
# Usage: ./scripts/create_graphic_novel.sh <workflow_id> [--quality high|medium|low]

set -e

WORKFLOW_ID=$1
QUALITY=${2:-medium}

if [ -z "$WORKFLOW_ID" ]; then
    echo "Usage: $0 <workflow_id> [--quality high|medium|low]"
    echo "Example: $0 43e21caa --quality medium"
    exit 1
fi

# Parse quality flag
if [ "$2" = "--quality" ]; then
    QUALITY=$3
fi

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

PAGES_DIR="output/book_${WORKFLOW_ID}/pages"
OUTPUT_DIR="output/book_${WORKFLOW_ID}/graphic_novel"
COMPRESSED_DIR="${OUTPUT_DIR}/compressed"
SPREAD_OUTPUT_DIR="${OUTPUT_DIR}/spreads"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Creating Graphic Novel${NC}"
echo -e "${BLUE}================================${NC}"
echo -e "Workflow ID: ${GREEN}${WORKFLOW_ID}${NC}"
echo -e "Quality: ${GREEN}${QUALITY}${NC}"
echo ""

# Check if pages directory exists
if [ ! -d "$PAGES_DIR" ]; then
    echo -e "${YELLOW}Error: Pages directory not found: $PAGES_DIR${NC}"
    exit 1
fi

# Create output directories
mkdir -p "$OUTPUT_DIR"
mkdir -p "$COMPRESSED_DIR"
mkdir -p "$SPREAD_OUTPUT_DIR"

# Count pages
TOTAL_PAGES=$(ls "$PAGES_DIR"/ch*.png 2>/dev/null | grep -v "clean\|annotated\|with_captions\|with_text" | wc -l | tr -d ' ')

if [ "$TOTAL_PAGES" -eq 0 ]; then
    echo -e "${YELLOW}Error: No pages found in $PAGES_DIR${NC}"
    exit 1
fi

echo -e "Found ${GREEN}${TOTAL_PAGES}${NC} pages"
echo ""

# Set compression quality based on flag
case $QUALITY in
    high)
        COMPRESS_QUALITY=95
        PDF_QUALITY="prepress"
        echo "Quality: High (95% JPEG, prepress PDF)"
        ;;
    low)
        COMPRESS_QUALITY=70
        PDF_QUALITY="ebook"
        echo "Quality: Low (70% JPEG, ebook PDF)"
        ;;
    *)
        COMPRESS_QUALITY=85
        PDF_QUALITY="printer"
        echo "Quality: Medium (85% JPEG, printer PDF)"
        ;;
esac

echo ""

# Step 1: Compress images
echo -e "${BLUE}Step 1: Compressing images...${NC}"
echo ""

function compress_images() {
    # Get list of page files in order
    PAGE_FILES=$(ls "$PAGES_DIR"/ch*.png | grep -v "clean\|annotated\|with_captions\|with_text" | sort -V)

    counter=1

    for page in $PAGE_FILES; do
        filename=$(basename "$page")
        output_file="${COMPRESSED_DIR}/page_$(printf '%03d' $counter).jpg"

        # Compress using ImageMagick
        if command -v magick &> /dev/null; then
            # ImageMagick v7
            magick "$page" -quality "$COMPRESS_QUALITY" "$output_file"
        elif command -v convert &> /dev/null; then
            # ImageMagick v6
            convert "$page" -quality "$COMPRESS_QUALITY" "$output_file"
        else
            # No compression tool, just copy
            cp "$page" "$output_file"
        fi

        if [ $((counter % 10)) -eq 0 ]; then
            echo "  Compressed $counter/$TOTAL_PAGES pages..."
        fi

        counter=$((counter + 1))
    done

}


function get_spread() {
    echo "Compressed $COMPRESSED_DIR"

    files=($(ls "${COMPRESSED_DIR}"/*.jpg | sort -V))

    total=${#files[@]}
    index=0
    spread_num=1

    while [ $index -lt $total ]; do
        left="${files[$index]}"
        right=""

        echo "Left:: $left"

        if [ $((index+1)) -lt $total ]; then
            right="${files[$((index+1))]}"
        fi

        out=$(printf "%s/spread_%03d.jpg" "$SPREAD_OUTPUT_DIR" "$spread_num")

        if [ -n "$right" ]; then
            echo "Building spread $spread_num : $(basename "$left") + $(basename "$right")"

            # convert -gravity center -splice 40x0 +append "$left" "$right" "$out"
            convert "$left" \( -size 40x1152 canvas:white \) "$right" +append "$out"

        else
            echo "Building spread $spread_num : $(basename "$left") (single)"
            cp "$left" "$out"
        fi

        index=$((index+2))
        spread_num=$((spread_num+1))
    done


    echo "Done. Spreads saved to ${SPREAD_OUTPUT_DIR}/"
}


PDF_OUTPUT="${OUTPUT_DIR}/book.pdf"

function create_pdf_spread() {
    echo "Using ImageMagick to create PDF..."

    if command -v magick &> /dev/null; then
        magick -density 300 "$SPREAD_OUTPUT_DIR"/spread_*.jpg \
               -quality 100 "$PDF_OUTPUT"
    else
        convert -density 300 "$SPREAD_OUTPUT_DIR"/spread_*.jpg \
                -quality 100 "$PDF_OUTPUT"
    fi

    echo -e "${GREEN}✓ PDF created:${NC} $PDF_OUTPUT"
}

function create_pdf() {
    echo "Using ImageMagick to create PDF..."

    if command -v magick &> /dev/null; then
        magick -density 300 "$COMPRESSED_DIR"/page_*.jpg \
               -quality 100 "$PDF_OUTPUT"
    else
        convert -density 300 "$COMPRESSED_DIR"/page_*.jpg \
                -quality 100 "$PDF_OUTPUT"
    fi

    echo -e "${GREEN}✓ PDF created:${NC} $PDF_OUTPUT"
}

function get_stats() {
    COMPRESSED_SIZE=$(du -sh "$SPREAD_OUTPUT_DIR" | cut -f1)
    PDF_SIZE=$(du -sh "$PDF_OUTPUT" | cut -f1)

    # Step 3: Create metadata file
    echo -e "${BLUE}Step 3: Creating metadata...${NC}"

    # Load novel metadata
    NOVEL_FILE="output/book_${WORKFLOW_ID}/novel.md"
    TITLE="Graphic Novel"
    SUBTITLE=""

    if [ -f "$NOVEL_FILE" ]; then
        TITLE=$(grep "^# " "$NOVEL_FILE" | head -1 | sed 's/^# //')
        SUBTITLE=$(grep "^## Subtitle:" "$NOVEL_FILE" | head -1 | sed 's/^## Subtitle: //')
    fi

    cat > "${OUTPUT_DIR}/metadata.txt" << EOF
Graphic Novel Metadata
======================

Title: $TITLE
Subtitle: $SUBTITLE
Workflow ID: $WORKFLOW_ID
Generated: $(date)

Statistics:
-----------
Total Pages: $TOTAL_PAGES
Chapters: $(ls output/book_${WORKFLOW_ID}/chapter_*.json 2>/dev/null | wc -l | tr -d ' ')
Compression Quality: $QUALITY ($COMPRESS_QUALITY%)
Compressed Images Size: $COMPRESSED_SIZE
PDF Size: $PDF_SIZE

Files:
------
PDF: ${PDF_OUTPUT}
Compressed Images: ${COMPRESSED_DIR}/
Original Pages: ${PAGES_DIR}/
EOF

    echo -e "${GREEN}✓ Metadata created${NC}"
    echo ""

    # Summary
    echo -e "${BLUE}================================${NC}"
    echo -e "${GREEN}✓ Graphic Novel Complete!${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
    echo "Title: $TITLE"
    if [ -n "$SUBTITLE" ]; then
        echo "Subtitle: $SUBTITLE"
    fi
    echo ""
    echo "Statistics:"
    echo "  Pages: $TOTAL_PAGES"
    echo "  Quality: $QUALITY"
    echo "  Compressed size: $COMPRESSED_SIZE"
    echo "  PDF size: $PDF_SIZE"
    echo ""
    echo "Output files:"
    echo "  PDF: ${PDF_OUTPUT}"
    echo "  Compressed images: ${COMPRESSED_DIR}/"
    echo "  Metadata: ${OUTPUT_DIR}/metadata.txt"
    echo ""
    echo -e "${BLUE}================================${NC}"
    echo ""
    echo "Open PDF:"
    echo "  open ${PDF_OUTPUT}"
    echo ""
}

compress_images
echo -e "${GREEN}✓ All images compressed${NC}"
echo ""

get_spread
echo -e "${GREEN}✓ All spreads for 2/2 pages ${NC}"
echo ""


create_pdf
echo -e "${BLUE}Step 2: Creating PDF...${NC}"
echo ""


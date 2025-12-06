#!/bin/bash
# Full book generation script - generates all chapters and pages from novel.md
# Usage: ./scripts/generate_full_book.sh <workflow_id>

set -e

WORKFLOW_ID=$1

if [ -z "$WORKFLOW_ID" ]; then
    echo "Usage: $0 <workflow_id>"
    echo "Example: $0 43e21caa"
    exit 1
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log file
LOG_DIR="output/book_${WORKFLOW_ID}/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/full_generation_$(date +%Y%m%d_%H%M%S).log"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Full Book Generation${NC}"
echo -e "${BLUE}================================${NC}"
echo -e "Workflow ID: ${GREEN}${WORKFLOW_ID}${NC}"
echo -e "Log file: ${LOG_FILE}"
echo -e "${BLUE}================================${NC}"
echo ""

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to log error and exit
error_exit() {
    echo -e "${RED}[ERROR] $1${NC}" | tee -a "$LOG_FILE"
    exit 1
}

# Check if novel exists, generate if needed
NOVEL_FILE="output/book_${WORKFLOW_ID}/novel.md"
if [ ! -f "$NOVEL_FILE" ]; then
    log "Novel not found, generating content first..."
    log "=========================================="
    log "STEP 0: Generating Novel Content"
    log "=========================================="
    
    if python cinema/cmd/krearts.py book "$WORKFLOW_ID" --continue >> "$LOG_FILE" 2>&1; then
        log "✓ Novel content generated"
    else
        error_exit "Failed to generate novel content"
    fi
    
    # Verify novel was created
    if [ ! -f "$NOVEL_FILE" ]; then
        error_exit "Novel generation completed but file not found: $NOVEL_FILE"
    fi
fi

log "✓ Found novel: $NOVEL_FILE"

# Count chapters in novel (try different heading formats)
CHAPTER_COUNT=$(grep -c "^### Chapter" "$NOVEL_FILE" || grep -c "^## Chapter" "$NOVEL_FILE" || grep -c "^# Chapter" "$NOVEL_FILE" || echo "0")
log "✓ Detected $CHAPTER_COUNT chapters in novel"

if [ "$CHAPTER_COUNT" -eq 0 ]; then
    error_exit "No chapters found in novel"
fi

# Reset workflow state
log "=========================================="
log "Resetting workflow state..."
log "=========================================="

WORKFLOW_STATE="output/book_${WORKFLOW_ID}/workflow_state.json"
if [ -f "$WORKFLOW_STATE" ]; then
    python -c "
import json
with open('$WORKFLOW_STATE', 'r') as f:
    state = json.load(f)

print(f'Before reset:')
print(f'  chapters_generated: {state.get(\"chapters_generated\", [])}')
print(f'  pages_generated: {state.get(\"pages_generated\", [])}')

# Reset generation state
state['chapters_generated'] = []
state['pages_generated'] = []
state['current_stage'] = 'chapters'

with open('$WORKFLOW_STATE', 'w') as f:
    json.dump(state, f, indent=2)

print(f'After reset:')
print(f'  chapters_generated: {state[\"chapters_generated\"]}')
print(f'  pages_generated: {state[\"pages_generated\"]}')
" | tee -a "$LOG_FILE"
    
    log "✓ Workflow state reset"
else
    log "⚠ Workflow state file not found, will be created during generation"
fi

echo ""
echo -e "${YELLOW}Starting generation...${NC}"
echo ""

# Step 1: Generate all chapter JSONs
log "=========================================="
log "STEP 1: Generating Chapter JSONs"
log "=========================================="

for ((i=1; i<=CHAPTER_COUNT; i++)); do
    log "Generating Chapter $i JSON..."
    
    if python cinema/cmd/krearts.py book "$WORKFLOW_ID" --chapters "$i" >> "$LOG_FILE" 2>&1; then
        log "✓ Chapter $i JSON generated"
    else
        error_exit "Failed to generate Chapter $i JSON"
    fi
    
    # Sleep between chapters to avoid rate limits
    if [ $i -lt $CHAPTER_COUNT ]; then
        log "Sleeping 60 seconds before next chapter..."
        sleep 60
    fi
done

log "✓ All chapter JSONs generated"
echo ""

# Step 2: Generate pages for each chapter
log "=========================================="
log "STEP 2: Generating Pages"
log "=========================================="

# Count total pages across all chapters
TOTAL_PAGES=0
for ((i=1; i<=CHAPTER_COUNT; i++)); do
    CHAPTER_FILE="output/book_${WORKFLOW_ID}/chapter_$(printf '%02d' $i).json"
    if [ -f "$CHAPTER_FILE" ]; then
        # Count pages in this chapter
        PAGE_COUNT=$(python -c "
import json
with open('$CHAPTER_FILE', 'r') as f:
    data = json.load(f)
    pages = 0
    for ch in data.get('chapters', []):
        for scene in ch.get('scenes', []):
            pages += len(scene.get('pages', []))
    print(pages)
" 2>/dev/null || echo "0")
        
        log "Chapter $i has $PAGE_COUNT pages"
        TOTAL_PAGES=$((TOTAL_PAGES + PAGE_COUNT))
    fi
done

log "Total pages to generate: $TOTAL_PAGES"
echo ""

# Generate all pages in batches of 10 to avoid issues
log "Generating all $TOTAL_PAGES pages in batches..."

BATCH_SIZE=10
for ((start=1; start<=TOTAL_PAGES; start+=BATCH_SIZE)); do
    end=$((start + BATCH_SIZE - 1))
    if [ $end -gt $TOTAL_PAGES ]; then
        end=$TOTAL_PAGES
    fi
    
    # Build page range
    PAGE_RANGE=""
    for ((p=start; p<=end; p++)); do
        if [ -z "$PAGE_RANGE" ]; then
            PAGE_RANGE="$p"
        else
            PAGE_RANGE="$PAGE_RANGE,$p"
        fi
    done
    
    log "Generating pages $start-$end..."
    if python cinema/cmd/krearts.py chapters "$WORKFLOW_ID" --pages "$PAGE_RANGE" >> "$LOG_FILE" 2>&1; then
        log "✓ Pages $start-$end generated"
    else
        log "⚠ Warning: Some pages in batch $start-$end may have failed"
    fi
done

log "✓ All pages generated"

echo ""
log "=========================================="
log "GENERATION COMPLETE"
log "=========================================="
log "Workflow ID: $WORKFLOW_ID"
log "Chapters: $CHAPTER_COUNT"
log "Pages: $TOTAL_PAGES"
log "Output: output/book_${WORKFLOW_ID}/"
log "Log: $LOG_FILE"
log "=========================================="

echo ""
echo -e "${GREEN}✓ Full book generation complete!${NC}"
echo -e "Output: ${BLUE}output/book_${WORKFLOW_ID}/${NC}"
echo -e "Log: ${BLUE}${LOG_FILE}${NC}"

#!/bin/bash
# Continue generating remaining pages
# Usage: ./scripts/continue_pages.sh <workflow_id>

WORKFLOW_ID=$1

if [ -z "$WORKFLOW_ID" ]; then
    echo "Usage: $0 <workflow_id>"
    exit 1
fi

# Get total pages and generated count
STATS=$(python -c "
import json
from pathlib import Path

total_pages = 0
for i in range(1, 20):
    chapter_file = Path(f'output/book_${WORKFLOW_ID}/chapter_{i:02d}.json')
    if chapter_file.exists():
        with open(chapter_file, 'r') as f:
            data = json.load(f)
            for ch in data.get('chapters', []):
                for scene in ch.get('scenes', []):
                    total_pages += len(scene.get('pages', []))

with open('output/book_${WORKFLOW_ID}/workflow_state.json', 'r') as f:
    state = json.load(f)

generated = len(state.get('pages_generated', []))
print(f'{total_pages} {generated}')
")

TOTAL=$(echo $STATS | cut -d' ' -f1)
GENERATED=$(echo $STATS | cut -d' ' -f2)
REMAINING=$((TOTAL - GENERATED))

echo "================================"
echo "Continue Page Generation"
echo "================================"
echo "Total pages: $TOTAL"
echo "Generated: $GENERATED"
echo "Remaining: $REMAINING"
echo ""

if [ $REMAINING -eq 0 ]; then
    echo "✓ All pages already generated!"
    exit 0
fi

echo "Generating remaining $REMAINING pages..."
echo ""

# Generate in batches of 10
BATCH_SIZE=10
for ((i=GENERATED+1; i<=TOTAL; i+=BATCH_SIZE)); do
    end=$((i + BATCH_SIZE - 1))
    if [ $end -gt $TOTAL ]; then
        end=$TOTAL
    fi
    
    # Build page range
    PAGE_RANGE=""
    for ((p=i; p<=end; p++)); do
        if [ -z "$PAGE_RANGE" ]; then
            PAGE_RANGE="$p"
        else
            PAGE_RANGE="$PAGE_RANGE,$p"
        fi
    done
    
    echo "Generating pages $i-$end..."
    python cinema/cmd/krearts.py chapters "$WORKFLOW_ID" --pages "$PAGE_RANGE"
    
    if [ $? -eq 0 ]; then
        echo "✓ Batch complete"
    else
        echo "✗ Batch failed"
        exit 1
    fi
    
    echo ""
done

echo "================================"
echo "✓ All pages generated!"
echo "================================"

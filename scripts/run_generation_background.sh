#!/bin/bash
# Run full book generation in background with progress tracking
# Usage: ./scripts/run_generation_background.sh <workflow_id> [--no-reset]

WORKFLOW_ID=$1
NO_RESET=false

if [ -z "$WORKFLOW_ID" ]; then
    echo "Usage: $0 <workflow_id> [--no-reset]"
    echo "Example: $0 43e21caa"
    echo "         $0 43e21caa --no-reset  # Continue from current state"
    exit 1
fi

# Check for --no-reset flag
if [ "$2" = "--no-reset" ]; then
    NO_RESET=true
fi

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Create PID file directory
PID_DIR="output/book_${WORKFLOW_ID}/logs"
mkdir -p "$PID_DIR"
PID_FILE="${PID_DIR}/generation.pid"
STATUS_FILE="${PID_DIR}/generation.status"

# Check if already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}Generation already running (PID: $OLD_PID)${NC}"
        echo "To check status: ./scripts/check_generation_status.sh $WORKFLOW_ID"
        echo "To stop: kill $OLD_PID"
        exit 1
    else
        echo "Removing stale PID file"
        rm "$PID_FILE"
    fi
fi

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Starting Background Generation${NC}"
echo -e "${BLUE}================================${NC}"
echo -e "Workflow ID: ${GREEN}${WORKFLOW_ID}${NC}"
echo ""

# Initialize status file
cat > "$STATUS_FILE" <<EOF
{
  "workflow_id": "$WORKFLOW_ID",
  "status": "starting",
  "started_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "current_stage": "initialization",
  "chapters_completed": 0,
  "pages_completed": 0,
  "total_chapters": 0,
  "total_pages": 0
}
EOF

# Start generation in background
nohup bash scripts/generate_full_book.sh "$WORKFLOW_ID" > "${PID_DIR}/generation_output.log" 2>&1 &
GENERATION_PID=$!

# Save PID
echo "$GENERATION_PID" > "$PID_FILE"

# Update status
python -c "
import json
with open('$STATUS_FILE', 'r') as f:
    status = json.load(f)
status['status'] = 'running'
status['pid'] = $GENERATION_PID
with open('$STATUS_FILE', 'w') as f:
    json.dump(status, f, indent=2)
"

echo -e "${GREEN}✓ Generation started in background${NC}"
echo -e "PID: ${BLUE}${GENERATION_PID}${NC}"
echo ""
echo "Commands:"
echo -e "  Check status: ${BLUE}./scripts/check_generation_status.sh $WORKFLOW_ID${NC}"
echo -e "  View logs:    ${BLUE}tail -f ${PID_DIR}/generation_output.log${NC}"
echo -e "  Stop:         ${BLUE}kill ${GENERATION_PID}${NC}"
echo ""

#!/bin/bash
# Check status of background generation
# Usage: ./scripts/check_generation_status.sh <workflow_id>

WORKFLOW_ID=$1

if [ -z "$WORKFLOW_ID" ]; then
    echo "Usage: $0 <workflow_id>"
    echo "Example: $0 43e21caa"
    exit 1
fi

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PID_DIR="output/book_${WORKFLOW_ID}/logs"
PID_FILE="${PID_DIR}/generation.pid"
STATUS_FILE="${PID_DIR}/generation.status"
LOG_FILE="${PID_DIR}/generation_output.log"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Generation Status${NC}"
echo -e "${BLUE}================================${NC}"
echo -e "Workflow ID: ${GREEN}${WORKFLOW_ID}${NC}"
echo ""

# Check if PID file exists
if [ ! -f "$PID_FILE" ]; then
    echo -e "${YELLOW}No generation process found${NC}"
    echo "Start with: ./scripts/run_generation_background.sh $WORKFLOW_ID"
    exit 0
fi

# Read PID
PID=$(cat "$PID_FILE")

# Check if process is running
if ps -p "$PID" > /dev/null 2>&1; then
    echo -e "Status: ${GREEN}RUNNING${NC}"
    echo -e "PID: ${BLUE}${PID}${NC}"
else
    echo -e "Status: ${RED}STOPPED${NC}"
    echo -e "PID: ${BLUE}${PID}${NC} (not running)"
    
    # Check if completed successfully
    if [ -f "$LOG_FILE" ]; then
        if grep -q "GENERATION COMPLETE" "$LOG_FILE"; then
            echo -e "${GREEN}✓ Generation completed successfully${NC}"
        else
            echo -e "${RED}✗ Generation may have failed${NC}"
            echo "Check logs: tail -50 $LOG_FILE"
        fi
    fi
fi

echo ""

# Show workflow state
WORKFLOW_STATE="output/book_${WORKFLOW_ID}/workflow_state.json"
if [ -f "$WORKFLOW_STATE" ]; then
    echo -e "${BLUE}Workflow Progress:${NC}"
    python -c "
import json
with open('$WORKFLOW_STATE', 'r') as f:
    state = json.load(f)

print(f\"  Chapters generated: {len(state.get('chapters_generated', []))}\")
print(f\"  Pages generated: {len(state.get('pages_generated', []))}\")

if state.get('chapters_generated'):
    print(f\"  Chapter list: {sorted(state['chapters_generated'])}\")
"
    echo ""
fi

# Show recent log entries
if [ -f "$LOG_FILE" ]; then
    echo -e "${BLUE}Recent Activity (main log):${NC}"
    tail -10 "$LOG_FILE" | sed 's/^/  /'
    echo ""
fi

# Show most recent workflow log
WORKFLOW_LOG=$(ls -t workflow_logs/workflow_${WORKFLOW_ID}_*.log 2>/dev/null | head -1)
if [ -n "$WORKFLOW_LOG" ]; then
    echo -e "${BLUE}Recent Activity (workflow log):${NC}"
    echo -e "  Log: ${WORKFLOW_LOG}"
    tail -5 "$WORKFLOW_LOG" | grep -E "(Chapter|Scene|Page|Panel|✓|✅|❌|ERROR)" | sed 's/^/  /' || echo "  (generating...)"
    echo ""
fi

echo -e "${BLUE}================================${NC}"
echo "Commands:"
echo -e "  Main log:     ${BLUE}tail -f $LOG_FILE${NC}"
if [ -n "$WORKFLOW_LOG" ]; then
    echo -e "  Workflow log: ${BLUE}tail -f $WORKFLOW_LOG${NC}"
fi
echo -e "  Stop process: ${BLUE}kill $PID${NC}"
echo -e "${BLUE}================================${NC}"

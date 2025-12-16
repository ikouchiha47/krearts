#!/bin/bash
# Reset a workflow's chapter generation state

if [ -z "$1" ]; then
    echo "Usage: $0 <workflow_id>"
    echo "Example: $0 c778f39d"
    exit 1
fi

WORKFLOW_ID="$1"

cd "$(dirname "$0")/.."

echo "Resetting chapters_generated for workflow: $WORKFLOW_ID"
sqlite3 cinema_server.db "UPDATE workflow_states SET state_json = json_set(state_json, '\$.chapters_generated', json('[]')) WHERE id = '$WORKFLOW_ID'"

echo "✅ Reset complete. Workflow $WORKFLOW_ID can now regenerate chapters."

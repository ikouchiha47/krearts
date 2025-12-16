#!/bin/bash
# Start cyberpunk detective book generation
# Inspired by Altered Carbon

set -e

echo "================================"
echo "Cyberpunk Detective Book"
echo "Altered Carbon Style"
echo "================================"
echo ""

# Initialize workflow
echo "🚀 Initializing workflow..."
python cinema/cmd/krearts.py init book --config configs/altered_carbon_detective.json

# The init command will output the workflow ID
# You'll need to copy it and use it for the next steps

echo ""
echo "================================"
echo "Next Steps:"
echo "================================"
echo ""
echo "1. Copy the workflow ID from above"
echo "2. Generate content:"
echo "   python cinema/cmd/krearts.py book <workflow_id> --continue"
echo ""
echo "3. Generate chapters:"
echo "   python cinema/cmd/krearts.py book <workflow_id> --chapters all"
echo ""
echo "4. Generate pages:"
echo "   python cinema/cmd/krearts.py chapters <workflow_id> --pages 1,10"
echo ""
echo "Or use the full generation script:"
echo "   ./scripts/run_generation_background.sh <workflow_id>"
echo ""

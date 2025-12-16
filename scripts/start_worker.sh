#!/bin/bash
# Start the background worker

cd "$(dirname "$0")/.."
source .venv/bin/activate
python -m cinema.server.worker

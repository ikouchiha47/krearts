#!/bin/bash
# Start the FastAPI server

cd "$(dirname "$0")/.."
source .venv/bin/activate
uvicorn cinema.server.app:app --reload --port 8000

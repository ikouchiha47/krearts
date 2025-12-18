#!/bin/bash
set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Activate virtual environment
source .venv/bin/activate

# Create output directory if it doesn't exist
mkdir -p /app/output

# Initialize database if needed
if [ ! -f cinema.db ]; then
    echo "Initializing database..."
    python -c "
from cinema.db.database import init_db
init_db()
print('Database initialized')
"
fi

# Start services based on command
case "$1" in
    api)
        echo "Starting API server..."
        exec uvicorn cinema.server.app:app --host 0.0.0.0 --port 8000
        ;;
    worker)
        echo "Starting worker..."
        exec python -m cinema.server.worker
        ;;
    frontend)
        echo "Starting frontend..."
        cd frontend && exec npm run dev -- --host 0.0.0.0 --port 5173
        ;;
    all|"")
        echo "Starting all services with runit..."
        exec runsvdir /etc/service
        ;;
    *)
        echo "Usage: $0 {api|worker|frontend|all}"
        exit 1
        ;;
esac
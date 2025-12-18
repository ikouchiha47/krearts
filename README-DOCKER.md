# Cinema AI - Docker Deployment

## Quick Start

```bash
# Build and start all services
make deploy

# Or manually
docker-compose up --build -d
```

**Services:**
- API: http://localhost:8000
- Frontend: http://localhost:5173 (if available)
- Health: http://localhost:8000/health

## Architecture

Single Docker container running 3 processes via runit:
- **API Server**: `uvicorn cinema.server.app:app --port 8000`
- **Worker**: `python -m cinema.server.worker`
- **Frontend**: `npm run dev --port 5173` (if exists)

## Environment

Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
# Edit .env with your API keys
```

## Commands

```bash
# Development
make dev              # Start with live reload
make logs             # View all logs
make shell            # Get container shell

# Production  
make prod             # Start in production mode
make restart          # Restart services
make status           # Check service status

# Maintenance
make clean            # Stop and clean up
make test             # Test build
```

## Volumes

Only `/app/output` is mounted for generated files:
- Stories, images, videos
- SQLite databases are internal (no persistence needed for demo)

## Scaling

To run services separately:
```yaml
# Uncomment in docker-compose.yml
services:
  cinema-api:
    # API only
  cinema-worker:  
    # Worker only
```

## Troubleshooting

```bash
# Check logs
docker-compose logs cinema

# Get shell access
docker-compose exec cinema bash

# Check processes inside container
docker-compose exec cinema ps aux

# Restart specific service
docker-compose exec cinema sv restart api
docker-compose exec cinema sv restart worker
```

## Health Checks

- Container: `curl http://localhost:8000/health`
- Individual services monitored by runit
- Auto-restart on failure
# Cinema AI Story Generator - Docker Commands

.PHONY: build up down logs shell clean test deploy

# Build the Docker image
build:
	docker-compose build

# Start all services
up:
	docker-compose up -d

# Stop all services
down:
	docker-compose down

# View logs
logs:
	docker-compose logs -f

# Get a shell in the container
shell:
	docker-compose exec cinema bash

# Clean up everything
clean:
	docker-compose down -v
	docker system prune -f

# Test the build
test:
	docker build -t cinema-test .
	docker run --rm cinema-test api --help

# Deploy (build and start)
deploy: build up
	@echo "Cinema AI deployed!"
	@echo "API: http://localhost:8000"
	@echo "Frontend: http://localhost:5173"
	@echo "Health: http://localhost:8000/health"

# Quick development setup
dev:
	@echo "Starting development environment..."
	docker-compose up --build

# Production deployment
prod:
	@echo "Starting production environment..."
	docker-compose -f docker-compose.yml up -d --build

# View API logs only
api-logs:
	docker-compose logs -f cinema

# Restart services
restart:
	docker-compose restart

# Check status
status:
	docker-compose ps
	@echo ""
	@echo "Health check:"
	@curl -s http://localhost:8000/health || echo "API not ready"
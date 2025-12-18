# Multi-stage build for Cinema AI Story Generator
FROM python:3.12-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    runit \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies (no dev dependencies)
RUN poetry config virtualenvs.in-project true && \
    poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY cinema ./cinema
COPY knowledge ./knowledge
COPY .env.example ./.env

# Create output directory
RUN mkdir -p /app/output

# Setup runit services
RUN mkdir -p /etc/service/api /etc/service/worker /etc/service/frontend

# API service
RUN echo '#!/bin/sh\n\
cd /app\n\
source .venv/bin/activate\n\
exec uvicorn cinema.server.app:app --host 0.0.0.0 --port 8000 2>&1' > /etc/service/api/run && \
    chmod +x /etc/service/api/run

# Worker service
RUN echo '#!/bin/sh\n\
cd /app\n\
source .venv/bin/activate\n\
exec python -m cinema.server.worker 2>&1' > /etc/service/worker/run && \
    chmod +x /etc/service/worker/run

# Frontend service (if exists)
RUN if [ -d "frontend" ]; then \
    echo '#!/bin/sh\n\
cd /app/frontend\n\
exec npm run dev -- --host 0.0.0.0 --port 5173 2>&1' > /etc/service/frontend/run && \
    chmod +x /etc/service/frontend/run; \
fi

# Expose ports
EXPOSE 8000 5173

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Copy entrypoint
COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

# Start with entrypoint
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["all"]

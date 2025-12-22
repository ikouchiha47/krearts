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
COPY . .
COPY .env.example ./.env

# Create output directory
RUN mkdir -p /app/output

# Setup runit services
RUN mkdir -p /etc/service/api /etc/service/worker /etc/service/frontend

RUN cp /app/infra/frontend /etc/service/frontend/run && \
    cp /app/infra/server /etc/service/api/run && \
    cp /app/infra/worker /etc/service/worker/run

# Expose ports
EXPOSE 8000 5173

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

# Start with entrypoint
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["all"]

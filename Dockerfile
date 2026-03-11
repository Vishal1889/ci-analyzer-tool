# CI Analyzer Tool — Docker image (CLI mode, no GUI)
# Usage:
#   docker run --rm \
#     -v $(pwd)/.env:/app/.env \
#     -v $(pwd)/runs:/app/runs \
#     ghcr.io/vishal1889/ci-analyzer:latest

FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (better layer caching)
COPY requirements-cli.txt .
RUN pip install --no-cache-dir -r requirements-cli.txt

# Copy application source
COPY src/ ./src/
COPY main.py .

# Output directory — mount a host directory here to persist results
VOLUME ["/app/runs"]

ENTRYPOINT ["python", "main.py"]
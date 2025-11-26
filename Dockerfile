# Use Python 3.11 slim as base
FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffer output
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Install only the build dependency we need
RUN apt-get update && apt-get install -y --no-install-recommends gcc \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Copy requirements early for caching
COPY requirements.txt .

# Install Python packages
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install "fastapi[standard]" "uvicorn[standard]" sqlmodel

# Copy the entire project
# Note: Environment variables should be passed at runtime via docker-compose or -e flags
COPY . .

# Make sure .env is readable by appuser and create necessary dirs
RUN chown -R appuser:appuser /app && \
    mkdir -p /app/api

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import requests; exit(0 if requests.get('http://localhost:8000/health', timeout=2).status_code == 200 else 1)"

# Start the application
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4"]
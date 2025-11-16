# Multi-stage build for production-ready FastAPI application
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appuser . .

# Copy and set permissions for entrypoint script
COPY --chown=appuser:appuser entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Switch to non-root user
USER appuser

# Expose port (Railway will use PORT env var, but we expose 8000 as fallback)
EXPOSE 8000

# Note: Railway handles health checks via healthcheckPath in railway.json/toml
# We don't need Docker HEALTHCHECK as it can conflict with Railway's health check system

# Run the application using entrypoint script
# Railway sets PORT environment variable, default to 8000 if not set
ENTRYPOINT ["/app/entrypoint.sh"]


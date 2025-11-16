#!/bin/sh
# Entrypoint script for Railway deployment
# This script runs database migrations and starts the server

set -e

echo "=========================================="
echo "ENTRYPOINT SCRIPT STARTING"
echo "=========================================="
echo "Starting Post-Meeting Generator Backend..."
echo "Running database migrations..."

# Run database migrations
alembic upgrade head

echo "Migrations completed successfully!"

# Debug: Show PORT value (Railway sets this automatically)
if [ -z "$PORT" ]; then
    echo "WARNING: PORT environment variable is not set, using default 8000"
    ACTUAL_PORT=8000
else
    echo "PORT environment variable is set to: $PORT"
    ACTUAL_PORT=$PORT
fi
echo "Starting uvicorn server on port ${ACTUAL_PORT}..."

# Start the server
# Railway sets PORT environment variable
echo "=========================================="
echo "Starting uvicorn with:"
echo "  Host: 0.0.0.0"
echo "  Port: ${ACTUAL_PORT}"
echo "  Workers: ${WORKERS:-4}"
echo "=========================================="
exec uvicorn app.main:app --host 0.0.0.0 --port ${ACTUAL_PORT} --workers ${WORKERS:-4}


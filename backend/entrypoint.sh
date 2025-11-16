#!/bin/sh
# Entrypoint script for Railway deployment
# This script runs database migrations and starts the server

set -e

echo "Starting Post-Meeting Generator Backend..."
echo "Running database migrations..."

# Run database migrations
alembic upgrade head

echo "Migrations completed successfully!"
echo "Starting uvicorn server on port ${PORT:-8000}..."

# Start the server
# Railway sets PORT environment variable
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WORKERS:-4}


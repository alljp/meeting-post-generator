#!/bin/sh
# This script runs as part of nginx's docker-entrypoint.sh sequence
# It modifies the nginx config to use Railway's dynamic PORT

# Railway provides PORT environment variable
# Default to 80 if not set (for local development)
PORT=${PORT:-80}

echo "=========================================="
echo "Configuring Nginx for Railway..."
echo "PORT environment variable is set to: $PORT"
echo "=========================================="

# Modify the nginx config to use Railway's PORT
# This runs BEFORE nginx starts (as part of docker-entrypoint.sh)
# Scripts in /docker-entrypoint.d/ run in order, and our script (99-*) runs last
# This means nginx setup scripts have already run, so we can safely modify the config

# Replace listen 80 with listen ${PORT} in the config
if [ -f /etc/nginx/conf.d/default.conf ]; then
    echo "Updating nginx config to use port $PORT..."
    sed -i "s/listen 80;/listen ${PORT};/g" /etc/nginx/conf.d/default.conf
    sed -i "s/listen \[::\]:80;/listen [::]:${PORT};/g" /etc/nginx/conf.d/default.conf 2>/dev/null || true
    echo "✓ Nginx config updated to listen on port $PORT"
    
    # Verify the change
    if grep -q "listen ${PORT};" /etc/nginx/conf.d/default.conf; then
        echo "✓ Config verification: Port $PORT found in nginx config"
    else
        echo "✗ Warning: Port update may have failed. Config contents:"
        grep "listen" /etc/nginx/conf.d/default.conf || echo "No listen directive found!"
    fi
else
    echo "✗ Error: /etc/nginx/conf.d/default.conf not found!"
    exit 1
fi

# nginx's docker-entrypoint.sh will start nginx after this script completes
echo "Nginx configuration complete, waiting for nginx to start..."

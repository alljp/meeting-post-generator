#!/bin/sh
# This script runs as part of nginx's docker-entrypoint.sh sequence
# It ensures PORT is set before envsubst processes the template
# Scripts in /docker-entrypoint.d/ run in order - this runs BEFORE envsubst (20-*)

# Railway provides PORT environment variable
# If not set, default to 80 (for local development)
if [ -z "$PORT" ]; then
    export PORT=80
    echo "PORT not set, using default: 80"
else
    export PORT
    echo "PORT environment variable is set to: $PORT"
fi

# nginx's envsubst (script 20-*) will process the template and substitute ${PORT}
# No further action needed - just ensure PORT is exported

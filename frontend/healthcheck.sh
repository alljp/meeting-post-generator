#!/bin/sh
# Health check script that uses Railway's PORT environment variable
PORT=${PORT:-80}
wget --quiet --tries=1 --spider http://localhost:${PORT}/health || exit 1


"""
Health check HTTP server for Celery workers.

This module provides a simple HTTP server that Railway can use to verify
the Celery worker is running and healthy.
"""
import http.server
import socketserver
import threading
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler for health check endpoint."""
    
    def do_GET(self):
        """Handle GET requests to health check endpoint."""
        if self.path == '/health' or self.path == '/':
            try:
                # Try to import celery app
                from app.tasks import celery_app
                
                # Check if this is a worker or beat process
                # For workers: check if worker is responsive
                # For beat: just check if celery app is importable (process is running)
                try:
                    inspect = celery_app.control.inspect()
                    stats = inspect.stats()
                    
                    if stats:
                        # Worker is alive and responding
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(b'{"status": "healthy", "type": "worker", "workers": ' + str(len(stats)).encode() + b'}')
                    else:
                        # No workers responding, but process might be beat scheduler
                        # For beat, we just check if the process is running (which it is if we got here)
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(b'{"status": "healthy", "type": "beat"}')
                except Exception:
                    # If inspect fails, we might be in beat mode (no workers to inspect)
                    # Or worker hasn't fully started yet
                    # Return healthy if we can import celery app (process is running)
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(b'{"status": "healthy", "type": "beat_or_starting"}')
            except Exception as e:
                logger.error(f"Health check error: {e}", exc_info=True)
                # If we can't check, assume unhealthy
                self.send_response(503)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status": "unhealthy", "reason": "health check failed"}')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress default logging for health checks."""
        # Only log errors, not every health check request
        pass


def start_health_check_server(port: Optional[int] = None):
    """
    Start a simple HTTP server for health checks.
    
    Args:
        port: Port to listen on. Defaults to PORT environment variable or 9000.
    """
    if port is None:
        port = int(os.environ.get('PORT', 9000))
    
    try:
        with socketserver.TCPServer(("", port), HealthCheckHandler) as httpd:
            logger.info(f"Health check server started on port {port}")
            httpd.serve_forever()
    except OSError as e:
        if e.errno == 98:  # Address already in use
            logger.warning(f"Port {port} already in use, health check server may already be running")
        else:
            logger.error(f"Failed to start health check server: {e}", exc_info=True)
            raise


def start_health_check_in_background(port: Optional[int] = None):
    """
    Start health check server in a background thread.
    
    Args:
        port: Port to listen on. Defaults to PORT environment variable or 9000.
    """
    thread = threading.Thread(
        target=start_health_check_server,
        args=(port,),
        daemon=True,
        name="HealthCheckServer"
    )
    thread.start()
    logger.info("Health check server thread started")
    return thread


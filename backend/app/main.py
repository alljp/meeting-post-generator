import logging
import sys
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import api_router

# Fix for Windows: Set event loop policy to use SelectorEventLoop instead of ProactorEventLoop
# This is required for psycopg (async PostgreSQL driver) to work on Windows
if sys.platform == 'win32':
    # Windows uses ProactorEventLoop by default (Python 3.8+), but psycopg needs SelectorEventLoop
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    print("Windows detected: Using SelectorEventLoop for async database operations", flush=True)

# Configure logging with explicit handler to ensure output
log_level = logging.DEBUG if settings.DEBUG else logging.INFO

# IMPORTANT: Don't clear all handlers - uvicorn needs its handlers too
# Instead, just add our handler without clearing existing ones
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(log_level)
console_handler.setFormatter(
    logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
)

# Configure root logger - set level but don't clear handlers
root_logger = logging.getLogger()
root_logger.setLevel(log_level)
# Only add our handler if it's not already there
if not any(isinstance(h, logging.StreamHandler) and h.stream == sys.stdout for h in root_logger.handlers):
    root_logger.addHandler(console_handler)

# Configure specific loggers for our app
logging.getLogger("app").setLevel(log_level)
# Don't override uvicorn loggers - let them use their defaults

# Get logger for this module
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Post-Meeting Generator API",
    description="API for post-meeting social media content generator",
    version="1.0.0",
)

# Force immediate output to verify server is running
print("\n" + "="*80, flush=True)
print(f"BACKEND SERVER STARTING: {app.title} v{app.version}", flush=True)
print(f"Platform: {sys.platform}", flush=True)
if sys.platform == 'win32':
    print(f"Event loop policy: WindowsSelectorEventLoopPolicy (required for psycopg)", flush=True)
print(f"Debug mode: {settings.DEBUG}", flush=True)
print(f"Log level: {log_level}", flush=True)
print("="*80 + "\n", flush=True)

logger.info(f"Starting {app.title} v{app.version}")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Post-Meeting Generator API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


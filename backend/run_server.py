"""
Wrapper script to run uvicorn with proper Windows event loop policy.
This ensures SelectorEventLoop is used instead of ProactorEventLoop for psycopg compatibility.
"""
import sys
import asyncio
import uvicorn

# Fix for Windows: Set event loop policy BEFORE anything else
# This must happen before uvicorn creates any event loops
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    print("Windows detected: Set event loop policy to WindowsSelectorEventLoopPolicy", flush=True)

if __name__ == "__main__":
    # Run uvicorn with the same arguments as the original command
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


"""SmartKCET / ExamForge backend entry-point.

The application logic lives in the :mod:`smartkcet` package.  This file
exists so existing run commands (``python app.py``) keep working: it
imports the configured FastAPI ``app`` and starts Uvicorn.  The legacy
single-file layout was split into ``smartkcet/`` during the platform
upgrade refactor (task 1.1).

Run::

    python app.py
"""

from __future__ import annotations

import logging
import os
import socket  # noqa: F401  (kept for backward-compatible imports)
import subprocess
import sys
import time  # noqa: F401  (kept for backward-compatible imports)

import uvicorn

# Configure logging BEFORE importing the app so all modules get the config
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

from smartkcet.main import app  # re-exported so ``uvicorn app:app`` still works


def _free_port(port: int) -> None:
    """Best-effort cleanup of any process already listening on ``port``."""

    try:
        result = subprocess.run(
            ["netstat", "-ano"], capture_output=True, text=True
        )
        for line in result.stdout.split("\n"):
            if f":{port}" in line:
                pid = line.split()[-1]
                if pid.isdigit():
                    os.system(f"taskkill /PID {pid} /F 2>nul")
                break
    except Exception:
        pass


def main() -> None:
    import asyncio
    
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except AttributeError:
            pass
            
    port = int(os.getenv("SMARTKCET_PORT", "8000"))
    host = os.getenv("SMARTKCET_HOST", "127.0.0.1")
    _free_port(port)

    bar = "=" * 60
    print(f"\n{bar}")
    print("\U0001F680 ExamForge Backend Starting")
    print(bar)
    print(f"Server: http://{host}:{port}")
    print(f"Health: http://{host}:{port}/health")
    print(f"{bar}\n")

    # Set the event loop policy for Python 3.14 compatibility
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    uvicorn.run(
        app, 
        host=host, 
        port=port, 
        log_level="info",
        loop="asyncio"  # Explicitly set the event loop
    )


if __name__ == "__main__":
    sys.exit(main())

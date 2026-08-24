"""SmartKCET / ExamForge Flask backend entry-point.

Imports the configured Flask ``app`` and runs the WSGI server.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

from smartkcet.main import app


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
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except AttributeError:
            pass

    port = int(os.getenv("SMARTKCET_PORT", "8000"))
    host = os.getenv("SMARTKCET_HOST", "0.0.0.0")
    _free_port(port)

    bar = "=" * 60
    print(f"\n{bar}")
    print("🚀 ExamForge Flask Backend Starting")
    print(bar)
    print(f"Server: http://{host}:{port}")
    print(f"Health: http://{host}:{port}/api/health")
    print(f"{bar}\n")

    app.run(host=host, port=port, debug=False, threaded=True)


if __name__ == "__main__":
    sys.exit(main())

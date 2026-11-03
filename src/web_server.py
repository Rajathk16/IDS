"""Dedicated launcher entrypoint for DEVRAKSHAK Web Dashboard."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.core.logging_config import setup_logging
from src.web.server import run_web_server


def main() -> None:
    """Parse web server arguments and start the dashboard."""
    setup_logging()
    parser = argparse.ArgumentParser(
        description="DEVRAKSHAK Web-Based Management & Telemetry Dashboard"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host address to bind (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port number to listen on (default: 8000)"
    )

    args = parser.parse_args()
    run_web_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()


"""Start the Kiana RenderDoc MCP server over local streamable HTTP."""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.server import mcp


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    # FastMCP stores its HTTP binding in settings. Keep this endpoint local;
    # Kiana Studio is the process that exposes it to the desktop UI.
    mcp.settings.host = args.host
    mcp.settings.port = args.port
    mcp.settings.streamable_http_path = "/mcp"
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()

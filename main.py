#!/usr/bin/env python3
"""Entry point for the Typesense MCP server."""

import os

from src.server import create_server

transport = os.environ.get("MCP_TRANSPORT", "streamable-http")

mcp = create_server()

if __name__ == "__main__":
    mcp.run(transport=transport)

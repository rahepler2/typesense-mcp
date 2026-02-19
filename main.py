#!/usr/bin/env python3
"""Entry point for the Typesense MCP server."""

from src.server import create_server

mcp = create_server()

if __name__ == "__main__":
    mcp.run()

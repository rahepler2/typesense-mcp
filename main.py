#!/usr/bin/env python3
"""Entry point for the Typesense MCP server."""

import os

from src.server import CORS_MIDDLEWARE, create_server

transport = os.environ.get("MCP_TRANSPORT", "streamable-http")
host = os.environ.get("MCP_HOST", "0.0.0.0")
port = int(os.environ.get("MCP_PORT", "8000"))

mcp = create_server()

if __name__ == "__main__":
    if transport in ("streamable-http", "sse", "http"):
        mcp.run(
            transport=transport,
            host=host,
            port=port,
            stateless_http=True,
            middleware=[CORS_MIDDLEWARE],
        )
    else:
        mcp.run(transport=transport)

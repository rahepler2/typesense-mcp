"""Typesense MCP Server — main server module.

Provides hybrid search, natural language queries (v29.0), RAG retrieval,
and read-only collection introspection via the Model Context Protocol.
"""

from __future__ import annotations

import logging
import os

from fastmcp import FastMCP
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from .client import TypesenseClientManager
from .config import TypesenseConfig
from .tools import collections, rag, search

logger = logging.getLogger(__name__)

# CORS middleware for MS MCP Gateway, Open WebUI, and other browser-based clients
CORS_MIDDLEWARE = Middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)


def create_server(config: TypesenseConfig | None = None) -> FastMCP:
    """Create and configure the Typesense MCP server.

    Args:
        config: Optional Typesense connection configuration.
            If None, reads from environment variables.

    Returns:
        A configured FastMCP server instance ready to run.
    """
    mcp = FastMCP(
        "typesense-mcp",
        instructions="""Typesense MCP Server — read-only search interface for RAG applications.

This server connects to a Typesense 29.0+ cluster and provides search and
collection introspection tools. It does NOT provide write operations.

1. **Hybrid Search** — Combine keyword + semantic/vector search for best results.
   Use `hybrid_search` with both text and embedding fields in `query_by`.

2. **Natural Language Search** (v29.0) — Let an LLM convert natural language queries
   into structured Typesense filters and sorts automatically.
   Use `natural_language_search` with a pre-configured NL model ID.

3. **RAG Retrieval** — Search a metadata collection, then retrieve linked chunks
   from an embeddings collection using `rag_search_and_retrieve_chunks`.

4. **Collection Introspection** — List, describe, and analyze collections (read-only).

**Typical RAG workflow:**
1. Use `analyze_collection` to understand available collections and fields.
2. Use `hybrid_search` or `natural_language_search` to find relevant documents.
3. Use `rag_search_and_retrieve_chunks` or `get_document_chunks` to get content chunks.

**Filter syntax:** field:=value, field:!=value, field:>N, field:<N, field:[val1,val2]
Combine with && (AND) and || (OR).
""",
    )

    ts = TypesenseClientManager(config)
    ts_config = config or TypesenseConfig()
    logger.info(
        "Typesense target: %s://%s:%s",
        ts_config.protocol,
        ts_config.host,
        ts_config.port,
    )

    # Register read-only tool modules (search + collection introspection)
    collections.register(mcp, ts)
    search.register(mcp, ts)
    rag.register(mcp, ts)

    # --- Azure Container Apps health probes ---

    @mcp.custom_route("/health", methods=["GET"])
    async def health(request: Request) -> Response:
        """Liveness probe — confirms the process is running."""
        return JSONResponse({"status": "alive"})

    @mcp.custom_route("/ready", methods=["GET"])
    async def ready(request: Request) -> Response:
        """Readiness probe — checks Typesense connectivity."""
        try:
            result = ts.health()
            if result.get("ok"):
                return JSONResponse({"status": "ready"})
            logger.warning("Typesense health returned not ok: %s", result)
            return JSONResponse({"status": "not ready"}, status_code=503)
        except Exception as exc:
            logger.warning("Readiness probe failed: %s", exc)
            return JSONResponse({"status": "not ready", "error": str(exc)}, status_code=503)

    @mcp.custom_route("/startup", methods=["GET"])
    async def startup(request: Request) -> Response:
        """Startup probe — confirms the server process is running."""
        return JSONResponse({"status": "started"})

    return mcp

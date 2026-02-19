"""Typesense MCP Server — main server module.

Provides hybrid search, natural language queries (v29.0), RAG retrieval,
collection management, and document operations via the Model Context Protocol.
"""

from __future__ import annotations

from fastmcp import FastMCP

from .client import TypesenseClientManager
from .config import TypesenseConfig
from .tools import collections, documents, nl_models, rag, search


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
        instructions="""Typesense MCP Server — search engine interface for RAG applications.

This server connects to a Typesense 29.0+ cluster and provides:

1. **Hybrid Search** — Combine keyword + semantic/vector search for best results.
   Use `hybrid_search` with both text and embedding fields in `query_by`.

2. **Natural Language Search** (v29.0) — Let an LLM convert natural language queries
   into structured Typesense filters and sorts automatically.
   Set up a model with `create_nl_search_model`, then use `natural_language_search`.

3. **RAG Retrieval** — Search a metadata collection, then retrieve linked chunks
   from an embeddings collection using `rag_search_and_retrieve_chunks`.

4. **Collection Management** — List, describe, analyze, create, and modify collections.

5. **Document Operations** — CRUD operations, bulk import/export.

**Typical RAG workflow:**
1. Use `analyze_collection` to understand available collections and fields.
2. Use `hybrid_search` or `natural_language_search` to find relevant documents.
3. Use `rag_search_and_retrieve_chunks` or `get_document_chunks` to get content chunks.

**Filter syntax:** field:=value, field:!=value, field:>N, field:<N, field:[val1,val2]
Combine with && (AND) and || (OR).
""",
    )

    ts = TypesenseClientManager(config)

    # Register all tool modules
    collections.register(mcp, ts)
    search.register(mcp, ts)
    rag.register(mcp, ts)
    documents.register(mcp, ts)
    nl_models.register(mcp, ts)

    return mcp

# typesense-mcp

A read-only MCP (Model Context Protocol) server for [Typesense](https://typesense.org/) 29.0+, built for LLM RAG chatbot applications. Provides hybrid search, natural language queries, metadata-to-chunks retrieval, and collection introspection over Streamable HTTP.

## Features

- **Hybrid Search** — Combine keyword + semantic/vector search with configurable rank fusion
- **Natural Language Search** (v29.0) — LLM-powered intent detection that converts free-form queries into structured Typesense filters and sorts
- **RAG Retrieval** — Search metadata collections and retrieve linked chunks from embeddings collections via `doc_id`
- **Collection Introspection** — List, describe, and analyze collections (read-only, no write operations)
- **Multi-Search** — Federated search across multiple collections in one request
- **Azure-ready** — Built-in health, readiness, and startup probe endpoints for Azure Container Apps

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- A running Typesense 29.0+ cluster

## Configuration

Set the following environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `TYPESENSE_HOST` | `localhost` | Typesense server hostname |
| `TYPESENSE_PORT` | `8108` | Typesense server port |
| `TYPESENSE_PROTOCOL` | `http` | Protocol (`http` or `https`) |
| `TYPESENSE_API_KEY` | *(required)* | Your Typesense API key |
| `TYPESENSE_CONNECTION_TIMEOUT` | `10` | Connection timeout in seconds |
| `MCP_TRANSPORT` | `streamable-http` | Transport mode (`streamable-http` or `stdio`) |
| `MCP_HOST` | `0.0.0.0` | Server bind address |
| `MCP_PORT` | `8000` | Server port |

## Running the Server

### Local (pip / uv)

```bash
# Clone and install
git clone https://github.com/rahepler2/typesense-mcp.git
cd typesense-mcp

# Install with uv (recommended)
uv sync

# Or with pip
pip install -e .

# Run
python main.py
```

### Docker

```bash
# Build
docker build -t typesense-mcp .

# Run
docker run -p 8000:8000 \
  -e TYPESENSE_HOST=your-typesense-host \
  -e TYPESENSE_PORT=8108 \
  -e TYPESENSE_PROTOCOL=https \
  -e TYPESENSE_API_KEY=your-api-key \
  typesense-mcp
```

The server will be available at `http://localhost:8000/mcp`.

### Azure Container Apps

The server includes built-in health probe endpoints for Azure Container Apps:

| Endpoint | Probe Type | Behavior |
|----------|-----------|----------|
| `GET /health` | Liveness | Returns `200` if the process is alive |
| `GET /ready` | Readiness | Returns `200` if Typesense is reachable, `503` if not |
| `GET /startup` | Startup | Returns `200` once Typesense is reachable, `503` while starting |

Example probe configuration for your container app:

```yaml
probes:
  - type: Startup
    httpGet:
      path: /startup
      port: 8000
    initialDelaySeconds: 3
    periodSeconds: 5
    failureThreshold: 10
  - type: Liveness
    httpGet:
      path: /health
      port: 8000
    periodSeconds: 10
    failureThreshold: 3
  - type: Readiness
    httpGet:
      path: /ready
      port: 8000
    periodSeconds: 5
    failureThreshold: 3
```

## Claude Desktop / Claude Code Configuration

Add this to your MCP server config:

```json
{
  "mcpServers": {
    "typesense": {
      "command": "uv",
      "args": ["--directory", "/path/to/typesense-mcp", "run", "mcp", "run", "main.py"],
      "env": {
        "TYPESENSE_HOST": "your-host",
        "TYPESENSE_PORT": "8108",
        "TYPESENSE_PROTOCOL": "http",
        "TYPESENSE_API_KEY": "your-api-key"
      }
    }
  }
}
```

## Available Tools

### Collection Introspection (read-only)

| Tool | Description |
|------|-------------|
| `check_health` | Check Typesense cluster health |
| `list_collections` | List all collections with doc counts |
| `describe_collection` | Get full schema for a collection |
| `get_collection_fields` | Get concise field info (types, facets, embedding fields) |
| `analyze_collection` | Deep analysis: schema, samples, facet distributions, embedding fields |

### Search

| Tool | Description |
|------|-------------|
| `hybrid_search` | Combined keyword + semantic search with filters, facets, grouping |
| `keyword_search` | Keyword-only search |
| `natural_language_search` | NL query → structured filters via LLM (v29.0) |
| `multi_search` | Federated search across multiple collections |

### RAG Retrieval

| Tool | Description |
|------|-------------|
| `rag_search_and_retrieve_chunks` | Search metadata → fetch linked chunks by `doc_id` |
| `rag_hybrid_chunk_search` | Hybrid search directly in the chunks/embeddings collection |
| `get_document_chunks` | Get all chunks for a specific document by `doc_id` |

## Usage Examples

### Typical RAG Workflow

```
1. analyze_collection("my_metadata")     → Understand schema and data
2. hybrid_search("my_metadata", ...)     → Find relevant documents
3. rag_search_and_retrieve_chunks(       → Get chunks for top docs
     metadata_collection="my_metadata",
     chunks_collection="my_chunks",
     query="...",
     query_by="title,description,embedding"
   )
```

### Natural Language Search (v29.0)

```
1. create_nl_search_model({              → Set up the NL model
     "id": "my-model",
     "model_name": "google/gemini-2.5-flash",
     "api_key": "..."
   })
2. natural_language_search(              → Search with natural language
     collection_name="cars",
     query="red SUVs under $30k with good mpg",
     query_by="make,model,description",
     nl_model_id="my-model"
   )
```

### Filter Syntax

```
category:=electronics                    # Exact match
price:<100                              # Numeric comparison
brand:[Apple, Samsung]                  # Multiple values (OR)
status:!=archived                       # Not equal
category:=electronics && price:<100     # AND
category:=electronics || category:=books # OR
```

## Extending

The server is modular — each tool category is a separate module under `src/tools/`. To add new tools:

1. Create a new module in `src/tools/`
2. Define a `register(mcp, ts)` function that adds tools via `@mcp.tool()`
3. Import and register it in `src/server.py`

## License

MIT

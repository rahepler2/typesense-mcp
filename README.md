# typesense-mcp

An MCP (Model Context Protocol) server for [Typesense](https://typesense.org/) 29.0+, built for LLM RAG chatbot applications. Provides hybrid search, natural language queries, metadata-to-chunks retrieval, and full collection/document management.

## Features

- **Hybrid Search** — Combine keyword + semantic/vector search with configurable rank fusion
- **Natural Language Search** (v29.0) — LLM-powered intent detection that converts free-form queries into structured Typesense filters and sorts
- **RAG Retrieval** — Search metadata collections and retrieve linked chunks from embeddings collections via `doc_id`
- **Collection Management** — List, describe, analyze (with facet summaries and sample docs), create, update, delete
- **Document Operations** — CRUD, bulk import/export, filtered deletes
- **Multi-Search** — Federated search across multiple collections in one request
- **NL Model Management** — Configure and manage natural language search models (OpenAI, Gemini, Cloudflare, etc.)

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- A running Typesense 29.0+ cluster

## Installation

```bash
# Clone the repo
git clone https://github.com/rahepler2/typesense-mcp.git
cd typesense-mcp

# Install with uv (recommended)
uv sync

# Or with pip
pip install -e .
```

## Configuration

Set the following environment variables to connect to your Typesense cluster:

| Variable | Default | Description |
|----------|---------|-------------|
| `TYPESENSE_HOST` | `localhost` | Typesense server hostname |
| `TYPESENSE_PORT` | `8108` | Typesense server port |
| `TYPESENSE_PROTOCOL` | `http` | Protocol (`http` or `https`) |
| `TYPESENSE_API_KEY` | *(required)* | Your Typesense API key |
| `TYPESENSE_CONNECTION_TIMEOUT` | `10` | Connection timeout in seconds |

## Running the Server

```bash
# With uv
uv run mcp run main.py

# Or directly
python main.py
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

### Collection Management

| Tool | Description |
|------|-------------|
| `check_health` | Check Typesense cluster health |
| `list_collections` | List all collections with doc counts |
| `describe_collection` | Get full schema for a collection |
| `get_collection_fields` | Get concise field info (types, facets, embedding fields) |
| `analyze_collection` | Deep analysis: schema, samples, facet distributions, embedding fields |
| `create_collection` | Create a new collection from a JSON schema |
| `delete_collection` | Delete a collection |
| `update_collection_schema` | Add or drop fields on an existing collection |

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

### Document Operations

| Tool | Description |
|------|-------------|
| `get_document` | Retrieve a document by ID |
| `create_document` | Create a new document |
| `upsert_document` | Create or replace a document |
| `update_document` | Partially update a document |
| `delete_document` | Delete a document by ID |
| `delete_documents_by_filter` | Delete all documents matching a filter |
| `import_documents` | Bulk import documents |
| `export_documents` | Export documents (with optional filters) |

### NL Search Models (v29.0)

| Tool | Description |
|------|-------------|
| `create_nl_search_model` | Configure an LLM for natural language query understanding |
| `list_nl_search_models` | List all configured NL models |
| `get_nl_search_model` | Get details of an NL model |
| `update_nl_search_model` | Update an NL model's configuration |
| `delete_nl_search_model` | Remove an NL model |

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

The server is modular — each tool category is a separate module under `src/typesense_mcp/tools/`. To add new tools:

1. Create a new module in `src/typesense_mcp/tools/`
2. Define a `register(mcp, ts)` function that adds tools via `@mcp.tool()`
3. Import and register it in `src/typesense_mcp/server.py`

## License

MIT

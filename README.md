# typesense-mcp

MCP tools for searching policy/procedure documents in Typesense.

## Collection Architecture

This project uses a two-collection design to separate concerns and optimize different search patterns:

### Collection 1: `documents_metadata`

Stores document-level information for filtering, faceting, and display.

| Field | Type | Purpose |
|-------|------|---------|
| `id` | string | Primary key |
| `title` | string | Document title (searchable, infix) |
| `document_type` | string | policy, procedure, form |
| `department` | string | Owning department |
| `categories` | string[] | Classification tags |
| `status` | string | active, draft, archived, superseded |
| `effective_date` | int64 | Unix timestamp |
| `review_date` | int64 | Next review date |
| `version` | string | e.g., "2.1" |
| `author` | string | Document owner |
| `approver` | string | Who approved it |
| `summary` | string | Brief description |
| `source_url` | string | Link to original |
| `chunk_count` | int32 | Number of chunks |
| `created_at` | int64 | Unix timestamp |
| `updated_at` | int64 | Unix timestamp |

### Collection 2: `document_chunks`

Stores text chunks with embeddings for semantic and keyword search.

| Field | Type | Purpose |
|-------|------|---------|
| `id` | string | Composite: `{document_id}_{chunk_index}` |
| `document_id` | string | Foreign key to metadata |
| `chunk_index` | int32 | Order within document |
| `text` | string | The actual content |
| `embedding` | float[] | 1536-dim vector (OpenAI small) |
| `section_title` | string | Section heading |
| `page_number` | int32 | Source page |
| `document_type` | string | Denormalized for filtering |
| `department` | string | Denormalized for filtering |
| `status` | string | Denormalized for filtering |
| `document_title` | string | For display |
| `created_at` | int64 | Unix timestamp |

## Why Two Collections?

1. **Search efficiency** - Filter by metadata without loading embeddings
2. **Update flexibility** - Change metadata without re-embedding
3. **Query patterns** - Different queries hit different collections
4. **Cost optimization** - Smaller metadata collection for quick lookups

## Query Flow

```
User Question → Chatbot generates query
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
   Metadata Search         Semantic Search
   (filter/facet)          (vector + keyword)
        │                       │
        └───────────┬───────────┘
                    ▼
              Merge Results
                    │
                    ▼
            Return to Chatbot
```

## Search Patterns

See `src/typesense_mcp/search_examples.py` for detailed examples:

- **Semantic Search** - Natural language questions
- **Keyword Search** - Specific term lookup
- **Hybrid Search** - Combined vector + keyword
- **Filtered Search** - Constrained by metadata
- **Faceted Search** - For building filter UIs
- **Multi-Search** - Parallel queries

## Installation

```bash
pip install -e .
```

## Usage

```python
from typesense_mcp.collection_manager import CollectionManager, create_typesense_client
from typesense_mcp.schemas import DOCUMENTS_METADATA_SCHEMA, DOCUMENT_CHUNKS_SCHEMA

# Create client
client = create_typesense_client(
    host="localhost",
    port=8108,
    api_key="your-api-key"
)

# Create collections
manager = CollectionManager(client)
manager.create_collections(use_auto_embedding=True)

# Check stats
print(manager.get_collection_stats())
```

## Configuration

The chunks collection uses Typesense's built-in embedding with OpenAI:

```python
"embed": {
    "from": ["text"],
    "model_config": {
        "model_name": "openai/text-embedding-3-small",
        "api_key": "${OPENAI_API_KEY}",
    },
}
```

Set your `OPENAI_API_KEY` environment variable, or use the manual embedding schema if you want to generate embeddings yourself.

## Next Steps

- [ ] Implement MCP tools for chatbot integration
- [ ] Add document ingestion pipeline
- [ ] Create search result ranking/fusion logic

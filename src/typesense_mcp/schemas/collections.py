"""
Typesense Collection Schemas for Policy/Procedure Document Search

Architecture:
    - documents_metadata: Document-level info for filtering, faceting, display
    - document_chunks: Text chunks with embeddings for semantic/keyword search

This separation allows:
    1. Efficient metadata-only queries (no embedding overhead)
    2. Independent updates to metadata without re-embedding
    3. Optimized search patterns for different use cases
"""

# =============================================================================
# Constants
# =============================================================================

DOCUMENT_TYPES = ["policy", "procedure", "form"]

DOCUMENT_STATUSES = ["active", "draft", "archived", "superseded"]

EMBEDDING_DIMENSIONS = 1536  # OpenAI text-embedding-3-small

# Vector search configuration
# Using cosine distance (best for normalized embeddings like OpenAI's)
VECTOR_DISTANCE_METRIC = "cosine"

# =============================================================================
# Vector Search Strategy: Exact (Flat) vs HNSW
# =============================================================================
# We explicitly choose EXACT (flat) search over HNSW for this use case:
#
# WHY EXACT SEARCH:
#   1. Accuracy is critical - policy documents have legal/compliance implications
#      HNSW achieves ~95-99% recall, meaning 1-5% of relevant docs may be missed
#   2. Dataset size is bounded - single-tenant org with ~100-500 policies
#      yields ~5,000-25,000 chunks, well within exact search performance
#   3. Query volume is low - chatbot queries, not high-throughput API
#   4. Hybrid search pre-filters - keyword matching reduces vector search space
#
# WHEN TO CONSIDER HNSW:
#   - Collection exceeds 100,000+ vectors
#   - Search latency exceeds acceptable thresholds (>500ms)
#   - You can tolerate 1-5% missed relevant results
#
# Typesense uses flat search by default for smaller collections.
# To force HNSW if needed later, set at search time:
#   vector_query: "embedding:([...], k:10, flat_search_cutoff:0)"
# =============================================================================


# =============================================================================
# Collection 1: documents_metadata
# =============================================================================
# Purpose: Store document-level information for filtering, faceting, and display
# Use cases:
#   - "List all active HR policies"
#   - "What policies were updated this month?"
#   - "Show me all forms for the Finance department"

DOCUMENTS_METADATA_SCHEMA = {
    "name": "documents_metadata",
    "fields": [
        # Primary identifier
        {
            "name": "id",
            "type": "string",
            "facet": False,
        },
        # Document title - primary text search field
        {
            "name": "title",
            "type": "string",
            "facet": False,
            "infix": True,  # Enable partial matching for titles
        },
        # Document classification
        {
            "name": "document_type",
            "type": "string",
            "facet": True,  # Enable faceting for filtering UI
        },
        # Organizational ownership
        {
            "name": "department",
            "type": "string",
            "facet": True,
        },
        # Multiple classification tags
        {
            "name": "categories",
            "type": "string[]",
            "facet": True,
        },
        # Lifecycle status
        {
            "name": "status",
            "type": "string",
            "facet": True,
        },
        # When the document became/becomes effective (unix timestamp)
        {
            "name": "effective_date",
            "type": "int64",
            "facet": False,
            "sort": True,
        },
        # Next scheduled review date (unix timestamp)
        {
            "name": "review_date",
            "type": "int64",
            "facet": False,
            "sort": True,
            "optional": True,
        },
        # Document version string (e.g., "2.1", "v3")
        {
            "name": "version",
            "type": "string",
            "facet": False,
            "optional": True,
        },
        # Document owner/author
        {
            "name": "author",
            "type": "string",
            "facet": True,
            "optional": True,
        },
        # Approval authority
        {
            "name": "approver",
            "type": "string",
            "facet": True,
            "optional": True,
        },
        # Brief description - searchable but secondary to chunks
        {
            "name": "summary",
            "type": "string",
            "facet": False,
            "optional": True,
        },
        # Link to original document (SharePoint, Drive, etc.)
        {
            "name": "source_url",
            "type": "string",
            "facet": False,
            "index": False,  # Not searchable, just stored
            "optional": True,
        },
        # How many chunks this document has in document_chunks
        {
            "name": "chunk_count",
            "type": "int32",
            "facet": False,
            "optional": True,
        },
        # Timestamps
        {
            "name": "created_at",
            "type": "int64",
            "facet": False,
            "sort": True,
        },
        {
            "name": "updated_at",
            "type": "int64",
            "facet": False,
            "sort": True,
        },
    ],
    # Default sorting by most recently updated
    "default_sorting_field": "updated_at",
    # Enable nested field queries if needed later
    "enable_nested_fields": False,
}


# =============================================================================
# Collection 2: document_chunks
# =============================================================================
# Purpose: Store text chunks with embeddings for semantic and keyword search
# Use cases:
#   - "What is the policy on remote work?" (semantic search)
#   - "Find sections mentioning 'expense reimbursement'" (keyword search)
#   - Hybrid search combining both approaches

DOCUMENT_CHUNKS_SCHEMA = {
    "name": "document_chunks",
    "fields": [
        # Composite key: {document_id}_{chunk_index}
        {
            "name": "id",
            "type": "string",
            "facet": False,
        },
        # Foreign key to documents_metadata
        {
            "name": "document_id",
            "type": "string",
            "facet": True,  # Allow filtering by specific document
        },
        # Order within the source document (0-indexed)
        {
            "name": "chunk_index",
            "type": "int32",
            "facet": False,
            "sort": True,
        },
        # The actual text content - primary search field
        {
            "name": "text",
            "type": "string",
            "facet": False,
        },
        # Vector embedding for semantic search
        # Using cosine distance for normalized OpenAI embeddings
        # Typesense will use exact (flat) search by default for this collection size
        {
            "name": "embedding",
            "type": "float[]",
            "embed": {
                "from": ["text"],
                "model_config": {
                    "model_name": "openai/text-embedding-3-small",
                    "api_key": "${OPENAI_API_KEY}",  # Set via environment
                },
            },
            "num_dim": EMBEDDING_DIMENSIONS,
            "vec_dist": VECTOR_DISTANCE_METRIC,
        },
        # Section heading for context (e.g., "Section 3: Eligibility")
        {
            "name": "section_title",
            "type": "string",
            "facet": False,
            "optional": True,
        },
        # Source page number if from PDF
        {
            "name": "page_number",
            "type": "int32",
            "facet": False,
            "optional": True,
        },
        # === Denormalized fields for filtering without JOIN ===
        # These duplicate metadata but enable filtered semantic search
        {
            "name": "document_type",
            "type": "string",
            "facet": True,
        },
        {
            "name": "department",
            "type": "string",
            "facet": True,
        },
        {
            "name": "status",
            "type": "string",
            "facet": True,
        },
        # Document title for display in search results
        {
            "name": "document_title",
            "type": "string",
            "facet": False,
            "index": False,  # Not searchable, just for display
        },
        # Timestamp for sorting/freshness
        {
            "name": "created_at",
            "type": "int64",
            "facet": False,
            "sort": True,
        },
    ],
    # Default sort by chunk order within document
    "default_sorting_field": "chunk_index",
}


# =============================================================================
# Alternative: Manual Embeddings Schema
# =============================================================================
# Use this if you want to generate embeddings yourself (not via Typesense)
# This gives you more control over chunking strategy and embedding model

DOCUMENT_CHUNKS_MANUAL_EMBEDDING_SCHEMA = {
    "name": "document_chunks",
    "fields": [
        {"name": "id", "type": "string"},
        {"name": "document_id", "type": "string", "facet": True},
        {"name": "chunk_index", "type": "int32", "sort": True},
        {"name": "text", "type": "string"},
        # Pre-computed embedding (you provide the vector)
        # Uses exact (flat) search for 100% recall
        {
            "name": "embedding",
            "type": "float[]",
            "num_dim": EMBEDDING_DIMENSIONS,
            "vec_dist": VECTOR_DISTANCE_METRIC,
        },
        {"name": "section_title", "type": "string", "optional": True},
        {"name": "page_number", "type": "int32", "optional": True},
        {"name": "document_type", "type": "string", "facet": True},
        {"name": "department", "type": "string", "facet": True},
        {"name": "status", "type": "string", "facet": True},
        {"name": "document_title", "type": "string", "index": False},
        {"name": "created_at", "type": "int64", "sort": True},
    ],
    "default_sorting_field": "chunk_index",
}

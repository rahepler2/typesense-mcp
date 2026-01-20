"""
Example search queries for policy/procedure documents.

This module demonstrates the various search patterns your chatbot can use.
These examples serve as documentation and can be adapted for MCP tools.
"""

# =============================================================================
# Search Pattern 1: Semantic Search (Vector)
# =============================================================================
# Use when: User asks a question in natural language
# Example: "What are the requirements for expense reimbursement?"

SEMANTIC_SEARCH_EXAMPLE = {
    "collection": "document_chunks",
    "q": "*",  # Wildcard for text (we're using vector search)
    "vector_query": "embedding:([], k:10)",  # Top 10 nearest neighbors
    # The query text goes in the API call separately for auto-embedding
    # Or you pre-compute the embedding and insert it in the brackets
    "filter_by": "status:=active",  # Only search active documents
    "include_fields": "document_id,document_title,text,section_title,chunk_index",
    "exclude_fields": "embedding",  # Don't return the large vector
}


# =============================================================================
# Search Pattern 2: Keyword Search
# =============================================================================
# Use when: User searches for specific terms
# Example: "expense reimbursement policy"

KEYWORD_SEARCH_EXAMPLE = {
    "collection": "document_chunks",
    "q": "expense reimbursement",
    "query_by": "text",
    "filter_by": "status:=active",
    "sort_by": "_text_match:desc",  # Rank by text relevance
    "highlight_full_fields": "text",
    "highlight_start_tag": "<mark>",
    "highlight_end_tag": "</mark>",
    "per_page": 10,
}


# =============================================================================
# Search Pattern 3: Hybrid Search (Semantic + Keyword)
# =============================================================================
# Use when: You want best of both worlds
# Combines vector similarity with keyword matching

HYBRID_SEARCH_EXAMPLE = {
    "collection": "document_chunks",
    "q": "expense reimbursement",
    "query_by": "text",
    "vector_query": "embedding:([], k:20, distance_threshold:0.5)",
    "filter_by": "status:=active",
    # Blend keyword and vector scores
    "sort_by": "_text_match:desc,_vector_distance:asc",
    "per_page": 10,
}


# =============================================================================
# Search Pattern 4: Filtered Semantic Search
# =============================================================================
# Use when: User wants to search within specific constraints
# Example: "remote work policy in HR department"

FILTERED_SEMANTIC_SEARCH = {
    "collection": "document_chunks",
    "q": "*",
    "vector_query": "embedding:([], k:10)",
    "filter_by": "status:=active && department:=HR && document_type:=policy",
    "include_fields": "document_id,document_title,text,section_title",
}


# =============================================================================
# Search Pattern 5: Metadata-Only Search
# =============================================================================
# Use when: User wants to browse/list documents
# Example: "Show me all Finance department forms"

METADATA_SEARCH_EXAMPLE = {
    "collection": "documents_metadata",
    "q": "*",
    "filter_by": "department:=Finance && document_type:=form && status:=active",
    "sort_by": "updated_at:desc",
    "facet_by": "categories",
    "per_page": 20,
}


# =============================================================================
# Search Pattern 6: Faceted Search
# =============================================================================
# Use when: Building a search UI with filters
# Returns document counts by category

FACETED_SEARCH_EXAMPLE = {
    "collection": "documents_metadata",
    "q": "*",
    "filter_by": "status:=active",
    "facet_by": "document_type,department,categories",
    "max_facet_values": 20,
    "per_page": 0,  # Just get facets, no documents
}


# =============================================================================
# Search Pattern 7: Multi-Search (Parallel Queries)
# =============================================================================
# Use when: You need multiple search strategies at once
# Typesense can execute multiple searches in one request

MULTI_SEARCH_EXAMPLE = {
    "searches": [
        # Search 1: Semantic search in chunks
        {
            "collection": "document_chunks",
            "q": "*",
            "vector_query": "embedding:([], k:5)",
            "filter_by": "status:=active",
        },
        # Search 2: Keyword search in chunks
        {
            "collection": "document_chunks",
            "q": "expense policy",
            "query_by": "text",
            "filter_by": "status:=active",
            "per_page": 5,
        },
        # Search 3: Title search in metadata
        {
            "collection": "documents_metadata",
            "q": "expense",
            "query_by": "title",
            "filter_by": "status:=active",
            "per_page": 5,
        },
    ]
}


# =============================================================================
# Search Pattern 8: Document Retrieval with All Chunks
# =============================================================================
# Use when: You found a document and want all its content
# Example: After finding a relevant chunk, get the full document

GET_DOCUMENT_CHUNKS = {
    "collection": "document_chunks",
    "q": "*",
    "filter_by": "document_id:=doc_12345",
    "sort_by": "chunk_index:asc",
    "per_page": 100,  # Get all chunks
}


# =============================================================================
# Search Pattern 9: Recent Documents
# =============================================================================
# Use when: User asks "what's new" or "recent updates"

RECENT_DOCUMENTS = {
    "collection": "documents_metadata",
    "q": "*",
    "filter_by": "status:=active",
    "sort_by": "updated_at:desc",
    "per_page": 10,
}


# =============================================================================
# Search Pattern 10: Documents Due for Review
# =============================================================================
# Use when: Admin wants to see documents needing attention

DOCUMENTS_DUE_FOR_REVIEW = {
    "collection": "documents_metadata",
    "q": "*",
    "filter_by": "status:=active && review_date:<{current_timestamp}",
    "sort_by": "review_date:asc",
    "per_page": 20,
}


# =============================================================================
# Filter Syntax Reference
# =============================================================================
"""
Typesense Filter Syntax for Chatbot Use:

Equality:
    field:=value           → department:=HR
    field:=[val1,val2]     → document_type:=[policy,procedure]

Comparison (numeric/dates):
    field:>value           → effective_date:>1704067200
    field:>=value          → chunk_index:>=5
    field:<value           → review_date:<1735689600
    field:<=value          → page_number:<=10
    field:[min..max]       → effective_date:[1704067200..1735689600]

Boolean:
    field:=true/false      → (if you add boolean fields)

Combining:
    &&                     → status:=active && department:=HR
    ||                     → document_type:=policy || document_type:=procedure

Negation:
    field:!=value          → status:!=archived
    field:!=[val1,val2]    → department:!=[HR,Finance]
"""


# =============================================================================
# Recommended Tool Design for MCP
# =============================================================================
"""
Based on these patterns, here are the recommended MCP tools:

1. search_policies
   - Semantic search with optional filters
   - Input: query (str), filters (dict), limit (int)
   - Uses: Hybrid search pattern

2. list_documents
   - Browse/filter documents by metadata
   - Input: document_type, department, status, sort_by
   - Uses: Metadata search pattern

3. get_document
   - Get full document with all chunks
   - Input: document_id
   - Uses: Document retrieval pattern

4. get_facets
   - Get available filter values
   - Input: facet_fields
   - Uses: Faceted search pattern

5. find_related
   - Find similar documents to a given one
   - Input: document_id, limit
   - Uses: Vector search with chunk embedding

These tools give the chatbot flexibility while keeping the interface simple.
"""

"""RAG-specific tools for metadata-to-chunks retrieval patterns."""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import TypesenseClientManager


def register(mcp: FastMCP, ts: TypesenseClientManager) -> None:
    """Register RAG retrieval tools on the MCP server."""

    @mcp.tool()
    def rag_search_and_retrieve_chunks(
        metadata_collection: str,
        chunks_collection: str,
        query: str,
        query_by: str,
        doc_id_field: str = "doc_id",
        chunk_content_field: str = "content",
        filter_by: str = "",
        per_page: int = 5,
        chunks_per_doc: int = 50,
        include_metadata: bool = True,
        chunks_sort_by: str = "",
        chunks_filter_by: str = "",
        exclude_fields: str = "",
    ) -> dict:
        """Search a metadata collection and retrieve linked chunks from an embeddings collection.

        This is the core RAG retrieval pattern: first search metadata to find relevant
        documents, then fetch all associated chunks from the embeddings collection using
        the doc_id field as the link.

        Args:
            metadata_collection: Name of the metadata collection to search.
            chunks_collection: Name of the embeddings/chunks collection containing
                the actual content chunks.
            query: The search query.
            query_by: Comma-separated fields to search in the metadata collection.
                Can include embedding fields for hybrid search.
            doc_id_field: The field name that links metadata to chunks (default "doc_id").
                Must exist in both collections.
            chunk_content_field: The field containing chunk text in the chunks collection
                (default "content").
            filter_by: Filter expression for the metadata search.
            per_page: Number of metadata documents to retrieve (default 5).
            chunks_per_doc: Max chunks to retrieve per document (default 50).
            include_metadata: Whether to include metadata document info in results (default true).
            chunks_sort_by: Sort expression for chunks (e.g., "chunk_index:asc").
            chunks_filter_by: Additional filter for chunks beyond the doc_id link.
            exclude_fields: Fields to exclude from chunks (e.g., embedding fields).
        """
        # Step 1: Search metadata collection
        meta_params: dict[str, Any] = {
            "q": query,
            "query_by": query_by,
            "per_page": min(per_page, 50),
        }
        if filter_by:
            meta_params["filter_by"] = filter_by

        meta_result = ts.search(metadata_collection, meta_params)
        meta_hits = meta_result.get("hits", [])

        if not meta_hits:
            return {
                "found": 0,
                "message": "No matching documents found in metadata collection.",
                "results": [],
            }

        # Step 2: Extract doc_ids from metadata results
        doc_ids = []
        metadata_by_id: dict[str, dict] = {}
        for hit in meta_hits:
            doc = hit.get("document", {})
            did = doc.get(doc_id_field)
            if did is not None:
                did_str = str(did)
                doc_ids.append(did_str)
                if include_metadata:
                    # Store metadata, excluding large embedding fields
                    metadata_by_id[did_str] = {
                        k: v for k, v in doc.items()
                        if not (isinstance(v, list) and len(v) > 50
                                and v and isinstance(v[0], (int, float)))
                    }

        if not doc_ids:
            return {
                "found": len(meta_hits),
                "message": f"Documents found but none have '{doc_id_field}' field.",
                "results": [],
            }

        # Step 3: Fetch chunks for all matched doc_ids
        # Build filter for chunks: doc_id in [id1, id2, ...]
        escaped_ids = [did.replace("`", "\\`") for did in doc_ids]
        chunk_filter = f"{doc_id_field}:[{','.join(escaped_ids)}]"
        if chunks_filter_by:
            chunk_filter = f"{chunk_filter} && {chunks_filter_by}"

        chunk_params: dict[str, Any] = {
            "q": "*",
            "query_by": chunk_content_field,
            "filter_by": chunk_filter,
            "per_page": min(chunks_per_doc * len(doc_ids), 250),
        }
        if chunks_sort_by:
            chunk_params["sort_by"] = chunks_sort_by
        if exclude_fields:
            chunk_params["exclude_fields"] = exclude_fields

        chunks_result = ts.search(chunks_collection, chunk_params)

        # Step 4: Organize chunks by doc_id
        chunks_by_doc: dict[str, list[dict]] = {did: [] for did in doc_ids}
        for hit in chunks_result.get("hits", []):
            doc = hit.get("document", {})
            did = str(doc.get(doc_id_field, ""))
            if did in chunks_by_doc:
                # Clean up chunk document (remove embedding vectors)
                cleaned = {
                    k: v for k, v in doc.items()
                    if not (isinstance(v, list) and len(v) > 50
                            and v and isinstance(v[0], (int, float)))
                }
                chunks_by_doc[did].append(cleaned)

        # Step 5: Build final results
        results = []
        for did in doc_ids:
            entry: dict[str, Any] = {"doc_id": did}
            if include_metadata and did in metadata_by_id:
                entry["metadata"] = metadata_by_id[did]
            entry["chunks"] = chunks_by_doc.get(did, [])
            entry["chunk_count"] = len(entry["chunks"])
            results.append(entry)

        return {
            "found": len(results),
            "total_chunks": sum(r["chunk_count"] for r in results),
            "results": results,
        }

    @mcp.tool()
    def rag_hybrid_chunk_search(
        chunks_collection: str,
        query: str,
        query_by: str,
        filter_by: str = "",
        per_page: int = 20,
        alpha: float = 0.3,
        rerank_hybrid_matches: bool = True,
        group_by_doc: str = "",
        group_limit: int = 5,
        exclude_fields: str = "",
        include_fields: str = "",
    ) -> dict:
        """Search directly in the chunks/embeddings collection using hybrid search.

        This bypasses the metadata collection and searches chunks directly.
        Ideal when you want to find the most semantically relevant chunks
        regardless of document-level metadata.

        Args:
            chunks_collection: Name of the chunks/embeddings collection.
            query: The search query.
            query_by: Comma-separated fields to search. Include both text and embedding
                fields for hybrid search (e.g., "content,embedding").
            filter_by: Filter expression (e.g., "doc_id:=123 && chunk_type:=paragraph").
            per_page: Number of chunks to return (default 20).
            alpha: Keyword vs semantic weight (0.0=semantic, 1.0=keyword, default 0.3).
            rerank_hybrid_matches: Compute both scores for all results (default true).
            group_by_doc: Field to group chunks by (e.g., "doc_id") to get
                top chunks per document instead of globally.
            group_limit: Max chunks per group (default 5).
            exclude_fields: Fields to exclude (recommend excluding embedding fields).
            include_fields: Fields to include in response.
        """
        params: dict[str, Any] = {
            "q": query,
            "query_by": query_by,
            "per_page": min(per_page, 250),
            "rerank_hybrid_matches": rerank_hybrid_matches,
        }

        if filter_by:
            params["filter_by"] = filter_by
        if exclude_fields:
            params["exclude_fields"] = exclude_fields
        if include_fields:
            params["include_fields"] = include_fields
        if group_by_doc:
            params["group_by"] = group_by_doc
            params["group_limit"] = group_limit

        result = ts.search(chunks_collection, params)

        # Format the results
        output: dict[str, Any] = {
            "found": result.get("found", 0),
            "search_time_ms": result.get("search_time_ms", 0),
        }

        if result.get("grouped_hits"):
            output["grouped_hits"] = result["grouped_hits"]
        else:
            chunks = []
            for hit in result.get("hits", []):
                entry: dict[str, Any] = {
                    "document": hit.get("document", {}),
                }
                if "vector_distance" in hit:
                    entry["vector_distance"] = hit["vector_distance"]
                if "text_match_info" in hit:
                    entry["text_match_info"] = hit["text_match_info"]
                if "hybrid_search_info" in hit:
                    entry["hybrid_search_info"] = hit["hybrid_search_info"]
                chunks.append(entry)
            output["chunks"] = chunks

        return output

    @mcp.tool()
    def get_document_chunks(
        chunks_collection: str,
        doc_id: str,
        doc_id_field: str = "doc_id",
        sort_by: str = "",
        filter_by: str = "",
        per_page: int = 100,
        exclude_fields: str = "",
        include_fields: str = "",
    ) -> dict:
        """Retrieve all chunks for a specific document by its doc_id.

        Use this when you already know which document you want and need to
        retrieve all its chunks from the embeddings collection.

        Args:
            chunks_collection: Name of the chunks/embeddings collection.
            doc_id: The document ID to retrieve chunks for.
            doc_id_field: The field name for doc_id in the chunks collection (default "doc_id").
            sort_by: Sort expression for chunks (e.g., "chunk_index:asc").
            filter_by: Additional filter expression to apply.
            per_page: Max chunks to return (default 100).
            exclude_fields: Fields to exclude (recommend excluding embedding fields).
            include_fields: Fields to include.
        """
        chunk_filter = f"{doc_id_field}:={doc_id}"
        if filter_by:
            chunk_filter = f"{chunk_filter} && {filter_by}"

        params: dict[str, Any] = {
            "q": "*",
            "query_by": doc_id_field,
            "filter_by": chunk_filter,
            "per_page": min(per_page, 250),
        }
        if sort_by:
            params["sort_by"] = sort_by
        if exclude_fields:
            params["exclude_fields"] = exclude_fields
        if include_fields:
            params["include_fields"] = include_fields

        result = ts.search(chunks_collection, params)

        chunks = []
        for hit in result.get("hits", []):
            doc = hit.get("document", {})
            cleaned = {
                k: v for k, v in doc.items()
                if not (isinstance(v, list) and len(v) > 50
                        and v and isinstance(v[0], (int, float)))
            }
            chunks.append(cleaned)

        return {
            "doc_id": doc_id,
            "chunk_count": len(chunks),
            "total_found": result.get("found", 0),
            "chunks": chunks,
        }

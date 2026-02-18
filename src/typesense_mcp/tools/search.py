"""Search tools for Typesense MCP server — hybrid, vector, keyword, and NL search."""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import TypesenseClientManager


def register(mcp: FastMCP, ts: TypesenseClientManager) -> None:
    """Register search tools on the MCP server."""

    @mcp.tool()
    def hybrid_search(
        collection_name: str,
        query: str,
        query_by: str,
        filter_by: str = "",
        sort_by: str = "",
        per_page: int = 10,
        page: int = 1,
        vector_query: str = "",
        alpha: float = 0.3,
        rerank_hybrid_matches: bool = True,
        group_by: str = "",
        group_limit: int = 3,
        facet_by: str = "",
        max_facet_values: int = 10,
        prefix: str = "true",
        exclude_fields: str = "",
        include_fields: str = "",
        highlight_fields: str = "",
    ) -> dict:
        """Perform a hybrid search combining keyword and semantic/vector search.

        This is the primary search tool for RAG applications. It combines keyword
        matching with vector/embedding similarity for best results.

        Args:
            collection_name: The collection to search.
            query: The search query text. Use '*' to match all documents (useful with filters).
            query_by: Comma-separated list of fields to search. Include both text fields
                and embedding fields for hybrid search (e.g., "title,description,embedding").
            filter_by: Typesense filter expression (e.g., "category:=shoes && price:<100").
                Supports: :=, :!=, :>, :<, :>=, :<=, :[], &&, ||
            sort_by: Comma-separated sort fields (e.g., "price:asc,_text_match:desc").
            per_page: Results per page (default 10, max 250).
            page: Page number (default 1).
            vector_query: Optional vector query override. If empty and query_by includes
                an embedding field, Typesense auto-generates the vector query.
                Format: "embedding_field:([], k:200, distance_threshold:0.5, alpha:0.3)"
            alpha: Weight for keyword vs semantic results in rank fusion.
                0.0 = pure semantic, 1.0 = pure keyword (default 0.3).
            rerank_hybrid_matches: If true, compute both text match and vector distance
                scores for all results, enabling better cross-ranking (default true).
            group_by: Field to group results by (e.g., "category").
            group_limit: Max results per group (default 3).
            facet_by: Comma-separated fields to facet on.
            max_facet_values: Max number of facet values to return per field.
            prefix: Whether to do prefix matching ("true" or "false").
            exclude_fields: Comma-separated fields to exclude from response.
                Recommended: exclude embedding fields to save bandwidth.
            include_fields: Comma-separated fields to include in response.
            highlight_fields: Comma-separated fields to highlight matches in.
        """
        params: dict[str, Any] = {
            "q": query,
            "query_by": query_by,
            "per_page": min(per_page, 250),
            "page": page,
            "rerank_hybrid_matches": rerank_hybrid_matches,
        }

        if filter_by:
            params["filter_by"] = filter_by
        if sort_by:
            params["sort_by"] = sort_by
        if vector_query:
            params["vector_query"] = vector_query
        elif alpha != 0.3:
            # If no explicit vector_query but alpha is set, we need to find the
            # embedding field from query_by and set alpha on it
            fields = [f.strip() for f in query_by.split(",")]
            for field in fields:
                # The user should include an embedding field in query_by for hybrid
                params["vector_query"] = f"{field}:([], k:{per_page * 5}, alpha:{alpha})"
                break
        if group_by:
            params["group_by"] = group_by
            params["group_limit"] = group_limit
        if facet_by:
            params["facet_by"] = facet_by
            params["max_facet_values"] = max_facet_values
        if prefix != "true":
            params["prefix"] = prefix
        if exclude_fields:
            params["exclude_fields"] = exclude_fields
        if include_fields:
            params["include_fields"] = include_fields
        if highlight_fields:
            params["highlight_fields"] = highlight_fields

        result = ts.search(collection_name, params)
        return _format_search_result(result)

    @mcp.tool()
    def keyword_search(
        collection_name: str,
        query: str,
        query_by: str,
        filter_by: str = "",
        sort_by: str = "",
        per_page: int = 10,
        page: int = 1,
        facet_by: str = "",
        group_by: str = "",
        group_limit: int = 3,
        include_fields: str = "",
        exclude_fields: str = "",
    ) -> dict:
        """Perform a keyword-only search (no vector/semantic component).

        Best for exact matching, filtering, and when you know the exact terms.

        Args:
            collection_name: The collection to search.
            query: The search query. Use '*' to match all (useful with filters).
            query_by: Comma-separated text fields to search (e.g., "title,description").
                Do NOT include embedding fields here.
            filter_by: Filter expression (e.g., "status:=active && price:<50").
            sort_by: Sort expression (e.g., "created_at:desc").
            per_page: Results per page (default 10).
            page: Page number (default 1).
            facet_by: Comma-separated fields to facet on.
            group_by: Field to group results by.
            group_limit: Max results per group.
            include_fields: Fields to include in response.
            exclude_fields: Fields to exclude from response.
        """
        params: dict[str, Any] = {
            "q": query,
            "query_by": query_by,
            "per_page": min(per_page, 250),
            "page": page,
        }

        if filter_by:
            params["filter_by"] = filter_by
        if sort_by:
            params["sort_by"] = sort_by
        if facet_by:
            params["facet_by"] = facet_by
        if group_by:
            params["group_by"] = group_by
            params["group_limit"] = group_limit
        if include_fields:
            params["include_fields"] = include_fields
        if exclude_fields:
            params["exclude_fields"] = exclude_fields

        result = ts.search(collection_name, params)
        return _format_search_result(result)

    @mcp.tool()
    def natural_language_search(
        collection_name: str,
        query: str,
        query_by: str,
        nl_model_id: str,
        filter_by: str = "",
        sort_by: str = "",
        per_page: int = 10,
        page: int = 1,
        nl_query_debug: bool = False,
        nl_query_prompt_cache_ttl: int = 86400,
        include_fields: str = "",
        exclude_fields: str = "",
        facet_by: str = "",
    ) -> dict:
        """Perform a natural language search using Typesense 29.0's NL query feature.

        This uses an LLM to automatically convert natural language queries into
        structured Typesense filters and sorts. For example:
        "red shirts under $50" → filter_by: color:=red && category:=shirt && price:<50

        An NL search model must be configured first using create_nl_search_model.

        Args:
            collection_name: The collection to search.
            query: Natural language query (e.g., "affordable running shoes in size 10").
            query_by: Comma-separated fields to search against.
            nl_model_id: ID of the NL search model to use (created via create_nl_search_model).
            filter_by: Additional explicit filters to combine with NL-generated filters.
            sort_by: Explicit sort to apply (NL may also generate sorts).
            per_page: Results per page (default 10).
            page: Page number (default 1).
            nl_query_debug: If true, returns parsed NL query details in the response.
            nl_query_prompt_cache_ttl: Cache TTL for the schema prompt in seconds (default 86400).
            include_fields: Fields to include in response.
            exclude_fields: Fields to exclude from response.
            facet_by: Comma-separated fields to facet on.
        """
        params: dict[str, Any] = {
            "q": query,
            "query_by": query_by,
            "nl_query": True,
            "nl_model_id": nl_model_id,
            "per_page": min(per_page, 250),
            "page": page,
        }

        if filter_by:
            params["filter_by"] = filter_by
        if sort_by:
            params["sort_by"] = sort_by
        if nl_query_debug:
            params["nl_query_debug"] = True
        if nl_query_prompt_cache_ttl != 86400:
            params["nl_query_prompt_cache_ttl"] = nl_query_prompt_cache_ttl
        if include_fields:
            params["include_fields"] = include_fields
        if exclude_fields:
            params["exclude_fields"] = exclude_fields
        if facet_by:
            params["facet_by"] = facet_by

        result = ts.search(collection_name, params)
        return _format_search_result(result)

    @mcp.tool()
    def multi_search(
        searches_json: str,
        common_query_by: str = "",
        common_filter_by: str = "",
        common_per_page: int = 10,
    ) -> dict:
        """Perform multiple searches across one or more collections in a single request.

        Useful for federated search, searching across multiple collections simultaneously,
        or running several different queries at once.

        Args:
            searches_json: JSON string containing an array of search objects. Each object
                must include 'collection' and 'q' at minimum. Example:
                [
                    {"collection": "products", "q": "laptop", "query_by": "title,description"},
                    {"collection": "reviews", "q": "laptop", "query_by": "content"}
                ]
            common_query_by: Common query_by applied to all searches (can be overridden per search).
            common_filter_by: Common filter_by applied to all searches.
            common_per_page: Common per_page applied to all searches.
        """
        searches = json.loads(searches_json)
        common: dict[str, Any] = {}
        if common_query_by:
            common["query_by"] = common_query_by
        if common_filter_by:
            common["filter_by"] = common_filter_by
        if common_per_page != 10:
            common["per_page"] = common_per_page

        result = ts.multi_search(searches, common)

        formatted_results = []
        for i, res in enumerate(result.get("results", [])):
            formatted_results.append({
                "search_index": i,
                **_format_search_result(res),
            })

        return {"results": formatted_results}


def _format_search_result(result: dict) -> dict:
    """Format a Typesense search result into a cleaner structure."""
    output: dict[str, Any] = {
        "found": result.get("found", 0),
        "page": result.get("page", 1),
        "search_time_ms": result.get("search_time_ms", 0),
    }

    # Format hits
    hits = []
    for hit in result.get("hits", []):
        formatted_hit: dict[str, Any] = {
            "document": hit.get("document", {}),
        }

        # Include text match info if available
        if "text_match_info" in hit:
            formatted_hit["text_match_info"] = hit["text_match_info"]

        # Include vector distance if available (for hybrid/vector searches)
        if "vector_distance" in hit:
            formatted_hit["vector_distance"] = hit["vector_distance"]

        # Include highlights
        if hit.get("highlights"):
            formatted_hit["highlights"] = hit["highlights"]

        # Include hybrid score if available
        if "hybrid_search_info" in hit:
            formatted_hit["hybrid_search_info"] = hit["hybrid_search_info"]

        hits.append(formatted_hit)

    output["hits"] = hits

    # Include facet counts if present
    if result.get("facet_counts"):
        output["facet_counts"] = result["facet_counts"]

    # Include group results if present
    if result.get("grouped_hits"):
        output["grouped_hits"] = result["grouped_hits"]

    # Include NL query debug info if present (v29.0)
    if result.get("parsed_nl_query"):
        output["parsed_nl_query"] = result["parsed_nl_query"]

    return output

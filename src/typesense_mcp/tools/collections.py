"""Collection management tools for Typesense MCP server."""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from ..client import TypesenseClientManager


def register(mcp: FastMCP, ts: TypesenseClientManager) -> None:
    """Register collection management tools on the MCP server."""

    @mcp.tool()
    def check_health() -> dict:
        """Check Typesense cluster health status."""
        return ts.health()

    @mcp.tool()
    def list_collections() -> list[dict]:
        """List all collections in the Typesense cluster.

        Returns a summary of each collection including name, number of documents,
        and field count.
        """
        collections = ts.list_collections()
        return [
            {
                "name": c["name"],
                "num_documents": c.get("num_documents", 0),
                "num_fields": len(c.get("fields", [])),
                "created_at": c.get("created_at"),
            }
            for c in collections
        ]

    @mcp.tool()
    def describe_collection(collection_name: str) -> dict:
        """Get full schema and metadata for a specific collection.

        Args:
            collection_name: Name of the collection to describe.

        Returns the collection schema including all fields with their types,
        facet/index/optional settings, default sorting field, token separators,
        and document count.
        """
        return ts.get_collection(collection_name)

    @mcp.tool()
    def get_collection_fields(collection_name: str) -> list[dict]:
        """Get the field definitions for a collection in a concise format.

        Useful for understanding what fields are searchable, facetable, and
        what types they are before constructing queries.

        Args:
            collection_name: Name of the collection.
        """
        col = ts.get_collection(collection_name)
        fields = col.get("fields", [])
        return [
            {
                "name": f["name"],
                "type": f["type"],
                "facet": f.get("facet", False),
                "index": f.get("index", True),
                "optional": f.get("optional", False),
                "sort": f.get("sort", False),
                "embed": f.get("embed") is not None,
            }
            for f in fields
        ]

    @mcp.tool()
    def analyze_collection(collection_name: str, sample_size: int = 5) -> dict:
        """Analyze a collection: schema, document count, sample documents, and facet value summaries.

        This is useful for understanding what data is in a collection before searching it.

        Args:
            collection_name: Name of the collection to analyze.
            sample_size: Number of sample documents to retrieve (default 5, max 20).
        """
        sample_size = min(max(1, sample_size), 20)

        col = ts.get_collection(collection_name)
        fields = col.get("fields", [])

        # Get sample documents
        search_result = ts.search(collection_name, {
            "q": "*",
            "per_page": sample_size,
        })

        samples = []
        for hit in search_result.get("hits", []):
            doc = hit.get("document", {})
            # Exclude embedding fields from samples to keep output concise
            cleaned = {
                k: v for k, v in doc.items()
                if not isinstance(v, list) or not (v and isinstance(v[0], (int, float)))
                or len(v) < 50
            }
            samples.append(cleaned)

        # Identify facetable fields and get value distributions
        facet_fields = [f["name"] for f in fields if f.get("facet")]
        facet_summaries = {}

        if facet_fields:
            facet_result = ts.search(collection_name, {
                "q": "*",
                "facet_by": ",".join(facet_fields[:10]),
                "max_facet_values": 10,
                "per_page": 0,
            })
            for fc in facet_result.get("facet_counts", []):
                facet_summaries[fc["field_name"]] = {
                    "total_values": fc.get("stats", {}).get("total_values", None),
                    "top_values": [
                        {"value": v["value"], "count": v["count"]}
                        for v in fc.get("counts", [])[:10]
                    ],
                }

        # Identify embedding/vector fields
        embedding_fields = [
            f["name"] for f in fields
            if f["type"] in ("float[]",) and f.get("embed") is not None
        ]

        return {
            "name": col["name"],
            "num_documents": col.get("num_documents", 0),
            "fields": [
                {
                    "name": f["name"],
                    "type": f["type"],
                    "facet": f.get("facet", False),
                    "optional": f.get("optional", False),
                }
                for f in fields
            ],
            "embedding_fields": embedding_fields,
            "default_sorting_field": col.get("default_sorting_field", ""),
            "facet_summaries": facet_summaries,
            "sample_documents": samples,
        }

    @mcp.tool()
    def create_collection(schema_json: str) -> dict:
        """Create a new collection in Typesense.

        Args:
            schema_json: JSON string of the collection schema. Must include 'name'
                and 'fields' at minimum. Example:
                {
                    "name": "products",
                    "fields": [
                        {"name": "title", "type": "string"},
                        {"name": "price", "type": "float", "facet": true}
                    ]
                }
        """
        schema = json.loads(schema_json)
        return ts.create_collection(schema)

    @mcp.tool()
    def delete_collection(collection_name: str) -> dict:
        """Delete a collection and all its documents. This is irreversible.

        Args:
            collection_name: Name of the collection to delete.
        """
        return ts.delete_collection(collection_name)

    @mcp.tool()
    def update_collection_schema(collection_name: str, schema_changes_json: str) -> dict:
        """Update a collection's schema (add/drop fields).

        Args:
            collection_name: Name of the collection to update.
            schema_changes_json: JSON string with the schema changes. Example:
                {"fields": [{"name": "new_field", "type": "string"}]}
        """
        changes = json.loads(schema_changes_json)
        return ts.update_collection(collection_name, changes)

"""Document CRUD tools for Typesense MCP server."""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import TypesenseClientManager


def register(mcp: FastMCP, ts: TypesenseClientManager) -> None:
    """Register document management tools on the MCP server."""

    @mcp.tool()
    def get_document(collection_name: str, document_id: str) -> dict:
        """Retrieve a single document by its ID.

        Args:
            collection_name: The collection containing the document.
            document_id: The document's ID.
        """
        return ts.get_document(collection_name, document_id)

    @mcp.tool()
    def create_document(collection_name: str, document_json: str) -> dict:
        """Create a new document in a collection.

        Args:
            collection_name: The collection to add the document to.
            document_json: JSON string of the document. Must conform to the
                collection's schema. Example:
                {"title": "Product A", "price": 29.99, "category": "electronics"}
        """
        document = json.loads(document_json)
        return ts.create_document(collection_name, document)

    @mcp.tool()
    def upsert_document(collection_name: str, document_json: str) -> dict:
        """Create or update a document (insert if new, update if exists).

        Args:
            collection_name: The collection to upsert into.
            document_json: JSON string of the document. If the document has an 'id'
                field that matches an existing document, it will be updated.
        """
        document = json.loads(document_json)
        return ts.upsert_document(collection_name, document)

    @mcp.tool()
    def update_document(
        collection_name: str,
        document_id: str,
        partial_document_json: str,
    ) -> dict:
        """Partially update an existing document.

        Only the fields included in the partial document will be updated.

        Args:
            collection_name: The collection containing the document.
            document_id: The document's ID.
            partial_document_json: JSON string with the fields to update. Example:
                {"price": 19.99, "in_stock": true}
        """
        partial = json.loads(partial_document_json)
        return ts.update_document(collection_name, document_id, partial)

    @mcp.tool()
    def delete_document(collection_name: str, document_id: str) -> dict:
        """Delete a single document by its ID.

        Args:
            collection_name: The collection containing the document.
            document_id: The document's ID.
        """
        return ts.delete_document(collection_name, document_id)

    @mcp.tool()
    def delete_documents_by_filter(collection_name: str, filter_by: str) -> dict:
        """Delete all documents matching a filter expression.

        Args:
            collection_name: The collection to delete from.
            filter_by: Typesense filter expression (e.g., "status:=archived").
                All matching documents will be permanently deleted.
        """
        return ts.delete_documents(collection_name, filter_by)

    @mcp.tool()
    def import_documents(
        collection_name: str,
        documents_json: str,
        action: str = "upsert",
    ) -> dict:
        """Bulk import documents into a collection.

        Args:
            collection_name: The collection to import into.
            documents_json: JSON string containing an array of document objects.
            action: Import action — "create", "upsert", or "update" (default "upsert").
                - create: Only insert new documents (fails on existing IDs).
                - upsert: Insert new or replace existing documents.
                - update: Only update existing documents (fails on missing IDs).
        """
        documents = json.loads(documents_json)
        results = ts.import_documents(collection_name, documents, action)

        successes = 0
        failures = []
        for i, r in enumerate(results):
            if isinstance(r, dict) and r.get("success") is False:
                failures.append({"index": i, "error": r.get("error", "unknown")})
            elif isinstance(r, str):
                parsed = json.loads(r)
                if parsed.get("success") is False:
                    failures.append({"index": i, "error": parsed.get("error", "unknown")})
                else:
                    successes += 1
            else:
                successes += 1

        return {
            "total": len(documents),
            "successes": successes,
            "failures": failures,
        }

    @mcp.tool()
    def export_documents(
        collection_name: str,
        filter_by: str = "",
        include_fields: str = "",
        exclude_fields: str = "",
    ) -> dict:
        """Export documents from a collection as JSONL.

        Args:
            collection_name: The collection to export from.
            filter_by: Optional filter to export a subset of documents.
            include_fields: Comma-separated fields to include.
            exclude_fields: Comma-separated fields to exclude.
        """
        params: dict[str, str] = {}
        if filter_by:
            params["filter_by"] = filter_by
        if include_fields:
            params["include_fields"] = include_fields
        if exclude_fields:
            params["exclude_fields"] = exclude_fields

        raw = ts.export_documents(collection_name, params)

        lines = [l for l in raw.strip().split("\n") if l]
        documents = []
        for line in lines[:100]:  # Cap at 100 to prevent overwhelming output
            try:
                documents.append(json.loads(line))
            except json.JSONDecodeError:
                continue

        return {
            "total_exported": len(lines),
            "documents_shown": len(documents),
            "documents": documents,
            "truncated": len(lines) > 100,
        }

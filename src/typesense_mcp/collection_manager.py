"""
Collection management utilities for Typesense.

Provides functions to create, update, and manage the document collections.
"""

import typesense
from typesense.exceptions import ObjectNotFound

from .schemas.collections import (
    DOCUMENTS_METADATA_SCHEMA,
    DOCUMENT_CHUNKS_SCHEMA,
    DOCUMENT_CHUNKS_MANUAL_EMBEDDING_SCHEMA,
)


class CollectionManager:
    """Manages Typesense collections for the policy document system."""

    def __init__(self, client: typesense.Client):
        """
        Initialize the collection manager.

        Args:
            client: Configured Typesense client
        """
        self.client = client

    def create_collections(self, use_auto_embedding: bool = True) -> dict:
        """
        Create both document collections.

        Args:
            use_auto_embedding: If True, use Typesense's built-in embedding.
                               If False, you'll provide embeddings manually.

        Returns:
            Dict with creation results for each collection
        """
        chunks_schema = (
            DOCUMENT_CHUNKS_SCHEMA
            if use_auto_embedding
            else DOCUMENT_CHUNKS_MANUAL_EMBEDDING_SCHEMA
        )

        results = {}

        # Create metadata collection
        try:
            self.client.collections.create(DOCUMENTS_METADATA_SCHEMA)
            results["documents_metadata"] = "created"
        except Exception as e:
            if "already exists" in str(e):
                results["documents_metadata"] = "already_exists"
            else:
                results["documents_metadata"] = f"error: {e}"

        # Create chunks collection
        try:
            self.client.collections.create(chunks_schema)
            results["document_chunks"] = "created"
        except Exception as e:
            if "already exists" in str(e):
                results["document_chunks"] = "already_exists"
            else:
                results["document_chunks"] = f"error: {e}"

        return results

    def drop_collections(self, confirm: bool = False) -> dict:
        """
        Drop both collections. Requires explicit confirmation.

        Args:
            confirm: Must be True to actually delete

        Returns:
            Dict with deletion results
        """
        if not confirm:
            return {"error": "Must pass confirm=True to delete collections"}

        results = {}

        for name in ["documents_metadata", "document_chunks"]:
            try:
                self.client.collections[name].delete()
                results[name] = "deleted"
            except ObjectNotFound:
                results[name] = "not_found"
            except Exception as e:
                results[name] = f"error: {e}"

        return results

    def get_collection_stats(self) -> dict:
        """
        Get statistics for both collections.

        Returns:
            Dict with document counts and other stats
        """
        stats = {}

        for name in ["documents_metadata", "document_chunks"]:
            try:
                collection = self.client.collections[name].retrieve()
                stats[name] = {
                    "num_documents": collection.get("num_documents", 0),
                    "fields": len(collection.get("fields", [])),
                }
            except ObjectNotFound:
                stats[name] = {"error": "collection not found"}
            except Exception as e:
                stats[name] = {"error": str(e)}

        return stats

    def collection_exists(self, name: str) -> bool:
        """Check if a collection exists."""
        try:
            self.client.collections[name].retrieve()
            return True
        except ObjectNotFound:
            return False

    def ensure_collections_exist(self, use_auto_embedding: bool = True) -> bool:
        """
        Ensure collections exist, creating them if needed.

        Returns:
            True if collections exist (created or already existed)
        """
        results = self.create_collections(use_auto_embedding)
        return all(
            r in ["created", "already_exists"] for r in results.values()
        )


def create_typesense_client(
    host: str = "localhost",
    port: int = 8108,
    protocol: str = "http",
    api_key: str = "",
    connection_timeout: int = 5,
) -> typesense.Client:
    """
    Create a configured Typesense client.

    Args:
        host: Typesense server host
        port: Typesense server port
        protocol: http or https
        api_key: Typesense API key
        connection_timeout: Connection timeout in seconds

    Returns:
        Configured Typesense client
    """
    return typesense.Client({
        "nodes": [{"host": host, "port": str(port), "protocol": protocol}],
        "api_key": api_key,
        "connection_timeout_seconds": connection_timeout,
    })

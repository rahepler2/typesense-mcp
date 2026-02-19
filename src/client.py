"""Typesense client wrapper with connection management."""

from __future__ import annotations

import typesense

from .config import TypesenseConfig


class TypesenseClientManager:
    """Manages the Typesense client instance and provides convenience methods."""

    def __init__(self, config: TypesenseConfig | None = None):
        self._config = config or TypesenseConfig()
        self._client: typesense.Client | None = None

    @property
    def client(self) -> typesense.Client:
        if self._client is None:
            self._client = typesense.Client(self._config.to_client_config())
        return self._client

    def health(self) -> dict:
        return self.client.operations.perform("health")

    # -- Collections ----------------------------------------------------------

    def list_collections(self) -> list[dict]:
        return self.client.collections.retrieve()

    def get_collection(self, name: str) -> dict:
        return self.client.collections[name].retrieve()

    def create_collection(self, schema: dict) -> dict:
        return self.client.collections.create(schema)

    def delete_collection(self, name: str) -> dict:
        return self.client.collections[name].delete()

    def update_collection(self, name: str, schema: dict) -> dict:
        return self.client.collections[name].update(schema)

    # -- Documents ------------------------------------------------------------

    def get_document(self, collection: str, doc_id: str) -> dict:
        return self.client.collections[collection].documents[doc_id].retrieve()

    def create_document(self, collection: str, document: dict) -> dict:
        return self.client.collections[collection].documents.create(document)

    def upsert_document(self, collection: str, document: dict) -> dict:
        return self.client.collections[collection].documents.upsert(document)

    def update_document(self, collection: str, doc_id: str, partial: dict) -> dict:
        return self.client.collections[collection].documents[doc_id].update(partial)

    def delete_document(self, collection: str, doc_id: str) -> dict:
        return self.client.collections[collection].documents[doc_id].delete()

    def delete_documents(self, collection: str, filter_by: str) -> dict:
        return self.client.collections[collection].documents.delete(
            {"filter_by": filter_by}
        )

    def import_documents(
        self, collection: str, documents: list[dict], action: str = "upsert"
    ) -> list:
        return self.client.collections[collection].documents.import_(
            documents, {"action": action}
        )

    def export_documents(self, collection: str, params: dict | None = None) -> str:
        return self.client.collections[collection].documents.export(params or {})

    # -- Search ---------------------------------------------------------------

    def search(self, collection: str, params: dict) -> dict:
        return self.client.collections[collection].documents.search(params)

    def multi_search(self, searches: list[dict], common_params: dict | None = None) -> dict:
        body = {"searches": searches}
        return self.client.multi_search.perform(body, common_params or {})

    # -- NL Search Models (v29.0) ---------------------------------------------

    def create_nl_search_model(self, model_config: dict) -> dict:
        """Create a natural language search model via the REST API."""
        import httpx

        base = f"{self._config.protocol}://{self._config.host}:{self._config.port}"
        resp = httpx.post(
            f"{base}/nl_search_models",
            json=model_config,
            headers={"X-TYPESENSE-API-KEY": self._config.api_key},
            timeout=self._config.connection_timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def get_nl_search_model(self, model_id: str) -> dict:
        import httpx

        base = f"{self._config.protocol}://{self._config.host}:{self._config.port}"
        resp = httpx.get(
            f"{base}/nl_search_models/{model_id}",
            headers={"X-TYPESENSE-API-KEY": self._config.api_key},
            timeout=self._config.connection_timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def list_nl_search_models(self) -> list[dict]:
        import httpx

        base = f"{self._config.protocol}://{self._config.host}:{self._config.port}"
        resp = httpx.get(
            f"{base}/nl_search_models",
            headers={"X-TYPESENSE-API-KEY": self._config.api_key},
            timeout=self._config.connection_timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def update_nl_search_model(self, model_id: str, updates: dict) -> dict:
        import httpx

        base = f"{self._config.protocol}://{self._config.host}:{self._config.port}"
        resp = httpx.put(
            f"{base}/nl_search_models/{model_id}",
            json=updates,
            headers={"X-TYPESENSE-API-KEY": self._config.api_key},
            timeout=self._config.connection_timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def delete_nl_search_model(self, model_id: str) -> dict:
        import httpx

        base = f"{self._config.protocol}://{self._config.host}:{self._config.port}"
        resp = httpx.delete(
            f"{base}/nl_search_models/{model_id}",
            headers={"X-TYPESENSE-API-KEY": self._config.api_key},
            timeout=self._config.connection_timeout,
        )
        resp.raise_for_status()
        return resp.json()

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
        return {"ok": self.client.operations.is_healthy()}

    # -- Collections ----------------------------------------------------------

    def list_collections(self) -> list[dict]:
        return self.client.collections.retrieve()

    def get_collection(self, name: str) -> dict:
        return self.client.collections[name].retrieve()

    # -- Search ---------------------------------------------------------------

    def search(self, collection: str, params: dict) -> dict:
        return self.client.collections[collection].documents.search(params)

    def multi_search(self, searches: list[dict], common_params: dict | None = None) -> dict:
        body = {"searches": searches}
        return self.client.multi_search.perform(body, common_params or {})


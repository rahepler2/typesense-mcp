"""Configuration management for the Typesense MCP server."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class TypesenseConfig:
    """Configuration for connecting to a Typesense cluster."""

    host: str = field(default_factory=lambda: os.environ.get("TYPESENSE_HOST", "localhost"))
    port: str = field(default_factory=lambda: os.environ.get("TYPESENSE_PORT", "8108"))
    protocol: str = field(default_factory=lambda: os.environ.get("TYPESENSE_PROTOCOL", "http"))
    api_key: str = field(default_factory=lambda: os.environ.get("TYPESENSE_API_KEY", ""))
    connection_timeout: int = field(
        default_factory=lambda: int(os.environ.get("TYPESENSE_CONNECTION_TIMEOUT", "10"))
    )

    def to_client_config(self) -> dict:
        """Convert to a typesense client configuration dict."""
        return {
            "nodes": [
                {
                    "host": self.host,
                    "port": self.port,
                    "protocol": self.protocol,
                }
            ],
            "api_key": self.api_key,
            "connection_timeout_seconds": self.connection_timeout,
        }

"""Natural Language search model management tools (Typesense 29.0)."""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from ..client import TypesenseClientManager


def register(mcp: FastMCP, ts: TypesenseClientManager) -> None:
    """Register NL search model management tools on the MCP server."""

    @mcp.tool()
    def create_nl_search_model(model_config_json: str) -> dict:
        """Create a natural language search model for converting NL queries to structured searches.

        This sets up an LLM that Typesense will use to understand user intent and
        convert natural language into filters, sorts, and query parameters.

        Supported providers: Google Gemini, OpenAI, Cloudflare Workers AI, GCP Vertex AI.

        Args:
            model_config_json: JSON string with the model configuration. Examples:

                Google AI Studio (Gemini):
                {
                    "id": "my-nl-model",
                    "model_name": "google/gemini-2.5-flash",
                    "api_key": "your-google-ai-studio-key",
                    "max_bytes": 10000,
                    "temperature": 0.1
                }

                OpenAI:
                {
                    "id": "my-openai-model",
                    "model_name": "openai/gpt-4.1",
                    "api_key": "your-openai-key",
                    "max_bytes": 10000,
                    "system_prompt": "You help convert queries about car listings."
                }

                Cloudflare Workers AI:
                {
                    "id": "my-cf-model",
                    "model_name": "cloudflare/@cf/meta/llama-2-7b-chat-int8",
                    "api_key": "your-cloudflare-key",
                    "account_id": "your-cf-account-id"
                }
        """
        config = json.loads(model_config_json)
        return ts.create_nl_search_model(config)

    @mcp.tool()
    def list_nl_search_models() -> list[dict]:
        """List all configured natural language search models."""
        return ts.list_nl_search_models()

    @mcp.tool()
    def get_nl_search_model(model_id: str) -> dict:
        """Get details of a specific NL search model.

        Args:
            model_id: The ID of the NL search model.
        """
        return ts.get_nl_search_model(model_id)

    @mcp.tool()
    def update_nl_search_model(model_id: str, updates_json: str) -> dict:
        """Update an existing NL search model configuration.

        Args:
            model_id: The ID of the NL search model to update.
            updates_json: JSON string with the fields to update. Example:
                {"temperature": 0.2, "system_prompt": "Focus on product searches."}
        """
        updates = json.loads(updates_json)
        return ts.update_nl_search_model(model_id, updates)

    @mcp.tool()
    def delete_nl_search_model(model_id: str) -> dict:
        """Delete a natural language search model.

        Args:
            model_id: The ID of the NL search model to delete.
        """
        return ts.delete_nl_search_model(model_id)

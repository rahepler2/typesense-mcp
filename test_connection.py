#!/usr/bin/env python3
"""Quick test script to verify the Typesense MCP server tools work against a live cluster."""

import json
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.client import TypesenseClientManager
from src.config import TypesenseConfig


def main():
    config = TypesenseConfig()

    if not config.api_key:
        print("ERROR: Set TYPESENSE_API_KEY environment variable first.")
        print("  export TYPESENSE_API_KEY=your-api-key")
        print("  export TYPESENSE_HOST=localhost   # optional, default localhost")
        print("  export TYPESENSE_PORT=8108        # optional, default 8108")
        sys.exit(1)

    ts = TypesenseClientManager(config)
    print(f"Connecting to {config.protocol}://{config.host}:{config.port}\n")

    # 1. Health check
    print("=" * 60)
    print("1. HEALTH CHECK")
    print("=" * 60)
    try:
        health = ts.health()
        print(f"   Status: {json.dumps(health)}")
    except Exception as e:
        print(f"   FAILED: {e}")
        print("   Cannot reach Typesense. Check your connection settings.")
        sys.exit(1)

    # 2. List collections
    print("\n" + "=" * 60)
    print("2. LIST COLLECTIONS")
    print("=" * 60)
    collections = ts.list_collections()
    if not collections:
        print("   No collections found. Create one first to test search.")
        sys.exit(0)

    for c in collections:
        num_fields = len(c.get("fields", []))
        print(f"   - {c['name']} ({c.get('num_documents', 0)} docs, {num_fields} fields)")

    # 3. Analyze first collection
    target = collections[0]["name"]
    print(f"\n{'=' * 60}")
    print(f"3. ANALYZE COLLECTION: {target}")
    print("=" * 60)

    col = ts.get_collection(target)
    fields = col.get("fields", [])

    text_fields = []
    embedding_fields = []
    facet_fields = []

    for f in fields:
        print(f"   {f['name']:30s}  type={f['type']:15s}  "
              f"facet={f.get('facet', False)}  optional={f.get('optional', False)}")
        if f["type"] in ("string", "string[]") and f.get("index", True):
            text_fields.append(f["name"])
        if f.get("embed") is not None:
            embedding_fields.append(f["name"])
        if f.get("facet"):
            facet_fields.append(f["name"])

    print(f"\n   Text fields:      {text_fields}")
    print(f"   Embedding fields: {embedding_fields}")
    print(f"   Facet fields:     {facet_fields}")

    # 4. Sample documents
    print(f"\n{'=' * 60}")
    print(f"4. SAMPLE DOCUMENTS FROM: {target}")
    print("=" * 60)

    sample = ts.search(target, {"q": "*", "per_page": 3})
    for i, hit in enumerate(sample.get("hits", [])):
        doc = hit.get("document", {})
        # Filter out large embedding arrays for display
        display = {
            k: v for k, v in doc.items()
            if not (isinstance(v, list) and len(v) > 50)
        }
        print(f"\n   Document {i + 1}:")
        print(f"   {json.dumps(display, indent=4, default=str)[:500]}")

    # 5. Keyword search
    if text_fields:
        query_by = ",".join(text_fields[:3])
        print(f"\n{'=' * 60}")
        print(f"5. KEYWORD SEARCH (query_by={query_by})")
        print("=" * 60)

        result = ts.search(target, {
            "q": "*",
            "query_by": query_by,
            "per_page": 3,
        })
        print(f"   Found: {result.get('found', 0)} documents")
        print(f"   Search time: {result.get('search_time_ms', '?')}ms")

    # 6. Hybrid search (if embedding fields exist)
    if embedding_fields and text_fields:
        hybrid_query_by = ",".join(text_fields[:2] + embedding_fields[:1])
        exclude = ",".join(embedding_fields)
        print(f"\n{'=' * 60}")
        print(f"6. HYBRID SEARCH (query_by={hybrid_query_by})")
        print("=" * 60)

        result = ts.search(target, {
            "q": "test",
            "query_by": hybrid_query_by,
            "exclude_fields": exclude,
            "per_page": 3,
            "rerank_hybrid_matches": True,
        })
        print(f"   Found: {result.get('found', 0)} documents")
        print(f"   Search time: {result.get('search_time_ms', '?')}ms")
        for i, hit in enumerate(result.get("hits", [])):
            doc = hit.get("document", {})
            vd = hit.get("vector_distance", "N/A")
            tm = hit.get("text_match_info", {}).get("score", "N/A")
            first_field = next(
                (doc[f] for f in text_fields if f in doc and doc[f]), "?"
            )
            label = str(first_field)[:80]
            print(f"   [{i + 1}] vector_dist={vd}  text_score={tm}  {label}")
    elif not embedding_fields:
        print(f"\n   Skipping hybrid search — no embedding fields found in '{target}'.")

    # 7. Facet search
    if facet_fields:
        print(f"\n{'=' * 60}")
        print(f"7. FACET QUERY (facet_by={facet_fields[0]})")
        print("=" * 60)

        result = ts.search(target, {
            "q": "*",
            "query_by": text_fields[0] if text_fields else facet_fields[0],
            "facet_by": facet_fields[0],
            "max_facet_values": 5,
            "per_page": 0,
        })
        for fc in result.get("facet_counts", []):
            print(f"   Field: {fc['field_name']}")
            for v in fc.get("counts", [])[:5]:
                print(f"     {v['value']:30s}  count={v['count']}")

    print(f"\n{'=' * 60}")
    print("ALL TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()

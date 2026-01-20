"""Typesense collection schemas for policy/procedure document search."""

from .collections import (
    DOCUMENTS_METADATA_SCHEMA,
    DOCUMENT_CHUNKS_SCHEMA,
    DOCUMENT_TYPES,
    DOCUMENT_STATUSES,
)

__all__ = [
    "DOCUMENTS_METADATA_SCHEMA",
    "DOCUMENT_CHUNKS_SCHEMA",
    "DOCUMENT_TYPES",
    "DOCUMENT_STATUSES",
]

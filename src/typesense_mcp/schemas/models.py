"""
Pydantic models for policy/procedure documents.

These models provide:
    - Type safety and validation
    - Serialization to/from Typesense documents
    - Clear API contracts for MCP tools
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, computed_field


class DocumentType(str, Enum):
    """Valid document types in the system."""

    POLICY = "policy"
    PROCEDURE = "procedure"
    FORM = "form"


class DocumentStatus(str, Enum):
    """Document lifecycle status."""

    ACTIVE = "active"
    DRAFT = "draft"
    ARCHIVED = "archived"
    SUPERSEDED = "superseded"


# =============================================================================
# Document Metadata Models
# =============================================================================


class DocumentMetadataBase(BaseModel):
    """Base fields for document metadata."""

    title: str = Field(..., min_length=1, max_length=500)
    document_type: DocumentType
    department: str = Field(..., min_length=1, max_length=100)
    categories: list[str] = Field(default_factory=list)
    status: DocumentStatus = DocumentStatus.DRAFT
    effective_date: datetime
    review_date: Optional[datetime] = None
    version: Optional[str] = Field(None, max_length=20)
    author: Optional[str] = Field(None, max_length=200)
    approver: Optional[str] = Field(None, max_length=200)
    summary: Optional[str] = Field(None, max_length=2000)
    source_url: Optional[str] = None


class DocumentMetadataCreate(DocumentMetadataBase):
    """Model for creating a new document."""

    pass


class DocumentMetadata(DocumentMetadataBase):
    """Full document metadata model with all fields."""

    id: str
    chunk_count: int = 0
    created_at: datetime
    updated_at: datetime

    def to_typesense(self) -> dict:
        """Convert to Typesense document format."""
        return {
            "id": self.id,
            "title": self.title,
            "document_type": self.document_type.value,
            "department": self.department,
            "categories": self.categories,
            "status": self.status.value,
            "effective_date": int(self.effective_date.timestamp()),
            "review_date": int(self.review_date.timestamp()) if self.review_date else None,
            "version": self.version,
            "author": self.author,
            "approver": self.approver,
            "summary": self.summary,
            "source_url": self.source_url,
            "chunk_count": self.chunk_count,
            "created_at": int(self.created_at.timestamp()),
            "updated_at": int(self.updated_at.timestamp()),
        }

    @classmethod
    def from_typesense(cls, doc: dict) -> "DocumentMetadata":
        """Create model from Typesense document."""
        return cls(
            id=doc["id"],
            title=doc["title"],
            document_type=DocumentType(doc["document_type"]),
            department=doc["department"],
            categories=doc.get("categories", []),
            status=DocumentStatus(doc["status"]),
            effective_date=datetime.fromtimestamp(doc["effective_date"]),
            review_date=datetime.fromtimestamp(doc["review_date"]) if doc.get("review_date") else None,
            version=doc.get("version"),
            author=doc.get("author"),
            approver=doc.get("approver"),
            summary=doc.get("summary"),
            source_url=doc.get("source_url"),
            chunk_count=doc.get("chunk_count", 0),
            created_at=datetime.fromtimestamp(doc["created_at"]),
            updated_at=datetime.fromtimestamp(doc["updated_at"]),
        )


# =============================================================================
# Document Chunk Models
# =============================================================================


class DocumentChunkBase(BaseModel):
    """Base fields for a document chunk."""

    document_id: str
    chunk_index: int = Field(..., ge=0)
    text: str = Field(..., min_length=1)
    section_title: Optional[str] = Field(None, max_length=500)
    page_number: Optional[int] = Field(None, ge=1)


class DocumentChunkCreate(DocumentChunkBase):
    """Model for creating a new chunk (with denormalized metadata)."""

    document_type: DocumentType
    department: str
    status: DocumentStatus
    document_title: str
    embedding: Optional[list[float]] = None  # Optional if Typesense generates it


class DocumentChunk(DocumentChunkBase):
    """Full document chunk model."""

    id: str
    document_type: DocumentType
    department: str
    status: DocumentStatus
    document_title: str
    embedding: Optional[list[float]] = None
    created_at: datetime

    @computed_field
    @property
    def chunk_id(self) -> str:
        """Generate the composite chunk ID."""
        return f"{self.document_id}_{self.chunk_index}"

    def to_typesense(self, include_embedding: bool = True) -> dict:
        """Convert to Typesense document format."""
        doc = {
            "id": self.id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "text": self.text,
            "section_title": self.section_title,
            "page_number": self.page_number,
            "document_type": self.document_type.value,
            "department": self.department,
            "status": self.status.value,
            "document_title": self.document_title,
            "created_at": int(self.created_at.timestamp()),
        }
        if include_embedding and self.embedding:
            doc["embedding"] = self.embedding
        return doc

    @classmethod
    def from_typesense(cls, doc: dict) -> "DocumentChunk":
        """Create model from Typesense document."""
        return cls(
            id=doc["id"],
            document_id=doc["document_id"],
            chunk_index=doc["chunk_index"],
            text=doc["text"],
            section_title=doc.get("section_title"),
            page_number=doc.get("page_number"),
            document_type=DocumentType(doc["document_type"]),
            department=doc["department"],
            status=DocumentStatus(doc["status"]),
            document_title=doc["document_title"],
            embedding=doc.get("embedding"),
            created_at=datetime.fromtimestamp(doc["created_at"]),
        )


# =============================================================================
# Search Result Models
# =============================================================================


class ChunkSearchResult(BaseModel):
    """A single chunk search result with relevance info."""

    chunk: DocumentChunk
    score: float = Field(..., description="Relevance score from Typesense")
    highlights: dict = Field(default_factory=dict, description="Highlighted snippets")


class SearchResults(BaseModel):
    """Aggregated search results."""

    query: str
    total_found: int
    results: list[ChunkSearchResult]
    facets: dict = Field(default_factory=dict)
    search_time_ms: int


class DocumentWithChunks(BaseModel):
    """A document with its matching chunks (for grouped results)."""

    metadata: DocumentMetadata
    chunks: list[DocumentChunk]
    max_chunk_score: float = Field(..., description="Highest chunk score for ranking")

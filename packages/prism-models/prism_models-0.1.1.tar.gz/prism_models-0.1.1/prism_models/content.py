import enum
from typing import Any, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from prism_models.base import Base, BaseModel
from prism_models.chat import Contact
from prism_models.qdrant import QdrantVectorPayload, PydanticType


class DocumentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class DocumentPublishStatus(str, enum.Enum):
    PREVIEW = "preview"
    ACTIVE = "active"
    INACTIVE = "inactive"

class SyncFrequency(str, enum.Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    REALTIME = "realtime"


class ChunkStrategy(str, enum.Enum):
    FIXED_SIZE = "fixed_size"
    SEMANTIC = "semantic"
    PARAGRAPH = "paragraph"
    DOCLING_HYBRID = "docling_hybrid"
    LLM = "llm"


class ProvenanceType(str, enum.Enum):
    GENERATED = "generated"
    MANUAL = "manual"
    VERIFIED = "verified"


class SourceName(str, enum.Enum):
    S3 = "S3"
    SHARE_POINT = "SHARE_POINT"
    GRID = "GRID"
    GRID_DESTINATION_REPORT = "GRID_DESTINATION_REPORT"
    GRID_EVENT_REPORT = "GRID_EVENT_REPORT"
    CRM = "CRM"
    CONFLUENCE = "CONFLUENCE"
    CUSTOM = "CUSTOM"
    TRAVEL_ADVISORY = "TRAVEL_ADVISORY"
    MSA = "MSA"

class Source(BaseModel):
    """Source model for tracking origin of content."""

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True
    )
    
    type: Mapped[SourceName] = mapped_column(
        Enum(SourceName, native_enum=False),
        nullable=True,
        index=True,
        default=SourceName.CUSTOM
    )

    connection_config: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True, default=dict
    )
    additional_data: Mapped[dict[str, Any] | None] = mapped_column(
        "additional_data", JSON, nullable=True, default=dict
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # New fields (nullable, only meaningful if name == S3)
    s3_bucket: Mapped[str | None] = mapped_column(String(255), nullable=True)
    s3_directory: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    # One-to-one relationship to Collection via unique FK - NOTE NOT UNIQUE
    collection_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("collection.id"), nullable=False, unique=True, index=True
    )
    collection: Mapped[Optional["Collection"]] = relationship(
        "Collection", back_populates="source", uselist=False
    )


    def __repr__(self):
        return f"<Source(id={getattr(self, 'id', None)}, name='{self.name}')>"


class Collection(BaseModel):
    """Collection model for grouping documents."""

    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    additional_data: Mapped[dict[str, Any] | None] = mapped_column("additional_data", JSON, nullable=True, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("contact.id"), nullable=True, index=True)
    # Relationships
    owner: Mapped[Optional["Contact"]] = relationship("Contact")
    documents: Mapped[list["CollectionDocument"]] = relationship(back_populates="collection")
    # One-to-one backref to Source
    source: Mapped[Optional["Source"]] = relationship(
        "Source", back_populates="collection", uselist=False
    )

    __table_args__ = (UniqueConstraint("name", name="uq_collection_name"),)

    def __repr__(self):
        return f"<Collection(id={self.id}, name='{self.name}', is_active={self.is_active})>"


class Document(BaseModel):
    """Document model for storing various types of content."""

    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("source.id"), nullable=False, index=True)
    parent_document_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("document.id"), nullable=True, index=True)

    uploaded_by_id: Mapped[int | None] = mapped_column(ForeignKey("contact.id"), nullable=True, index=True)
    file_path_s3: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    file_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_latest: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    additional_data: Mapped[dict[str, Any] | None] = mapped_column("additional_data", JSON, nullable=True, default=dict)
    status: Mapped[DocumentStatus] = mapped_column(String(50), nullable=False, index=True, default=DocumentStatus.PENDING)
    publish_status: Mapped[DocumentPublishStatus] = mapped_column(String(50), nullable=False, index=True, default=DocumentPublishStatus.PREVIEW)
    markdown_file_path_s3:Mapped[str | None] = mapped_column(String(2048), nullable=True)
    chunk_config_id: Mapped[int | None] = mapped_column(ForeignKey("chunk_config.id", ondelete="SET NULL"), nullable=True)
    sharepoint_drive_item_id: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    # Relationships
    source: Mapped["Source"] = relationship("Source")
    # Use string-based remote_side to avoid resolving Python built-in id
    parent_document: Mapped[Optional["Document"]] = relationship("Document", remote_side="Document.id")
    chunk_config: Mapped[Optional["ChunkConfig"]] = relationship("ChunkConfig", back_populates="documents")
    uploaded_by: Mapped[Optional["Contact"]] = relationship("Contact", foreign_keys=[uploaded_by_id])
    collections: Mapped[list["CollectionDocument"]] = relationship(back_populates="document")
    chunks: Mapped[list["Chunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    qa_pairs: Mapped[list["QAPair"]] = relationship(back_populates="document", cascade="all, delete-orphan")


    def __repr__(self):
        return f"<Document(id={self.id}, title='{self.title[:50]}...')>"


class CollectionDocument(BaseModel):
    """Association object between Collections and Documents."""

    collection_id: Mapped[int] = mapped_column(ForeignKey("collection.id"), nullable=False)
    document_id: Mapped[int] = mapped_column(ForeignKey("document.id"), nullable=False)

    collection: Mapped["Collection"] = relationship(back_populates="documents")
    document: Mapped["Document"] = relationship(back_populates="collections")

    __table_args__ = (UniqueConstraint("collection_id", "document_id", name="uq_collection_document"),)


class IntegrationConfig(BaseModel):
    source_id: Mapped[int] = mapped_column(ForeignKey("source.id"), nullable=False, index=True)
    chunk_config_id: Mapped[int | None] = mapped_column(ForeignKey("chunk_config.id"))
    external_id: Mapped[str | None] = mapped_column(String(255))
    target_collection_ids: Mapped[list[int] | None] = mapped_column(ARRAY(Integer))
    sync_frequency: Mapped[SyncFrequency] = mapped_column(String(20), default=SyncFrequency.DAILY)
    sync_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    source: Mapped["Source"] = relationship()
    chunk_config: Mapped["ChunkConfig"] = relationship()


class ChunkConfig(BaseModel):
    name: Mapped[str] = mapped_column(String(255))
    strategy: Mapped[ChunkStrategy] = mapped_column(String(50), default=ChunkStrategy.DOCLING_HYBRID)
    chunk_size: Mapped[int] = mapped_column(Integer, default=600)
    chunk_overlap: Mapped[int] = mapped_column(Integer, default=60)
    internal_qa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    external_qa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    internal_qa_prompt: Mapped[str | None] = mapped_column(Text)
    external_qa_prompt: Mapped[str | None] = mapped_column(Text)
    additional_data: Mapped[dict[str, Any] | None] = mapped_column("additional_data", JSON, nullable=True, default=dict)
    is_template: Mapped[bool] = mapped_column(Boolean, default=False)

    documents: Mapped[list["Document"]] = relationship("Document", back_populates="chunk_config")


qa_pair_chunk_association_table = Table(
    "qa_pair_chunk_association",
    Base.metadata,
    Column("qa_pair_id", ForeignKey("qa_pair.id"), primary_key=True),
    Column("chunk_id", ForeignKey("chunk.id"), primary_key=True),
)


class Chunk(BaseModel):
    document_id: Mapped[int] = mapped_column(ForeignKey("document.id"), nullable=False, index=True)
    chunk_config_id: Mapped[int | None] = mapped_column(ForeignKey("chunk_config.id"))
    text: Mapped[str] = mapped_column(Text, nullable=False)
    text_hash: Mapped[str | None] = mapped_column(String(64), index=True)

    document: Mapped["Document"] = relationship(back_populates="chunks")
    chunk_config: Mapped[Optional["ChunkConfig"]] = relationship()
    qa_pairs: Mapped[list["QAPair"]] = relationship(secondary=qa_pair_chunk_association_table, back_populates="source_chunks")
    vector: Mapped[Optional["Vector"]] = relationship(back_populates="chunk", uselist=False, cascade="all, delete-orphan")


class QAPair(BaseModel):
    document_id: Mapped[int] = mapped_column(ForeignKey("document.id"), nullable=False, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    provenance: Mapped[ProvenanceType] = mapped_column(String(50), default=ProvenanceType.GENERATED)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    document: Mapped["Document"] = relationship(back_populates="qa_pairs")
    source_chunks: Mapped[list["Chunk"]] = relationship(secondary=qa_pair_chunk_association_table, back_populates="qa_pairs")
    vector: Mapped[Optional["Vector"]] = relationship(back_populates="qa_pair", uselist=False, cascade="all, delete-orphan")

class Vector(BaseModel):
    chunk_id: Mapped[int] = mapped_column(ForeignKey("chunk.id"), nullable=True, unique=True)
    qa_pair_id: Mapped[int] = mapped_column(ForeignKey("qa_pair.id"), nullable=True, unique=True)
    model: Mapped[str] = mapped_column(String(100))
    qdrant_point_id: Mapped[str | None] = mapped_column(String(100), unique=True)
    vector_embeddings: Mapped[list[float] | None] = mapped_column(ARRAY(Float), nullable=True)
    additional_data: Mapped[QdrantVectorPayload | None] = mapped_column(
        PydanticType(QdrantVectorPayload), 
        nullable=True
    )
    

    chunk: Mapped["Chunk"] = relationship(back_populates="vector")
    qa_pair: Mapped["QAPair"] = relationship(back_populates="vector")
import enum
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    JSON,
    TIMESTAMP,
    Boolean,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from prism_models.base import BaseModel
from prism_models.chat import Contact, ConversationMessage
from prism_models.content import Chunk, QAPair

# MessageFeedback model removed - using new Feedback model below


class FeedbackType(str, enum.Enum):
    THUMBS_DOWN = "thumbs_down"
    CORRECTION = "correction"
    ENHANCEMENT = "enhancement"
    DELETION = "deletion"
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"


class FeedbackStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"


class FeedbackConfidence(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ABSOLUTE = "absolute"


class AugmentationAction(str, enum.Enum):
    CREATE = "create"
    CORRECT = "correct"
    ENHANCE = "enhance"
    DELETE = "delete"


class AugmentationStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisType(str, enum.Enum):
    CONTENT_ANALYSIS = "content_analysis"
    IMPACT_ASSESSMENT = "impact_assessment"
    ROOT_CAUSE_ANALYSIS = "root_cause_analysis"


class Feedback(BaseModel):
    manager_id: Mapped[int] = mapped_column(Integer, ForeignKey("contact.id"), nullable=False, index=True)
    chunk_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("chunk.id"), nullable=True, index=True)
    qa_pair_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("qa_pair.id"), nullable=True, index=True)
    # Link feedback to a specific conversation message
    message_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("conversation_message.id"),
        nullable=True,
        index=True,
    )
    assigned_reviewer_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("contact.id"), nullable=True, index=True)

    authority_domain: Mapped[str | None] = mapped_column(String(255))
    confidence_level: Mapped[FeedbackConfidence | None] = mapped_column(String(50))
    feedback_type: Mapped[FeedbackType] = mapped_column(String(50), nullable=False)

    # user query, agent response, correction note,
    query: Mapped[str | None] = mapped_column(Text)
    provided_response: Mapped[str | None] = mapped_column(Text)
    correction: Mapped[str | None] = mapped_column(Text)
    requires_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[FeedbackStatus] = mapped_column(String(50), default=FeedbackStatus.PENDING, nullable=False, index=True)
    admin_notes: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    routed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    manager: Mapped["Contact"] = relationship(foreign_keys=[manager_id])
    chunk: Mapped[Optional["Chunk"]] = relationship()
    qa_pair: Mapped[Optional["QAPair"]] = relationship()
    message: Mapped[Optional["ConversationMessage"]] = relationship()
    assigned_reviewer: Mapped[Optional["Contact"]] = relationship(foreign_keys=[assigned_reviewer_id])

    analysis: Mapped[list["FeedbackAnalysis"]] = relationship(back_populates="feedback", cascade="all, delete-orphan")
    augmentations: Mapped[list["Augmentation"]] = relationship(back_populates="feedback", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Feedback(id={self.id}, type='{self.feedback_type}', status='{self.status}')>"


class FeedbackAnalysis(BaseModel):
    __tablename__ = "feedback_analysis"
    feedback_id: Mapped[int] = mapped_column(Integer, ForeignKey("feedback.id"), nullable=False, index=True)

    analysis_type: Mapped[AnalysisType] = mapped_column(String(50), nullable=False)
    llm_response: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    confidence_score: Mapped[float | None] = mapped_column(Float)
    model_used: Mapped[str | None] = mapped_column(String(255))
    analyzed_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reason_to_reject: Mapped[str | None] = mapped_column(Text)

    # Relationships
    feedback: Mapped["Feedback"] = relationship(back_populates="analysis")

    def __repr__(self):
        return f"<FeedbackAnalysis(id={self.id}, feedback_id={self.feedback_id}, type='{self.analysis_type}')>"


class Augmentation(BaseModel):
    feedback_id: Mapped[int] = mapped_column(Integer, ForeignKey("feedback.id"), nullable=False, index=True)
    original_chunk_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("chunk.id"), nullable=True)
    original_qa_pair_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("qa_pair.id"), nullable=True)
    generated_chunk_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("chunk.id"), nullable=True)
    generated_qa_pair_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("qa_pair.id"), nullable=True)

    action_type: Mapped[AugmentationAction] = mapped_column(String(50), nullable=False)
    change_summary: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    status: Mapped[AugmentationStatus] = mapped_column(String(50), default=AugmentationStatus.PENDING, nullable=False, index=True)
    # Relationships
    feedback: Mapped["Feedback"] = relationship(back_populates="augmentations")
    original_chunk: Mapped[Optional["Chunk"]] = relationship(foreign_keys=[original_chunk_id])
    original_qa_pair: Mapped[Optional["QAPair"]] = relationship(foreign_keys=[original_qa_pair_id])
    generated_chunk: Mapped[Optional["Chunk"]] = relationship(foreign_keys=[generated_chunk_id])
    generated_qa_pair: Mapped[Optional["QAPair"]] = relationship(foreign_keys=[generated_qa_pair_id])

    def __repr__(self):
        return f"<Augmentation(id={self.id}, action='{self.action_type}', status='{self.status}')>"

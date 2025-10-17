"""Profile model for storing user profile information."""

from datetime import datetime
from enum import Enum

from sqlalchemy import TIMESTAMP, Boolean
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import Text

from prism_models.base import BaseModel
from prism_models.content import Collection


class Profile(BaseModel):
    """
    Profile model for organizing prompt variants by team/use case.

    Profiles allow admins to create different prompt variations for different
    teams or scenarios (e.g., "marketing_aggressive", "support_friendly", "default").
    Each profile allows configuration of multiple agents.

    Relationships:
        - profile_prompts: One-to-many with ProfilePrompt
        - agent_profiles: One-to-many with AgentProfile
        - conversation_profiles: One-to-many with ConversationProfile
    """

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(1024))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (UniqueConstraint("name", name="uq_profile_name"),)

    def __repr__(self) -> str:
        return f"<Profile(id={self.id}, name='{self.name}', active={self.is_active})>"


class Agent(BaseModel):
    """Agent model for storing agent information."""

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    display_name: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String(1024))

    __table_args__ = (
        UniqueConstraint("name", name="uq_agent_name"),
        UniqueConstraint("display_name", name="uq_agent_display_name"),
    )

    def __repr__(self) -> str:
        return f"<Agent(id={self.id}, name='{self.name}')>"


class AgentProfileStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PREVIEW = "preview"


class AgentProfile(BaseModel):
    """AgentProfile model for storing agent profile information."""

    agent_id: Mapped[int] = mapped_column(Integer, ForeignKey("agent.id"), nullable=False, index=True)
    profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("profile.id"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[AgentProfileStatus] = mapped_column(
        SAEnum(AgentProfileStatus, name="agent_profile_status"),
        default=AgentProfileStatus.PREVIEW,
        nullable=False,
    )
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    prompt: Mapped[str | None] = mapped_column(Text)

    # NOT SURE IF WE NEED THIS could lead to N+1 queries
    # TODO: Add relationship if needed
    # agent: Mapped["Agent"] = relationship(back_populates="profile")
    # profile: Mapped["Profile"] = relationship(back_populates="agent")


class ProfileCollectionAccess(BaseModel):
    """ProfileCollectionAccess model for storing profile collection access information."""

    profile_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("profile.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    collection_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("collection.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    access_granted_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=True)
    
    collection: Mapped["Collection"] = relationship()

    __table_args__ = (UniqueConstraint("profile_id", "collection_id", name="uq_profile_collection"),)

from typing import List, Optional
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import uuid
from sqlalchemy import DateTime, ForeignKey, String, Text, Enum, JSON, UniqueConstraint
from backend.app.core.enums import IngestionStatus, SourceType, Roles
from datetime import datetime, timezone

# NOTE: Base defined here because was removed from database.py and model.Base.metadata.create_all() was used in init_db
class Base(DeclarativeBase):
    pass


class Tenant(Base):
    __tablename__ = "tenants"

    tenant_id: Mapped[str] = mapped_column(primary_key = True, default = lambda: str(uuid.uuid4()))

    organization_name: Mapped[str] = mapped_column(String)
    # TODO = Email casing: the unique constraint treats A@x.com and a@x.com as different. Lowercase the email in the tenant service
    admin_email: Mapped[str] = mapped_column(unique = True)
    hashed_api_key: Mapped[str] = mapped_column(unique = True)

    agents: Mapped[List["Agent"]] = relationship(back_populates = "tenant", cascade = "all, delete-orphan", passive_deletes = True)


class Agent(Base):
    __tablename__ = "agents"

    agent_id: Mapped[str] = mapped_column(primary_key = True, default = lambda: str(uuid.uuid4()))

    agent_name: Mapped[str] = mapped_column(String)
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable = True)
    indexed_chunk_count: Mapped[int] = mapped_column(default = 0)
    ingestion_status: Mapped[IngestionStatus] = mapped_column(Enum(IngestionStatus), default = IngestionStatus.PROCESSING)
    created_at: Mapped[datetime] = mapped_column(DateTime, default = lambda: datetime.now(timezone.utc))
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable = True)
    website_url: Mapped[str] = mapped_column(String)

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.tenant_id", ondelete = "CASCADE"), index = True)

    tenant: Mapped["Tenant"] = relationship(back_populates = "agents")
    conversations: Mapped[List["Conversation"]] = relationship(back_populates = "agent", cascade = "all, delete-orphan", passive_deletes = True)
    sources: Mapped[List["Source"]] = relationship(back_populates = "agent", cascade = "all, delete-orphan", passive_deletes = True)


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = (UniqueConstraint("tenant_id", "agent_id", "session_id", name = "uq_conversation_session"),)

    conversation_id: Mapped[str] = mapped_column(primary_key = True, default = lambda: str(uuid.uuid4()))

    session_id: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default = lambda: datetime.now(timezone.utc))

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.tenant_id", ondelete = "CASCADE"), index = True)
    agent_id: Mapped[str] = mapped_column(ForeignKey("agents.agent_id", ondelete = "CASCADE"), index = True)

    tenant: Mapped["Tenant"] = relationship()
    agent: Mapped["Agent"] = relationship(back_populates = "conversations")
    messages: Mapped[List["Message"]] = relationship(back_populates = "conversation", cascade = "all, delete-orphan", passive_deletes = True)


class Source(Base):
    __tablename__ = "sources"

    source_id: Mapped[str] = mapped_column(primary_key = True, default = lambda: str(uuid.uuid4()))

    source_type: Mapped[SourceType] = mapped_column(Enum(SourceType), default = SourceType.DOCUMENT)
    title: Mapped[str] = mapped_column(Text)
    url: Mapped[Optional[str]] = mapped_column(String, nullable = True)
    status: Mapped[IngestionStatus] = mapped_column(Enum(IngestionStatus), default = IngestionStatus.PROCESSING)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable = True)
    file_path: Mapped[Optional[str]] = mapped_column(String, nullable = True)

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.tenant_id", ondelete = "CASCADE"), index = True)
    agent_id: Mapped[str] = mapped_column(ForeignKey("agents.agent_id", ondelete = "CASCADE"), index = True)

    tenant: Mapped["Tenant"] = relationship()
    agent: Mapped["Agent"] = relationship(back_populates = "sources")


class Message(Base):
    __tablename__ = "messages"

    message_id: Mapped[str] = mapped_column(primary_key = True, default = lambda: str(uuid.uuid4()))
    role: Mapped[Roles] = mapped_column(Enum(Roles), default = Roles.ASSISTANT)
    content: Mapped[str] = mapped_column(Text)
    citation: Mapped[Optional[str]] = mapped_column(JSON, nullable = True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default = lambda: datetime.now(timezone.utc))

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.tenant_id", ondelete = "CASCADE"), index = True)
    agent_id: Mapped[str] = mapped_column(ForeignKey("agents.agent_id", ondelete = "CASCADE"), index = True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.conversation_id", ondelete = "CASCADE"), index = True)

    tenant: Mapped["Tenant"] = relationship()
    agent: Mapped["Agent"] = relationship()
    conversation: Mapped["Conversation"] = relationship(back_populates = "messages")

# Tenant
#  └── Agent
#       ├── Source
#       └── Conversation
#            └── Message
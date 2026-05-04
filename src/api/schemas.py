"""Database models for PostgreSQL persistence."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(256), default="")
    raw_requirement: Mapped[str] = mapped_column(Text, default="")
    clarified_requirement: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="created")
    phase: Mapped[str] = mapped_column(String(32), default="init")

    project_info: Mapped[dict] = mapped_column(JSON, default=dict)
    dialog_history: Mapped[list] = mapped_column(JSON, default=list)
    reasoning_chain: Mapped[list] = mapped_column(JSON, default=list)
    review_flags: Mapped[list] = mapped_column(JSON, default=list)

    feasibility_result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    resource_result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    risk_result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    final_decision: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    final_recommendation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    key_assumptions: Mapped[list] = mapped_column(JSON, default=list)
    uncertainties: Mapped[list] = mapped_column(JSON, default=list)
    document_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    needs_review: Mapped[bool] = mapped_column(Boolean, default=False)
    human_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    review_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    review_approved: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

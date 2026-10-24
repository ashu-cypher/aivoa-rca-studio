import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def _id() -> str:
    return str(uuid.uuid4())


class Investigation(Base):
    __tablename__ = "investigations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    title: Mapped[str] = mapped_column(String(500), default="Untitled investigation")
    deviation_reference: Mapped[str | None] = mapped_column(String(200), nullable=True)
    event_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    manufacturing_stage: Mapped[str | None] = mapped_column(String(300), nullable=True)
    product_batch: Mapped[str | None] = mapped_column(String(300), nullable=True)
    site_equipment: Mapped[str | None] = mapped_column(String(300), nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    observed_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    containment_actions: Mapped[str | None] = mapped_column(Text, nullable=True)
    impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="Draft", index=True)
    source_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_filename: Mapped[str | None] = mapped_column(String(300), nullable=True)
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    reviewer_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    reviewer_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    evidence = relationship("EvidenceItem", back_populates="investigation", cascade="all, delete-orphan")
    root_causes = relationship("RootCauseCandidate", back_populates="investigation", cascade="all, delete-orphan")
    five_whys = relationship("FiveWhyEntry", back_populates="investigation", cascade="all, delete-orphan")
    fishbone = relationship("FishboneCause", back_populates="investigation", cascade="all, delete-orphan")
    capas = relationship("CapaAction", back_populates="investigation", cascade="all, delete-orphan")
    reviews = relationship("ReviewEvent", back_populates="investigation", cascade="all, delete-orphan")


class EvidenceItem(Base):
    __tablename__ = "evidence_items"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    investigation_id: Mapped[str] = mapped_column(String(36), ForeignKey("investigations.id"), index=True)
    kind: Mapped[str] = mapped_column(String(50))  # confirmed|hypothesis|contradictory|missing|followup|checklist|excerpt
    text: Mapped[str] = mapped_column(Text)
    source_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="Open")
    investigation = relationship("Investigation", back_populates="evidence")


class RootCauseCandidate(Base):
    __tablename__ = "root_cause_candidates"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    investigation_id: Mapped[str] = mapped_column(String(36), ForeignKey("investigations.id"), index=True)
    rank: Mapped[int] = mapped_column(default=1)
    cause: Mapped[str] = mapped_column(Text)
    rationale: Mapped[str] = mapped_column(Text, default="")
    supporting_evidence: Mapped[str] = mapped_column(Text, default="")
    contradictory_evidence: Mapped[str] = mapped_column(Text, default="")
    contributing_factors: Mapped[str] = mapped_column(Text, default="")
    verification_steps: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(50), default="Hypothesis")
    investigation = relationship("Investigation", back_populates="root_causes")


class FiveWhyEntry(Base):
    __tablename__ = "five_whys_entries"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    investigation_id: Mapped[str] = mapped_column(String(36), ForeignKey("investigations.id"), index=True)
    position: Mapped[int] = mapped_column(default=1)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    connection: Mapped[str] = mapped_column(Text, default="")
    is_hypothesis: Mapped[bool] = mapped_column(default=True)
    investigation = relationship("Investigation", back_populates="five_whys")


class FishboneCause(Base):
    __tablename__ = "fishbone_causes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    investigation_id: Mapped[str] = mapped_column(String(36), ForeignKey("investigations.id"), index=True)
    category: Mapped[str] = mapped_column(String(100))
    cause: Mapped[str] = mapped_column(Text)
    supporting_evidence: Mapped[str] = mapped_column(Text, default="")
    evidence_gap: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(50), default="Hypothesis")
    investigation = relationship("Investigation", back_populates="fishbone")


class CapaAction(Base):
    __tablename__ = "capa_actions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    investigation_id: Mapped[str] = mapped_column(String(36), ForeignKey("investigations.id"), index=True)
    action_type: Mapped[str] = mapped_column(String(50))  # Correction|Corrective Action|Preventive Action
    description: Mapped[str] = mapped_column(Text)
    rationale: Mapped[str] = mapped_column(Text, default="")
    linked_cause: Mapped[str] = mapped_column(Text, default="")
    priority: Mapped[str] = mapped_column(String(20), default="Medium")
    owner_role: Mapped[str] = mapped_column(String(200), default="")
    target_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    effectiveness_method: Mapped[str] = mapped_column(Text, default="")
    evidence_to_close: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(50), default="Proposed")
    investigation = relationship("Investigation", back_populates="capas")


class ReviewEvent(Base):
    __tablename__ = "review_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    investigation_id: Mapped[str] = mapped_column(String(36), ForeignKey("investigations.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(50))
    actor: Mapped[str] = mapped_column(String(200), default="Reviewer (demo, unauthenticated)")
    comment: Mapped[str] = mapped_column(Text, default="")
    from_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    to_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    investigation = relationship("Investigation", back_populates="reviews")

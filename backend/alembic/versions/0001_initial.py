"""Initial schema: investigations + evidence + RCA + CAPA + review events.

This migration mirrors app/models/models.py. For local SQLite dev the app also
runs Base.metadata.create_all on startup; for PostgreSQL, run `alembic upgrade head`.
Revision: 0001
"""
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text, Boolean
    from alembic import op

    op.create_table("investigations",
        Column("id", String(36), primary_key=True),
        Column("title", String(500)), Column("deviation_reference", String(200), nullable=True),
        Column("event_date", String(50), nullable=True), Column("manufacturing_stage", String(300), nullable=True),
        Column("product_batch", String(300), nullable=True), Column("site_equipment", String(300), nullable=True),
        Column("description", Text), Column("observed_result", Text, nullable=True),
        Column("expected_result", Text, nullable=True), Column("containment_actions", Text, nullable=True),
        Column("impact", Text, nullable=True), Column("summary", Text, nullable=True),
        Column("status", String(50)), Column("source_type", String(50), nullable=True),
        Column("source_filename", String(300), nullable=True), Column("source_text", Text, nullable=True),
        Column("extracted_json", JSON, nullable=True), Column("reviewer_name", String(200), nullable=True),
        Column("reviewer_comment", Text, nullable=True), Column("created_at", DateTime), Column("updated_at", DateTime))
    op.create_table("evidence_items",
        Column("id", String(36), primary_key=True), Column("investigation_id", String(36), ForeignKey("investigations.id")),
        Column("kind", String(50)), Column("text", Text), Column("source_excerpt", Text, nullable=True), Column("status", String(50)))
    op.create_table("root_cause_candidates",
        Column("id", String(36), primary_key=True), Column("investigation_id", String(36), ForeignKey("investigations.id")),
        Column("rank", Integer), Column("cause", Text), Column("rationale", Text), Column("supporting_evidence", Text),
        Column("contradictory_evidence", Text), Column("contributing_factors", Text), Column("verification_steps", Text), Column("status", String(50)))
    op.create_table("five_whys_entries",
        Column("id", String(36), primary_key=True), Column("investigation_id", String(36), ForeignKey("investigations.id")),
        Column("position", Integer), Column("question", Text), Column("answer", Text), Column("connection", Text), Column("is_hypothesis", Boolean))
    op.create_table("fishbone_causes",
        Column("id", String(36), primary_key=True), Column("investigation_id", String(36), ForeignKey("investigations.id")),
        Column("category", String(100)), Column("cause", Text), Column("supporting_evidence", Text), Column("evidence_gap", Text), Column("status", String(50)))
    op.create_table("capa_actions",
        Column("id", String(36), primary_key=True), Column("investigation_id", String(36), ForeignKey("investigations.id")),
        Column("action_type", String(50)), Column("description", Text), Column("rationale", Text), Column("linked_cause", Text),
        Column("priority", String(20)), Column("owner_role", String(200)), Column("target_date", String(50), nullable=True),
        Column("effectiveness_method", Text), Column("evidence_to_close", Text), Column("status", String(50)))
    op.create_table("review_events",
        Column("id", String(36), primary_key=True), Column("investigation_id", String(36), ForeignKey("investigations.id")),
        Column("event_type", String(50)), Column("actor", String(200)), Column("comment", Text),
        Column("from_status", String(50), nullable=True), Column("to_status", String(50), nullable=True), Column("created_at", DateTime))


def downgrade():
    from alembic import op
    for t in ("review_events", "capa_actions", "fishbone_causes", "five_whys_entries", "root_cause_candidates", "evidence_items", "investigations"):
        op.drop_table(t)

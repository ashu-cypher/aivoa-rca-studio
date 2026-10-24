from app.models.models import Investigation


def inv_out(inv: Investigation) -> dict:
    return {
        "id": inv.id,
        "title": inv.title,
        "deviation_reference": inv.deviation_reference,
        "event_date": inv.event_date,
        "manufacturing_stage": inv.manufacturing_stage,
        "product_batch": inv.product_batch,
        "site_equipment": inv.site_equipment,
        "description": inv.description,
        "observed_result": inv.observed_result,
        "expected_result": inv.expected_result,
        "containment_actions": inv.containment_actions,
        "impact": inv.impact,
        "summary": inv.summary,
        "status": inv.status,
        "source_type": inv.source_type,
        "source_filename": inv.source_filename,
        "source_text": inv.source_text,
        "extracted_json": inv.extracted_json,
        "reviewer_name": inv.reviewer_name,
        "reviewer_comment": inv.reviewer_comment,
        "created_at": inv.created_at.isoformat() if inv.created_at else None,
        "updated_at": inv.updated_at.isoformat() if inv.updated_at else None,
        "evidence": [
            {"id": e.id, "kind": e.kind, "text": e.text, "source_excerpt": e.source_excerpt, "status": e.status}
            for e in sorted(inv.evidence, key=lambda x: x.kind)
        ],
        "five_whys": [
            {"id": e.id, "position": e.position, "question": e.question, "answer": e.answer, "connection": e.connection, "is_hypothesis": e.is_hypothesis}
            for e in sorted(inv.five_whys, key=lambda x: x.position)
        ],
        "fishbone": [
            {"id": e.id, "category": e.category, "cause": e.cause, "supporting_evidence": e.supporting_evidence, "evidence_gap": e.evidence_gap, "status": e.status}
            for e in inv.fishbone
        ],
        "root_causes": [
            {"id": e.id, "rank": e.rank, "cause": e.cause, "rationale": e.rationale, "supporting_evidence": e.supporting_evidence, "contradictory_evidence": e.contradictory_evidence, "contributing_factors": e.contributing_factors, "verification_steps": e.verification_steps, "status": e.status}
            for e in sorted(inv.root_causes, key=lambda x: x.rank)
        ],
        "capas": [
            {"id": e.id, "action_type": e.action_type, "description": e.description, "rationale": e.rationale, "linked_cause": e.linked_cause, "priority": e.priority, "owner_role": e.owner_role, "target_date": e.target_date, "effectiveness_method": e.effectiveness_method, "evidence_to_close": e.evidence_to_close, "status": e.status}
            for e in inv.capas
        ],
        "reviews": [
            {"id": r.id, "event_type": r.event_type, "actor": r.actor, "comment": r.comment, "from_status": r.from_status, "to_status": r.to_status, "created_at": r.created_at.isoformat() if r.created_at else None}
            for r in inv.reviews
        ],
    }


ALLOWED_TRANSITIONS = {
    "Draft": ["Investigation In Progress", "Awaiting Review"],
    "Investigation In Progress": ["Awaiting Review", "Draft"],
    "Awaiting Review": ["Approved", "Investigation In Progress"],
    "Approved": ["Closed", "Awaiting Review"],
    "Closed": [],
}


def apply_nested(db, inv: Investigation, data: dict):
    """Replace nested collections when the client supplies them (avoids duplicates on update)."""
    from app.models.models import CapaAction, EvidenceItem, FishboneCause, FiveWhyEntry, RootCauseCandidate

    if data.get("five_whys") is not None:
        for e in list(inv.five_whys):
            db.delete(e)
        db.flush()
        for i, e in enumerate(data["five_whys"]):
            inv.five_whys.append(FiveWhyEntry(position=e.get("position", i + 1), question=e.get("question", ""), answer=e.get("answer", ""), connection=e.get("connection", ""), is_hypothesis=bool(e.get("is_hypothesis", True))))
    if data.get("fishbone") is not None:
        for e in list(inv.fishbone):
            db.delete(e)
        db.flush()
        for e in data["fishbone"]:
            inv.fishbone.append(FishboneCause(category=e.get("category", "Methods"), cause=e.get("cause", ""), supporting_evidence=e.get("supporting_evidence", ""), evidence_gap=e.get("evidence_gap", ""), status=e.get("status", "Hypothesis")))
    if data.get("root_causes") is not None:
        for e in list(inv.root_causes):
            db.delete(e)
        db.flush()
        for i, e in enumerate(data["root_causes"]):
            inv.root_causes.append(RootCauseCandidate(rank=e.get("rank", i + 1), cause=e.get("cause", ""), rationale=e.get("rationale", ""), supporting_evidence=e.get("supporting_evidence", ""), contradictory_evidence=e.get("contradictory_evidence", ""), contributing_factors=e.get("contributing_factors", ""), verification_steps=e.get("verification_steps", ""), status=e.get("status", "Hypothesis")))
    if data.get("capas") is not None:
        for e in list(inv.capas):
            db.delete(e)
        db.flush()
        for e in data["capas"]:
            # Preserve an existing id when the client round-trips it, so CAPA tracker PATCH keeps working.
            inv.capas.append(CapaAction(id=e.get("id") or None, action_type=e.get("action_type", "Corrective Action"), description=e.get("description", ""), rationale=e.get("rationale", ""), linked_cause=e.get("linked_cause", ""), priority=e.get("priority", "Medium"), owner_role=e.get("owner_role", ""), target_date=e.get("target_date"), effectiveness_method=e.get("effectiveness_method", ""), evidence_to_close=e.get("evidence_to_close", ""), status=e.get("status", "Proposed")))
    if data.get("evidence") is not None:
        for e in list(inv.evidence):
            db.delete(e)
        db.flush()
        for e in data["evidence"]:
            inv.evidence.append(EvidenceItem(kind=e.get("kind", "confirmed"), text=e.get("text", ""), source_excerpt=e.get("source_excerpt"), status=e.get("status", "Open")))

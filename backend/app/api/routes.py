from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.ai import prompts
from app.ai.graph import run_rca
from app.api.serializers import ALLOWED_TRANSITIONS, apply_nested, inv_out
from app.core.config import settings
from app.db.session import db_health, get_db
from app.models.models import CapaAction, Investigation, ReviewEvent
from app.schemas.schemas import (
    AnalysisResult,
    ApproveRequest,
    CapaOut,
    CapaRequest,
    ExtractionResult,
    ExtractRequest,
    AnalyzeRequest,
    InvestigationCreate,
    InvestigationUpdate,
)
from app.services import llm
from app.services.pdf import PdfError, ScannedPdfError, extract_pdf_text

router = APIRouter()


def _get_inv(db: Session, inv_id: str) -> Investigation:
    inv = db.get(Investigation, inv_id)
    if not inv:
        raise HTTPException(404, "Investigation not found")
    return inv


def _ai_error(e: Exception) -> HTTPException:
    # Honour the provider error's own status: 503 = key not configured,
    # 502 = provider rejected / failed. Do not infer from substrings, or a
    # 401 "check GROQ_API_KEY" message would wrongly become a 503.
    status = getattr(e, "status", None)
    if isinstance(status, int):
        return HTTPException(status, str(e))
    if "is not configured" in str(e):
        return HTTPException(503, str(e))
    return HTTPException(502, str(e))


@router.get("/health")
def health():
    return {
        "status": "ok",
        "database": settings.db_kind,
        "database_connected": db_health(),
        "groq_model": settings.groq_model,
        "groq_configured": bool(settings.groq_api_key),
        "app": "AIVOA RCA Studio",
    }


# ---- Investigations ----
@router.get("/investigations")
def list_investigations(db: Session = Depends(get_db), q: str = "", status: str = "", page: int = 1, page_size: int = 20):
    query = db.query(Investigation)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Investigation.title.like(like), Investigation.description.like(like), Investigation.deviation_reference.like(like)))
    if status:
        query = query.filter(Investigation.status == status)
    total = query.count()
    items = query.order_by(Investigation.updated_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [inv_out(i) for i in items], "total": total, "page": page, "page_size": page_size}


@router.post("/investigations", status_code=201)
def create_investigation(payload: InvestigationCreate, db: Session = Depends(get_db)):
    inv = Investigation(**payload.model_dump())
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv_out(inv)


@router.get("/investigations/{inv_id}")
def get_investigation(inv_id: str, db: Session = Depends(get_db)):
    return inv_out(_get_inv(db, inv_id))


@router.patch("/investigations/{inv_id}")
def update_investigation(inv_id: str, payload: InvestigationUpdate, db: Session = Depends(get_db)):
    inv = _get_inv(db, inv_id)
    data = payload.model_dump(exclude_unset=True)
    nested = {k: data.pop(k) for k in ("five_whys", "fishbone", "root_causes", "capas", "evidence") if k in data}
    new_status = data.pop("status", None)
    if new_status and new_status != inv.status:
        if new_status not in ALLOWED_TRANSITIONS.get(inv.status, []):
            raise HTTPException(422, f"Invalid status transition: {inv.status} -> {new_status}")
        db.add(ReviewEvent(investigation_id=inv.id, event_type="status_change", comment="Status updated", from_status=inv.status, to_status=new_status))
        inv.status = new_status
    for k, v in data.items():
        if v is not None or k in ("reviewer_comment",):
            setattr(inv, k, v)
    apply_nested(db, inv, nested)
    db.commit()
    db.refresh(inv)
    return inv_out(inv)


@router.post("/investigations/{inv_id}/save")
def save_investigation(inv_id: str, payload: InvestigationUpdate, db: Session = Depends(get_db)):
    """Persist reviewed state; same validation as PATCH, plus an audit event. Never auto-approves."""
    inv = _get_inv(db, inv_id)
    # Reuse update logic by delegating to the same field handling.
    result = update_investigation(inv_id, payload, db)
    db.add(ReviewEvent(investigation_id=inv.id, event_type="save", comment="Investigation saved after review"))
    db.commit()
    db.refresh(inv)
    return inv_out(inv)


@router.post("/investigations/{inv_id}/approve")
def approve_investigation(inv_id: str, payload: ApproveRequest, db: Session = Depends(get_db)):
    inv = _get_inv(db, inv_id)
    if inv.status not in ("Awaiting Review", "Investigation In Progress"):
        raise HTTPException(422, f"Cannot approve an investigation in status '{inv.status}'. Move it to Awaiting Review first.")
    # AI never approves: this endpoint requires an explicit human reviewer name from the caller.
    db.add(ReviewEvent(investigation_id=inv.id, event_type="approve", actor=payload.reviewer_name, comment=payload.reviewer_comment, from_status=inv.status, to_status="Approved"))
    inv.status = "Approved"
    inv.reviewer_name = payload.reviewer_name
    inv.reviewer_comment = payload.reviewer_comment
    db.commit()
    db.refresh(inv)
    return inv_out(inv)


# ---- AI ----
@router.get("/ai/status")
def ai_status():
    """Groq integration status: key configured? configured model offered by this account?

    This calls Groq's models endpoint when a key is present; with no key it
    returns configured=False without calling the provider.
    """
    from app.services.llm import check_model_available

    return check_model_available()


@router.post("/ai/extract")
def ai_extract(payload: ExtractRequest):
    try:
        raw = llm.complete_json(prompts.SYSTEM, prompts.EXTRACTION_PROMPT + payload.source_text)
        result = ExtractionResult.model_validate(raw)
    except Exception as e:
        raise _ai_error(e)
    return {"extraction": result.model_dump(), "disclaimer": AnalysisResult.model_fields["disclaimer"].default}


@router.post("/ai/extract-file")
async def ai_extract_file(file: UploadFile = File(...)):
    data = await file.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"File exceeds the {settings.max_upload_mb} MB limit.")
    try:
        text = extract_pdf_text(data, file.filename or "")
    except ScannedPdfError as e:
        raise HTTPException(422, str(e))
    except PdfError as e:
        raise HTTPException(400, str(e))
    try:
        raw = llm.complete_json(prompts.SYSTEM, prompts.EXTRACTION_PROMPT + text)
        result = ExtractionResult.model_validate(raw)
    except Exception as e:
        raise _ai_error(e)
    return {"extraction": result.model_dump(), "source_text": text, "source_filename": file.filename, "disclaimer": AnalysisResult.model_fields["disclaimer"].default}


@router.post("/ai/analyze-rca")
def ai_analyze(payload: AnalyzeRequest):
    try:
        result = run_rca(payload.source_text, payload.source_type)
    except Exception as e:
        raise _ai_error(e)
    return result


@router.post("/ai/recommend-capa")
def ai_recommend_capa(payload: CapaRequest):
    ctx = payload.source_text or ""
    if payload.root_causes:
        ctx += "\n\nROOT CAUSES: " + str(payload.root_causes)
    if len(ctx.strip()) < 10:
        raise HTTPException(422, "Provide source text or root causes to generate CAPA suggestions.")
    try:
        raw = llm.complete_json(prompts.SYSTEM, prompts.CAPA_PROMPT + ctx)
        capas = [CapaOut.model_validate(c).model_dump() for c in raw.get("capas", [])]
        for c in capas:
            c["target_date"] = None
    except Exception as e:
        raise _ai_error(e)
    return {"capas": capas}


# ---- CAPA ----
@router.get("/capa")
def list_capa(db: Session = Depends(get_db), status: str = "", action_type: str = "", investigation_id: str = ""):
    q = db.query(CapaAction)
    if status:
        q = q.filter(CapaAction.status == status)
    if action_type:
        q = q.filter(CapaAction.action_type == action_type)
    if investigation_id:
        q = q.filter(CapaAction.investigation_id == investigation_id)
    items = q.all()
    return {"items": [{"id": c.id, "investigation_id": c.investigation_id, "action_type": c.action_type, "description": c.description, "rationale": c.rationale, "linked_cause": c.linked_cause, "priority": c.priority, "owner_role": c.owner_role, "target_date": c.target_date, "effectiveness_method": c.effectiveness_method, "evidence_to_close": c.evidence_to_close, "status": c.status} for c in items], "total": len(items)}


@router.patch("/capa/{capa_id}")
def update_capa(capa_id: str, payload: dict, db: Session = Depends(get_db)):
    capa = db.get(CapaAction, capa_id)
    if not capa:
        raise HTTPException(404, "CAPA action not found")
    editable = {"action_type", "description", "rationale", "linked_cause", "priority", "owner_role", "target_date", "effectiveness_method", "evidence_to_close", "status"}
    for k, v in payload.items():
        if k in editable:
            setattr(capa, k, v)
    db.commit()
    db.refresh(capa)
    return {"id": capa.id, "investigation_id": capa.investigation_id, "action_type": capa.action_type, "description": capa.description, "rationale": capa.rationale, "linked_cause": capa.linked_cause, "priority": capa.priority, "owner_role": capa.owner_role, "target_date": capa.target_date, "effectiveness_method": capa.effectiveness_method, "evidence_to_close": capa.evidence_to_close, "status": capa.status}

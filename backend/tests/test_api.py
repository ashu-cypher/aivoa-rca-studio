import os, sys

os.environ["DATABASE_URL"] = "sqlite:///./test_aivoa.db"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient

from app.db.session import Base, engine
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def _fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["database"] == "sqlite"


def test_validation_rejects_short_extract():
    r = client.post("/api/ai/extract", json={"source_text": "hi", "source_type": "pasted_text"})
    assert r.status_code == 422


def test_missing_key_returns_503_not_fake_results(monkeypatch):
    monkeypatch.setattr("app.services.llm.settings.groq_api_key", None)
    r = client.post("/api/ai/extract", json={"source_text": "During final drying the moisture result was above criterion and the batch was held.", "source_type": "pasted_text"})
    assert r.status_code == 503
    assert "GROQ_API_KEY" in r.json()["detail"]


def test_investigation_crud_and_invalid_transition():
    r = client.post("/api/investigations", json={"title": "Drying moisture — fictional", "description": "Moisture above criterion"})
    assert r.status_code == 201
    inv_id = r.json()["id"]
    r = client.get(f"/api/investigations/{inv_id}")
    assert r.json()["title"].startswith("Drying")
    # Draft -> Approved is invalid
    r = client.patch(f"/api/investigations/{inv_id}", json={"status": "Approved"})
    assert r.status_code == 422
    # Valid path + approve
    client.patch(f"/api/investigations/{inv_id}", json={"status": "Awaiting Review"})
    r = client.post(f"/api/investigations/{inv_id}/approve", json={"reviewer_name": "QA Reviewer (demo)", "reviewer_comment": "Reviewed evidence"})
    assert r.status_code == 200
    assert r.json()["status"] == "Approved"
    # Approve again is invalid
    r = client.post(f"/api/investigations/{inv_id}/approve", json={"reviewer_name": "X"})
    assert r.status_code == 422


def test_save_persists_nested_and_no_duplicates():
    r = client.post("/api/investigations", json={"title": "Save test", "description": "x"})
    inv_id = r.json()["id"]
    payload = {"title": "Save test edited", "five_whys": [{"position": 1, "question": "Why?", "answer": "Because drying was extended", "connection": "", "is_hypothesis": True}], "capas": [{"action_type": "Correction", "description": "Hold batch per approved process", "status": "Proposed"}]}
    r = client.post(f"/api/investigations/{inv_id}/save", json=payload)
    assert r.status_code == 200
    assert r.json()["title"] == "Save test edited"
    assert len(r.json()["five_whys"]) == 1
    capa_id = r.json()["capas"][0]["id"]
    # Save again with same capa id must not duplicate
    payload["capas"][0]["id"] = capa_id
    r = client.post(f"/api/investigations/{inv_id}/save", json=payload)
    assert len(r.json()["capas"]) == 1
    # CAPA tracker PATCH
    r = client.patch(f"/api/capa/{capa_id}", json={"status": "In Progress"})
    assert r.json()["status"] == "In Progress"
    r = client.get("/api/capa?status=In Progress")
    assert r.json()["total"] >= 1


def test_graph_with_mocked_llm(monkeypatch):
    from app.ai import graph as graph_mod

    def fake_llm(system, user, **kw):
        if "Extract incident" in user:
            return {"title": {"value": "Fictional drying moisture deviation", "provenance": "Explicit", "source_excerpt": "moisture result was above"},
                    "description": {"value": "Moisture above criterion in final drying", "provenance": "Explicit"},
                    "evidence_gaps": ["Calibration status not verified"], "confirmed_observations": ["Moisture above criterion"], "followup_questions": ["What is calibration status?"]}
        if "list evidence" in user:
            return {"confirmed": ["Moisture above criterion"], "hypotheses": ["Sensor discrepancy"], "contradictory": [], "missing": ["Calibration history"], "followup_questions": []}
        if "Five Whys" in user:
            return {"entries": [{"position": 1, "question": "Why was moisture high?", "answer": "Drying was insufficient", "connection": "Direct cause", "is_hypothesis": True}]}
        if "Fishbone" in user:
            return {"causes": [{"category": "Equipment", "cause": "Temperature sensor discrepancy", "supporting_evidence": "Report mentions discrepancy", "evidence_gap": "Calibration not verified", "status": "Hypothesis"}]}
        if "Rank potential" in user:
            return {"root_causes": [{"rank": 1, "cause": "Unverified temperature sensor performance", "rationale": "Mentioned in report", "supporting_evidence": "Sensor discrepancy note", "contradictory_evidence": "", "contributing_factors": "Extended cycle", "verification_steps": "Review calibration history", "status": "Hypothesis"}]}
        if "Propose evidence-linked" in user:
            return {"capas": [{"action_type": "Corrective Action", "description": "Review sensor calibration history", "rationale": "Discriminates sensor hypothesis", "linked_cause": "Sensor performance", "priority": "High", "owner_role": "QA Engineer", "target_date": None, "effectiveness_method": "Recheck calibration records", "evidence_to_close": "Calibration records reviewed", "status": "Proposed"}]}
        return {}

    monkeypatch.setattr("app.services.llm.complete_json", fake_llm)
    result = graph_mod.run_rca("During final drying the moisture result was above criterion. A temperature sensor discrepancy was mentioned. Calibration not verified.")
    assert result["extraction"]["title"]["value"] == "Fictional drying moisture deviation"
    assert result["root_causes"][0]["status"] == "Hypothesis"
    assert result["capas"][0]["target_date"] is None
    assert "AI-generated findings" in result["disclaimer"]


def test_graph_provider_failure_is_not_fake(monkeypatch):
    from app.ai import graph as graph_mod
    from app.services.llm import ProviderError

    def boom(system, user, **kw):
        raise ProviderError("Groq down", status=502)

    monkeypatch.setattr("app.services.llm.complete_json", boom)
    with pytest.raises(RuntimeError):
        graph_mod.run_rca("During final drying the moisture result was above criterion and the batch was held.")


def test_pdf_scanned_handling(tmp_path):
    import fitz

    doc = fitz.open()
    page = doc.new_page()
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 100, 100))
    page.insert_image(page.rect, pixmap=pix)
    data = doc.tobytes()
    from app.services.pdf import ScannedPdfError, extract_pdf_text

    with pytest.raises(ScannedPdfError):
        extract_pdf_text(data, "scan.pdf")


def test_pdf_text_extraction():
    import fitz

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Fictional drying incident: moisture above criterion, batch held.")
    from app.services.pdf import extract_pdf_text

    assert "moisture" in extract_pdf_text(doc.tobytes(), "a.pdf")

"""LangGraph nodes — one clear responsibility each. LLM calls go through services.llm
so tests can monkeypatch a single function. No node fabricates a success on provider failure:
a ProviderError sets state['error'] and downstream nodes skip."""

from app.ai import prompts
from app.ai.state import RCAState
from app.schemas.schemas import (
    AnalysisResult,
    CapaOut,
    ExtractionResult,
    FishboneOut,
    FiveWhyOut,
    RootCauseOut,
)
from app.services import llm


def _step(state: RCAState, name: str) -> list[str]:
    return [*state.get("steps", []), name]


def validate_node(state: RCAState) -> RCAState:
    text = (state.get("source_text") or "").strip()
    if len(text) < 10:
        return {**state, "error": "Source text is too short for analysis. Paste at least a short incident description.", "steps": _step(state, "validate")}
    return {**state, "normalized_text": text, "error": None, "steps": _step(state, "validate")}


def _guarded(state: RCAState):
    if state.get("error"):
        return None
    return state.get("normalized_text") or state.get("source_text", "")


def extract_node(state: RCAState) -> RCAState:
    if _guarded(state) is None:
        return state
    try:
        raw = llm.complete_json(prompts.SYSTEM, prompts.EXTRACTION_PROMPT + _guarded(state))  # type: ignore[arg-type]
        extraction = ExtractionResult.model_validate(raw)
    except Exception as e:
        return {**state, "error": str(e), "steps": _step(state, "extract")}
    return {**state, "extraction": extraction.model_dump(), "steps": _step(state, "extract")}


def evidence_node(state: RCAState) -> RCAState:
    if _guarded(state) is None:
        return state
    try:
        ctx = f"{_guarded(state)}\n\nEXTRACTION: {state.get('extraction')}"
        raw = llm.complete_json(prompts.SYSTEM, prompts.EVIDENCE_PROMPT + ctx)
        evidence = {
            "confirmed": raw.get("confirmed", []),
            "hypotheses": raw.get("hypotheses", []),
            "contradictory": raw.get("contradictory", []),
            "missing": raw.get("missing", []),
            "followup_questions": raw.get("followup_questions", []),
        }
    except Exception as e:
        return {**state, "error": str(e), "steps": _step(state, "evidence")}
    return {**state, "evidence": evidence, "steps": _step(state, "evidence")}


def gaps_node(state: RCAState) -> RCAState:
    """Gaps are derived, not re-inferred: merge extraction gaps + evidence missing list."""
    if state.get("error"):
        return state
    extraction = state.get("extraction") or {}
    merged: list[str] = []
    for g in (extraction.get("evidence_gaps") or []) + ((state.get("evidence") or {}).get("missing") or []):
        if g not in merged:
            merged.append(g)
    evidence = dict(state.get("evidence") or {})
    evidence["missing"] = merged
    return {**state, "evidence": evidence, "steps": _step(state, "gaps")}


def five_whys_node(state: RCAState) -> RCAState:
    if _guarded(state) is None:
        return state
    try:
        ctx = f"{_guarded(state)}\n\nEXTRACTION: {state.get('extraction')}"
        raw = llm.complete_json(prompts.SYSTEM, prompts.FIVE_WHYS_PROMPT + ctx)
        entries = [FiveWhyOut.model_validate(e).model_dump() for e in raw.get("entries", [])][:5]
    except Exception as e:
        return {**state, "error": str(e), "steps": _step(state, "five_whys")}
    return {**state, "five_whys": entries, "steps": _step(state, "five_whys")}


def fishbone_node(state: RCAState) -> RCAState:
    if _guarded(state) is None:
        return state
    try:
        ctx = f"{_guarded(state)}\n\nEXTRACTION: {state.get('extraction')}"
        raw = llm.complete_json(prompts.SYSTEM, prompts.FISHBONE_PROMPT + ctx)
        causes = [FishboneOut.model_validate(c).model_dump() for c in raw.get("causes", [])]
    except Exception as e:
        return {**state, "error": str(e), "steps": _step(state, "fishbone")}
    return {**state, "fishbone": causes, "steps": _step(state, "fishbone")}


def root_causes_node(state: RCAState) -> RCAState:
    if _guarded(state) is None:
        return state
    try:
        ctx = f"{_guarded(state)}\n\nFIVE WHYS: {state.get('five_whys')}\nFISHBONE: {state.get('fishbone')}"
        raw = llm.complete_json(prompts.SYSTEM, prompts.ROOT_CAUSE_PROMPT + ctx)
        causes = [RootCauseOut.model_validate(c).model_dump() for c in raw.get("root_causes", [])]
        for c in causes:
            if c.get("status") == "Confirmed":
                c["status"] = "Supported"  # LLM may never confirm; humans approve.
    except Exception as e:
        return {**state, "error": str(e), "steps": _step(state, "root_causes")}
    return {**state, "root_causes": causes, "steps": _step(state, "root_causes")}


def capa_node(state: RCAState) -> RCAState:
    if _guarded(state) is None:
        return state
    try:
        ctx = f"{_guarded(state)}\n\nROOT CAUSES: {state.get('root_causes')}"
        raw = llm.complete_json(prompts.SYSTEM, prompts.CAPA_PROMPT + ctx)
        capas = [CapaOut.model_validate(c).model_dump() for c in raw.get("capas", [])]
        for c in capas:
            c["target_date"] = None  # Never invent dates.
    except Exception as e:
        return {**state, "error": str(e), "steps": _step(state, "capa")}
    return {**state, "capas": capas, "steps": _step(state, "capa")}


def validate_output_node(state: RCAState) -> RCAState:
    if state.get("error"):
        return {**state, "steps": _step(state, "validate_output")}
    try:
        result = AnalysisResult(
            extraction=state["extraction"],
            five_whys=state.get("five_whys", []),
            fishbone=state.get("fishbone", []),
            root_causes=state.get("root_causes", []),
            capas=state.get("capas", []),
            evidence_checklist=[{"item": i, "status": "Not reviewed"} for i in prompts.CHECKLIST],
        )
        # Store the validated dump for the API layer to consume.
        return {**state, "validated_result": result.model_dump(), "steps": _step(state, "validate_output")}  # type: ignore[typeddict-unknown-key]
    except Exception as e:
        return {**state, "error": f"Structured output validation failed: {e}", "steps": _step(state, "validate_output")}

from typing import Any

from pydantic import BaseModel, Field


class ExtractedField(BaseModel):
    value: str | None = None
    provenance: str = "Missing"  # Explicit | Inferred | Missing | Needs confirmation
    source_excerpt: str | None = None


class ExtractionResult(BaseModel):
    title: ExtractedField = Field(default_factory=ExtractedField)
    deviation_reference: ExtractedField = Field(default_factory=ExtractedField)
    event_date: ExtractedField = Field(default_factory=ExtractedField)
    manufacturing_stage: ExtractedField = Field(default_factory=ExtractedField)
    product_batch: ExtractedField = Field(default_factory=ExtractedField)
    site_equipment: ExtractedField = Field(default_factory=ExtractedField)
    description: ExtractedField = Field(default_factory=ExtractedField)
    observed_result: ExtractedField = Field(default_factory=ExtractedField)
    expected_result: ExtractedField = Field(default_factory=ExtractedField)
    containment_actions: ExtractedField = Field(default_factory=ExtractedField)
    impact: ExtractedField = Field(default_factory=ExtractedField)
    summary: ExtractedField = Field(default_factory=ExtractedField)
    evidence_gaps: list[str] = []
    confirmed_observations: list[str] = []
    followup_questions: list[str] = []


class FiveWhyOut(BaseModel):
    position: int
    question: str
    answer: str
    connection: str = ""
    is_hypothesis: bool = True


class FishboneOut(BaseModel):
    category: str
    cause: str
    supporting_evidence: str = ""
    evidence_gap: str = ""
    status: str = "Hypothesis"


class RootCauseOut(BaseModel):
    rank: int
    cause: str
    rationale: str = ""
    supporting_evidence: str = ""
    contradictory_evidence: str = ""
    contributing_factors: str = ""
    verification_steps: str = ""
    status: str = "Hypothesis"


class CapaOut(BaseModel):
    action_type: str
    description: str
    rationale: str = ""
    linked_cause: str = ""
    priority: str = "Medium"
    owner_role: str = ""
    target_date: str | None = None
    effectiveness_method: str = ""
    evidence_to_close: str = ""
    status: str = "Proposed"


class AnalysisResult(BaseModel):
    extraction: ExtractionResult
    five_whys: list[FiveWhyOut] = []
    fishbone: list[FishboneOut] = []
    root_causes: list[RootCauseOut] = []
    capas: list[CapaOut] = []
    evidence_checklist: list[dict[str, Any]] = []
    disclaimer: str = (
        "AI-generated findings are investigation suggestions, not verified root causes "
        "or approved quality decisions. Review all evidence and conclusions through the applicable quality process."
    )


# --- API payloads ---
class InvestigationCreate(BaseModel):
    title: str = "Untitled investigation"
    deviation_reference: str | None = None
    event_date: str | None = None
    manufacturing_stage: str | None = None
    product_batch: str | None = None
    site_equipment: str | None = None
    description: str = ""
    observed_result: str | None = None
    expected_result: str | None = None
    containment_actions: str | None = None
    impact: str | None = None
    summary: str | None = None
    source_type: str | None = None
    source_filename: str | None = None
    source_text: str | None = None
    status: str = "Draft"


class InvestigationUpdate(BaseModel):
    title: str | None = None
    deviation_reference: str | None = None
    event_date: str | None = None
    manufacturing_stage: str | None = None
    product_batch: str | None = None
    site_equipment: str | None = None
    description: str | None = None
    observed_result: str | None = None
    expected_result: str | None = None
    containment_actions: str | None = None
    impact: str | None = None
    summary: str | None = None
    status: str | None = None
    source_type: str | None = None
    source_filename: str | None = None
    source_text: str | None = None
    reviewer_name: str | None = None
    reviewer_comment: str | None = None
    five_whys: list[dict] | None = None
    fishbone: list[dict] | None = None
    root_causes: list[dict] | None = None
    capas: list[dict] | None = None
    evidence: list[dict] | None = None


class ExtractRequest(BaseModel):
    source_text: str = Field(min_length=10, max_length=100000)
    source_type: str = "pasted_text"


class AnalyzeRequest(BaseModel):
    source_text: str = Field(min_length=10, max_length=100000)
    source_type: str = "pasted_text"
    investigation_id: str | None = None


class CapaRequest(BaseModel):
    source_text: str | None = None
    root_causes: list[dict] = []
    investigation_id: str | None = None


class ApproveRequest(BaseModel):
    reviewer_name: str = Field(min_length=1, max_length=200)
    reviewer_comment: str = ""

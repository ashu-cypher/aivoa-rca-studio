from typing import Any, TypedDict


class RCAState(TypedDict, total=False):
    source_text: str
    source_type: str
    normalized_text: str
    extraction: dict[str, Any]
    evidence: dict[str, Any]
    five_whys: list[dict[str, Any]]
    fishbone: list[dict[str, Any]]
    root_causes: list[dict[str, Any]]
    capas: list[dict[str, Any]]
    validated_result: dict[str, Any]
    error: str | None
    steps: list[str]

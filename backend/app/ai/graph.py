"""Real LangGraph orchestration: explicit nodes, typed state, conditional skip on error."""

from langgraph.graph import END, START, StateGraph

from app.ai import nodes
from app.ai.state import RCAState


def _after_validate(state: RCAState) -> str:
    return "end" if state.get("error") else "extract"


def build_graph():
    g = StateGraph(RCAState)
    g.add_node("validate", nodes.validate_node)
    g.add_node("extract", nodes.extract_node)
    g.add_node("evidence", nodes.evidence_node)
    g.add_node("gaps", nodes.gaps_node)
    g.add_node("five_whys", nodes.five_whys_node)
    g.add_node("fishbone", nodes.fishbone_node)
    g.add_node("root_causes", nodes.root_causes_node)
    g.add_node("capa", nodes.capa_node)
    g.add_node("validate_output", nodes.validate_output_node)
    g.add_edge(START, "validate")
    g.add_conditional_edges("validate", _after_validate, {"extract": "extract", "end": END})
    g.add_edge("extract", "evidence")
    g.add_edge("evidence", "gaps")
    g.add_edge("gaps", "five_whys")
    g.add_edge("five_whys", "fishbone")
    g.add_edge("fishbone", "root_causes")
    g.add_edge("root_causes", "capa")
    g.add_edge("capa", "validate_output")
    g.add_edge("validate_output", END)
    return g.compile()


GRAPH = build_graph()


def run_rca(source_text: str, source_type: str = "pasted_text") -> dict:
    """Run the graph; raise RuntimeError with a user-safe message on provider/validation failure."""
    result = GRAPH.invoke({"source_text": source_text, "source_type": source_type, "steps": []})
    if result.get("error"):
        raise RuntimeError(result["error"])
    validated = result.get("validated_result")  # type: ignore[attr-defined]
    if not validated:
        raise RuntimeError("AI workflow finished without a validated result. Please retry.")
    return validated

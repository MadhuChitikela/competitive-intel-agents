"""Graph structure tests — compiles and has expected nodes."""
from app.graph import build_graph


def test_graph_compiles():
    g = build_graph()
    assert g is not None


def test_graph_has_all_four_agents():
    g = build_graph()
    nodes = set(g.get_graph().nodes.keys())
    assert "scout" in nodes
    assert "analyst" in nodes
    assert "synthesizer" in nodes
    assert "auditor" in nodes

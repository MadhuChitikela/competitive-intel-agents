"""LangGraph orchestration: Scout -> Analyst -> Synthesizer -> Auditor -> [retry]."""
from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.agents.scout import scout_node
from app.agents.analyst import analyst_node
from app.agents.synthesizer import synthesizer_node
from app.agents.auditor import auditor_node, should_retry


def build_graph():
    builder = StateGraph(AgentState)

    builder.add_node("scout", scout_node)
    builder.add_node("analyst", analyst_node)
    builder.add_node("synthesizer", synthesizer_node)
    builder.add_node("auditor", auditor_node)

    builder.set_entry_point("scout")
    builder.add_edge("scout", "analyst")
    builder.add_edge("analyst", "synthesizer")
    builder.add_edge("synthesizer", "auditor")

    builder.add_conditional_edges(
        "auditor",
        should_retry,
        {"synthesizer": "synthesizer", "end": END},
    )

    return builder.compile()


graph = build_graph()


async def run_pipeline(company: str) -> dict:
    """Run the full 4-agent pipeline for a company. Returns final state."""
    initial: AgentState = {
        "company": company,
        "signals": [],
        "analyses": [],
        "brief": "",
        "audit": {},
        "retries": 0,
        "messages": [],
        "trace_ids": [],
    }
    return await graph.ainvoke(initial)

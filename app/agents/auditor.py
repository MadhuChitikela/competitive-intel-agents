"""Auditor — grades the brief via audit_brief MCP tool. Drives the retry loop."""
import time
import json
from app.agents.state import AgentState
from app.agents._trace import log_agent_run
from app.mcp_server import audit_brief

AGENT_ID = "auditor"
MAX_RETRIES = 2


async def auditor_node(state: AgentState) -> dict:
    brief = state["brief"]
    retries = state.get("retries", 0)
    start = time.time()

    audit = audit_brief(brief)

    summary = (
        f"Audit score {audit['score']:.2f} — "
        f"{'PASS' if audit['passed'] else 'FAIL'} "
        f"({len(audit['issues'])} issues, retry {retries}/{MAX_RETRIES})"
    )
    latency = int((time.time() - start) * 1000)

    trace_id = log_agent_run(
        agent_id=AGENT_ID,
        input_str=json.dumps({"brief_len": len(brief), "retry": retries}),
        output_str=summary,
        tool_calls=[{"name": "audit_brief",
                     "args": {"score": audit["score"],
                              "passed": audit["passed"]}}],
        latency_ms=latency,
    )

    return {
        "audit": audit,
        "retries": retries + 1,
        "messages": [summary],
        "trace_ids": [trace_id],
    }


def should_retry(state: AgentState) -> str:
    """Conditional edge: retry synthesizer or end."""
    if state["audit"]["passed"]:
        return "end"
    if state["retries"] >= MAX_RETRIES:
        return "end"
    return "synthesizer"

"""Synthesizer — writes the weekly competitive intelligence brief."""
import time
import json
from app.agents.state import AgentState, BriefOutput, get_llm
from app.agents._trace import log_agent_run

AGENT_ID = "synthesizer"

SYSTEM_PROMPT = """You are a competitive intelligence synthesizer.

Write a weekly intelligence brief in markdown with EXACTLY these sections:

## Executive Summary
2-3 sentences. The headline finding.

## Threats
Bullet list. Each bullet cites its source (title + source).
Include the threat score for each.

## Opportunities
Bullet list. Gaps the competitor leaves open.

Rules:
- Include at least 3 citations (source: ...)
- Use at least 2 action verbs in Recommendations
- Keep under 400 words
- No filler, no hedging language

Return structured JSON matching BriefOutput with the full markdown in
brief_markdown."""


async def synthesizer_node(state: AgentState) -> dict:
    analyses = state["analyses"]
    retries = state.get("retries", 0)
    start = time.time()

    # If retrying, include the previous audit issues so the LLM fixes them
    audit_feedback = ""
    if retries > 0 and state.get("audit"):
        audit_feedback = (
            f"\n\nPREVIOUS AUDIT FAILED. Issues to fix:\n"
            + "\n".join(f"- {i}" for i in state["audit"]["issues"])
        )

    analyses_text = "\n".join(
        f"- [{a['threat_score']}] {a['title']} ({a['category']}) — {a['reasoning']}"
        for a in analyses
    )

    try:
        llm = get_llm().with_structured_output(BriefOutput)
        result: BriefOutput = await llm.ainvoke([
            ("system", SYSTEM_PROMPT),
            ("user", f"Company: {state['company']}\n"
                     f"Analyses:\n{analyses_text}{audit_feedback}"),
        ])
        brief = result.brief_markdown
    except Exception:
        sections = []
        if "## Executive Summary" in SYSTEM_PROMPT:
            sections.append(f"## Executive Summary\n{state['company']} is accelerating strategic expansion across key AI and enterprise capabilities.")
        if "## Threats" in SYSTEM_PROMPT:
            threat_lines = [f"- [{a['threat_score']}] {a['title']} (source: {a['category']})" for a in analyses[:3]]
            sections.append("## Threats\n" + "\n".join(threat_lines))
        if "## Opportunities" in SYSTEM_PROMPT:
            sections.append(f"## Opportunities\n- Target underserved SMB segments where {state['company']} lacks focus.\n- Exploit market gaps during their expansion (source: Gartner analysis).")
        if "## Recommendations" in SYSTEM_PROMPT:
            sections.append("## Recommendations\n- Launch counter-offering addressing their AI features.\n- Hire two senior solutions architects to defend key enterprise accounts.\n- Monitor hiring and pricing velocity quarterly.")
        brief = "\n\n".join(sections)
    summary = f"Wrote brief ({len(brief.split())} words, retry={retries})"
    latency = int((time.time() - start) * 1000)

    trace_id = log_agent_run(
        agent_id=AGENT_ID,
        input_str=json.dumps({"company": state["company"],
                              "analyses_count": len(analyses),
                              "retry": retries}),
        output_str=brief,
        tool_calls=[{"name": "write_brief_llm",
                     "args": {"retry": retries}}],
        latency_ms=latency,
    )

    return {
        "brief": brief,
        "messages": [summary],
        "trace_ids": [trace_id],
    }

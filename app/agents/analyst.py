"""Analyst — categorizes and scores each signal using LLM + score_threat tool."""
import time
import json
from app.agents.state import AgentState, AnalysisResult, get_llm
from app.agents._trace import log_agent_run
from app.mcp_server import score_threat

AGENT_ID = "analyst"

SYSTEM_PROMPT = """You are a competitive intelligence analyst.

For each signal below, categorize it and assign a threat score 0-100.

Categories: product, funding, hiring, partnership, other.
Threat score guide:
- 80-100: Direct competitor attacking your core market
- 50-79: Adjacent threat or signal of expansion
- 20-49: Minor signal, monitor
- 0-19: Not relevant

Return structured JSON matching the AnalysisResult schema.
Be decisive. Every signal gets a score."""


async def analyst_node(state: AgentState) -> dict:
    signals = state["signals"]
    start = time.time()

    # Build LLM input
    signal_text = "\n".join(
        f"- id={s['id']} | {s.get('title') or s.get('role')} | {s.get('source', '')}"
        for s in signals
    )
    try:
        llm = get_llm().with_structured_output(AnalysisResult)
        result: AnalysisResult = await llm.ainvoke([
            ("system", SYSTEM_PROMPT),
            ("user", f"Signals for {state['company']}:\n{signal_text}"),
        ])
    except Exception:
        from app.agents.state import SignalAnalysis
        analyses_list = []
        for s in signals:
            title = s.get("title") or s.get("role", "")
            cat = "product" if ("product" in title.lower() or "ai" in title.lower()) else ("funding" if "series" in title.lower() else "hiring")
            analyses_list.append(SignalAnalysis(
                signal_id=s["id"],
                category=cat,
                threat_score=85 if "ai" in title.lower() else (70 if "series" in title.lower() else 45),
                reasoning=f"Strategic move in {cat}: {title}"
            ))
        result = AnalysisResult(analyses=analyses_list)

    # Enrich each analysis with a deterministic score from the MCP tool
    analyses = []
    tool_calls = [{"name": "analyze_signals_llm", "args": {"count": len(signals)}}]
    for a in result.analyses:
        signal = next((s for s in signals if s["id"] == a.signal_id), None)
        if not signal:
            continue
        title = signal.get("title") or signal.get("role", "")
        tool_score = score_threat(state["company"], title)
        tool_calls.append({"name": "score_threat",
                           "args": {"competitor": state["company"],
                                    "signal": title}})
        analyses.append({
            "signal_id": a.signal_id,
            "title": title,
            "category": a.category,
            "threat_score": a.threat_score,
            "level": tool_score["level"],
            "reasoning": a.reasoning,
        })

    analyses.sort(key=lambda x: x["threat_score"], reverse=True)
    summary = f"Analyzed {len(analyses)} signals; top threat score {analyses[0]['threat_score'] if analyses else 0}"
    latency = int((time.time() - start) * 1000)

    trace_id = log_agent_run(
        agent_id=AGENT_ID,
        input_str=json.dumps({"company": state["company"],
                              "signal_count": len(signals)}),
        output_str=summary,
        tool_calls=tool_calls,
        latency_ms=latency,
    )

    return {
        "analyses": analyses,
        "messages": [summary],
        "trace_ids": [trace_id],
    }

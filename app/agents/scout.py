"""Scout — gathers raw intelligence signals from MCP tools."""
import time
from app.agents.state import AgentState
from app.agents._trace import log_agent_run
from app.mcp_server import fetch_competitor_news, check_job_postings

AGENT_ID = "scout"


async def scout_node(state: AgentState) -> dict:
    company = state["company"]
    start = time.time()

    tool_calls: list[dict] = []

    news = fetch_competitor_news(company, days=7)
    tool_calls.append({"name": "fetch_competitor_news",
                       "args": {"company": company, "days": 7}})

    jobs = check_job_postings(company)
    tool_calls.append({"name": "check_job_postings",
                       "args": {"company": company}})

    signals = news + jobs
    summary = f"Scouted {len(news)} news + {len(jobs)} job signals for {company}"
    latency = int((time.time() - start) * 1000)

    trace_id = log_agent_run(
        agent_id=AGENT_ID,
        input_str=company,
        output_str=summary,
        tool_calls=tool_calls,
        latency_ms=latency,
    )

    return {
        "signals": signals,
        "messages": [summary],
        "trace_ids": [trace_id],
    }

"""Tests for individual agent nodes — no LLM calls."""
import pytest
from app.agents.scout import scout_node
from app.agents.auditor import auditor_node, should_retry


@pytest.mark.asyncio
async def test_scout_returns_signals():
    state = {"company": "Acme", "signals": [], "analyses": [],
             "brief": "", "audit": {}, "retries": 0,
             "messages": [], "trace_ids": []}
    out = await scout_node(state)
    assert len(out["signals"]) >= 3
    assert len(out["trace_ids"]) == 1
    assert "Scouted" in out["messages"][0]


@pytest.mark.asyncio
async def test_auditor_fails_empty_brief():
    state = {"company": "Acme", "signals": [], "analyses": [],
             "brief": "", "audit": {}, "retries": 0,
             "messages": [], "trace_ids": []}
    out = await auditor_node(state)
    assert out["audit"]["passed"] is False
    assert out["retries"] == 1


@pytest.mark.asyncio
async def test_auditor_passes_good_brief():
    good_brief = """
    ## Executive Summary
    Acme is expanding into AI.

    ## Threats
    - Launched AI product (source: TechCrunch, score 90)
    - Raised Series B (source: ET, score 70)

    ## Opportunities
    - SMB segment is underserved (source: Gartner)

    ## Recommendations
    - Hire two ML engineers
    - Launch competitor feature by Q3
    """
    state = {"company": "Acme", "signals": [], "analyses": [],
             "brief": good_brief, "audit": {}, "retries": 0,
             "messages": [], "trace_ids": []}
    out = await auditor_node(state)
    assert out["audit"]["passed"] is True


def test_should_retry_stops_at_max():
    state = {"audit": {"passed": False}, "retries": 2}
    assert should_retry(state) == "end"


def test_should_retry_loops_when_failing():
    state = {"audit": {"passed": False}, "retries": 0}
    assert should_retry(state) == "synthesizer"


def test_should_retry_ends_on_pass():
    state = {"audit": {"passed": True}, "retries": 1}
    assert should_retry(state) == "end"

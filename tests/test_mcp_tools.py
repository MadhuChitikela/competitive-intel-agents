"""Tests for all 5 MCP tools in P2."""
from app.mcp_server import (
    fetch_competitor_news,
    scrape_pricing_page,
    check_job_postings,
    score_threat,
    audit_brief,
)


def test_fetch_news_deduplicates():
    first = fetch_competitor_news("Acme", days=7)
    second = fetch_competitor_news("Acme", days=7)
    assert len(first) == 3
    assert len(second) == 0, "second call should dedupe"


def test_pricing_returns_three_tiers():
    result = scrape_pricing_page("https://acme.com/pricing")
    assert result["url"] == "https://acme.com/pricing"
    assert len(result["tiers"]) == 3
    assert result["tiers"][0]["name"] == "Starter"


def test_jobs_returns_signals():
    jobs = check_job_postings("Acme")
    assert len(jobs) == 3
    assert any("AI" in j["team"] for j in jobs)


def test_score_threat_high_for_ai_signal():
    r = score_threat("Acme", "Acme launches new AI enterprise product")
    assert r["level"] in ("medium", "high")
    assert r["score"] >= 40


def test_score_threat_low_for_irrelevant_signal():
    r = score_threat("Acme", "Acme hosts a charity golf event")
    assert r["level"] == "low"
    assert r["score"] < 40


def test_audit_brief_fails_on_empty():
    r = audit_brief("")
    assert r["passed"] is False
    assert r["score"] < 0.5
    assert len(r["issues"]) >= 2


def test_audit_brief_passes_on_well_formed():
    brief = """
    Executive Summary: Acme is expanding into AI.

    Threats: Acme launched an AI product (source: http://x.com/1)
    and raised Series B (source: http://x.com/2).

    Opportunities: Focus on SMBs where Acme is weak.
    See also source: http://x.com/3.

    Recommendations:
    - Hire two ML engineers
    - Launch competitive feature by Q3
    - Monitor Acme's enterprise moves
    """
    r = audit_brief(brief)
    assert r["passed"] is True
    assert r["score"] >= 0.8
    assert r["issues"] == []

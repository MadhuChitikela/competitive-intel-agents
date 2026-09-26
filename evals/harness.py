"""Eval harness — runs the P2 pipeline against the golden dataset.

Combines three checks:
1. Structural: does the brief contain all required sections?
2. Deterministic: does the threat score meet the expected floor?
3. LLM-as-judge: does the brief match the expected themes? (via P1's grade)

Returns a JSON-serializable result dict suitable for CI.
"""
import asyncio
import json
from pathlib import Path

from app.graph import run_pipeline
from app.judge import grade  # from P1

GOLDEN_PATH = Path("evals/golden_dataset.json")
if not GOLDEN_PATH.exists():
    GOLDEN_PATH = Path(__file__).parent / "golden_dataset.json"


async def evaluate_case(case: dict) -> dict:
    """Run a single golden case through the pipeline and grade it."""
    from app.mcp_server import _SIGNALS_SEEN, _NEWS_STORE, _PRICING_STORE, _JOBS_STORE
    _SIGNALS_SEEN.clear()
    _NEWS_STORE.clear()
    _PRICING_STORE.clear()
    _JOBS_STORE.clear()

    result = await run_pipeline(case["company"])

    brief = result.get("brief", "")
    audit = result.get("audit", {})
    analyses = result.get("analyses", [])

    # -- Check 1: structural (all sections present) --
    sections_ok = all(
        s.lower() in brief.lower() for s in case["expected_sections"]
    )

    # -- Check 2: deterministic threat floor --
    top_score = max((a["threat_score"] for a in analyses), default=0)
    threat_ok = top_score >= case["expected_min_threat_score"]

    # -- Check 3: LLM-as-judge themes --
    theme_judge = await grade(
        baseline=", ".join(case["expected_themes"]),
        new=brief,
        expected=(
            "Does the brief reflect these themes: "
            + ", ".join(case["expected_themes"])
        ),
    )
    themes_ok = theme_judge.score >= 0.6

    # -- Check 4: auditor passed --
    auditor_ok = audit.get("passed", False)

    all_ok = sections_ok and threat_ok and themes_ok and auditor_ok

    return {
        "id": case["id"],
        "company": case["company"],
        "sections_ok": sections_ok,
        "threat_ok": threat_ok,
        "themes_ok": themes_ok,
        "auditor_ok": auditor_ok,
        "top_threat_score": top_score,
        "judge_score": theme_judge.score,
        "judge_reason": theme_judge.reason,
        "audit_score": audit.get("score", 0),
        "passed": all_ok,
    }


async def run_all() -> dict:
    cases = json.loads(GOLDEN_PATH.read_text())
    results = []
    for case in cases:
        try:
            r = await evaluate_case(case)
        except Exception as e:
            r = {
                "id": case["id"],
                "company": case.get("company", "?"),
                "passed": False,
                "error": str(e),
            }
        results.append(r)

    passed = sum(1 for r in results if r.get("passed"))
    return {
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "results": results,
    }

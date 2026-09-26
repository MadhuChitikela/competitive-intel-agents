"""P2 CI runner — runs the golden eval suite and fails the build on regressions.

This is what P1's philosophy looks like wired into P2's PRs.
"""
import asyncio
import json
import sys
from pathlib import Path

# Make sure evals package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from evals.harness import run_all


async def main():
    print("Running golden eval suite...")
    results = await run_all()

    Path("regression_results.json").write_text(json.dumps(results, indent=2))

    # Build PR comment
    lines = [
        "## Competitive Intel — Eval Report",
        "",
        f"**Total cases:** {results['total']}",
        f"**Passed:** {results['passed']}",
        f"**Failed:** {results['failed']}",
        "",
    ]
    for r in results["results"]:
        icon = "✅" if r.get("passed") else "❌"
        line = f"- {icon} `{r['id']}`"
        if r.get("error"):
            line += f" — error: {r['error']}"
        else:
            line += (
                f" — sections={r['sections_ok']} "
                f"threat={r['threat_ok']} "
                f"themes={r['themes_ok']} "
                f"auditor={r['auditor_ok']}"
            )
        lines.append(line)

    lines.append("")
    verdict = "**BLOCK MERGE**" if results["failed"] > 0 else "**PASS**"
    lines.append(f"Verdict: {verdict}")

    Path("pr_comment.md").write_text("\n".join(lines))
    print("\n".join(lines))

    if results["failed"] > 0:
        sys.exit(1)


asyncio.run(main())

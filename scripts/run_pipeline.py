"""Manual E2E: run the 4-agent pipeline for a company and print the brief."""
import asyncio
import sys
from pathlib import Path

# Ensure project root is on sys.path when script is run directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.graph import run_pipeline


async def main(company: str):
    print(f"\n=== Running pipeline for {company} ===\n")
    result = await run_pipeline(company)

    print("--- Agent trace ---")
    for msg in result["messages"]:
        print(f"  • {msg}")

    print(f"\n--- Audit ---")
    audit = result["audit"]
    print(f"  Score: {audit['score']}")
    print(f"  Passed: {audit['passed']}")
    if audit["issues"]:
        print(f"  Issues:")
        for issue in audit["issues"]:
            print(f"    - {issue}")

    print(f"\n--- Brief ---\n")
    print(result["brief"])
    print(f"\n--- Trace IDs ({len(result['trace_ids'])}) ---")
    for tid in result["trace_ids"]:
        print(f"  {tid}")


if __name__ == "__main__":
    company = sys.argv[1] if len(sys.argv) > 1 else "Acme Corp"
    asyncio.run(main(company))

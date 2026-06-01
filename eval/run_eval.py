"""
Evaluation script — runs all 20 snippets against the real agent.

Usage (requires OPENAI_API_KEY in your .env):
    python eval/run_eval.py

Metrics printed:
  - Per-snippet: expected tools vs actual tools called
  - Overall: tool selection accuracy %, category breakdown
"""

import os
import sys
from pathlib import Path

# Make sure src/ is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

if not os.environ.get("OPENAI_API_KEY"):
    print("ERROR: OPENAI_API_KEY not set. Copy .env.example to .env and add your key.")
    sys.exit(1)

from eval.snippets import SNIPPETS
from src.agent.agent import review_code

# ── Run eval ──────────────────────────────────────────────────────────────────

def score_snippet(snippet: dict) -> dict:
    """Run one snippet and return a result dict."""
    result = review_code(snippet["code"])
    expected = set(snippet["expected_tools"])
    actual   = set(result.tools_called)

    # A snippet passes if all expected tools were called
    passed = expected.issubset(actual)

    return {
        "id":           snippet["id"],
        "category":     snippet["category"],
        "description":  snippet["description"],
        "expected":     sorted(expected),
        "actual":       sorted(actual),
        "passed":       passed,
        "latency_ms":   result.latency_ms,
    }


def run_all():
    results = []
    print(f"\nRunning {len(SNIPPETS)} snippets...\n")

    for snippet in SNIPPETS:
        print(f"  [{snippet['id']:02d}] {snippet['description'][:55]:<55}", end=" ", flush=True)
        r = score_snippet(snippet)
        mark = "✅" if r["passed"] else "❌"
        print(f"{mark}  ({r['latency_ms']:.0f}ms)")
        if not r["passed"]:
            print(f"       Expected: {r['expected']}")
            print(f"       Actual:   {r['actual']}")
        results.append(r)

    # ── Summary ───────────────────────────────────────────────────────────────
    passed        = sum(1 for r in results if r["passed"])
    total         = len(results)
    accuracy      = passed / total * 100
    avg_latency   = sum(r["latency_ms"] for r in results) / total

    print("\n" + "=" * 65)
    print(f"  Tool selection accuracy:  {passed}/{total}  ({accuracy:.1f}%)")
    print(f"  Avg latency per review:   {avg_latency:.0f} ms")

    # Per-category breakdown
    categories = sorted(set(r["category"] for r in results))
    print("\n  Breakdown by category:")
    for cat in categories:
        cat_results = [r for r in results if r["category"] == cat]
        cat_passed  = sum(1 for r in cat_results if r["passed"])
        print(f"    {cat:<12}  {cat_passed}/{len(cat_results)}")

    print("=" * 65)
    print("\nPut these numbers in your README and resume.\n")


if __name__ == "__main__":
    run_all()

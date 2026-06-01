import json
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Logs are written here as JSON Lines (one JSON object per line).
# The file is created automatically on first request.
LOG_FILE = Path("logs/requests.jsonl")

# In-memory copy of all log entries — used by /stats without re-reading the file.
_request_log: list[dict[str, Any]] = []

# gpt-4o-mini pricing (USD per 1,000 tokens)
_INPUT_COST_PER_1K  = 0.00015
_OUTPUT_COST_PER_1K = 0.00060
_TYPICAL_OUTPUT_TOKENS = 300   # estimated tokens in a typical review


def estimate_cost(code: str) -> float:
    """Rough cost estimate for one review.

    Input tokens  = code length / 4  +  500 (system prompt + agent overhead)
    Output tokens = fixed 300 (typical review length)

    This is an approximation — the agent makes multiple internal LLM calls,
    so actual cost may be 3-5x higher. Good enough for a portfolio demo.
    """
    input_tokens = len(code) / 4 + 500
    cost = (input_tokens * _INPUT_COST_PER_1K + _TYPICAL_OUTPUT_TOKENS * _OUTPUT_COST_PER_1K) / 1000
    return round(cost, 6)


def log_request(
    trace_id: str,
    code: str,
    tools_called: list[str],
    latency_ms: float,
    num_issues: int,
) -> float:
    """Write one log entry and return the estimated cost."""
    cost_usd = estimate_cost(code)

    entry = {
        "trace_id": trace_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "code_length_chars": len(code),
        "tools_called": tools_called,
        "num_tools": len(tools_called),
        "latency_ms": latency_ms,
        "num_issues": num_issues,
        "cost_usd": cost_usd,
    }

    # Keep in memory for /stats
    _request_log.append(entry)

    # Persist to disk
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

    return cost_usd


def get_stats() -> dict[str, Any]:
    """Aggregate all logged requests into a stats summary."""
    if not _request_log:
        return {"total_requests": 0, "message": "No requests logged yet."}

    latencies   = [e["latency_ms"] for e in _request_log]
    costs       = [e["cost_usd"]   for e in _request_log]
    tool_counts: dict[str, int] = defaultdict(int)

    for entry in _request_log:
        for tool in entry["tools_called"]:
            tool_counts[tool] += 1

    return {
        "total_requests": len(_request_log),
        "avg_latency_ms": round(sum(latencies) / len(latencies), 2),
        "p95_latency_ms": round(sorted(latencies)[int(len(latencies) * 0.95)], 2),
        "avg_cost_usd":   round(sum(costs) / len(costs), 6),
        "total_cost_usd": round(sum(costs), 6),
        "tool_usage":     dict(sorted(tool_counts.items(), key=lambda x: -x[1])),
    }

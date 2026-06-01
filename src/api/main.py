import uuid
from fastapi import FastAPI, HTTPException
from src.models import CodeReviewRequest, CodeReviewResponse
from src.agent.agent import review_code
from src.api.logger import log_request, get_stats

app = FastAPI(
    title="AI Code Review Agent",
    description="A LlamaIndex ReAct agent that autonomously reviews Python code.",
    version="1.0.0",
)


@app.get("/health")
def health():
    """Liveness check — returns ok if the server is running."""
    return {"status": "ok"}


@app.post("/review", response_model=CodeReviewResponse)
def review(request: CodeReviewRequest) -> CodeReviewResponse:
    """Submit a code snippet for review.

    The agent autonomously selects which analysis tools to run,
    synthesizes their output, and returns a structured review.
    """
    trace_id = str(uuid.uuid4())

    try:
        result = review_code(request.code)
    except Exception as e:
        # Unexpected error — log it and return a 500 with a safe message
        raise HTTPException(status_code=500, detail=f"Review failed: {e}")

    log_request(
        trace_id=trace_id,
        code=request.code,
        tools_called=result.tools_called,
        latency_ms=result.latency_ms,
        num_issues=len(result.issues),
    )

    return result


@app.get("/stats")
def stats():
    """Aggregated metrics across all reviews since server start.

    Returns: total requests, avg/p95 latency, avg cost, tool usage counts.
    """
    return get_stats()

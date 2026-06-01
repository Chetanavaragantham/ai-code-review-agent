import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from src.models import CodeReviewResponse, Issue
from src.api.main import app

client = TestClient(app)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _fake_review(code: str) -> CodeReviewResponse:
    """Stand-in for review_code() — returns a fixed response instantly."""
    return CodeReviewResponse(
        summary="Clean code with minor style issues.",
        issues=[Issue(description="Missing docstring", severity="low", tool="analyze_style")],
        suggestions=["Add docstrings to all public functions."],
        tools_called=["analyze_ast", "analyze_style"],
        latency_ms=123.4,
    )


# ── GET /health ───────────────────────────────────────────────────────────────

class TestHealth:
    def test_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200

    def test_returns_ok_status(self):
        response = client.get("/health")
        assert response.json() == {"status": "ok"}


# ── POST /review ──────────────────────────────────────────────────────────────

class TestReviewEndpoint:
    def test_returns_200_for_valid_code(self):
        with patch("src.api.main.review_code", side_effect=_fake_review):
            response = client.post("/review", json={"code": "def foo(): pass"})
        assert response.status_code == 200

    def test_response_has_required_fields(self):
        with patch("src.api.main.review_code", side_effect=_fake_review):
            response = client.post("/review", json={"code": "def foo(): pass"})
        body = response.json()
        assert "summary" in body
        assert "issues" in body
        assert "suggestions" in body
        assert "tools_called" in body
        assert "latency_ms" in body

    def test_issue_has_severity_and_tool(self):
        with patch("src.api.main.review_code", side_effect=_fake_review):
            response = client.post("/review", json={"code": "def foo(): pass"})
        issue = response.json()["issues"][0]
        assert issue["severity"] in ("low", "medium", "high")
        assert "tool" in issue

    def test_rejects_empty_code(self):
        """Pydantic min_length=1 on CodeReviewRequest.code should reject empty strings."""
        response = client.post("/review", json={"code": ""})
        assert response.status_code == 422   # FastAPI validation error

    def test_rejects_missing_code_field(self):
        response = client.post("/review", json={"language": "python"})
        assert response.status_code == 422

    def test_returns_500_when_agent_fails(self):
        with patch("src.api.main.review_code", side_effect=RuntimeError("LLM error")):
            response = client.post("/review", json={"code": "def foo(): pass"})
        assert response.status_code == 500
        assert "Review failed" in response.json()["detail"]


# ── GET /stats ────────────────────────────────────────────────────────────────

class TestStatsEndpoint:
    def test_returns_200(self):
        response = client.get("/stats")
        assert response.status_code == 200

    def test_stats_update_after_review(self):
        """After a successful review, /stats must show at least 1 request."""
        with patch("src.api.main.review_code", side_effect=_fake_review):
            client.post("/review", json={"code": "def foo(): pass"})

        response = client.get("/stats")
        body = response.json()
        assert body["total_requests"] >= 1
        assert "avg_latency_ms" in body
        assert "avg_cost_usd" in body
        assert "tool_usage" in body

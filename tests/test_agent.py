import asyncio
import pytest
from unittest.mock import patch, MagicMock

from src.tools.tools import (
    analyze_ast,
    analyze_complexity,
    analyze_security,
    analyze_style,
)
from src.models import CodeReviewResponse, Issue

# ── Fixtures ──────────────────────────────────────────────────────────────────

SIMPLE_CODE = """\
def add(a, b):
    return a + b


class Calculator:
    def multiply(self, x, y):
        return x * y
"""

INSECURE_CODE = """\
import subprocess


def run_cmd(cmd):
    subprocess.call(cmd, shell=True)
"""


# ── analyze_ast ───────────────────────────────────────────────────────────────

class TestAnalyzeAst:
    def test_detects_function_names(self):
        result = analyze_ast(SIMPLE_CODE)
        assert "add" in result
        assert "multiply" in result

    def test_detects_class_names(self):
        result = analyze_ast(SIMPLE_CODE)
        assert "Calculator" in result

    def test_function_and_class_counts(self):
        result = analyze_ast(SIMPLE_CODE)
        assert "Functions: 2" in result
        assert "Classes: 1" in result

    def test_empty_code_returns_zeros(self):
        result = analyze_ast("")
        assert "Functions: 0" in result
        assert "Classes: 0" in result


# ── analyze_complexity ────────────────────────────────────────────────────────

class TestAnalyzeComplexity:
    def test_returns_string(self):
        result = analyze_complexity(SIMPLE_CODE)
        assert isinstance(result, str)

    def test_output_contains_function_name(self):
        result = analyze_complexity(SIMPLE_CODE)
        assert "add" in result or result == ""


# ── analyze_security ──────────────────────────────────────────────────────────

class TestAnalyzeSecurity:
    def test_flags_shell_true(self):
        result = analyze_security(INSECURE_CODE)
        assert "B602" in result or "shell=True" in result or "subprocess" in result.lower()

    def test_clean_code_returns_string(self):
        result = analyze_security(SIMPLE_CODE)
        assert isinstance(result, str)


# ── analyze_style ─────────────────────────────────────────────────────────────

class TestAnalyzeStyle:
    def test_returns_string(self):
        result = analyze_style(SIMPLE_CODE)
        assert isinstance(result, str)

    def test_flags_missing_docstrings(self):
        result = analyze_style(SIMPLE_CODE)
        assert "C0116" in result or "docstring" in result.lower() or "missing" in result.lower()


# ── Tool wrapper behaviour ────────────────────────────────────────────────────

class TestMakeToolWrapper:
    def test_records_tool_name_in_tracker(self):
        """Calling a wrapped tool appends its name to _tools_called."""
        import src.agent.agent as agent_mod

        agent_mod._tools_called = []
        # Call the real wrapped ast tool (no LLM needed — it runs locally)
        agent_mod.ast_tool._fn(SIMPLE_CODE)
        assert "analyze_ast" in agent_mod._tools_called

    def test_graceful_failure_returns_error_string(self):
        """If the underlying tool raises, the wrapper returns an error string (not an exception)."""
        import src.agent.agent as agent_mod

        agent_mod._tools_called = []

        def always_fails(code: str) -> str:
            raise RuntimeError("subprocess crashed")

        tool = agent_mod._make_tool(always_fails, "bad_tool", "A failing tool.")
        result = tool._fn("def foo(): pass")

        assert "bad_tool" in agent_mod._tools_called
        assert "encountered an error" in result
        assert "subprocess crashed" in result

    def test_tracker_is_reset_between_reviews(self):
        """_tools_called is cleared at the start of each review_code() call."""
        import src.agent.agent as agent_mod
        from llama_index.core.agent import ReActAgent

        agent_mod._tools_called = ["stale_entry"]

        async def _fake_coro(result="ok"):
            return result

        fake_content = MagicMock()
        fake_content.summary = "ok"
        fake_content.issues = []
        fake_content.suggestions = []

        with patch.object(ReActAgent, "run", side_effect=lambda *a, **k: _fake_coro()), \
             patch("src.agent.agent._parse_to_structured", return_value=fake_content):
            from src.agent.agent import review_code
            review_code(SIMPLE_CODE)

        # stale_entry must be gone — only fresh calls remain
        assert "stale_entry" not in agent_mod._tools_called


# ── review_code (agent integration) ──────────────────────────────────────────
#
# We mock two things:
#   1. ReActAgent.run  — so no real LLM call is made
#   2. _parse_to_structured — so no second OpenAI call is made
#
# review_code() still runs asyncio.run() with a real coroutine, so the
# async plumbing is exercised without hitting any external API.

async def _fake_coro(result="ok"):
    return result


def _make_fake_content(summary="Clean code.", issues=None, suggestions=None):
    """Build a MagicMock that looks like _ReviewContent."""
    content = MagicMock()
    content.summary = summary
    content.issues = issues or [
        Issue(description="Missing docstrings", severity="low", tool="analyze_style")
    ]
    content.suggestions = suggestions or ["Add docstrings."]
    return content


class TestReviewCode:
    def test_returns_code_review_response(self):
        """review_code() must return a CodeReviewResponse, not a plain string."""
        from llama_index.core.agent import ReActAgent
        from src.agent.agent import review_code

        with patch.object(ReActAgent, "run", side_effect=lambda *a, **k: _fake_coro()), \
             patch("src.agent.agent._parse_to_structured", return_value=_make_fake_content()):
            result = review_code(SIMPLE_CODE)

        assert isinstance(result, CodeReviewResponse)

    def test_response_fields_are_populated(self):
        """summary, issues, suggestions, and latency_ms must all be filled."""
        from llama_index.core.agent import ReActAgent
        from src.agent.agent import review_code

        fake = _make_fake_content(
            summary="Two issues found.",
            issues=[Issue(description="No docstring", severity="low", tool="analyze_style")],
            suggestions=["Add docstrings."],
        )

        with patch.object(ReActAgent, "run", side_effect=lambda *a, **k: _fake_coro()), \
             patch("src.agent.agent._parse_to_structured", return_value=fake):
            result = review_code(SIMPLE_CODE)

        assert result.summary == "Two issues found."
        assert len(result.issues) == 1
        assert result.issues[0].severity == "low"
        assert result.suggestions == ["Add docstrings."]
        assert isinstance(result.latency_ms, float)
        assert result.latency_ms >= 0

    def test_code_is_passed_to_agent(self):
        """The code string must appear in the prompt sent to agent.run."""
        from llama_index.core.agent import ReActAgent
        from src.agent.agent import review_code

        with patch.object(ReActAgent, "run", side_effect=lambda *a, **k: _fake_coro()) as mock_run, \
             patch("src.agent.agent._parse_to_structured", return_value=_make_fake_content()):
            review_code(SIMPLE_CODE)

        assert "def add" in mock_run.call_args.kwargs["user_msg"]

    def test_timeout_returns_valid_response(self):
        """On timeout, review_code() must return a valid CodeReviewResponse with an error summary."""
        from llama_index.core.agent import ReActAgent
        from src.agent.agent import review_code

        with patch.object(ReActAgent, "run", side_effect=lambda *a, **k: _fake_coro()), \
             patch("src.agent.agent._run_with_timeout", side_effect=asyncio.TimeoutError()):
            result = review_code(SIMPLE_CODE)

        assert isinstance(result, CodeReviewResponse)
        assert "timed out" in result.summary.lower()
        assert result.issues == []
        assert isinstance(result.latency_ms, float)

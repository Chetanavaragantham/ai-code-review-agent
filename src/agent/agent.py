import asyncio
import time
from pydantic import BaseModel

from llama_index.core.agent import ReActAgent
from llama_index.core.tools import FunctionTool
from llama_index.llms.openai import OpenAI
from openai import OpenAI as RawOpenAI

from src.tools.tools import analyze_ast, analyze_complexity, analyze_security, analyze_style
from src.models import CodeReviewResponse, Issue

# ── TOOL CALL TRACKER ────────────────────────────────────────────────────────
# Reset to [] at the start of every review_code() call.
# NOT thread-safe: two simultaneous requests would mix their tool lists.
# Production fix: replace with contextvars.ContextVar for request-scoped isolation.
_tools_called: list[str] = []


def _make_tool(fn, tool_name: str, description: str) -> FunctionTool:
    """Wrap a tool function to:
    1. Record its name in _tools_called when invoked.
    2. Catch exceptions so one failing tool does not kill the whole review.
    """
    def wrapper(code: str) -> str:
        _tools_called.append(tool_name)
        try:
            return fn(code)
        except Exception as e:
            # Return an error string — the agent reads this and continues
            return f"[{tool_name} encountered an error: {e}. Skipping this tool.]"
    wrapper.__name__ = fn.__name__
    return FunctionTool.from_defaults(fn=wrapper, description=description)


# ── TOOLS ────────────────────────────────────────────────────────────────────
ast_tool = _make_tool(
    analyze_ast,
    "analyze_ast",
    """Use this tool to analyze the structure of Python code.
    It identifies functions, classes, and their names.
    Use it when you need to understand what the code contains structurally.""",
)

complexity_tool = _make_tool(
    analyze_complexity,
    "analyze_complexity",
    """Use this tool to measure the cyclomatic complexity of Python code.
    It grades each function from A (simple) to F (dangerously complex).
    Use it when you need to assess how complex or hard to maintain the code is.""",
)

security_tool = _make_tool(
    analyze_security,
    "analyze_security",
    """Use this tool to scan Python code for security vulnerabilities.
    It detects issues like SQL injection, use of dangerous functions, hardcoded passwords.
    Use it on any code that handles user input, databases, or system commands.""",
)

style_tool = _make_tool(
    analyze_style,
    "analyze_style",
    """Use this tool to check Python code for style and convention issues.
    It checks PEP8 compliance, missing docstrings, naming conventions.
    Use it when you need to assess code quality and readability.""",
)

# ── AGENT ────────────────────────────────────────────────────────────────────
llm = OpenAI(model="gpt-4o-mini", temperature=0)

agent = ReActAgent(
    tools=[ast_tool, complexity_tool, security_tool, style_tool],
    llm=llm,
    verbose=True,
    max_iterations=6,
    system_prompt="""You are a senior Python code reviewer.
    When given code, use the available tools to analyze it thoroughly.
    Always call at least 2 tools before writing your review.
    Return a structured review with: Summary, Issues Found, Severity, Suggestions.""",
)


# ── PARSING MODEL ─────────────────────────────────────────────────────────────
# Internal model used only for the second LLM call.
# We do NOT ask OpenAI to fill tools_called or latency_ms — we track those ourselves.
class _ReviewContent(BaseModel):
    summary: str
    issues: list[Issue]
    suggestions: list[str]


def _parse_to_structured(raw_review: str) -> _ReviewContent:
    """
    Second LLM call: takes the agent's free-text review and returns
    a Pydantic-validated object using OpenAI structured output.

    OpenAI guarantees the response matches _ReviewContent's schema exactly —
    no missing keys, no wrong types, no hallucinated fields.
    """
    client = RawOpenAI()
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a parser. Extract structured fields from the code review text. "
                    "Classify each issue severity as 'low', 'medium', or 'high' based on impact. "
                    "For the tool field, use the tool name that found the issue "
                    "(e.g. 'analyze_security', 'analyze_style', 'analyze_complexity', 'analyze_ast'). "
                    "If unclear, use 'agent'."
                ),
            },
            {"role": "user", "content": raw_review},
        ],
        response_format=_ReviewContent,
    )
    return completion.choices[0].message.parsed


# ── TIMEOUT WRAPPER ───────────────────────────────────────────────────────────
async def _run_with_timeout(handler, timeout: float = 25.0):
    """Run the agent workflow with a hard timeout.
    asyncio.wait_for cancels the coroutine if it exceeds `timeout` seconds.
    """
    return await asyncio.wait_for(handler, timeout=timeout)


# ── PUBLIC ENTRY POINT ────────────────────────────────────────────────────────
def review_code(code: str) -> CodeReviewResponse:
    global _tools_called
    _tools_called = []          # reset tracker for this request
    start = time.time()

    handler = agent.run(user_msg=f"Please review this Python code:\n\n{code}")

    try:
        raw_review = asyncio.run(_run_with_timeout(handler))
    except asyncio.TimeoutError:
        latency_ms = round((time.time() - start) * 1000, 2)
        return CodeReviewResponse(
            summary="Review timed out after 25 seconds. The code may be too large or complex.",
            issues=[],
            suggestions=["Consider breaking the code into smaller, focused functions."],
            tools_called=list(_tools_called),
            latency_ms=latency_ms,
        )

    latency_ms = round((time.time() - start) * 1000, 2)

    # Parse the agent's free-text output into a structured Pydantic object
    content = _parse_to_structured(str(raw_review))

    return CodeReviewResponse(
        summary=content.summary,
        issues=content.issues,
        suggestions=content.suggestions,
        tools_called=list(_tools_called),
        latency_ms=latency_ms,
    )

# AI Code Review Agent

A LlamaIndex ReAct agent that autonomously reviews Python code using static analysis tools, then synthesizes the results into a structured report via GPT-4o-mini.

[![CI](https://github.com/Chetanavaragantham/ai-code-review-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/Chetanavaragantham/ai-code-review-agent/actions/workflows/ci.yml)

---

## What it does

Paste Python code → the agent decides which tools to run → returns a structured review:

- **Summary** — plain-English overview of code quality
- **Issues** — each flagged problem with severity (low / medium / high) and the tool that found it
- **Suggestions** — actionable fixes

## Architecture

```
User Input (Gradio UI)
        │
        ▼
FastAPI  POST /review
        │
        ▼
LlamaIndex ReActAgent  (GPT-4o-mini)
        │
        ├──▶ analyze_ast        → structure: functions, classes
        ├──▶ analyze_complexity → cyclomatic complexity (radon)
        ├──▶ analyze_security   → vulnerability scan (bandit)
        └──▶ analyze_style      → PEP8 / docstrings (pylint)
        │
        ▼
_parse_to_structured  (second GPT-4o-mini call)
        │
        ▼
CodeReviewResponse  (Pydantic model)
```

## Tech stack

| Layer | Technology |
|---|---|
| Agent framework | LlamaIndex ReActAgent |
| LLM | GPT-4o-mini (OpenAI) |
| Static analysis | radon, bandit, pylint |
| API | FastAPI + uvicorn |
| UI | Gradio |
| Validation | Pydantic v2 |
| Tests | pytest (27 tests, fully mocked) |
| CI | GitHub Actions |
| Container | Docker |

## Project structure

```
ai-code-review-agent/
├── src/
│   ├── agent/agent.py      # ReActAgent, tool wrappers, review_code()
│   ├── tools/tools.py      # analyze_ast, analyze_complexity, analyze_security, analyze_style
│   ├── api/
│   │   ├── main.py         # FastAPI app: POST /review, GET /health, GET /stats
│   │   └── logger.py       # JSON Lines structured logging + cost estimation
│   ├── ui/app.py           # Gradio interface (launches FastAPI in background thread)
│   └── models.py           # Pydantic models: CodeReviewRequest, CodeReviewResponse, Issue
├── tests/
│   ├── test_agent.py       # 17 unit tests: tools, wrapper, review_code()
│   └── test_api.py         # 10 integration tests: FastAPI endpoints
├── eval/
│   ├── snippets.py         # 20 labeled code snippets (clean / style / security / complexity)
│   └── run_eval.py         # Scoring script: accuracy % by category
├── .github/workflows/ci.yml
├── Dockerfile
└── requirements.txt
```

## Run locally

```bash
git clone https://github.com/Chetanavaragantham/ai-code-review-agent.git
cd ai-code-review-agent

pip install -r requirements.txt

cp .env.example .env
# edit .env and add your OpenAI key

# Launch Gradio UI (starts FastAPI automatically on port 8000)
python src/ui/app.py
```

Open `http://localhost:7860` in your browser.

**API only:**
```bash
uvicorn src.api.main:app --reload --port 8000
# Docs at http://localhost:8000/docs
```

## Run tests

```bash
pytest tests/ -v
```

No API key needed — all LLM calls are mocked.

## Run evaluation

```bash
OPENAI_API_KEY=your-key python eval/run_eval.py
```

Scores the agent against 20 labeled snippets across 4 categories and prints accuracy per category.

## Key engineering decisions

**ReActAgent over a simple chain** — the agent autonomously decides which tools to run based on the code, rather than always running all four. This mirrors how a real reviewer focuses attention.

**Two-pass LLM design** — the first call drives tool selection and reasoning; the second call uses OpenAI structured output (`response_format=PydanticModel`) to guarantee a machine-readable response with no hallucinated fields.

**Tool call tracking** — a module-level list records which tools fired per request, returned in the response and logged for observability.

**Graceful degradation** — each tool is wrapped in a try/except. If one tool crashes, the agent gets an error string and continues rather than failing the whole review.

**25-second timeout** — `asyncio.wait_for` enforces a hard timeout on the agent loop, returning a valid `CodeReviewResponse` with an error summary instead of hanging.

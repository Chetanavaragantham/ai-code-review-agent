import threading
import uvicorn
import gradio as gr
from src.agent.agent import review_code
from src.api.logger import get_stats
from src.api.main import app as fastapi_app


# ── Start FastAPI in background ───────────────────────────────────────────────
# This lets the /review and /stats HTTP endpoints stay live alongside the UI.
def _start_fastapi():
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000, log_level="warning")

threading.Thread(target=_start_fastapi, daemon=True).start()


# ── Core review function called by Gradio ────────────────────────────────────
def run_review(code: str):
    if not code.strip():
        return "Please paste some code first.", "", "", "", ""

    result = review_code(code)

    # Summary
    summary = result.summary

    # Issues table — color-coded by severity
    severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}
    if result.issues:
        rows = "| Severity | Tool | Description |\n|----------|------|-------------|\n"
        for issue in result.issues:
            icon = severity_icon.get(issue.severity, "⚪")
            rows += f"| {icon} {issue.severity} | `{issue.tool}` | {issue.description} |\n"
        issues_md = rows
    else:
        issues_md = "✅ No issues found."

    # Suggestions
    if result.suggestions:
        suggestions_md = "\n".join(f"- {s}" for s in result.suggestions)
    else:
        suggestions_md = "No suggestions."

    # Tools called
    tools_md = ", ".join(f"`{t}`" for t in result.tools_called) if result.tools_called else "none"

    # Metadata
    meta = f"⏱ **Latency:** {result.latency_ms:.0f} ms"

    return summary, issues_md, suggestions_md, tools_md, meta


# ── Gradio UI layout ──────────────────────────────────────────────────────────
with gr.Blocks(title="AI Code Review Agent", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🔍 AI Code Review Agent")
    gr.Markdown(
        "Paste Python code below. The agent autonomously selects which analysis tools "
        "to run, then synthesizes a structured review."
    )

    with gr.Row():
        with gr.Column(scale=1):
            code_input = gr.Code(
                label="Python Code",
                language="python",
                lines=20,
                placeholder="# Paste your Python code here...",
            )
            review_btn = gr.Button("Review Code", variant="primary")

        with gr.Column(scale=1):
            summary_out     = gr.Textbox(label="Summary", lines=4, interactive=False)
            issues_out      = gr.Markdown(label="Issues Found")
            suggestions_out = gr.Markdown(label="Suggestions")
            tools_out       = gr.Textbox(label="Tools Called", interactive=False)
            meta_out        = gr.Markdown()

    review_btn.click(
        fn=run_review,
        inputs=[code_input],
        outputs=[summary_out, issues_out, suggestions_out, tools_out, meta_out],
    )

    gr.Examples(
        examples=[
            ["def add(a, b):\n    return a + b"],
            ["import subprocess\ndef run(cmd):\n    subprocess.call(cmd, shell=True)"],
            [
                "def process(data):\n"
                "    result = []\n"
                "    for i in range(len(data)):\n"
                "        for j in range(len(data)):\n"
                "            if data[i] == data[j] and i != j:\n"
                "                result.append(data[i])\n"
                "    return result"
            ],
        ],
        inputs=[code_input],
        label="Try an example",
    )


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)

from pydantic import BaseModel, Field
from typing import Literal, Optional


class CodeReviewRequest(BaseModel):
    """What the API receives from the caller."""

    code: str = Field(
        ...,
        description="The Python code to review.",
        min_length=1,
    )
    language: str = Field(
        default="python",
        description="Programming language of the snippet.",
    )
    context: Optional[str] = Field(
        default=None,
        description="Optional extra context (e.g. 'this is a Django view').",
    )


class Issue(BaseModel):
    """A single problem found in the code."""

    description: str = Field(..., description="What the issue is.")
    severity: Literal["low", "medium", "high"] = Field(
        ...,
        description="How serious the issue is.",
    )
    tool: str = Field(..., description="Which tool detected this issue.")


class CodeReviewResponse(BaseModel):
    """What the API returns to the caller."""

    summary: str = Field(..., description="One-paragraph overview of the review.")
    issues: list[Issue] = Field(
        default_factory=list,
        description="List of specific problems found.",
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="Actionable improvement suggestions.",
    )
    tools_called: list[str] = Field(
        default_factory=list,
        description="Names of tools the agent invoked.",
    )
    latency_ms: float = Field(
        ...,
        description="Total time taken to produce the review, in milliseconds.",
    )

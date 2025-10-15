# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import Literal

from ..._models import BaseModel

__all__ = ["EvalListResponse", "Eval"]


class Eval(BaseModel):
    criteria: str
    """
    The evaluation criteria text that describes what aspect is being evaluated and
    how
    """

    display_name: str
    """Human-friendly name for display.

    For default evals, prefer standardized labels; otherwise use configured name.
    """

    eval_key: str
    """
    Unique key for eval metric - currently maps to the TrustworthyRAG name property
    and eval_scores dictionary key to check against threshold
    """

    name: str
    """Display name/label for the evaluation metric"""

    context_identifier: Optional[str] = None
    """
    The exact string used in your evaluation criteria to reference the retrieved
    context.
    """

    enabled: Optional[bool] = None
    """Allows the evaluation to be disabled without removing it"""

    guardrailed_fallback_message: Optional[str] = None
    """
    Fallback message to use if this eval fails and causes the response to be
    guardrailed
    """

    is_default: Optional[bool] = None
    """Whether the eval is a default, built-in eval or a custom eval"""

    priority: Optional[int] = None
    """
    Priority order for evals (lower number = higher priority) to determine primary
    eval issue to surface
    """

    query_identifier: Optional[str] = None
    """
    The exact string used in your evaluation criteria to reference the user's query.
    """

    response_identifier: Optional[str] = None
    """
    The exact string used in your evaluation criteria to reference the RAG/LLM
    response.
    """

    should_escalate: Optional[bool] = None
    """
    If true, failing this eval means the question should be escalated to Codex for
    an SME to review
    """

    should_guardrail: Optional[bool] = None
    """If true, failing this eval means the response should be guardrailed"""

    threshold: Optional[float] = None
    """Threshold value that determines if the evaluation fails"""

    threshold_direction: Optional[Literal["above", "below"]] = None
    """Whether the evaluation fails when score is above or below the threshold"""


class EvalListResponse(BaseModel):
    evals: List[Eval]

    total_count: int

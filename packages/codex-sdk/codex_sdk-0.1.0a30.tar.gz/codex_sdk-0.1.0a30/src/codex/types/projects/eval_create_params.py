# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Literal, Required, TypedDict

__all__ = ["EvalCreateParams"]


class EvalCreateParams(TypedDict, total=False):
    criteria: Required[str]
    """
    The evaluation criteria text that describes what aspect is being evaluated and
    how
    """

    eval_key: Required[str]
    """
    Unique key for eval metric - currently maps to the TrustworthyRAG name property
    and eval_scores dictionary key to check against threshold
    """

    name: Required[str]
    """Display name/label for the evaluation metric"""

    context_identifier: Optional[str]
    """
    The exact string used in your evaluation criteria to reference the retrieved
    context.
    """

    enabled: bool
    """Allows the evaluation to be disabled without removing it"""

    guardrailed_fallback_message: Optional[str]
    """
    Fallback message to use if this eval fails and causes the response to be
    guardrailed
    """

    is_default: bool
    """Whether the eval is a default, built-in eval or a custom eval"""

    priority: Optional[int]
    """
    Priority order for evals (lower number = higher priority) to determine primary
    eval issue to surface
    """

    query_identifier: Optional[str]
    """
    The exact string used in your evaluation criteria to reference the user's query.
    """

    response_identifier: Optional[str]
    """
    The exact string used in your evaluation criteria to reference the RAG/LLM
    response.
    """

    should_escalate: bool
    """
    If true, failing this eval means the question should be escalated to Codex for
    an SME to review
    """

    should_guardrail: bool
    """If true, failing this eval means the response should be guardrailed"""

    threshold: float
    """Threshold value that determines if the evaluation fails"""

    threshold_direction: Literal["above", "below"]
    """Whether the evaluation fails when score is above or below the threshold"""

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Optional
from datetime import datetime
from typing_extensions import Literal

from .._models import BaseModel

__all__ = [
    "ProjectReturnSchema",
    "Config",
    "ConfigEvalConfig",
    "ConfigEvalConfigCustomEvals",
    "ConfigEvalConfigCustomEvalsEvals",
    "ConfigEvalConfigDefaultEvals",
    "ConfigEvalConfigDefaultEvalsContextSufficiency",
    "ConfigEvalConfigDefaultEvalsQueryEase",
    "ConfigEvalConfigDefaultEvalsResponseGroundedness",
    "ConfigEvalConfigDefaultEvalsResponseHelpfulness",
    "ConfigEvalConfigDefaultEvalsTrustworthiness",
]


class ConfigEvalConfigCustomEvalsEvals(BaseModel):
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


class ConfigEvalConfigCustomEvals(BaseModel):
    evals: Optional[Dict[str, ConfigEvalConfigCustomEvalsEvals]] = None


class ConfigEvalConfigDefaultEvalsContextSufficiency(BaseModel):
    eval_key: str
    """
    Unique key for eval metric - currently maps to the TrustworthyRAG name property
    and eval_scores dictionary key to check against threshold
    """

    name: str
    """Display name/label for the evaluation metric"""

    enabled: Optional[bool] = None
    """Allows the evaluation to be disabled without removing it"""

    guardrailed_fallback_message: Optional[str] = None
    """
    Fallback message to use if this eval fails and causes the response to be
    guardrailed
    """

    priority: Optional[int] = None
    """
    Priority order for evals (lower number = higher priority) to determine primary
    eval issue to surface
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


class ConfigEvalConfigDefaultEvalsQueryEase(BaseModel):
    eval_key: str
    """
    Unique key for eval metric - currently maps to the TrustworthyRAG name property
    and eval_scores dictionary key to check against threshold
    """

    name: str
    """Display name/label for the evaluation metric"""

    enabled: Optional[bool] = None
    """Allows the evaluation to be disabled without removing it"""

    guardrailed_fallback_message: Optional[str] = None
    """
    Fallback message to use if this eval fails and causes the response to be
    guardrailed
    """

    priority: Optional[int] = None
    """
    Priority order for evals (lower number = higher priority) to determine primary
    eval issue to surface
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


class ConfigEvalConfigDefaultEvalsResponseGroundedness(BaseModel):
    eval_key: str
    """
    Unique key for eval metric - currently maps to the TrustworthyRAG name property
    and eval_scores dictionary key to check against threshold
    """

    name: str
    """Display name/label for the evaluation metric"""

    enabled: Optional[bool] = None
    """Allows the evaluation to be disabled without removing it"""

    guardrailed_fallback_message: Optional[str] = None
    """
    Fallback message to use if this eval fails and causes the response to be
    guardrailed
    """

    priority: Optional[int] = None
    """
    Priority order for evals (lower number = higher priority) to determine primary
    eval issue to surface
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


class ConfigEvalConfigDefaultEvalsResponseHelpfulness(BaseModel):
    eval_key: str
    """
    Unique key for eval metric - currently maps to the TrustworthyRAG name property
    and eval_scores dictionary key to check against threshold
    """

    name: str
    """Display name/label for the evaluation metric"""

    enabled: Optional[bool] = None
    """Allows the evaluation to be disabled without removing it"""

    guardrailed_fallback_message: Optional[str] = None
    """
    Fallback message to use if this eval fails and causes the response to be
    guardrailed
    """

    priority: Optional[int] = None
    """
    Priority order for evals (lower number = higher priority) to determine primary
    eval issue to surface
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


class ConfigEvalConfigDefaultEvalsTrustworthiness(BaseModel):
    eval_key: str
    """
    Unique key for eval metric - currently maps to the TrustworthyRAG name property
    and eval_scores dictionary key to check against threshold
    """

    name: str
    """Display name/label for the evaluation metric"""

    enabled: Optional[bool] = None
    """Allows the evaluation to be disabled without removing it"""

    guardrailed_fallback_message: Optional[str] = None
    """
    Fallback message to use if this eval fails and causes the response to be
    guardrailed
    """

    priority: Optional[int] = None
    """
    Priority order for evals (lower number = higher priority) to determine primary
    eval issue to surface
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


class ConfigEvalConfigDefaultEvals(BaseModel):
    context_sufficiency: Optional[ConfigEvalConfigDefaultEvalsContextSufficiency] = None
    """A pre-configured evaluation metric from TrustworthyRAG or built into the system.

    The evaluation criteria and identifiers are immutable and system-managed, while
    other properties like thresholds and priorities can be configured.
    """

    query_ease: Optional[ConfigEvalConfigDefaultEvalsQueryEase] = None
    """A pre-configured evaluation metric from TrustworthyRAG or built into the system.

    The evaluation criteria and identifiers are immutable and system-managed, while
    other properties like thresholds and priorities can be configured.
    """

    response_groundedness: Optional[ConfigEvalConfigDefaultEvalsResponseGroundedness] = None
    """A pre-configured evaluation metric from TrustworthyRAG or built into the system.

    The evaluation criteria and identifiers are immutable and system-managed, while
    other properties like thresholds and priorities can be configured.
    """

    response_helpfulness: Optional[ConfigEvalConfigDefaultEvalsResponseHelpfulness] = None
    """A pre-configured evaluation metric from TrustworthyRAG or built into the system.

    The evaluation criteria and identifiers are immutable and system-managed, while
    other properties like thresholds and priorities can be configured.
    """

    trustworthiness: Optional[ConfigEvalConfigDefaultEvalsTrustworthiness] = None
    """A pre-configured evaluation metric from TrustworthyRAG or built into the system.

    The evaluation criteria and identifiers are immutable and system-managed, while
    other properties like thresholds and priorities can be configured.
    """


class ConfigEvalConfig(BaseModel):
    custom_evals: Optional[ConfigEvalConfigCustomEvals] = None
    """Configuration for custom evaluation metrics."""

    default_evals: Optional[ConfigEvalConfigDefaultEvals] = None
    """Configuration for default evaluation metrics."""


class Config(BaseModel):
    clustering_use_llm_matching: Optional[bool] = None

    eval_config: Optional[ConfigEvalConfig] = None
    """Configuration for project-specific evaluation metrics"""

    llm_matching_model: Optional[str] = None

    llm_matching_quality_preset: Optional[Literal["best", "high", "medium", "low", "base"]] = None

    lower_llm_match_distance_threshold: Optional[float] = None

    max_distance: Optional[float] = None

    query_use_llm_matching: Optional[bool] = None

    question_match_llm_prompt: Optional[str] = None

    question_match_llm_prompt_with_answer: Optional[str] = None

    tlm_evals_model: Optional[str] = None

    upper_llm_match_distance_threshold: Optional[float] = None


class ProjectReturnSchema(BaseModel):
    id: str

    config: Config

    created_at: datetime

    created_by_user_id: str

    name: str

    organization_id: str

    updated_at: datetime

    auto_clustering_enabled: Optional[bool] = None

    description: Optional[str] = None

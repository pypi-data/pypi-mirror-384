# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from ..._models import BaseModel

__all__ = ["RemediationPublishResponse"]


class RemediationPublishResponse(BaseModel):
    id: str

    answered_at: Optional[datetime] = None

    answered_by: Optional[str] = None

    created_at: datetime

    last_edited_at: Optional[datetime] = None

    last_edited_by: Optional[str] = None

    needs_review: bool

    project_id: str

    question: str

    status: Literal["ACTIVE", "DRAFT", "ACTIVE_WITH_DRAFT", "NOT_STARTED", "PAUSED", "NO_ACTION_NEEDED"]

    answer: Optional[str] = None

    draft_answer: Optional[str] = None

    manual_review_status_override: Optional[Literal["addressed", "unaddressed"]] = None
    """Manual review status override for remediations."""

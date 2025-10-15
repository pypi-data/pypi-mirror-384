# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["QueryLogAddUserFeedbackParams"]


class QueryLogAddUserFeedbackParams(TypedDict, total=False):
    project_id: Required[str]

    key: Required[str]
    """A key describing the criteria of the feedback, eg 'rating'"""

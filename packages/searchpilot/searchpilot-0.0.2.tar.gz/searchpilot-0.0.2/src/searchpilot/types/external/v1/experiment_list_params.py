# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Optional
from datetime import datetime
from typing_extensions import Literal, Annotated, TypedDict

from ...._utils import PropertyInfo

__all__ = ["ExperimentListParams"]


class ExperimentListParams(TypedDict, total=False):
    account_slug: str
    """Account slug"""

    complete_state: Optional[Literal["accepted", "hidden", "invalid", "null", "rejected"]]
    """
    - `accepted` - Positive
    - `rejected` - Negative
    - `null` - Inconclusive
    - `invalid` - Invalid
    - `hidden` - Hidden
    """

    cursor: str
    """The pagination cursor value."""

    customer_slug: str
    """Customer slug"""

    ended_at_after: Annotated[Union[str, datetime], PropertyInfo(format="iso8601")]
    """Ended at"""

    ended_at_before: Annotated[Union[str, datetime], PropertyInfo(format="iso8601")]
    """Ended at"""

    has_ended: bool
    """Has Ended"""

    has_started: bool
    """Has Started"""

    section_slug: str
    """Section slug"""

    started_at_after: Annotated[Union[str, datetime], PropertyInfo(format="iso8601")]
    """Started At"""

    started_at_before: Annotated[Union[str, datetime], PropertyInfo(format="iso8601")]
    """Started At"""

    status: Literal[
        "ended",
        "failed-salt-shake",
        "paused",
        "published",
        "ready",
        "rolledout",
        "waiting-for-end",
        "waiting-for-manual-salt",
        "waiting-for-rollout",
        "waiting-for-salt",
    ]
    """
    - `waiting-for-salt` - Waiting for salt
    - `waiting-for-manual-salt` - Waiting for manual salt
    - `failed-salt-shake` - Failed salt shake
    - `ready` - Ready
    - `published` - Published
    - `paused` - Paused
    - `waiting-for-rollout` - Waiting for rollout
    - `rolledout` - Rolled out to 100%
    - `waiting-for-end` - Waiting for end
    - `ended` - Ended
    """

    test_type: Literal["cro", "full_funnel", "linear_full_funnel", "seo"]
    """
    - `seo` - SEO
    - `cro` - CRO
    - `full_funnel` - Full Funnel
    - `linear_full_funnel` - Linear Full Funnel
    """

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import TypedDict

__all__ = ["StepListParams"]


class StepListParams(TypedDict, total=False):
    account_slug: str
    """Account slug"""

    cursor: str
    """The pagination cursor value."""

    customer_slug: str
    """Customer slug"""

    enabled: bool

    rule_id: float
    """Rule ID"""

    section_slug: str
    """Section slug"""

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import TypedDict

__all__ = ["SeoExperimentResultListParams"]


class SeoExperimentResultListParams(TypedDict, total=False):
    account_slug: str
    """Account slug"""

    cursor: str
    """The pagination cursor value."""

    customer_slug: str
    """Customer slug"""

    experiment_id: float
    """Experiment ID"""

    section_slug: str
    """Section slug"""

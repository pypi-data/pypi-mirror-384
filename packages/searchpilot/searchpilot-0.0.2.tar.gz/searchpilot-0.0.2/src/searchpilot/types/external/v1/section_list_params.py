# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, TypedDict

__all__ = ["SectionListParams"]


class SectionListParams(TypedDict, total=False):
    account_slug: str
    """Account slug"""

    cursor: str
    """The pagination cursor value."""

    customer_slug: str
    """Customer slug"""

    published_to_live: bool

    type: Literal["api", "request", "response"]
    """
    - `response` - Response
    - `api` - API
    - `request` - Request
    """

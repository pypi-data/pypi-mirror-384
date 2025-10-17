# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from .section import Section
from ...._models import BaseModel

__all__ = ["SectionListResponse"]


class SectionListResponse(BaseModel):
    results: List[Section]

    next: Optional[str] = None

    previous: Optional[str] = None

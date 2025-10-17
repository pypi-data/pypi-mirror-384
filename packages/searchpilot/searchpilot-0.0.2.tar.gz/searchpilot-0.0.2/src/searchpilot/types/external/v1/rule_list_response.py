# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from .rule import Rule
from ...._models import BaseModel

__all__ = ["RuleListResponse"]


class RuleListResponse(BaseModel):
    results: List[Rule]

    next: Optional[str] = None

    previous: Optional[str] = None

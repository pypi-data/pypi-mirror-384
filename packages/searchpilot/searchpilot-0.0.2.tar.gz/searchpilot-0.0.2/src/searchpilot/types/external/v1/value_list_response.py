# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from .value import Value
from ...._models import BaseModel

__all__ = ["ValueListResponse"]


class ValueListResponse(BaseModel):
    results: List[Value]

    next: Optional[str] = None

    previous: Optional[str] = None

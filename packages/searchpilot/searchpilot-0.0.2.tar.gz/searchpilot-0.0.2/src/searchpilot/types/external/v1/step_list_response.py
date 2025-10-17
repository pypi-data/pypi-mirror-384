# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from .step import Step
from ...._models import BaseModel

__all__ = ["StepListResponse"]


class StepListResponse(BaseModel):
    results: List[Step]

    next: Optional[str] = None

    previous: Optional[str] = None

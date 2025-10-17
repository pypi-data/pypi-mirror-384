# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from ...._models import BaseModel
from .experiment import Experiment

__all__ = ["ExperimentListResponse"]


class ExperimentListResponse(BaseModel):
    results: List[Experiment]

    next: Optional[str] = None

    previous: Optional[str] = None

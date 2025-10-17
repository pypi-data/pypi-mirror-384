# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from ...._models import BaseModel
from .seo_experiment_result import SeoExperimentResult

__all__ = ["SeoExperimentResultListResponse"]


class SeoExperimentResultListResponse(BaseModel):
    results: List[SeoExperimentResult]

    next: Optional[str] = None

    previous: Optional[str] = None

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Optional
from datetime import datetime
from typing_extensions import Literal

from ...._models import BaseModel

__all__ = ["Section", "CurrentExperiment", "LatestReadyToTestResult"]


class CurrentExperiment(BaseModel):
    id: int


class LatestReadyToTestResult(BaseModel):
    average_daily_metric_value_30: float

    coefficient_of_variance_30: float

    max_bucket_metric_value_range_mean: float

    num_days_missing_data: int

    number_unique_pages_30: float

    requested_at: datetime

    score: float

    score_breakdown_control_avg_daily_metric_value: float

    score_breakdown_correlation_mean: float

    score_breakdown_correlation_stddev: float

    score_breakdown_cov_diff_daily_metric_value: float

    score_breakdown_sufficient_path_score: float

    score_breakdown_variant_avg_daily_metric_value: float


class Section(BaseModel):
    id: int

    account_slug: str

    current_experiment: Optional[CurrentExperiment] = None

    customer_slug: str

    latest_ready_to_test_result: Optional[LatestReadyToTestResult] = None

    matching_expression: Dict[str, object]

    name: str

    params_to_keep: List[str]

    slug: str

    published_to_live: Optional[bool] = None

    type: Optional[Literal["response", "api", "request"]] = None
    """
    - `response` - Response
    - `api` - API
    - `request` - Request
    """

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

import datetime
from typing import Dict, List, Optional
from typing_extensions import Literal

from ...._models import BaseModel

__all__ = ["SeoExperimentResult", "Metric", "Pipeline"]


class Metric(BaseModel):
    id: int

    name: str


class Pipeline(BaseModel):
    id: int

    is_preferred: bool

    is_published: bool

    name: str

    steps: object


class SeoExperimentResult(BaseModel):
    id: int

    account_slug: str

    alpha: float

    customer_slug: str

    date: datetime.date

    dimension_combination: Dict[str, str]

    estimated_wait_time: Optional[Literal["no_valid_wait_time", "up_to_a_week", "up_to_two_weeks"]] = None

    expected_overall_extra_metric_value: Optional[float] = None

    expected_overall_extra_metric_value_lower: Optional[float] = None

    expected_overall_extra_metric_value_upper: Optional[float] = None

    experiment_id: int

    extra_alphas: List[float]

    intervention_date: datetime.date

    is_significant: bool

    metric: Metric

    pipeline: Pipeline

    post_pipeline_average_daily_metric_value: Optional[float] = None

    recommendation: str

    section_slug: Optional[str] = None

    steps: object

    bucket_correlation: Optional[float] = None

    coefficient_of_determination: Optional[float] = None

    confidence: Optional[float] = None

    days_running: Optional[int] = None

    end_date: Optional[datetime.date] = None

    expected_uplift_percent: Optional[float] = None

    expected_uplift_percent_lower: Optional[float] = None

    expected_uplift_percent_upper: Optional[float] = None

    forecast_reliability_score: Optional[float] = None

    generated_on: Optional[datetime.datetime] = None

    lower_percentage: Optional[float] = None

    mean_absolute_percentage_error: Optional[float] = None

    metric_value: Optional[float] = None

    monthly_change: Optional[float] = None

    monthly_lower: Optional[float] = None

    monthly_upper: Optional[float] = None

    percentage_change: Optional[float] = None

    post_pipeline_number_unique_paths: Optional[int] = None

    post_pipeline_ready_to_test_score: Optional[float] = None

    self_uplift: Optional[float] = None

    start_date: Optional[datetime.date] = None

    upper_percentage: Optional[float] = None

    volatility_index: Optional[float] = None

    yearly_change: Optional[float] = None

    yearly_lower: Optional[float] = None

    yearly_upper: Optional[float] = None

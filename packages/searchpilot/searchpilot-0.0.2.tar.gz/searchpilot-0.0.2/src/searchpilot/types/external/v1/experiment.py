# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime
from typing_extensions import Literal

from ...._models import BaseModel
from .hasher_enum import HasherEnum

__all__ = [
    "Experiment",
    "CroDetails",
    "SeoDetails",
    "SeoDetailsExperimentMetric",
    "SeoDetailsExperimentMetricMetric",
    "SeoDetailsLatestPrimarySeoExperimentResult",
    "SeoDetailsPreferredPipeline",
]


class CroDetails(BaseModel):
    cro_parameters: object

    hasher_parameters: object

    hasher: Optional[HasherEnum] = None
    """
    - `carbon.hashers.base.simple` - Simple
    - `carbon.hashers.base.random_by_percent` - Random (deprecated)
    - `carbon.hashers.base.random_by_percent_2` - Random (deprecated)
    - `carbon.hashers.base.random_by_percent_3` - Split by URL path into
      statistically similar buckets (deprecated)
    - `carbon.hashers.base.random_by_percent_4` - Split by normalised URL path into
      statistically similar buckets (deprecated)
    - `carbon.hashers.base.random_by_percent_5` - Split by normalised URL path into
      statistically similar buckets (recommended)
    - `carbon.hashers.base.hash_variable` - Split by Value into random buckets
    - `carbon.hashers.base.variable_matches` - Split by Value into manual buckets
    - `carbon.hashers.base.cro_random_user` - CRO Test
    - `carbon.hashers.base.cro_always_control` - CRO Test - always serve control
    """


class SeoDetailsExperimentMetricMetric(BaseModel):
    id: int

    name: str


class SeoDetailsExperimentMetric(BaseModel):
    is_primary: bool

    metric: SeoDetailsExperimentMetricMetric


class SeoDetailsLatestPrimarySeoExperimentResult(BaseModel):
    id: int


class SeoDetailsPreferredPipeline(BaseModel):
    id: int

    name: str

    steps: object


class SeoDetails(BaseModel):
    experiment_metrics: List[SeoDetailsExperimentMetric]

    hasher_parameters: object

    latest_primary_seo_experiment_result: Optional[SeoDetailsLatestPrimarySeoExperimentResult] = None

    preferred_pipeline: SeoDetailsPreferredPipeline

    hasher: Optional[HasherEnum] = None
    """
    - `carbon.hashers.base.simple` - Simple
    - `carbon.hashers.base.random_by_percent` - Random (deprecated)
    - `carbon.hashers.base.random_by_percent_2` - Random (deprecated)
    - `carbon.hashers.base.random_by_percent_3` - Split by URL path into
      statistically similar buckets (deprecated)
    - `carbon.hashers.base.random_by_percent_4` - Split by normalised URL path into
      statistically similar buckets (deprecated)
    - `carbon.hashers.base.random_by_percent_5` - Split by normalised URL path into
      statistically similar buckets (recommended)
    - `carbon.hashers.base.hash_variable` - Split by Value into random buckets
    - `carbon.hashers.base.variable_matches` - Split by Value into manual buckets
    - `carbon.hashers.base.cro_random_user` - CRO Test
    - `carbon.hashers.base.cro_always_control` - CRO Test - always serve control
    """

    primary_alpha: Optional[float] = None


class Experiment(BaseModel):
    id: int

    account_slug: str

    complete_state: Optional[Literal["accepted", "rejected", "null", "invalid", "hidden"]] = None

    cro_details: Optional[CroDetails] = None

    customer_slug: str

    ended_at: Optional[datetime] = None

    name: str
    """The name of the test"""

    section_slug: Optional[str] = None

    seo_details: Optional[SeoDetails] = None

    started_at: Optional[datetime] = None

    test_type: Literal["seo", "cro", "full_funnel", "linear_full_funnel"]
    """
    - `seo` - SEO
    - `cro` - CRO
    - `full_funnel` - Full Funnel
    - `linear_full_funnel` - Linear Full Funnel
    """

    notes: Optional[str] = None
    """Add any notes about the test"""

    status: Optional[
        Literal[
            "waiting-for-salt",
            "waiting-for-manual-salt",
            "failed-salt-shake",
            "ready",
            "published",
            "paused",
            "waiting-for-rollout",
            "rolledout",
            "waiting-for-end",
            "ended",
        ]
    ] = None
    """
    - `waiting-for-salt` - Waiting for salt
    - `waiting-for-manual-salt` - Waiting for manual salt
    - `failed-salt-shake` - Failed salt shake
    - `ready` - Ready
    - `published` - Published
    - `paused` - Paused
    - `waiting-for-rollout` - Waiting for rollout
    - `rolledout` - Rolled out to 100%
    - `waiting-for-end` - Waiting for end
    - `ended` - Ended
    """

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Optional
from datetime import datetime
from typing_extensions import Literal

import httpx

from ...._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ...._utils import maybe_transform, async_maybe_transform
from ...._compat import cached_property
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...._base_client import make_request_options
from ....types.external.v1 import experiment_list_params
from ....types.external.v1.experiment import Experiment
from ....types.external.v1.experiment_list_response import ExperimentListResponse

__all__ = ["ExperimentsResource", "AsyncExperimentsResource"]


class ExperimentsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ExperimentsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/adamsteele-sp/searchpilot-python#accessing-raw-response-data-eg-headers
        """
        return ExperimentsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ExperimentsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/adamsteele-sp/searchpilot-python#with_streaming_response
        """
        return ExperimentsResourceWithStreamingResponse(self)

    def retrieve(
        self,
        experiment_id: int,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Experiment:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            f"/api/external/v1/experiments/{experiment_id}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Experiment,
        )

    def list(
        self,
        *,
        account_slug: str | Omit = omit,
        complete_state: Optional[Literal["accepted", "hidden", "invalid", "null", "rejected"]] | Omit = omit,
        cursor: str | Omit = omit,
        customer_slug: str | Omit = omit,
        ended_at_after: Union[str, datetime] | Omit = omit,
        ended_at_before: Union[str, datetime] | Omit = omit,
        has_ended: bool | Omit = omit,
        has_started: bool | Omit = omit,
        section_slug: str | Omit = omit,
        started_at_after: Union[str, datetime] | Omit = omit,
        started_at_before: Union[str, datetime] | Omit = omit,
        status: Literal[
            "ended",
            "failed-salt-shake",
            "paused",
            "published",
            "ready",
            "rolledout",
            "waiting-for-end",
            "waiting-for-manual-salt",
            "waiting-for-rollout",
            "waiting-for-salt",
        ]
        | Omit = omit,
        test_type: Literal["cro", "full_funnel", "linear_full_funnel", "seo"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ExperimentListResponse:
        """
        Args:
          account_slug: Account slug

          complete_state: - `accepted` - Positive
              - `rejected` - Negative
              - `null` - Inconclusive
              - `invalid` - Invalid
              - `hidden` - Hidden

          cursor: The pagination cursor value.

          customer_slug: Customer slug

          ended_at_after: Ended at

          ended_at_before: Ended at

          has_ended: Has Ended

          has_started: Has Started

          section_slug: Section slug

          started_at_after: Started At

          started_at_before: Started At

          status: - `waiting-for-salt` - Waiting for salt
              - `waiting-for-manual-salt` - Waiting for manual salt
              - `failed-salt-shake` - Failed salt shake
              - `ready` - Ready
              - `published` - Published
              - `paused` - Paused
              - `waiting-for-rollout` - Waiting for rollout
              - `rolledout` - Rolled out to 100%
              - `waiting-for-end` - Waiting for end
              - `ended` - Ended

          test_type: - `seo` - SEO
              - `cro` - CRO
              - `full_funnel` - Full Funnel
              - `linear_full_funnel` - Linear Full Funnel

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/api/external/v1/experiments/",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "account_slug": account_slug,
                        "complete_state": complete_state,
                        "cursor": cursor,
                        "customer_slug": customer_slug,
                        "ended_at_after": ended_at_after,
                        "ended_at_before": ended_at_before,
                        "has_ended": has_ended,
                        "has_started": has_started,
                        "section_slug": section_slug,
                        "started_at_after": started_at_after,
                        "started_at_before": started_at_before,
                        "status": status,
                        "test_type": test_type,
                    },
                    experiment_list_params.ExperimentListParams,
                ),
            ),
            cast_to=ExperimentListResponse,
        )


class AsyncExperimentsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncExperimentsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/adamsteele-sp/searchpilot-python#accessing-raw-response-data-eg-headers
        """
        return AsyncExperimentsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncExperimentsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/adamsteele-sp/searchpilot-python#with_streaming_response
        """
        return AsyncExperimentsResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        experiment_id: int,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Experiment:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            f"/api/external/v1/experiments/{experiment_id}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Experiment,
        )

    async def list(
        self,
        *,
        account_slug: str | Omit = omit,
        complete_state: Optional[Literal["accepted", "hidden", "invalid", "null", "rejected"]] | Omit = omit,
        cursor: str | Omit = omit,
        customer_slug: str | Omit = omit,
        ended_at_after: Union[str, datetime] | Omit = omit,
        ended_at_before: Union[str, datetime] | Omit = omit,
        has_ended: bool | Omit = omit,
        has_started: bool | Omit = omit,
        section_slug: str | Omit = omit,
        started_at_after: Union[str, datetime] | Omit = omit,
        started_at_before: Union[str, datetime] | Omit = omit,
        status: Literal[
            "ended",
            "failed-salt-shake",
            "paused",
            "published",
            "ready",
            "rolledout",
            "waiting-for-end",
            "waiting-for-manual-salt",
            "waiting-for-rollout",
            "waiting-for-salt",
        ]
        | Omit = omit,
        test_type: Literal["cro", "full_funnel", "linear_full_funnel", "seo"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ExperimentListResponse:
        """
        Args:
          account_slug: Account slug

          complete_state: - `accepted` - Positive
              - `rejected` - Negative
              - `null` - Inconclusive
              - `invalid` - Invalid
              - `hidden` - Hidden

          cursor: The pagination cursor value.

          customer_slug: Customer slug

          ended_at_after: Ended at

          ended_at_before: Ended at

          has_ended: Has Ended

          has_started: Has Started

          section_slug: Section slug

          started_at_after: Started At

          started_at_before: Started At

          status: - `waiting-for-salt` - Waiting for salt
              - `waiting-for-manual-salt` - Waiting for manual salt
              - `failed-salt-shake` - Failed salt shake
              - `ready` - Ready
              - `published` - Published
              - `paused` - Paused
              - `waiting-for-rollout` - Waiting for rollout
              - `rolledout` - Rolled out to 100%
              - `waiting-for-end` - Waiting for end
              - `ended` - Ended

          test_type: - `seo` - SEO
              - `cro` - CRO
              - `full_funnel` - Full Funnel
              - `linear_full_funnel` - Linear Full Funnel

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/api/external/v1/experiments/",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "account_slug": account_slug,
                        "complete_state": complete_state,
                        "cursor": cursor,
                        "customer_slug": customer_slug,
                        "ended_at_after": ended_at_after,
                        "ended_at_before": ended_at_before,
                        "has_ended": has_ended,
                        "has_started": has_started,
                        "section_slug": section_slug,
                        "started_at_after": started_at_after,
                        "started_at_before": started_at_before,
                        "status": status,
                        "test_type": test_type,
                    },
                    experiment_list_params.ExperimentListParams,
                ),
            ),
            cast_to=ExperimentListResponse,
        )


class ExperimentsResourceWithRawResponse:
    def __init__(self, experiments: ExperimentsResource) -> None:
        self._experiments = experiments

        self.retrieve = to_raw_response_wrapper(
            experiments.retrieve,
        )
        self.list = to_raw_response_wrapper(
            experiments.list,
        )


class AsyncExperimentsResourceWithRawResponse:
    def __init__(self, experiments: AsyncExperimentsResource) -> None:
        self._experiments = experiments

        self.retrieve = async_to_raw_response_wrapper(
            experiments.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            experiments.list,
        )


class ExperimentsResourceWithStreamingResponse:
    def __init__(self, experiments: ExperimentsResource) -> None:
        self._experiments = experiments

        self.retrieve = to_streamed_response_wrapper(
            experiments.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            experiments.list,
        )


class AsyncExperimentsResourceWithStreamingResponse:
    def __init__(self, experiments: AsyncExperimentsResource) -> None:
        self._experiments = experiments

        self.retrieve = async_to_streamed_response_wrapper(
            experiments.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            experiments.list,
        )

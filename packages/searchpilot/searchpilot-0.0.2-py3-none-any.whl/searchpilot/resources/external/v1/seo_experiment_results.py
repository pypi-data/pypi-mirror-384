# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

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
from ....types.external.v1 import seo_experiment_result_list_params
from ....types.external.v1.seo_experiment_result import SeoExperimentResult
from ....types.external.v1.seo_experiment_result_list_response import SeoExperimentResultListResponse

__all__ = ["SeoExperimentResultsResource", "AsyncSeoExperimentResultsResource"]


class SeoExperimentResultsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> SeoExperimentResultsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/adamsteele-sp/searchpilot-python#accessing-raw-response-data-eg-headers
        """
        return SeoExperimentResultsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> SeoExperimentResultsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/adamsteele-sp/searchpilot-python#with_streaming_response
        """
        return SeoExperimentResultsResourceWithStreamingResponse(self)

    def retrieve(
        self,
        seo_experiment_result_id: int,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SeoExperimentResult:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            f"/api/external/v1/seo_experiment_results/{seo_experiment_result_id}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SeoExperimentResult,
        )

    def list(
        self,
        *,
        account_slug: str | Omit = omit,
        cursor: str | Omit = omit,
        customer_slug: str | Omit = omit,
        experiment_id: float | Omit = omit,
        section_slug: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SeoExperimentResultListResponse:
        """
        Args:
          account_slug: Account slug

          cursor: The pagination cursor value.

          customer_slug: Customer slug

          experiment_id: Experiment ID

          section_slug: Section slug

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/api/external/v1/seo_experiment_results/",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "account_slug": account_slug,
                        "cursor": cursor,
                        "customer_slug": customer_slug,
                        "experiment_id": experiment_id,
                        "section_slug": section_slug,
                    },
                    seo_experiment_result_list_params.SeoExperimentResultListParams,
                ),
            ),
            cast_to=SeoExperimentResultListResponse,
        )


class AsyncSeoExperimentResultsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncSeoExperimentResultsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/adamsteele-sp/searchpilot-python#accessing-raw-response-data-eg-headers
        """
        return AsyncSeoExperimentResultsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncSeoExperimentResultsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/adamsteele-sp/searchpilot-python#with_streaming_response
        """
        return AsyncSeoExperimentResultsResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        seo_experiment_result_id: int,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SeoExperimentResult:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            f"/api/external/v1/seo_experiment_results/{seo_experiment_result_id}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SeoExperimentResult,
        )

    async def list(
        self,
        *,
        account_slug: str | Omit = omit,
        cursor: str | Omit = omit,
        customer_slug: str | Omit = omit,
        experiment_id: float | Omit = omit,
        section_slug: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SeoExperimentResultListResponse:
        """
        Args:
          account_slug: Account slug

          cursor: The pagination cursor value.

          customer_slug: Customer slug

          experiment_id: Experiment ID

          section_slug: Section slug

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/api/external/v1/seo_experiment_results/",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "account_slug": account_slug,
                        "cursor": cursor,
                        "customer_slug": customer_slug,
                        "experiment_id": experiment_id,
                        "section_slug": section_slug,
                    },
                    seo_experiment_result_list_params.SeoExperimentResultListParams,
                ),
            ),
            cast_to=SeoExperimentResultListResponse,
        )


class SeoExperimentResultsResourceWithRawResponse:
    def __init__(self, seo_experiment_results: SeoExperimentResultsResource) -> None:
        self._seo_experiment_results = seo_experiment_results

        self.retrieve = to_raw_response_wrapper(
            seo_experiment_results.retrieve,
        )
        self.list = to_raw_response_wrapper(
            seo_experiment_results.list,
        )


class AsyncSeoExperimentResultsResourceWithRawResponse:
    def __init__(self, seo_experiment_results: AsyncSeoExperimentResultsResource) -> None:
        self._seo_experiment_results = seo_experiment_results

        self.retrieve = async_to_raw_response_wrapper(
            seo_experiment_results.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            seo_experiment_results.list,
        )


class SeoExperimentResultsResourceWithStreamingResponse:
    def __init__(self, seo_experiment_results: SeoExperimentResultsResource) -> None:
        self._seo_experiment_results = seo_experiment_results

        self.retrieve = to_streamed_response_wrapper(
            seo_experiment_results.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            seo_experiment_results.list,
        )


class AsyncSeoExperimentResultsResourceWithStreamingResponse:
    def __init__(self, seo_experiment_results: AsyncSeoExperimentResultsResource) -> None:
        self._seo_experiment_results = seo_experiment_results

        self.retrieve = async_to_streamed_response_wrapper(
            seo_experiment_results.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            seo_experiment_results.list,
        )

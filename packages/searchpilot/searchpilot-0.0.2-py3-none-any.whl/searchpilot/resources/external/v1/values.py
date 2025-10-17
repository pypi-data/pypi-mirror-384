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
from ....types.external.v1 import value_list_params
from ....types.external.v1.value import Value
from ....types.external.v1.value_list_response import ValueListResponse

__all__ = ["ValuesResource", "AsyncValuesResource"]


class ValuesResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ValuesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/adamsteele-sp/searchpilot-python#accessing-raw-response-data-eg-headers
        """
        return ValuesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ValuesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/adamsteele-sp/searchpilot-python#with_streaming_response
        """
        return ValuesResourceWithStreamingResponse(self)

    def retrieve(
        self,
        value_id: int,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Value:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            f"/api/external/v1/values/{value_id}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Value,
        )

    def list(
        self,
        *,
        account_slug: str | Omit = omit,
        cursor: str | Omit = omit,
        customer_slug: str | Omit = omit,
        is_in_preview_spec: bool | Omit = omit,
        section_slug: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ValueListResponse:
        """
        Args:
          account_slug: Account slug

          cursor: The pagination cursor value.

          customer_slug: Customer slug

          section_slug: Section slug

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/api/external/v1/values/",
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
                        "is_in_preview_spec": is_in_preview_spec,
                        "section_slug": section_slug,
                    },
                    value_list_params.ValueListParams,
                ),
            ),
            cast_to=ValueListResponse,
        )


class AsyncValuesResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncValuesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/adamsteele-sp/searchpilot-python#accessing-raw-response-data-eg-headers
        """
        return AsyncValuesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncValuesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/adamsteele-sp/searchpilot-python#with_streaming_response
        """
        return AsyncValuesResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        value_id: int,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Value:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            f"/api/external/v1/values/{value_id}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Value,
        )

    async def list(
        self,
        *,
        account_slug: str | Omit = omit,
        cursor: str | Omit = omit,
        customer_slug: str | Omit = omit,
        is_in_preview_spec: bool | Omit = omit,
        section_slug: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ValueListResponse:
        """
        Args:
          account_slug: Account slug

          cursor: The pagination cursor value.

          customer_slug: Customer slug

          section_slug: Section slug

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/api/external/v1/values/",
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
                        "is_in_preview_spec": is_in_preview_spec,
                        "section_slug": section_slug,
                    },
                    value_list_params.ValueListParams,
                ),
            ),
            cast_to=ValueListResponse,
        )


class ValuesResourceWithRawResponse:
    def __init__(self, values: ValuesResource) -> None:
        self._values = values

        self.retrieve = to_raw_response_wrapper(
            values.retrieve,
        )
        self.list = to_raw_response_wrapper(
            values.list,
        )


class AsyncValuesResourceWithRawResponse:
    def __init__(self, values: AsyncValuesResource) -> None:
        self._values = values

        self.retrieve = async_to_raw_response_wrapper(
            values.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            values.list,
        )


class ValuesResourceWithStreamingResponse:
    def __init__(self, values: ValuesResource) -> None:
        self._values = values

        self.retrieve = to_streamed_response_wrapper(
            values.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            values.list,
        )


class AsyncValuesResourceWithStreamingResponse:
    def __init__(self, values: AsyncValuesResource) -> None:
        self._values = values

        self.retrieve = async_to_streamed_response_wrapper(
            values.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            values.list,
        )

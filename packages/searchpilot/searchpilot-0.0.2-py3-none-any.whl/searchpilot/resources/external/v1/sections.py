# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

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
from ....types.external.v1 import section_list_params
from ....types.external.v1.section import Section
from ....types.external.v1.section_list_response import SectionListResponse

__all__ = ["SectionsResource", "AsyncSectionsResource"]


class SectionsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> SectionsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/adamsteele-sp/searchpilot-python#accessing-raw-response-data-eg-headers
        """
        return SectionsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> SectionsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/adamsteele-sp/searchpilot-python#with_streaming_response
        """
        return SectionsResourceWithStreamingResponse(self)

    def retrieve(
        self,
        section_slug: str,
        *,
        account_slug: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Section:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_slug:
            raise ValueError(f"Expected a non-empty value for `account_slug` but received {account_slug!r}")
        if not section_slug:
            raise ValueError(f"Expected a non-empty value for `section_slug` but received {section_slug!r}")
        return self._get(
            f"/api/external/v1/sections/{account_slug}/{section_slug}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Section,
        )

    def list(
        self,
        *,
        account_slug: str | Omit = omit,
        cursor: str | Omit = omit,
        customer_slug: str | Omit = omit,
        published_to_live: bool | Omit = omit,
        type: Literal["api", "request", "response"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SectionListResponse:
        """
        Args:
          account_slug: Account slug

          cursor: The pagination cursor value.

          customer_slug: Customer slug

          type: - `response` - Response
              - `api` - API
              - `request` - Request

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/api/external/v1/sections/",
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
                        "published_to_live": published_to_live,
                        "type": type,
                    },
                    section_list_params.SectionListParams,
                ),
            ),
            cast_to=SectionListResponse,
        )


class AsyncSectionsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncSectionsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/adamsteele-sp/searchpilot-python#accessing-raw-response-data-eg-headers
        """
        return AsyncSectionsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncSectionsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/adamsteele-sp/searchpilot-python#with_streaming_response
        """
        return AsyncSectionsResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        section_slug: str,
        *,
        account_slug: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Section:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_slug:
            raise ValueError(f"Expected a non-empty value for `account_slug` but received {account_slug!r}")
        if not section_slug:
            raise ValueError(f"Expected a non-empty value for `section_slug` but received {section_slug!r}")
        return await self._get(
            f"/api/external/v1/sections/{account_slug}/{section_slug}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Section,
        )

    async def list(
        self,
        *,
        account_slug: str | Omit = omit,
        cursor: str | Omit = omit,
        customer_slug: str | Omit = omit,
        published_to_live: bool | Omit = omit,
        type: Literal["api", "request", "response"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SectionListResponse:
        """
        Args:
          account_slug: Account slug

          cursor: The pagination cursor value.

          customer_slug: Customer slug

          type: - `response` - Response
              - `api` - API
              - `request` - Request

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/api/external/v1/sections/",
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
                        "published_to_live": published_to_live,
                        "type": type,
                    },
                    section_list_params.SectionListParams,
                ),
            ),
            cast_to=SectionListResponse,
        )


class SectionsResourceWithRawResponse:
    def __init__(self, sections: SectionsResource) -> None:
        self._sections = sections

        self.retrieve = to_raw_response_wrapper(
            sections.retrieve,
        )
        self.list = to_raw_response_wrapper(
            sections.list,
        )


class AsyncSectionsResourceWithRawResponse:
    def __init__(self, sections: AsyncSectionsResource) -> None:
        self._sections = sections

        self.retrieve = async_to_raw_response_wrapper(
            sections.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            sections.list,
        )


class SectionsResourceWithStreamingResponse:
    def __init__(self, sections: SectionsResource) -> None:
        self._sections = sections

        self.retrieve = to_streamed_response_wrapper(
            sections.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            sections.list,
        )


class AsyncSectionsResourceWithStreamingResponse:
    def __init__(self, sections: AsyncSectionsResource) -> None:
        self._sections = sections

        self.retrieve = async_to_streamed_response_wrapper(
            sections.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            sections.list,
        )

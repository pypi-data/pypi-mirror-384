# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from searchpilot import Searchpilot, AsyncSearchpilot
from tests.utils import assert_matches_type
from searchpilot.types.external.v1 import Value, ValueListResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestValues:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Searchpilot) -> None:
        value = client.external.v1.values.retrieve(
            0,
        )
        assert_matches_type(Value, value, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Searchpilot) -> None:
        response = client.external.v1.values.with_raw_response.retrieve(
            0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        value = response.parse()
        assert_matches_type(Value, value, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Searchpilot) -> None:
        with client.external.v1.values.with_streaming_response.retrieve(
            0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            value = response.parse()
            assert_matches_type(Value, value, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Searchpilot) -> None:
        value = client.external.v1.values.list()
        assert_matches_type(ValueListResponse, value, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: Searchpilot) -> None:
        value = client.external.v1.values.list(
            account_slug="account_slug",
            cursor="cursor",
            customer_slug="customer_slug",
            is_in_preview_spec=True,
            section_slug="section_slug",
        )
        assert_matches_type(ValueListResponse, value, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Searchpilot) -> None:
        response = client.external.v1.values.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        value = response.parse()
        assert_matches_type(ValueListResponse, value, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Searchpilot) -> None:
        with client.external.v1.values.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            value = response.parse()
            assert_matches_type(ValueListResponse, value, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncValues:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncSearchpilot) -> None:
        value = await async_client.external.v1.values.retrieve(
            0,
        )
        assert_matches_type(Value, value, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncSearchpilot) -> None:
        response = await async_client.external.v1.values.with_raw_response.retrieve(
            0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        value = await response.parse()
        assert_matches_type(Value, value, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncSearchpilot) -> None:
        async with async_client.external.v1.values.with_streaming_response.retrieve(
            0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            value = await response.parse()
            assert_matches_type(Value, value, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncSearchpilot) -> None:
        value = await async_client.external.v1.values.list()
        assert_matches_type(ValueListResponse, value, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncSearchpilot) -> None:
        value = await async_client.external.v1.values.list(
            account_slug="account_slug",
            cursor="cursor",
            customer_slug="customer_slug",
            is_in_preview_spec=True,
            section_slug="section_slug",
        )
        assert_matches_type(ValueListResponse, value, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncSearchpilot) -> None:
        response = await async_client.external.v1.values.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        value = await response.parse()
        assert_matches_type(ValueListResponse, value, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncSearchpilot) -> None:
        async with async_client.external.v1.values.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            value = await response.parse()
            assert_matches_type(ValueListResponse, value, path=["response"])

        assert cast(Any, response.is_closed) is True

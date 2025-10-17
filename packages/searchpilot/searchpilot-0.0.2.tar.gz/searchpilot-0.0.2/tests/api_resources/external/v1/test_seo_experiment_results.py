# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from searchpilot import Searchpilot, AsyncSearchpilot
from tests.utils import assert_matches_type
from searchpilot.types.external.v1 import (
    SeoExperimentResult,
    SeoExperimentResultListResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestSeoExperimentResults:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Searchpilot) -> None:
        seo_experiment_result = client.external.v1.seo_experiment_results.retrieve(
            0,
        )
        assert_matches_type(SeoExperimentResult, seo_experiment_result, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Searchpilot) -> None:
        response = client.external.v1.seo_experiment_results.with_raw_response.retrieve(
            0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        seo_experiment_result = response.parse()
        assert_matches_type(SeoExperimentResult, seo_experiment_result, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Searchpilot) -> None:
        with client.external.v1.seo_experiment_results.with_streaming_response.retrieve(
            0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            seo_experiment_result = response.parse()
            assert_matches_type(SeoExperimentResult, seo_experiment_result, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Searchpilot) -> None:
        seo_experiment_result = client.external.v1.seo_experiment_results.list()
        assert_matches_type(SeoExperimentResultListResponse, seo_experiment_result, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: Searchpilot) -> None:
        seo_experiment_result = client.external.v1.seo_experiment_results.list(
            account_slug="account_slug",
            cursor="cursor",
            customer_slug="customer_slug",
            experiment_id=0,
            section_slug="section_slug",
        )
        assert_matches_type(SeoExperimentResultListResponse, seo_experiment_result, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Searchpilot) -> None:
        response = client.external.v1.seo_experiment_results.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        seo_experiment_result = response.parse()
        assert_matches_type(SeoExperimentResultListResponse, seo_experiment_result, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Searchpilot) -> None:
        with client.external.v1.seo_experiment_results.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            seo_experiment_result = response.parse()
            assert_matches_type(SeoExperimentResultListResponse, seo_experiment_result, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncSeoExperimentResults:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncSearchpilot) -> None:
        seo_experiment_result = await async_client.external.v1.seo_experiment_results.retrieve(
            0,
        )
        assert_matches_type(SeoExperimentResult, seo_experiment_result, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncSearchpilot) -> None:
        response = await async_client.external.v1.seo_experiment_results.with_raw_response.retrieve(
            0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        seo_experiment_result = await response.parse()
        assert_matches_type(SeoExperimentResult, seo_experiment_result, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncSearchpilot) -> None:
        async with async_client.external.v1.seo_experiment_results.with_streaming_response.retrieve(
            0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            seo_experiment_result = await response.parse()
            assert_matches_type(SeoExperimentResult, seo_experiment_result, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncSearchpilot) -> None:
        seo_experiment_result = await async_client.external.v1.seo_experiment_results.list()
        assert_matches_type(SeoExperimentResultListResponse, seo_experiment_result, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncSearchpilot) -> None:
        seo_experiment_result = await async_client.external.v1.seo_experiment_results.list(
            account_slug="account_slug",
            cursor="cursor",
            customer_slug="customer_slug",
            experiment_id=0,
            section_slug="section_slug",
        )
        assert_matches_type(SeoExperimentResultListResponse, seo_experiment_result, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncSearchpilot) -> None:
        response = await async_client.external.v1.seo_experiment_results.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        seo_experiment_result = await response.parse()
        assert_matches_type(SeoExperimentResultListResponse, seo_experiment_result, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncSearchpilot) -> None:
        async with async_client.external.v1.seo_experiment_results.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            seo_experiment_result = await response.parse()
            assert_matches_type(SeoExperimentResultListResponse, seo_experiment_result, path=["response"])

        assert cast(Any, response.is_closed) is True

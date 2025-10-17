# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from searchpilot import Searchpilot, AsyncSearchpilot
from tests.utils import assert_matches_type
from searchpilot._utils import parse_datetime
from searchpilot.types.external.v1 import Experiment, ExperimentListResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestExperiments:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Searchpilot) -> None:
        experiment = client.external.v1.experiments.retrieve(
            0,
        )
        assert_matches_type(Experiment, experiment, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Searchpilot) -> None:
        response = client.external.v1.experiments.with_raw_response.retrieve(
            0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        experiment = response.parse()
        assert_matches_type(Experiment, experiment, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Searchpilot) -> None:
        with client.external.v1.experiments.with_streaming_response.retrieve(
            0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            experiment = response.parse()
            assert_matches_type(Experiment, experiment, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Searchpilot) -> None:
        experiment = client.external.v1.experiments.list()
        assert_matches_type(ExperimentListResponse, experiment, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: Searchpilot) -> None:
        experiment = client.external.v1.experiments.list(
            account_slug="account_slug",
            complete_state="accepted",
            cursor="cursor",
            customer_slug="customer_slug",
            ended_at_after=parse_datetime("2019-12-27T18:11:19.117Z"),
            ended_at_before=parse_datetime("2019-12-27T18:11:19.117Z"),
            has_ended=True,
            has_started=True,
            section_slug="section_slug",
            started_at_after=parse_datetime("2019-12-27T18:11:19.117Z"),
            started_at_before=parse_datetime("2019-12-27T18:11:19.117Z"),
            status="ended",
            test_type="cro",
        )
        assert_matches_type(ExperimentListResponse, experiment, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Searchpilot) -> None:
        response = client.external.v1.experiments.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        experiment = response.parse()
        assert_matches_type(ExperimentListResponse, experiment, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Searchpilot) -> None:
        with client.external.v1.experiments.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            experiment = response.parse()
            assert_matches_type(ExperimentListResponse, experiment, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncExperiments:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncSearchpilot) -> None:
        experiment = await async_client.external.v1.experiments.retrieve(
            0,
        )
        assert_matches_type(Experiment, experiment, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncSearchpilot) -> None:
        response = await async_client.external.v1.experiments.with_raw_response.retrieve(
            0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        experiment = await response.parse()
        assert_matches_type(Experiment, experiment, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncSearchpilot) -> None:
        async with async_client.external.v1.experiments.with_streaming_response.retrieve(
            0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            experiment = await response.parse()
            assert_matches_type(Experiment, experiment, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncSearchpilot) -> None:
        experiment = await async_client.external.v1.experiments.list()
        assert_matches_type(ExperimentListResponse, experiment, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncSearchpilot) -> None:
        experiment = await async_client.external.v1.experiments.list(
            account_slug="account_slug",
            complete_state="accepted",
            cursor="cursor",
            customer_slug="customer_slug",
            ended_at_after=parse_datetime("2019-12-27T18:11:19.117Z"),
            ended_at_before=parse_datetime("2019-12-27T18:11:19.117Z"),
            has_ended=True,
            has_started=True,
            section_slug="section_slug",
            started_at_after=parse_datetime("2019-12-27T18:11:19.117Z"),
            started_at_before=parse_datetime("2019-12-27T18:11:19.117Z"),
            status="ended",
            test_type="cro",
        )
        assert_matches_type(ExperimentListResponse, experiment, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncSearchpilot) -> None:
        response = await async_client.external.v1.experiments.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        experiment = await response.parse()
        assert_matches_type(ExperimentListResponse, experiment, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncSearchpilot) -> None:
        async with async_client.external.v1.experiments.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            experiment = await response.parse()
            assert_matches_type(ExperimentListResponse, experiment, path=["response"])

        assert cast(Any, response.is_closed) is True

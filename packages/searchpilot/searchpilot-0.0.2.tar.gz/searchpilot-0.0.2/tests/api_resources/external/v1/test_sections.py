# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from searchpilot import Searchpilot, AsyncSearchpilot
from tests.utils import assert_matches_type
from searchpilot.types.external.v1 import Section, SectionListResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestSections:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Searchpilot) -> None:
        section = client.external.v1.sections.retrieve(
            section_slug="section_slug",
            account_slug="account_slug",
        )
        assert_matches_type(Section, section, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Searchpilot) -> None:
        response = client.external.v1.sections.with_raw_response.retrieve(
            section_slug="section_slug",
            account_slug="account_slug",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        section = response.parse()
        assert_matches_type(Section, section, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Searchpilot) -> None:
        with client.external.v1.sections.with_streaming_response.retrieve(
            section_slug="section_slug",
            account_slug="account_slug",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            section = response.parse()
            assert_matches_type(Section, section, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: Searchpilot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_slug` but received ''"):
            client.external.v1.sections.with_raw_response.retrieve(
                section_slug="section_slug",
                account_slug="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `section_slug` but received ''"):
            client.external.v1.sections.with_raw_response.retrieve(
                section_slug="",
                account_slug="account_slug",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Searchpilot) -> None:
        section = client.external.v1.sections.list()
        assert_matches_type(SectionListResponse, section, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: Searchpilot) -> None:
        section = client.external.v1.sections.list(
            account_slug="account_slug",
            cursor="cursor",
            customer_slug="customer_slug",
            published_to_live=True,
            type="api",
        )
        assert_matches_type(SectionListResponse, section, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Searchpilot) -> None:
        response = client.external.v1.sections.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        section = response.parse()
        assert_matches_type(SectionListResponse, section, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Searchpilot) -> None:
        with client.external.v1.sections.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            section = response.parse()
            assert_matches_type(SectionListResponse, section, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncSections:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncSearchpilot) -> None:
        section = await async_client.external.v1.sections.retrieve(
            section_slug="section_slug",
            account_slug="account_slug",
        )
        assert_matches_type(Section, section, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncSearchpilot) -> None:
        response = await async_client.external.v1.sections.with_raw_response.retrieve(
            section_slug="section_slug",
            account_slug="account_slug",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        section = await response.parse()
        assert_matches_type(Section, section, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncSearchpilot) -> None:
        async with async_client.external.v1.sections.with_streaming_response.retrieve(
            section_slug="section_slug",
            account_slug="account_slug",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            section = await response.parse()
            assert_matches_type(Section, section, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncSearchpilot) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_slug` but received ''"):
            await async_client.external.v1.sections.with_raw_response.retrieve(
                section_slug="section_slug",
                account_slug="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `section_slug` but received ''"):
            await async_client.external.v1.sections.with_raw_response.retrieve(
                section_slug="",
                account_slug="account_slug",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncSearchpilot) -> None:
        section = await async_client.external.v1.sections.list()
        assert_matches_type(SectionListResponse, section, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncSearchpilot) -> None:
        section = await async_client.external.v1.sections.list(
            account_slug="account_slug",
            cursor="cursor",
            customer_slug="customer_slug",
            published_to_live=True,
            type="api",
        )
        assert_matches_type(SectionListResponse, section, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncSearchpilot) -> None:
        response = await async_client.external.v1.sections.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        section = await response.parse()
        assert_matches_type(SectionListResponse, section, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncSearchpilot) -> None:
        async with async_client.external.v1.sections.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            section = await response.parse()
            assert_matches_type(SectionListResponse, section, path=["response"])

        assert cast(Any, response.is_closed) is True

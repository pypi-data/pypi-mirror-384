# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from distillery import Distillery, AsyncDistillery
from tests.utils import assert_matches_type
from distillery.pagination import SyncCursorURLPage, AsyncCursorURLPage
from distillery.types.shared import Step

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestSteps:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Distillery) -> None:
        step = client.steps.retrieve(
            0,
        )
        assert_matches_type(Step, step, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Distillery) -> None:
        response = client.steps.with_raw_response.retrieve(
            0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        step = response.parse()
        assert_matches_type(Step, step, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Distillery) -> None:
        with client.steps.with_streaming_response.retrieve(
            0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            step = response.parse()
            assert_matches_type(Step, step, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Distillery) -> None:
        step = client.steps.list()
        assert_matches_type(SyncCursorURLPage[Step], step, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: Distillery) -> None:
        step = client.steps.list(
            account_slug="account_slug",
            cursor="cursor",
            customer_slug="customer_slug",
            enabled=True,
            rule_id=0,
            section_slug="section_slug",
        )
        assert_matches_type(SyncCursorURLPage[Step], step, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Distillery) -> None:
        response = client.steps.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        step = response.parse()
        assert_matches_type(SyncCursorURLPage[Step], step, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Distillery) -> None:
        with client.steps.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            step = response.parse()
            assert_matches_type(SyncCursorURLPage[Step], step, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncSteps:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncDistillery) -> None:
        step = await async_client.steps.retrieve(
            0,
        )
        assert_matches_type(Step, step, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncDistillery) -> None:
        response = await async_client.steps.with_raw_response.retrieve(
            0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        step = await response.parse()
        assert_matches_type(Step, step, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncDistillery) -> None:
        async with async_client.steps.with_streaming_response.retrieve(
            0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            step = await response.parse()
            assert_matches_type(Step, step, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncDistillery) -> None:
        step = await async_client.steps.list()
        assert_matches_type(AsyncCursorURLPage[Step], step, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncDistillery) -> None:
        step = await async_client.steps.list(
            account_slug="account_slug",
            cursor="cursor",
            customer_slug="customer_slug",
            enabled=True,
            rule_id=0,
            section_slug="section_slug",
        )
        assert_matches_type(AsyncCursorURLPage[Step], step, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncDistillery) -> None:
        response = await async_client.steps.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        step = await response.parse()
        assert_matches_type(AsyncCursorURLPage[Step], step, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncDistillery) -> None:
        async with async_client.steps.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            step = await response.parse()
            assert_matches_type(AsyncCursorURLPage[Step], step, path=["response"])

        assert cast(Any, response.is_closed) is True

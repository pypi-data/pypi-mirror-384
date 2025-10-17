# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from raindrop import Raindrop, AsyncRaindrop
from tests.utils import assert_matches_type
from raindrop.types import RehydrateSessionRehydrateResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestRehydrateSession:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_rehydrate(self, client: Raindrop) -> None:
        rehydrate_session = client.rehydrate_session.rehydrate(
            session_id="01jxanr45haeswhay4n0q8340y",
            smart_memory_location={
                "smartMemory": {
                    "name": "memory-name",
                    "application_name": "demo",
                    "version": "1234",
                }
            },
        )
        assert_matches_type(RehydrateSessionRehydrateResponse, rehydrate_session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_rehydrate_with_all_params(self, client: Raindrop) -> None:
        rehydrate_session = client.rehydrate_session.rehydrate(
            session_id="01jxanr45haeswhay4n0q8340y",
            smart_memory_location={
                "smartMemory": {
                    "name": "memory-name",
                    "application_name": "demo",
                    "version": "1234",
                }
            },
            summary_only=False,
        )
        assert_matches_type(RehydrateSessionRehydrateResponse, rehydrate_session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_rehydrate(self, client: Raindrop) -> None:
        response = client.rehydrate_session.with_raw_response.rehydrate(
            session_id="01jxanr45haeswhay4n0q8340y",
            smart_memory_location={
                "smartMemory": {
                    "name": "memory-name",
                    "application_name": "demo",
                    "version": "1234",
                }
            },
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        rehydrate_session = response.parse()
        assert_matches_type(RehydrateSessionRehydrateResponse, rehydrate_session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_rehydrate(self, client: Raindrop) -> None:
        with client.rehydrate_session.with_streaming_response.rehydrate(
            session_id="01jxanr45haeswhay4n0q8340y",
            smart_memory_location={
                "smartMemory": {
                    "name": "memory-name",
                    "application_name": "demo",
                    "version": "1234",
                }
            },
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            rehydrate_session = response.parse()
            assert_matches_type(RehydrateSessionRehydrateResponse, rehydrate_session, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncRehydrateSession:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_rehydrate(self, async_client: AsyncRaindrop) -> None:
        rehydrate_session = await async_client.rehydrate_session.rehydrate(
            session_id="01jxanr45haeswhay4n0q8340y",
            smart_memory_location={
                "smartMemory": {
                    "name": "memory-name",
                    "application_name": "demo",
                    "version": "1234",
                }
            },
        )
        assert_matches_type(RehydrateSessionRehydrateResponse, rehydrate_session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_rehydrate_with_all_params(self, async_client: AsyncRaindrop) -> None:
        rehydrate_session = await async_client.rehydrate_session.rehydrate(
            session_id="01jxanr45haeswhay4n0q8340y",
            smart_memory_location={
                "smartMemory": {
                    "name": "memory-name",
                    "application_name": "demo",
                    "version": "1234",
                }
            },
            summary_only=False,
        )
        assert_matches_type(RehydrateSessionRehydrateResponse, rehydrate_session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_rehydrate(self, async_client: AsyncRaindrop) -> None:
        response = await async_client.rehydrate_session.with_raw_response.rehydrate(
            session_id="01jxanr45haeswhay4n0q8340y",
            smart_memory_location={
                "smartMemory": {
                    "name": "memory-name",
                    "application_name": "demo",
                    "version": "1234",
                }
            },
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        rehydrate_session = await response.parse()
        assert_matches_type(RehydrateSessionRehydrateResponse, rehydrate_session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_rehydrate(self, async_client: AsyncRaindrop) -> None:
        async with async_client.rehydrate_session.with_streaming_response.rehydrate(
            session_id="01jxanr45haeswhay4n0q8340y",
            smart_memory_location={
                "smartMemory": {
                    "name": "memory-name",
                    "application_name": "demo",
                    "version": "1234",
                }
            },
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            rehydrate_session = await response.parse()
            assert_matches_type(RehydrateSessionRehydrateResponse, rehydrate_session, path=["response"])

        assert cast(Any, response.is_closed) is True

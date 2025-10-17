# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from raindrop import Raindrop, AsyncRaindrop
from tests.utils import assert_matches_type
from raindrop._utils import parse_datetime
from raindrop.types.query import MemorySearchResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestMemory:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_search(self, client: Raindrop) -> None:
        memory = client.query.memory.search(
            session_id="01jxanr45haeswhay4n0q8340y",
            smart_memory_location={
                "smartMemory": {
                    "name": "memory-name",
                    "application_name": "demo",
                    "version": "1234",
                }
            },
            terms="user interface preferences",
        )
        assert_matches_type(MemorySearchResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_search_with_all_params(self, client: Raindrop) -> None:
        memory = client.query.memory.search(
            session_id="01jxanr45haeswhay4n0q8340y",
            smart_memory_location={
                "smartMemory": {
                    "name": "memory-name",
                    "application_name": "demo",
                    "version": "1234",
                }
            },
            terms="user interface preferences",
            end_time=parse_datetime("2019-12-27T18:11:19.117Z"),
            n_most_recent=10,
            start_time=parse_datetime("2019-12-27T18:11:19.117Z"),
            timeline="user-conversation-2024",
        )
        assert_matches_type(MemorySearchResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_search(self, client: Raindrop) -> None:
        response = client.query.memory.with_raw_response.search(
            session_id="01jxanr45haeswhay4n0q8340y",
            smart_memory_location={
                "smartMemory": {
                    "name": "memory-name",
                    "application_name": "demo",
                    "version": "1234",
                }
            },
            terms="user interface preferences",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        memory = response.parse()
        assert_matches_type(MemorySearchResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_search(self, client: Raindrop) -> None:
        with client.query.memory.with_streaming_response.search(
            session_id="01jxanr45haeswhay4n0q8340y",
            smart_memory_location={
                "smartMemory": {
                    "name": "memory-name",
                    "application_name": "demo",
                    "version": "1234",
                }
            },
            terms="user interface preferences",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            memory = response.parse()
            assert_matches_type(MemorySearchResponse, memory, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncMemory:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_search(self, async_client: AsyncRaindrop) -> None:
        memory = await async_client.query.memory.search(
            session_id="01jxanr45haeswhay4n0q8340y",
            smart_memory_location={
                "smartMemory": {
                    "name": "memory-name",
                    "application_name": "demo",
                    "version": "1234",
                }
            },
            terms="user interface preferences",
        )
        assert_matches_type(MemorySearchResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_search_with_all_params(self, async_client: AsyncRaindrop) -> None:
        memory = await async_client.query.memory.search(
            session_id="01jxanr45haeswhay4n0q8340y",
            smart_memory_location={
                "smartMemory": {
                    "name": "memory-name",
                    "application_name": "demo",
                    "version": "1234",
                }
            },
            terms="user interface preferences",
            end_time=parse_datetime("2019-12-27T18:11:19.117Z"),
            n_most_recent=10,
            start_time=parse_datetime("2019-12-27T18:11:19.117Z"),
            timeline="user-conversation-2024",
        )
        assert_matches_type(MemorySearchResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_search(self, async_client: AsyncRaindrop) -> None:
        response = await async_client.query.memory.with_raw_response.search(
            session_id="01jxanr45haeswhay4n0q8340y",
            smart_memory_location={
                "smartMemory": {
                    "name": "memory-name",
                    "application_name": "demo",
                    "version": "1234",
                }
            },
            terms="user interface preferences",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        memory = await response.parse()
        assert_matches_type(MemorySearchResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_search(self, async_client: AsyncRaindrop) -> None:
        async with async_client.query.memory.with_streaming_response.search(
            session_id="01jxanr45haeswhay4n0q8340y",
            smart_memory_location={
                "smartMemory": {
                    "name": "memory-name",
                    "application_name": "demo",
                    "version": "1234",
                }
            },
            terms="user interface preferences",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            memory = await response.parse()
            assert_matches_type(MemorySearchResponse, memory, path=["response"])

        assert cast(Any, response.is_closed) is True

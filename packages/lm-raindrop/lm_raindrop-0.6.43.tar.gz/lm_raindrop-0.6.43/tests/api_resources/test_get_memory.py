# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from raindrop import Raindrop, AsyncRaindrop
from tests.utils import assert_matches_type
from raindrop.types import GetMemoryRetrieveResponse
from raindrop._utils import parse_datetime

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestGetMemory:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Raindrop) -> None:
        get_memory = client.get_memory.retrieve(
            session_id="01jxanr45haeswhay4n0q8340y",
            smart_memory_location={
                "smartMemory": {
                    "name": "memory-name",
                    "application_name": "demo",
                    "version": "1234",
                }
            },
        )
        assert_matches_type(GetMemoryRetrieveResponse, get_memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_with_all_params(self, client: Raindrop) -> None:
        get_memory = client.get_memory.retrieve(
            session_id="01jxanr45haeswhay4n0q8340y",
            smart_memory_location={
                "smartMemory": {
                    "name": "memory-name",
                    "application_name": "demo",
                    "version": "1234",
                }
            },
            end_time=parse_datetime("2019-12-27T18:11:19.117Z"),
            key="user-preference-theme",
            n_most_recent=10,
            start_time=parse_datetime("2019-12-27T18:11:19.117Z"),
            timeline="user-conversation-2024",
        )
        assert_matches_type(GetMemoryRetrieveResponse, get_memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Raindrop) -> None:
        response = client.get_memory.with_raw_response.retrieve(
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
        get_memory = response.parse()
        assert_matches_type(GetMemoryRetrieveResponse, get_memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Raindrop) -> None:
        with client.get_memory.with_streaming_response.retrieve(
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

            get_memory = response.parse()
            assert_matches_type(GetMemoryRetrieveResponse, get_memory, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncGetMemory:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncRaindrop) -> None:
        get_memory = await async_client.get_memory.retrieve(
            session_id="01jxanr45haeswhay4n0q8340y",
            smart_memory_location={
                "smartMemory": {
                    "name": "memory-name",
                    "application_name": "demo",
                    "version": "1234",
                }
            },
        )
        assert_matches_type(GetMemoryRetrieveResponse, get_memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_with_all_params(self, async_client: AsyncRaindrop) -> None:
        get_memory = await async_client.get_memory.retrieve(
            session_id="01jxanr45haeswhay4n0q8340y",
            smart_memory_location={
                "smartMemory": {
                    "name": "memory-name",
                    "application_name": "demo",
                    "version": "1234",
                }
            },
            end_time=parse_datetime("2019-12-27T18:11:19.117Z"),
            key="user-preference-theme",
            n_most_recent=10,
            start_time=parse_datetime("2019-12-27T18:11:19.117Z"),
            timeline="user-conversation-2024",
        )
        assert_matches_type(GetMemoryRetrieveResponse, get_memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncRaindrop) -> None:
        response = await async_client.get_memory.with_raw_response.retrieve(
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
        get_memory = await response.parse()
        assert_matches_type(GetMemoryRetrieveResponse, get_memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncRaindrop) -> None:
        async with async_client.get_memory.with_streaming_response.retrieve(
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

            get_memory = await response.parse()
            assert_matches_type(GetMemoryRetrieveResponse, get_memory, path=["response"])

        assert cast(Any, response.is_closed) is True

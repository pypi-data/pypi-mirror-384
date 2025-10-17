# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from raindrop import Raindrop, AsyncRaindrop
from tests.utils import assert_matches_type
from raindrop.types import GetSemanticMemoryCreateResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestGetSemanticMemory:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Raindrop) -> None:
        get_semantic_memory = client.get_semantic_memory.create(
            object_id="01jxanr45haeswhay4n0q8340y",
            smart_memory_location={
                "smartMemory": {
                    "name": "memory-name",
                    "application_name": "demo",
                    "version": "1234",
                }
            },
        )
        assert_matches_type(GetSemanticMemoryCreateResponse, get_semantic_memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Raindrop) -> None:
        response = client.get_semantic_memory.with_raw_response.create(
            object_id="01jxanr45haeswhay4n0q8340y",
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
        get_semantic_memory = response.parse()
        assert_matches_type(GetSemanticMemoryCreateResponse, get_semantic_memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Raindrop) -> None:
        with client.get_semantic_memory.with_streaming_response.create(
            object_id="01jxanr45haeswhay4n0q8340y",
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

            get_semantic_memory = response.parse()
            assert_matches_type(GetSemanticMemoryCreateResponse, get_semantic_memory, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncGetSemanticMemory:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncRaindrop) -> None:
        get_semantic_memory = await async_client.get_semantic_memory.create(
            object_id="01jxanr45haeswhay4n0q8340y",
            smart_memory_location={
                "smartMemory": {
                    "name": "memory-name",
                    "application_name": "demo",
                    "version": "1234",
                }
            },
        )
        assert_matches_type(GetSemanticMemoryCreateResponse, get_semantic_memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncRaindrop) -> None:
        response = await async_client.get_semantic_memory.with_raw_response.create(
            object_id="01jxanr45haeswhay4n0q8340y",
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
        get_semantic_memory = await response.parse()
        assert_matches_type(GetSemanticMemoryCreateResponse, get_semantic_memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncRaindrop) -> None:
        async with async_client.get_semantic_memory.with_streaming_response.create(
            object_id="01jxanr45haeswhay4n0q8340y",
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

            get_semantic_memory = await response.parse()
            assert_matches_type(GetSemanticMemoryCreateResponse, get_semantic_memory, path=["response"])

        assert cast(Any, response.is_closed) is True

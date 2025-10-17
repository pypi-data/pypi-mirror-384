# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from raindrop import Raindrop, AsyncRaindrop
from tests.utils import assert_matches_type
from raindrop.types import (
    QuerySearchResponse,
    QueryChunkSearchResponse,
    QuerySumarizePageResponse,
    QueryDocumentQueryResponse,
    LiquidmetalV1alpha1TextResult,
)
from raindrop.pagination import SyncPageNumber, AsyncPageNumber

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestQuery:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_chunk_search(self, client: Raindrop) -> None:
        query = client.query.chunk_search(
            bucket_locations=[{"bucket": {"name": "my-smartbucket"}}],
            input="Find documents about revenue in Q4 2023",
            request_id="<YOUR-REQUEST-ID>",
        )
        assert_matches_type(QueryChunkSearchResponse, query, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_chunk_search_with_all_params(self, client: Raindrop) -> None:
        query = client.query.chunk_search(
            bucket_locations=[
                {
                    "bucket": {
                        "name": "my-smartbucket",
                        "application_name": "my-app",
                        "version": "01jxanr45haeswhay4n0q8340y",
                    }
                }
            ],
            input="Find documents about revenue in Q4 2023",
            request_id="<YOUR-REQUEST-ID>",
            partition="tenant-123",
        )
        assert_matches_type(QueryChunkSearchResponse, query, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_chunk_search(self, client: Raindrop) -> None:
        response = client.query.with_raw_response.chunk_search(
            bucket_locations=[{"bucket": {"name": "my-smartbucket"}}],
            input="Find documents about revenue in Q4 2023",
            request_id="<YOUR-REQUEST-ID>",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        query = response.parse()
        assert_matches_type(QueryChunkSearchResponse, query, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_chunk_search(self, client: Raindrop) -> None:
        with client.query.with_streaming_response.chunk_search(
            bucket_locations=[{"bucket": {"name": "my-smartbucket"}}],
            input="Find documents about revenue in Q4 2023",
            request_id="<YOUR-REQUEST-ID>",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            query = response.parse()
            assert_matches_type(QueryChunkSearchResponse, query, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_document_query(self, client: Raindrop) -> None:
        query = client.query.document_query(
            bucket_location={"bucket": {"name": "my-smartbucket"}},
            input="What are the key points in this document?",
            object_id="document.pdf",
            request_id="<YOUR-REQUEST-ID>",
        )
        assert_matches_type(QueryDocumentQueryResponse, query, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_document_query_with_all_params(self, client: Raindrop) -> None:
        query = client.query.document_query(
            bucket_location={
                "bucket": {
                    "name": "my-smartbucket",
                    "application_name": "my-app",
                    "version": "01jxanr45haeswhay4n0q8340y",
                }
            },
            input="What are the key points in this document?",
            object_id="document.pdf",
            request_id="<YOUR-REQUEST-ID>",
            partition="tenant-123",
        )
        assert_matches_type(QueryDocumentQueryResponse, query, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_document_query(self, client: Raindrop) -> None:
        response = client.query.with_raw_response.document_query(
            bucket_location={"bucket": {"name": "my-smartbucket"}},
            input="What are the key points in this document?",
            object_id="document.pdf",
            request_id="<YOUR-REQUEST-ID>",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        query = response.parse()
        assert_matches_type(QueryDocumentQueryResponse, query, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_document_query(self, client: Raindrop) -> None:
        with client.query.with_streaming_response.document_query(
            bucket_location={"bucket": {"name": "my-smartbucket"}},
            input="What are the key points in this document?",
            object_id="document.pdf",
            request_id="<YOUR-REQUEST-ID>",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            query = response.parse()
            assert_matches_type(QueryDocumentQueryResponse, query, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_paginated_search(self, client: Raindrop) -> None:
        query = client.query.get_paginated_search(
            page=1,
            page_size=10,
            request_id="<YOUR-REQUEST-ID>",
        )
        assert_matches_type(SyncPageNumber[LiquidmetalV1alpha1TextResult], query, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_paginated_search_with_all_params(self, client: Raindrop) -> None:
        query = client.query.get_paginated_search(
            page=1,
            page_size=10,
            request_id="<YOUR-REQUEST-ID>",
            partition="tenant-123",
        )
        assert_matches_type(SyncPageNumber[LiquidmetalV1alpha1TextResult], query, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_paginated_search(self, client: Raindrop) -> None:
        response = client.query.with_raw_response.get_paginated_search(
            page=1,
            page_size=10,
            request_id="<YOUR-REQUEST-ID>",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        query = response.parse()
        assert_matches_type(SyncPageNumber[LiquidmetalV1alpha1TextResult], query, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_paginated_search(self, client: Raindrop) -> None:
        with client.query.with_streaming_response.get_paginated_search(
            page=1,
            page_size=10,
            request_id="<YOUR-REQUEST-ID>",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            query = response.parse()
            assert_matches_type(SyncPageNumber[LiquidmetalV1alpha1TextResult], query, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_search(self, client: Raindrop) -> None:
        query = client.query.search(
            bucket_locations=[{"bucket": {"name": "my-smartbucket"}}],
            input="All my files",
            request_id="<YOUR-REQUEST-ID>",
        )
        assert_matches_type(QuerySearchResponse, query, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_search_with_all_params(self, client: Raindrop) -> None:
        query = client.query.search(
            bucket_locations=[
                {
                    "bucket": {
                        "name": "my-smartbucket",
                        "application_name": "my-app",
                        "version": "01jxanr45haeswhay4n0q8340y",
                    }
                }
            ],
            input="All my files",
            request_id="<YOUR-REQUEST-ID>",
            partition="tenant-123",
        )
        assert_matches_type(QuerySearchResponse, query, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_search(self, client: Raindrop) -> None:
        response = client.query.with_raw_response.search(
            bucket_locations=[{"bucket": {"name": "my-smartbucket"}}],
            input="All my files",
            request_id="<YOUR-REQUEST-ID>",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        query = response.parse()
        assert_matches_type(QuerySearchResponse, query, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_search(self, client: Raindrop) -> None:
        with client.query.with_streaming_response.search(
            bucket_locations=[{"bucket": {"name": "my-smartbucket"}}],
            input="All my files",
            request_id="<YOUR-REQUEST-ID>",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            query = response.parse()
            assert_matches_type(QuerySearchResponse, query, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_sumarize_page(self, client: Raindrop) -> None:
        query = client.query.sumarize_page(
            page=1,
            page_size=10,
            request_id="<YOUR-REQUEST-ID>",
        )
        assert_matches_type(QuerySumarizePageResponse, query, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_sumarize_page_with_all_params(self, client: Raindrop) -> None:
        query = client.query.sumarize_page(
            page=1,
            page_size=10,
            request_id="<YOUR-REQUEST-ID>",
            partition="tenant-123",
        )
        assert_matches_type(QuerySumarizePageResponse, query, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_sumarize_page(self, client: Raindrop) -> None:
        response = client.query.with_raw_response.sumarize_page(
            page=1,
            page_size=10,
            request_id="<YOUR-REQUEST-ID>",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        query = response.parse()
        assert_matches_type(QuerySumarizePageResponse, query, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_sumarize_page(self, client: Raindrop) -> None:
        with client.query.with_streaming_response.sumarize_page(
            page=1,
            page_size=10,
            request_id="<YOUR-REQUEST-ID>",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            query = response.parse()
            assert_matches_type(QuerySumarizePageResponse, query, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncQuery:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_chunk_search(self, async_client: AsyncRaindrop) -> None:
        query = await async_client.query.chunk_search(
            bucket_locations=[{"bucket": {"name": "my-smartbucket"}}],
            input="Find documents about revenue in Q4 2023",
            request_id="<YOUR-REQUEST-ID>",
        )
        assert_matches_type(QueryChunkSearchResponse, query, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_chunk_search_with_all_params(self, async_client: AsyncRaindrop) -> None:
        query = await async_client.query.chunk_search(
            bucket_locations=[
                {
                    "bucket": {
                        "name": "my-smartbucket",
                        "application_name": "my-app",
                        "version": "01jxanr45haeswhay4n0q8340y",
                    }
                }
            ],
            input="Find documents about revenue in Q4 2023",
            request_id="<YOUR-REQUEST-ID>",
            partition="tenant-123",
        )
        assert_matches_type(QueryChunkSearchResponse, query, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_chunk_search(self, async_client: AsyncRaindrop) -> None:
        response = await async_client.query.with_raw_response.chunk_search(
            bucket_locations=[{"bucket": {"name": "my-smartbucket"}}],
            input="Find documents about revenue in Q4 2023",
            request_id="<YOUR-REQUEST-ID>",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        query = await response.parse()
        assert_matches_type(QueryChunkSearchResponse, query, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_chunk_search(self, async_client: AsyncRaindrop) -> None:
        async with async_client.query.with_streaming_response.chunk_search(
            bucket_locations=[{"bucket": {"name": "my-smartbucket"}}],
            input="Find documents about revenue in Q4 2023",
            request_id="<YOUR-REQUEST-ID>",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            query = await response.parse()
            assert_matches_type(QueryChunkSearchResponse, query, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_document_query(self, async_client: AsyncRaindrop) -> None:
        query = await async_client.query.document_query(
            bucket_location={"bucket": {"name": "my-smartbucket"}},
            input="What are the key points in this document?",
            object_id="document.pdf",
            request_id="<YOUR-REQUEST-ID>",
        )
        assert_matches_type(QueryDocumentQueryResponse, query, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_document_query_with_all_params(self, async_client: AsyncRaindrop) -> None:
        query = await async_client.query.document_query(
            bucket_location={
                "bucket": {
                    "name": "my-smartbucket",
                    "application_name": "my-app",
                    "version": "01jxanr45haeswhay4n0q8340y",
                }
            },
            input="What are the key points in this document?",
            object_id="document.pdf",
            request_id="<YOUR-REQUEST-ID>",
            partition="tenant-123",
        )
        assert_matches_type(QueryDocumentQueryResponse, query, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_document_query(self, async_client: AsyncRaindrop) -> None:
        response = await async_client.query.with_raw_response.document_query(
            bucket_location={"bucket": {"name": "my-smartbucket"}},
            input="What are the key points in this document?",
            object_id="document.pdf",
            request_id="<YOUR-REQUEST-ID>",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        query = await response.parse()
        assert_matches_type(QueryDocumentQueryResponse, query, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_document_query(self, async_client: AsyncRaindrop) -> None:
        async with async_client.query.with_streaming_response.document_query(
            bucket_location={"bucket": {"name": "my-smartbucket"}},
            input="What are the key points in this document?",
            object_id="document.pdf",
            request_id="<YOUR-REQUEST-ID>",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            query = await response.parse()
            assert_matches_type(QueryDocumentQueryResponse, query, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_paginated_search(self, async_client: AsyncRaindrop) -> None:
        query = await async_client.query.get_paginated_search(
            page=1,
            page_size=10,
            request_id="<YOUR-REQUEST-ID>",
        )
        assert_matches_type(AsyncPageNumber[LiquidmetalV1alpha1TextResult], query, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_paginated_search_with_all_params(self, async_client: AsyncRaindrop) -> None:
        query = await async_client.query.get_paginated_search(
            page=1,
            page_size=10,
            request_id="<YOUR-REQUEST-ID>",
            partition="tenant-123",
        )
        assert_matches_type(AsyncPageNumber[LiquidmetalV1alpha1TextResult], query, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_paginated_search(self, async_client: AsyncRaindrop) -> None:
        response = await async_client.query.with_raw_response.get_paginated_search(
            page=1,
            page_size=10,
            request_id="<YOUR-REQUEST-ID>",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        query = await response.parse()
        assert_matches_type(AsyncPageNumber[LiquidmetalV1alpha1TextResult], query, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_paginated_search(self, async_client: AsyncRaindrop) -> None:
        async with async_client.query.with_streaming_response.get_paginated_search(
            page=1,
            page_size=10,
            request_id="<YOUR-REQUEST-ID>",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            query = await response.parse()
            assert_matches_type(AsyncPageNumber[LiquidmetalV1alpha1TextResult], query, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_search(self, async_client: AsyncRaindrop) -> None:
        query = await async_client.query.search(
            bucket_locations=[{"bucket": {"name": "my-smartbucket"}}],
            input="All my files",
            request_id="<YOUR-REQUEST-ID>",
        )
        assert_matches_type(QuerySearchResponse, query, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_search_with_all_params(self, async_client: AsyncRaindrop) -> None:
        query = await async_client.query.search(
            bucket_locations=[
                {
                    "bucket": {
                        "name": "my-smartbucket",
                        "application_name": "my-app",
                        "version": "01jxanr45haeswhay4n0q8340y",
                    }
                }
            ],
            input="All my files",
            request_id="<YOUR-REQUEST-ID>",
            partition="tenant-123",
        )
        assert_matches_type(QuerySearchResponse, query, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_search(self, async_client: AsyncRaindrop) -> None:
        response = await async_client.query.with_raw_response.search(
            bucket_locations=[{"bucket": {"name": "my-smartbucket"}}],
            input="All my files",
            request_id="<YOUR-REQUEST-ID>",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        query = await response.parse()
        assert_matches_type(QuerySearchResponse, query, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_search(self, async_client: AsyncRaindrop) -> None:
        async with async_client.query.with_streaming_response.search(
            bucket_locations=[{"bucket": {"name": "my-smartbucket"}}],
            input="All my files",
            request_id="<YOUR-REQUEST-ID>",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            query = await response.parse()
            assert_matches_type(QuerySearchResponse, query, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_sumarize_page(self, async_client: AsyncRaindrop) -> None:
        query = await async_client.query.sumarize_page(
            page=1,
            page_size=10,
            request_id="<YOUR-REQUEST-ID>",
        )
        assert_matches_type(QuerySumarizePageResponse, query, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_sumarize_page_with_all_params(self, async_client: AsyncRaindrop) -> None:
        query = await async_client.query.sumarize_page(
            page=1,
            page_size=10,
            request_id="<YOUR-REQUEST-ID>",
            partition="tenant-123",
        )
        assert_matches_type(QuerySumarizePageResponse, query, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_sumarize_page(self, async_client: AsyncRaindrop) -> None:
        response = await async_client.query.with_raw_response.sumarize_page(
            page=1,
            page_size=10,
            request_id="<YOUR-REQUEST-ID>",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        query = await response.parse()
        assert_matches_type(QuerySumarizePageResponse, query, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_sumarize_page(self, async_client: AsyncRaindrop) -> None:
        async with async_client.query.with_streaming_response.sumarize_page(
            page=1,
            page_size=10,
            request_id="<YOUR-REQUEST-ID>",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            query = await response.parse()
            assert_matches_type(QuerySumarizePageResponse, query, path=["response"])

        assert cast(Any, response.is_closed) is True

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from raindrop import Raindrop, AsyncRaindrop
from tests.utils import assert_matches_type
from raindrop.types import (
    BucketGetResponse,
    BucketPutResponse,
    BucketListResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestBucket:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Raindrop) -> None:
        bucket = client.bucket.list(
            bucket_location={"bucket": {"name": "my-smartbucket"}},
        )
        assert_matches_type(BucketListResponse, bucket, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Raindrop) -> None:
        response = client.bucket.with_raw_response.list(
            bucket_location={"bucket": {"name": "my-smartbucket"}},
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        bucket = response.parse()
        assert_matches_type(BucketListResponse, bucket, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Raindrop) -> None:
        with client.bucket.with_streaming_response.list(
            bucket_location={"bucket": {"name": "my-smartbucket"}},
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            bucket = response.parse()
            assert_matches_type(BucketListResponse, bucket, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: Raindrop) -> None:
        bucket = client.bucket.delete(
            bucket_location={"bucket": {"name": "my-smartbucket"}},
            key="my-key",
        )
        assert_matches_type(object, bucket, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: Raindrop) -> None:
        response = client.bucket.with_raw_response.delete(
            bucket_location={"bucket": {"name": "my-smartbucket"}},
            key="my-key",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        bucket = response.parse()
        assert_matches_type(object, bucket, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: Raindrop) -> None:
        with client.bucket.with_streaming_response.delete(
            bucket_location={"bucket": {"name": "my-smartbucket"}},
            key="my-key",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            bucket = response.parse()
            assert_matches_type(object, bucket, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get(self, client: Raindrop) -> None:
        bucket = client.bucket.get(
            bucket_location={"bucket": {"name": "my-smartbucket"}},
            key="my-key",
        )
        assert_matches_type(BucketGetResponse, bucket, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get(self, client: Raindrop) -> None:
        response = client.bucket.with_raw_response.get(
            bucket_location={"bucket": {"name": "my-smartbucket"}},
            key="my-key",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        bucket = response.parse()
        assert_matches_type(BucketGetResponse, bucket, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get(self, client: Raindrop) -> None:
        with client.bucket.with_streaming_response.get(
            bucket_location={"bucket": {"name": "my-smartbucket"}},
            key="my-key",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            bucket = response.parse()
            assert_matches_type(BucketGetResponse, bucket, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_put(self, client: Raindrop) -> None:
        bucket = client.bucket.put(
            bucket_location={"bucket": {"name": "my-smartbucket"}},
            content="U3RhaW5sZXNzIHJvY2tz",
            content_type="application/pdf",
            key="my-key",
        )
        assert_matches_type(BucketPutResponse, bucket, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_put(self, client: Raindrop) -> None:
        response = client.bucket.with_raw_response.put(
            bucket_location={"bucket": {"name": "my-smartbucket"}},
            content="U3RhaW5sZXNzIHJvY2tz",
            content_type="application/pdf",
            key="my-key",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        bucket = response.parse()
        assert_matches_type(BucketPutResponse, bucket, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_put(self, client: Raindrop) -> None:
        with client.bucket.with_streaming_response.put(
            bucket_location={"bucket": {"name": "my-smartbucket"}},
            content="U3RhaW5sZXNzIHJvY2tz",
            content_type="application/pdf",
            key="my-key",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            bucket = response.parse()
            assert_matches_type(BucketPutResponse, bucket, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncBucket:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncRaindrop) -> None:
        bucket = await async_client.bucket.list(
            bucket_location={"bucket": {"name": "my-smartbucket"}},
        )
        assert_matches_type(BucketListResponse, bucket, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncRaindrop) -> None:
        response = await async_client.bucket.with_raw_response.list(
            bucket_location={"bucket": {"name": "my-smartbucket"}},
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        bucket = await response.parse()
        assert_matches_type(BucketListResponse, bucket, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncRaindrop) -> None:
        async with async_client.bucket.with_streaming_response.list(
            bucket_location={"bucket": {"name": "my-smartbucket"}},
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            bucket = await response.parse()
            assert_matches_type(BucketListResponse, bucket, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncRaindrop) -> None:
        bucket = await async_client.bucket.delete(
            bucket_location={"bucket": {"name": "my-smartbucket"}},
            key="my-key",
        )
        assert_matches_type(object, bucket, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncRaindrop) -> None:
        response = await async_client.bucket.with_raw_response.delete(
            bucket_location={"bucket": {"name": "my-smartbucket"}},
            key="my-key",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        bucket = await response.parse()
        assert_matches_type(object, bucket, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncRaindrop) -> None:
        async with async_client.bucket.with_streaming_response.delete(
            bucket_location={"bucket": {"name": "my-smartbucket"}},
            key="my-key",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            bucket = await response.parse()
            assert_matches_type(object, bucket, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get(self, async_client: AsyncRaindrop) -> None:
        bucket = await async_client.bucket.get(
            bucket_location={"bucket": {"name": "my-smartbucket"}},
            key="my-key",
        )
        assert_matches_type(BucketGetResponse, bucket, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get(self, async_client: AsyncRaindrop) -> None:
        response = await async_client.bucket.with_raw_response.get(
            bucket_location={"bucket": {"name": "my-smartbucket"}},
            key="my-key",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        bucket = await response.parse()
        assert_matches_type(BucketGetResponse, bucket, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get(self, async_client: AsyncRaindrop) -> None:
        async with async_client.bucket.with_streaming_response.get(
            bucket_location={"bucket": {"name": "my-smartbucket"}},
            key="my-key",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            bucket = await response.parse()
            assert_matches_type(BucketGetResponse, bucket, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_put(self, async_client: AsyncRaindrop) -> None:
        bucket = await async_client.bucket.put(
            bucket_location={"bucket": {"name": "my-smartbucket"}},
            content="U3RhaW5sZXNzIHJvY2tz",
            content_type="application/pdf",
            key="my-key",
        )
        assert_matches_type(BucketPutResponse, bucket, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_put(self, async_client: AsyncRaindrop) -> None:
        response = await async_client.bucket.with_raw_response.put(
            bucket_location={"bucket": {"name": "my-smartbucket"}},
            content="U3RhaW5sZXNzIHJvY2tz",
            content_type="application/pdf",
            key="my-key",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        bucket = await response.parse()
        assert_matches_type(BucketPutResponse, bucket, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_put(self, async_client: AsyncRaindrop) -> None:
        async with async_client.bucket.with_streaming_response.put(
            bucket_location={"bucket": {"name": "my-smartbucket"}},
            content="U3RhaW5sZXNzIHJvY2tz",
            content_type="application/pdf",
            key="my-key",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            bucket = await response.parse()
            assert_matches_type(BucketPutResponse, bucket, path=["response"])

        assert cast(Any, response.is_closed) is True

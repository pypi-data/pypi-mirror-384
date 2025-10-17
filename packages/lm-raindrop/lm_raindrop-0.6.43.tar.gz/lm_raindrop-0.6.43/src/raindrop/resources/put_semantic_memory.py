# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..types import put_semantic_memory_create_params
from .._types import Body, Query, Headers, NotGiven, not_given
from .._utils import maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options
from ..types.put_semantic_memory_create_response import PutSemanticMemoryCreateResponse

__all__ = ["PutSemanticMemoryResource", "AsyncPutSemanticMemoryResource"]


class PutSemanticMemoryResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> PutSemanticMemoryResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#accessing-raw-response-data-eg-headers
        """
        return PutSemanticMemoryResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> PutSemanticMemoryResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#with_streaming_response
        """
        return PutSemanticMemoryResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        document: str,
        smart_memory_location: put_semantic_memory_create_params.SmartMemoryLocation,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PutSemanticMemoryCreateResponse:
        """Stores a semantic memory document for long-term knowledge retrieval.

        Semantic
        memory is used for storing structured knowledge, facts, and information that can
        be searched and retrieved across different sessions.

        Args:
          document: JSON-encoded document content to store in semantic memory

          smart_memory_location: Smart memory locator for targeting the correct smart memory instance

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v1/put_semantic_memory",
            body=maybe_transform(
                {
                    "document": document,
                    "smart_memory_location": smart_memory_location,
                },
                put_semantic_memory_create_params.PutSemanticMemoryCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PutSemanticMemoryCreateResponse,
        )


class AsyncPutSemanticMemoryResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncPutSemanticMemoryResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncPutSemanticMemoryResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncPutSemanticMemoryResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#with_streaming_response
        """
        return AsyncPutSemanticMemoryResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        document: str,
        smart_memory_location: put_semantic_memory_create_params.SmartMemoryLocation,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PutSemanticMemoryCreateResponse:
        """Stores a semantic memory document for long-term knowledge retrieval.

        Semantic
        memory is used for storing structured knowledge, facts, and information that can
        be searched and retrieved across different sessions.

        Args:
          document: JSON-encoded document content to store in semantic memory

          smart_memory_location: Smart memory locator for targeting the correct smart memory instance

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v1/put_semantic_memory",
            body=await async_maybe_transform(
                {
                    "document": document,
                    "smart_memory_location": smart_memory_location,
                },
                put_semantic_memory_create_params.PutSemanticMemoryCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PutSemanticMemoryCreateResponse,
        )


class PutSemanticMemoryResourceWithRawResponse:
    def __init__(self, put_semantic_memory: PutSemanticMemoryResource) -> None:
        self._put_semantic_memory = put_semantic_memory

        self.create = to_raw_response_wrapper(
            put_semantic_memory.create,
        )


class AsyncPutSemanticMemoryResourceWithRawResponse:
    def __init__(self, put_semantic_memory: AsyncPutSemanticMemoryResource) -> None:
        self._put_semantic_memory = put_semantic_memory

        self.create = async_to_raw_response_wrapper(
            put_semantic_memory.create,
        )


class PutSemanticMemoryResourceWithStreamingResponse:
    def __init__(self, put_semantic_memory: PutSemanticMemoryResource) -> None:
        self._put_semantic_memory = put_semantic_memory

        self.create = to_streamed_response_wrapper(
            put_semantic_memory.create,
        )


class AsyncPutSemanticMemoryResourceWithStreamingResponse:
    def __init__(self, put_semantic_memory: AsyncPutSemanticMemoryResource) -> None:
        self._put_semantic_memory = put_semantic_memory

        self.create = async_to_streamed_response_wrapper(
            put_semantic_memory.create,
        )

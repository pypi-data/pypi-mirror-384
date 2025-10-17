# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..._types import Body, Query, Headers, NotGiven, not_given
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...types.query import semantic_memory_search_params
from ..._base_client import make_request_options
from ...types.query.semantic_memory_search_response import SemanticMemorySearchResponse

__all__ = ["SemanticMemoryResource", "AsyncSemanticMemoryResource"]


class SemanticMemoryResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> SemanticMemoryResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#accessing-raw-response-data-eg-headers
        """
        return SemanticMemoryResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> SemanticMemoryResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#with_streaming_response
        """
        return SemanticMemoryResourceWithStreamingResponse(self)

    def search(
        self,
        *,
        needle: str,
        smart_memory_location: semantic_memory_search_params.SmartMemoryLocation,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SemanticMemorySearchResponse:
        """Searches across semantic memory documents using natural language queries.

        Uses
        vector embeddings and semantic similarity to find relevant knowledge documents
        regardless of exact keyword matches.

        Args:
          needle: Natural language search query to find relevant documents

          smart_memory_location: Smart memory locator for targeting the correct smart memory instance

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v1/search_semantic_memory",
            body=maybe_transform(
                {
                    "needle": needle,
                    "smart_memory_location": smart_memory_location,
                },
                semantic_memory_search_params.SemanticMemorySearchParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SemanticMemorySearchResponse,
        )


class AsyncSemanticMemoryResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncSemanticMemoryResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncSemanticMemoryResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncSemanticMemoryResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#with_streaming_response
        """
        return AsyncSemanticMemoryResourceWithStreamingResponse(self)

    async def search(
        self,
        *,
        needle: str,
        smart_memory_location: semantic_memory_search_params.SmartMemoryLocation,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SemanticMemorySearchResponse:
        """Searches across semantic memory documents using natural language queries.

        Uses
        vector embeddings and semantic similarity to find relevant knowledge documents
        regardless of exact keyword matches.

        Args:
          needle: Natural language search query to find relevant documents

          smart_memory_location: Smart memory locator for targeting the correct smart memory instance

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v1/search_semantic_memory",
            body=await async_maybe_transform(
                {
                    "needle": needle,
                    "smart_memory_location": smart_memory_location,
                },
                semantic_memory_search_params.SemanticMemorySearchParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SemanticMemorySearchResponse,
        )


class SemanticMemoryResourceWithRawResponse:
    def __init__(self, semantic_memory: SemanticMemoryResource) -> None:
        self._semantic_memory = semantic_memory

        self.search = to_raw_response_wrapper(
            semantic_memory.search,
        )


class AsyncSemanticMemoryResourceWithRawResponse:
    def __init__(self, semantic_memory: AsyncSemanticMemoryResource) -> None:
        self._semantic_memory = semantic_memory

        self.search = async_to_raw_response_wrapper(
            semantic_memory.search,
        )


class SemanticMemoryResourceWithStreamingResponse:
    def __init__(self, semantic_memory: SemanticMemoryResource) -> None:
        self._semantic_memory = semantic_memory

        self.search = to_streamed_response_wrapper(
            semantic_memory.search,
        )


class AsyncSemanticMemoryResourceWithStreamingResponse:
    def __init__(self, semantic_memory: AsyncSemanticMemoryResource) -> None:
        self._semantic_memory = semantic_memory

        self.search = async_to_streamed_response_wrapper(
            semantic_memory.search,
        )

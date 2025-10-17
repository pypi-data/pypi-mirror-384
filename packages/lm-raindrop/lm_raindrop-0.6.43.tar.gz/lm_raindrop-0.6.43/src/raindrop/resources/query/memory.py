# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Optional
from datetime import datetime

import httpx

from ..._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...types.query import memory_search_params
from ..._base_client import make_request_options
from ...types.query.memory_search_response import MemorySearchResponse

__all__ = ["MemoryResource", "AsyncMemoryResource"]


class MemoryResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> MemoryResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#accessing-raw-response-data-eg-headers
        """
        return MemoryResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> MemoryResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#with_streaming_response
        """
        return MemoryResourceWithStreamingResponse(self)

    def search(
        self,
        *,
        session_id: str,
        smart_memory_location: memory_search_params.SmartMemoryLocation,
        terms: str,
        end_time: Union[str, datetime, None] | Omit = omit,
        n_most_recent: Optional[int] | Omit = omit,
        start_time: Union[str, datetime, None] | Omit = omit,
        timeline: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MemorySearchResponse:
        """
        Performs semantic search across stored memories using natural language queries.
        The system uses vector embeddings to find semantically similar content
        regardless of exact keyword matches.

        Search features:

        - Semantic similarity matching
        - Timeline-specific search
        - Temporal filtering
        - Relevance-based ranking

        Args:
          session_id: Unique session identifier for the working memory instance

          smart_memory_location: Smart memory locator for targeting the correct smart memory instance

          terms: Natural language search query

          end_time: End time for temporal filtering

          n_most_recent: Maximum number of most recent results to return

          start_time: Start time for temporal filtering

          timeline: Timeline to filter search results

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v1/search_memory",
            body=maybe_transform(
                {
                    "session_id": session_id,
                    "smart_memory_location": smart_memory_location,
                    "terms": terms,
                    "end_time": end_time,
                    "n_most_recent": n_most_recent,
                    "start_time": start_time,
                    "timeline": timeline,
                },
                memory_search_params.MemorySearchParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MemorySearchResponse,
        )


class AsyncMemoryResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncMemoryResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncMemoryResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncMemoryResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#with_streaming_response
        """
        return AsyncMemoryResourceWithStreamingResponse(self)

    async def search(
        self,
        *,
        session_id: str,
        smart_memory_location: memory_search_params.SmartMemoryLocation,
        terms: str,
        end_time: Union[str, datetime, None] | Omit = omit,
        n_most_recent: Optional[int] | Omit = omit,
        start_time: Union[str, datetime, None] | Omit = omit,
        timeline: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MemorySearchResponse:
        """
        Performs semantic search across stored memories using natural language queries.
        The system uses vector embeddings to find semantically similar content
        regardless of exact keyword matches.

        Search features:

        - Semantic similarity matching
        - Timeline-specific search
        - Temporal filtering
        - Relevance-based ranking

        Args:
          session_id: Unique session identifier for the working memory instance

          smart_memory_location: Smart memory locator for targeting the correct smart memory instance

          terms: Natural language search query

          end_time: End time for temporal filtering

          n_most_recent: Maximum number of most recent results to return

          start_time: Start time for temporal filtering

          timeline: Timeline to filter search results

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v1/search_memory",
            body=await async_maybe_transform(
                {
                    "session_id": session_id,
                    "smart_memory_location": smart_memory_location,
                    "terms": terms,
                    "end_time": end_time,
                    "n_most_recent": n_most_recent,
                    "start_time": start_time,
                    "timeline": timeline,
                },
                memory_search_params.MemorySearchParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MemorySearchResponse,
        )


class MemoryResourceWithRawResponse:
    def __init__(self, memory: MemoryResource) -> None:
        self._memory = memory

        self.search = to_raw_response_wrapper(
            memory.search,
        )


class AsyncMemoryResourceWithRawResponse:
    def __init__(self, memory: AsyncMemoryResource) -> None:
        self._memory = memory

        self.search = async_to_raw_response_wrapper(
            memory.search,
        )


class MemoryResourceWithStreamingResponse:
    def __init__(self, memory: MemoryResource) -> None:
        self._memory = memory

        self.search = to_streamed_response_wrapper(
            memory.search,
        )


class AsyncMemoryResourceWithStreamingResponse:
    def __init__(self, memory: AsyncMemoryResource) -> None:
        self._memory = memory

        self.search = async_to_streamed_response_wrapper(
            memory.search,
        )

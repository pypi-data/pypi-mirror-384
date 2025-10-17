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
from ...types.query import episodic_memory_search_params
from ..._base_client import make_request_options
from ...types.query.episodic_memory_search_response import EpisodicMemorySearchResponse

__all__ = ["EpisodicMemoryResource", "AsyncEpisodicMemoryResource"]


class EpisodicMemoryResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> EpisodicMemoryResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#accessing-raw-response-data-eg-headers
        """
        return EpisodicMemoryResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> EpisodicMemoryResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#with_streaming_response
        """
        return EpisodicMemoryResourceWithStreamingResponse(self)

    def search(
        self,
        *,
        smart_memory_location: episodic_memory_search_params.SmartMemoryLocation,
        terms: str,
        end_time: Union[str, datetime, None] | Omit = omit,
        n_most_recent: Optional[int] | Omit = omit,
        start_time: Union[str, datetime, None] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EpisodicMemorySearchResponse:
        """Searches across episodic memory documents stored in the SmartBucket.

        Allows
        finding relevant past sessions based on natural language queries. Returns
        summaries and metadata from stored episodic memory sessions.

        Args:
          smart_memory_location: Smart memory locator for targeting the correct smart memory instance

          terms: Natural language search query to find relevant episodic memory sessions

          end_time: End time for temporal filtering

          n_most_recent: Maximum number of most recent results to return

          start_time: Start time for temporal filtering

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v1/search_episodic_memory",
            body=maybe_transform(
                {
                    "smart_memory_location": smart_memory_location,
                    "terms": terms,
                    "end_time": end_time,
                    "n_most_recent": n_most_recent,
                    "start_time": start_time,
                },
                episodic_memory_search_params.EpisodicMemorySearchParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EpisodicMemorySearchResponse,
        )


class AsyncEpisodicMemoryResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncEpisodicMemoryResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncEpisodicMemoryResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncEpisodicMemoryResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#with_streaming_response
        """
        return AsyncEpisodicMemoryResourceWithStreamingResponse(self)

    async def search(
        self,
        *,
        smart_memory_location: episodic_memory_search_params.SmartMemoryLocation,
        terms: str,
        end_time: Union[str, datetime, None] | Omit = omit,
        n_most_recent: Optional[int] | Omit = omit,
        start_time: Union[str, datetime, None] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EpisodicMemorySearchResponse:
        """Searches across episodic memory documents stored in the SmartBucket.

        Allows
        finding relevant past sessions based on natural language queries. Returns
        summaries and metadata from stored episodic memory sessions.

        Args:
          smart_memory_location: Smart memory locator for targeting the correct smart memory instance

          terms: Natural language search query to find relevant episodic memory sessions

          end_time: End time for temporal filtering

          n_most_recent: Maximum number of most recent results to return

          start_time: Start time for temporal filtering

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v1/search_episodic_memory",
            body=await async_maybe_transform(
                {
                    "smart_memory_location": smart_memory_location,
                    "terms": terms,
                    "end_time": end_time,
                    "n_most_recent": n_most_recent,
                    "start_time": start_time,
                },
                episodic_memory_search_params.EpisodicMemorySearchParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EpisodicMemorySearchResponse,
        )


class EpisodicMemoryResourceWithRawResponse:
    def __init__(self, episodic_memory: EpisodicMemoryResource) -> None:
        self._episodic_memory = episodic_memory

        self.search = to_raw_response_wrapper(
            episodic_memory.search,
        )


class AsyncEpisodicMemoryResourceWithRawResponse:
    def __init__(self, episodic_memory: AsyncEpisodicMemoryResource) -> None:
        self._episodic_memory = episodic_memory

        self.search = async_to_raw_response_wrapper(
            episodic_memory.search,
        )


class EpisodicMemoryResourceWithStreamingResponse:
    def __init__(self, episodic_memory: EpisodicMemoryResource) -> None:
        self._episodic_memory = episodic_memory

        self.search = to_streamed_response_wrapper(
            episodic_memory.search,
        )


class AsyncEpisodicMemoryResourceWithStreamingResponse:
    def __init__(self, episodic_memory: AsyncEpisodicMemoryResource) -> None:
        self._episodic_memory = episodic_memory

        self.search = async_to_streamed_response_wrapper(
            episodic_memory.search,
        )

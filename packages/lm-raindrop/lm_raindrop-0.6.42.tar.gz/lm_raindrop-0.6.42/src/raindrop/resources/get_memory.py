# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Optional
from datetime import datetime

import httpx

from ..types import get_memory_retrieve_params
from .._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
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
from ..types.get_memory_retrieve_response import GetMemoryRetrieveResponse

__all__ = ["GetMemoryResource", "AsyncGetMemoryResource"]


class GetMemoryResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> GetMemoryResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#accessing-raw-response-data-eg-headers
        """
        return GetMemoryResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> GetMemoryResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#with_streaming_response
        """
        return GetMemoryResourceWithStreamingResponse(self)

    def retrieve(
        self,
        *,
        session_id: str,
        smart_memory_location: get_memory_retrieve_params.SmartMemoryLocation,
        end_time: Union[str, datetime, None] | Omit = omit,
        key: Optional[str] | Omit = omit,
        n_most_recent: Optional[int] | Omit = omit,
        start_time: Union[str, datetime, None] | Omit = omit,
        timeline: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> GetMemoryRetrieveResponse:
        """Retrieves memories based on timeline, key, or temporal criteria.

        Supports
        filtering by specific timelines, time ranges, and limiting results to the most
        recent entries.

        Query capabilities:

        - Timeline-specific retrieval
        - Key-based lookup
        - Temporal range queries
        - Most recent N entries

        Args:
          session_id: Unique session identifier for the working memory instance

          smart_memory_location: Smart memory locator for targeting the correct smart memory instance

          end_time: End time for temporal filtering

          key: Specific key to retrieve

          n_most_recent: Maximum number of most recent memories to return

          start_time: Start time for temporal filtering

          timeline: Timeline to filter memories

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v1/get_memory",
            body=maybe_transform(
                {
                    "session_id": session_id,
                    "smart_memory_location": smart_memory_location,
                    "end_time": end_time,
                    "key": key,
                    "n_most_recent": n_most_recent,
                    "start_time": start_time,
                    "timeline": timeline,
                },
                get_memory_retrieve_params.GetMemoryRetrieveParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=GetMemoryRetrieveResponse,
        )


class AsyncGetMemoryResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncGetMemoryResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncGetMemoryResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncGetMemoryResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#with_streaming_response
        """
        return AsyncGetMemoryResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        *,
        session_id: str,
        smart_memory_location: get_memory_retrieve_params.SmartMemoryLocation,
        end_time: Union[str, datetime, None] | Omit = omit,
        key: Optional[str] | Omit = omit,
        n_most_recent: Optional[int] | Omit = omit,
        start_time: Union[str, datetime, None] | Omit = omit,
        timeline: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> GetMemoryRetrieveResponse:
        """Retrieves memories based on timeline, key, or temporal criteria.

        Supports
        filtering by specific timelines, time ranges, and limiting results to the most
        recent entries.

        Query capabilities:

        - Timeline-specific retrieval
        - Key-based lookup
        - Temporal range queries
        - Most recent N entries

        Args:
          session_id: Unique session identifier for the working memory instance

          smart_memory_location: Smart memory locator for targeting the correct smart memory instance

          end_time: End time for temporal filtering

          key: Specific key to retrieve

          n_most_recent: Maximum number of most recent memories to return

          start_time: Start time for temporal filtering

          timeline: Timeline to filter memories

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v1/get_memory",
            body=await async_maybe_transform(
                {
                    "session_id": session_id,
                    "smart_memory_location": smart_memory_location,
                    "end_time": end_time,
                    "key": key,
                    "n_most_recent": n_most_recent,
                    "start_time": start_time,
                    "timeline": timeline,
                },
                get_memory_retrieve_params.GetMemoryRetrieveParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=GetMemoryRetrieveResponse,
        )


class GetMemoryResourceWithRawResponse:
    def __init__(self, get_memory: GetMemoryResource) -> None:
        self._get_memory = get_memory

        self.retrieve = to_raw_response_wrapper(
            get_memory.retrieve,
        )


class AsyncGetMemoryResourceWithRawResponse:
    def __init__(self, get_memory: AsyncGetMemoryResource) -> None:
        self._get_memory = get_memory

        self.retrieve = async_to_raw_response_wrapper(
            get_memory.retrieve,
        )


class GetMemoryResourceWithStreamingResponse:
    def __init__(self, get_memory: GetMemoryResource) -> None:
        self._get_memory = get_memory

        self.retrieve = to_streamed_response_wrapper(
            get_memory.retrieve,
        )


class AsyncGetMemoryResourceWithStreamingResponse:
    def __init__(self, get_memory: AsyncGetMemoryResource) -> None:
        self._get_memory = get_memory

        self.retrieve = async_to_streamed_response_wrapper(
            get_memory.retrieve,
        )

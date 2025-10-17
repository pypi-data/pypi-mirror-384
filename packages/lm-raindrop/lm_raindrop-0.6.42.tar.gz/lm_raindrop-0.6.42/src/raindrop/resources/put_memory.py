# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional

import httpx

from ..types import put_memory_create_params
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
from ..types.put_memory_create_response import PutMemoryCreateResponse

__all__ = ["PutMemoryResource", "AsyncPutMemoryResource"]


class PutMemoryResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> PutMemoryResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#accessing-raw-response-data-eg-headers
        """
        return PutMemoryResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> PutMemoryResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#with_streaming_response
        """
        return PutMemoryResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        content: str,
        session_id: str,
        smart_memory_location: put_memory_create_params.SmartMemoryLocation,
        agent: Optional[str] | Omit = omit,
        key: Optional[str] | Omit = omit,
        timeline: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PutMemoryCreateResponse:
        """Stores a new memory entry in the agent's working memory.

        Memories are organized
        by timeline and can include contextual information like the agent responsible
        and triggering events.

        The system will:

        - Store the memory with automatic timestamping
        - Generate embeddings for semantic search
        - Associate the memory with the specified timeline
        - Enable future retrieval and search operations

        Args:
          content: The actual memory content to store

          session_id: Unique session identifier for the working memory instance

          smart_memory_location: Smart memory locator for targeting the correct smart memory instance

          agent: Agent identifier responsible for this memory

          key: Optional key for direct memory retrieval

          timeline: Timeline identifier for organizing related memories

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v1/put_memory",
            body=maybe_transform(
                {
                    "content": content,
                    "session_id": session_id,
                    "smart_memory_location": smart_memory_location,
                    "agent": agent,
                    "key": key,
                    "timeline": timeline,
                },
                put_memory_create_params.PutMemoryCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PutMemoryCreateResponse,
        )


class AsyncPutMemoryResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncPutMemoryResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncPutMemoryResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncPutMemoryResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#with_streaming_response
        """
        return AsyncPutMemoryResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        content: str,
        session_id: str,
        smart_memory_location: put_memory_create_params.SmartMemoryLocation,
        agent: Optional[str] | Omit = omit,
        key: Optional[str] | Omit = omit,
        timeline: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PutMemoryCreateResponse:
        """Stores a new memory entry in the agent's working memory.

        Memories are organized
        by timeline and can include contextual information like the agent responsible
        and triggering events.

        The system will:

        - Store the memory with automatic timestamping
        - Generate embeddings for semantic search
        - Associate the memory with the specified timeline
        - Enable future retrieval and search operations

        Args:
          content: The actual memory content to store

          session_id: Unique session identifier for the working memory instance

          smart_memory_location: Smart memory locator for targeting the correct smart memory instance

          agent: Agent identifier responsible for this memory

          key: Optional key for direct memory retrieval

          timeline: Timeline identifier for organizing related memories

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v1/put_memory",
            body=await async_maybe_transform(
                {
                    "content": content,
                    "session_id": session_id,
                    "smart_memory_location": smart_memory_location,
                    "agent": agent,
                    "key": key,
                    "timeline": timeline,
                },
                put_memory_create_params.PutMemoryCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PutMemoryCreateResponse,
        )


class PutMemoryResourceWithRawResponse:
    def __init__(self, put_memory: PutMemoryResource) -> None:
        self._put_memory = put_memory

        self.create = to_raw_response_wrapper(
            put_memory.create,
        )


class AsyncPutMemoryResourceWithRawResponse:
    def __init__(self, put_memory: AsyncPutMemoryResource) -> None:
        self._put_memory = put_memory

        self.create = async_to_raw_response_wrapper(
            put_memory.create,
        )


class PutMemoryResourceWithStreamingResponse:
    def __init__(self, put_memory: PutMemoryResource) -> None:
        self._put_memory = put_memory

        self.create = to_streamed_response_wrapper(
            put_memory.create,
        )


class AsyncPutMemoryResourceWithStreamingResponse:
    def __init__(self, put_memory: AsyncPutMemoryResource) -> None:
        self._put_memory = put_memory

        self.create = async_to_streamed_response_wrapper(
            put_memory.create,
        )

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional

import httpx

from ..types import summarize_memory_create_params
from .._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
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
from ..types.summarize_memory_create_response import SummarizeMemoryCreateResponse

__all__ = ["SummarizeMemoryResource", "AsyncSummarizeMemoryResource"]


class SummarizeMemoryResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> SummarizeMemoryResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#accessing-raw-response-data-eg-headers
        """
        return SummarizeMemoryResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> SummarizeMemoryResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#with_streaming_response
        """
        return SummarizeMemoryResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        memory_ids: SequenceNotStr[str],
        session_id: str,
        smart_memory_location: summarize_memory_create_params.SmartMemoryLocation,
        system_prompt: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SummarizeMemoryCreateResponse:
        """Generates intelligent summaries of a collection of memories using AI.

        Can
        optionally accept custom system prompts to guide the summarization style.

        The summarization system:

        - Identifies key themes and patterns
        - Extracts important events and decisions
        - Maintains temporal context
        - Supports custom summarization instructions

        Args:
          memory_ids: List of memory IDs to summarize

          session_id: Unique session identifier for the working memory instance

          smart_memory_location: Smart memory locator for targeting the correct smart memory instance

          system_prompt: Optional custom system prompt for summarization

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v1/summarize_memory",
            body=maybe_transform(
                {
                    "memory_ids": memory_ids,
                    "session_id": session_id,
                    "smart_memory_location": smart_memory_location,
                    "system_prompt": system_prompt,
                },
                summarize_memory_create_params.SummarizeMemoryCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SummarizeMemoryCreateResponse,
        )


class AsyncSummarizeMemoryResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncSummarizeMemoryResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncSummarizeMemoryResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncSummarizeMemoryResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#with_streaming_response
        """
        return AsyncSummarizeMemoryResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        memory_ids: SequenceNotStr[str],
        session_id: str,
        smart_memory_location: summarize_memory_create_params.SmartMemoryLocation,
        system_prompt: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SummarizeMemoryCreateResponse:
        """Generates intelligent summaries of a collection of memories using AI.

        Can
        optionally accept custom system prompts to guide the summarization style.

        The summarization system:

        - Identifies key themes and patterns
        - Extracts important events and decisions
        - Maintains temporal context
        - Supports custom summarization instructions

        Args:
          memory_ids: List of memory IDs to summarize

          session_id: Unique session identifier for the working memory instance

          smart_memory_location: Smart memory locator for targeting the correct smart memory instance

          system_prompt: Optional custom system prompt for summarization

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v1/summarize_memory",
            body=await async_maybe_transform(
                {
                    "memory_ids": memory_ids,
                    "session_id": session_id,
                    "smart_memory_location": smart_memory_location,
                    "system_prompt": system_prompt,
                },
                summarize_memory_create_params.SummarizeMemoryCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SummarizeMemoryCreateResponse,
        )


class SummarizeMemoryResourceWithRawResponse:
    def __init__(self, summarize_memory: SummarizeMemoryResource) -> None:
        self._summarize_memory = summarize_memory

        self.create = to_raw_response_wrapper(
            summarize_memory.create,
        )


class AsyncSummarizeMemoryResourceWithRawResponse:
    def __init__(self, summarize_memory: AsyncSummarizeMemoryResource) -> None:
        self._summarize_memory = summarize_memory

        self.create = async_to_raw_response_wrapper(
            summarize_memory.create,
        )


class SummarizeMemoryResourceWithStreamingResponse:
    def __init__(self, summarize_memory: SummarizeMemoryResource) -> None:
        self._summarize_memory = summarize_memory

        self.create = to_streamed_response_wrapper(
            summarize_memory.create,
        )


class AsyncSummarizeMemoryResourceWithStreamingResponse:
    def __init__(self, summarize_memory: AsyncSummarizeMemoryResource) -> None:
        self._summarize_memory = summarize_memory

        self.create = async_to_streamed_response_wrapper(
            summarize_memory.create,
        )

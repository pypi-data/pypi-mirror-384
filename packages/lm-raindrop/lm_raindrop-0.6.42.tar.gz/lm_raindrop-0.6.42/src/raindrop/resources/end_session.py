# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional

import httpx

from ..types import end_session_create_params
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
from ..types.end_session_create_response import EndSessionCreateResponse

__all__ = ["EndSessionResource", "AsyncEndSessionResource"]


class EndSessionResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> EndSessionResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#accessing-raw-response-data-eg-headers
        """
        return EndSessionResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> EndSessionResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#with_streaming_response
        """
        return EndSessionResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        session_id: str,
        smart_memory_location: end_session_create_params.SmartMemoryLocation,
        flush: Optional[bool] | Omit = omit,
        system_prompt: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EndSessionCreateResponse:
        """
        Ends a working memory session, optionally flushing working memory to long-term
        storage. When flush is enabled, important memories are processed and stored for
        future retrieval.

        Args:
          session_id: Unique session identifier to end

          smart_memory_location: Smart memory locator for targeting the correct smart memory instance

          flush: Whether to flush working memory to long-term storage

          system_prompt: Optional custom system prompt for memory summarization during flush

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v1/end_session",
            body=maybe_transform(
                {
                    "session_id": session_id,
                    "smart_memory_location": smart_memory_location,
                    "flush": flush,
                    "system_prompt": system_prompt,
                },
                end_session_create_params.EndSessionCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EndSessionCreateResponse,
        )


class AsyncEndSessionResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncEndSessionResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncEndSessionResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncEndSessionResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#with_streaming_response
        """
        return AsyncEndSessionResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        session_id: str,
        smart_memory_location: end_session_create_params.SmartMemoryLocation,
        flush: Optional[bool] | Omit = omit,
        system_prompt: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EndSessionCreateResponse:
        """
        Ends a working memory session, optionally flushing working memory to long-term
        storage. When flush is enabled, important memories are processed and stored for
        future retrieval.

        Args:
          session_id: Unique session identifier to end

          smart_memory_location: Smart memory locator for targeting the correct smart memory instance

          flush: Whether to flush working memory to long-term storage

          system_prompt: Optional custom system prompt for memory summarization during flush

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v1/end_session",
            body=await async_maybe_transform(
                {
                    "session_id": session_id,
                    "smart_memory_location": smart_memory_location,
                    "flush": flush,
                    "system_prompt": system_prompt,
                },
                end_session_create_params.EndSessionCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EndSessionCreateResponse,
        )


class EndSessionResourceWithRawResponse:
    def __init__(self, end_session: EndSessionResource) -> None:
        self._end_session = end_session

        self.create = to_raw_response_wrapper(
            end_session.create,
        )


class AsyncEndSessionResourceWithRawResponse:
    def __init__(self, end_session: AsyncEndSessionResource) -> None:
        self._end_session = end_session

        self.create = async_to_raw_response_wrapper(
            end_session.create,
        )


class EndSessionResourceWithStreamingResponse:
    def __init__(self, end_session: EndSessionResource) -> None:
        self._end_session = end_session

        self.create = to_streamed_response_wrapper(
            end_session.create,
        )


class AsyncEndSessionResourceWithStreamingResponse:
    def __init__(self, end_session: AsyncEndSessionResource) -> None:
        self._end_session = end_session

        self.create = async_to_streamed_response_wrapper(
            end_session.create,
        )

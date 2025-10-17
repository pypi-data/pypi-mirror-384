# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..types import start_session_create_params
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
from ..types.start_session_create_response import StartSessionCreateResponse

__all__ = ["StartSessionResource", "AsyncStartSessionResource"]


class StartSessionResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> StartSessionResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#accessing-raw-response-data-eg-headers
        """
        return StartSessionResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> StartSessionResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#with_streaming_response
        """
        return StartSessionResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        smart_memory_location: start_session_create_params.SmartMemoryLocation,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> StartSessionCreateResponse:
        """Starts a new working memory session for an agent.

        Each session provides isolated
        memory operations and automatic cleanup capabilities.

        Args:
          smart_memory_location: Smart memory locator for targeting the correct smart memory instance

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v1/start_session",
            body=maybe_transform(
                {"smart_memory_location": smart_memory_location}, start_session_create_params.StartSessionCreateParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StartSessionCreateResponse,
        )


class AsyncStartSessionResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncStartSessionResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncStartSessionResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncStartSessionResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#with_streaming_response
        """
        return AsyncStartSessionResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        smart_memory_location: start_session_create_params.SmartMemoryLocation,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> StartSessionCreateResponse:
        """Starts a new working memory session for an agent.

        Each session provides isolated
        memory operations and automatic cleanup capabilities.

        Args:
          smart_memory_location: Smart memory locator for targeting the correct smart memory instance

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v1/start_session",
            body=await async_maybe_transform(
                {"smart_memory_location": smart_memory_location}, start_session_create_params.StartSessionCreateParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StartSessionCreateResponse,
        )


class StartSessionResourceWithRawResponse:
    def __init__(self, start_session: StartSessionResource) -> None:
        self._start_session = start_session

        self.create = to_raw_response_wrapper(
            start_session.create,
        )


class AsyncStartSessionResourceWithRawResponse:
    def __init__(self, start_session: AsyncStartSessionResource) -> None:
        self._start_session = start_session

        self.create = async_to_raw_response_wrapper(
            start_session.create,
        )


class StartSessionResourceWithStreamingResponse:
    def __init__(self, start_session: StartSessionResource) -> None:
        self._start_session = start_session

        self.create = to_streamed_response_wrapper(
            start_session.create,
        )


class AsyncStartSessionResourceWithStreamingResponse:
    def __init__(self, start_session: AsyncStartSessionResource) -> None:
        self._start_session = start_session

        self.create = async_to_streamed_response_wrapper(
            start_session.create,
        )

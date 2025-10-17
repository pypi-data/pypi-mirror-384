# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional

import httpx

from ..types import rehydrate_session_rehydrate_params
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
from ..types.rehydrate_session_rehydrate_response import RehydrateSessionRehydrateResponse

__all__ = ["RehydrateSessionResource", "AsyncRehydrateSessionResource"]


class RehydrateSessionResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> RehydrateSessionResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#accessing-raw-response-data-eg-headers
        """
        return RehydrateSessionResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> RehydrateSessionResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#with_streaming_response
        """
        return RehydrateSessionResourceWithStreamingResponse(self)

    def rehydrate(
        self,
        *,
        session_id: str,
        smart_memory_location: rehydrate_session_rehydrate_params.SmartMemoryLocation,
        summary_only: Optional[bool] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RehydrateSessionRehydrateResponse:
        """Rehydrates a previous session from episodic memory storage.

        Allows resuming work
        from where a previous session left off by restoring either all memories or just
        a summary of the previous session.

        Args:
          session_id: Session identifier to restore from episodic memory

          smart_memory_location: Smart memory locator for targeting the correct smart memory instance

          summary_only: If true, only restore a summary. If false, restore all memories

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v1/rehydrate_session",
            body=maybe_transform(
                {
                    "session_id": session_id,
                    "smart_memory_location": smart_memory_location,
                    "summary_only": summary_only,
                },
                rehydrate_session_rehydrate_params.RehydrateSessionRehydrateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RehydrateSessionRehydrateResponse,
        )


class AsyncRehydrateSessionResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncRehydrateSessionResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncRehydrateSessionResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncRehydrateSessionResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#with_streaming_response
        """
        return AsyncRehydrateSessionResourceWithStreamingResponse(self)

    async def rehydrate(
        self,
        *,
        session_id: str,
        smart_memory_location: rehydrate_session_rehydrate_params.SmartMemoryLocation,
        summary_only: Optional[bool] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RehydrateSessionRehydrateResponse:
        """Rehydrates a previous session from episodic memory storage.

        Allows resuming work
        from where a previous session left off by restoring either all memories or just
        a summary of the previous session.

        Args:
          session_id: Session identifier to restore from episodic memory

          smart_memory_location: Smart memory locator for targeting the correct smart memory instance

          summary_only: If true, only restore a summary. If false, restore all memories

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v1/rehydrate_session",
            body=await async_maybe_transform(
                {
                    "session_id": session_id,
                    "smart_memory_location": smart_memory_location,
                    "summary_only": summary_only,
                },
                rehydrate_session_rehydrate_params.RehydrateSessionRehydrateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RehydrateSessionRehydrateResponse,
        )


class RehydrateSessionResourceWithRawResponse:
    def __init__(self, rehydrate_session: RehydrateSessionResource) -> None:
        self._rehydrate_session = rehydrate_session

        self.rehydrate = to_raw_response_wrapper(
            rehydrate_session.rehydrate,
        )


class AsyncRehydrateSessionResourceWithRawResponse:
    def __init__(self, rehydrate_session: AsyncRehydrateSessionResource) -> None:
        self._rehydrate_session = rehydrate_session

        self.rehydrate = async_to_raw_response_wrapper(
            rehydrate_session.rehydrate,
        )


class RehydrateSessionResourceWithStreamingResponse:
    def __init__(self, rehydrate_session: RehydrateSessionResource) -> None:
        self._rehydrate_session = rehydrate_session

        self.rehydrate = to_streamed_response_wrapper(
            rehydrate_session.rehydrate,
        )


class AsyncRehydrateSessionResourceWithStreamingResponse:
    def __init__(self, rehydrate_session: AsyncRehydrateSessionResource) -> None:
        self._rehydrate_session = rehydrate_session

        self.rehydrate = async_to_streamed_response_wrapper(
            rehydrate_session.rehydrate,
        )

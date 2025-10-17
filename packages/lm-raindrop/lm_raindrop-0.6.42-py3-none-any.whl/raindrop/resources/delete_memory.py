# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..types import delete_memory_create_params
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
from ..types.delete_memory_create_response import DeleteMemoryCreateResponse

__all__ = ["DeleteMemoryResource", "AsyncDeleteMemoryResource"]


class DeleteMemoryResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> DeleteMemoryResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#accessing-raw-response-data-eg-headers
        """
        return DeleteMemoryResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> DeleteMemoryResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#with_streaming_response
        """
        return DeleteMemoryResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        memory_id: str,
        session_id: str,
        smart_memory_location: delete_memory_create_params.SmartMemoryLocation,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DeleteMemoryCreateResponse:
        """Removes a specific memory entry from storage.

        This operation is permanent and
        cannot be undone.

        Args:
          memory_id: Unique identifier of the memory entry to delete

          session_id: Unique session identifier for the working memory instance

          smart_memory_location: Smart memory locator for targeting the correct smart memory instance

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v1/delete_memory",
            body=maybe_transform(
                {
                    "memory_id": memory_id,
                    "session_id": session_id,
                    "smart_memory_location": smart_memory_location,
                },
                delete_memory_create_params.DeleteMemoryCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DeleteMemoryCreateResponse,
        )


class AsyncDeleteMemoryResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncDeleteMemoryResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncDeleteMemoryResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncDeleteMemoryResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#with_streaming_response
        """
        return AsyncDeleteMemoryResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        memory_id: str,
        session_id: str,
        smart_memory_location: delete_memory_create_params.SmartMemoryLocation,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DeleteMemoryCreateResponse:
        """Removes a specific memory entry from storage.

        This operation is permanent and
        cannot be undone.

        Args:
          memory_id: Unique identifier of the memory entry to delete

          session_id: Unique session identifier for the working memory instance

          smart_memory_location: Smart memory locator for targeting the correct smart memory instance

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v1/delete_memory",
            body=await async_maybe_transform(
                {
                    "memory_id": memory_id,
                    "session_id": session_id,
                    "smart_memory_location": smart_memory_location,
                },
                delete_memory_create_params.DeleteMemoryCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DeleteMemoryCreateResponse,
        )


class DeleteMemoryResourceWithRawResponse:
    def __init__(self, delete_memory: DeleteMemoryResource) -> None:
        self._delete_memory = delete_memory

        self.create = to_raw_response_wrapper(
            delete_memory.create,
        )


class AsyncDeleteMemoryResourceWithRawResponse:
    def __init__(self, delete_memory: AsyncDeleteMemoryResource) -> None:
        self._delete_memory = delete_memory

        self.create = async_to_raw_response_wrapper(
            delete_memory.create,
        )


class DeleteMemoryResourceWithStreamingResponse:
    def __init__(self, delete_memory: DeleteMemoryResource) -> None:
        self._delete_memory = delete_memory

        self.create = to_streamed_response_wrapper(
            delete_memory.create,
        )


class AsyncDeleteMemoryResourceWithStreamingResponse:
    def __init__(self, delete_memory: AsyncDeleteMemoryResource) -> None:
        self._delete_memory = delete_memory

        self.create = async_to_streamed_response_wrapper(
            delete_memory.create,
        )

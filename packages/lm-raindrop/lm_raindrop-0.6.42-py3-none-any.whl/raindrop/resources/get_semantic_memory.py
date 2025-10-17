# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..types import get_semantic_memory_create_params
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
from ..types.get_semantic_memory_create_response import GetSemanticMemoryCreateResponse

__all__ = ["GetSemanticMemoryResource", "AsyncGetSemanticMemoryResource"]


class GetSemanticMemoryResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> GetSemanticMemoryResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#accessing-raw-response-data-eg-headers
        """
        return GetSemanticMemoryResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> GetSemanticMemoryResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#with_streaming_response
        """
        return GetSemanticMemoryResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        object_id: str,
        smart_memory_location: get_semantic_memory_create_params.SmartMemoryLocation,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> GetSemanticMemoryCreateResponse:
        """Retrieves a specific semantic memory document by its object ID.

        Returns the
        complete document with all its stored properties and metadata.

        Args:
          object_id: Unique object identifier of the document to retrieve

          smart_memory_location: Smart memory locator for targeting the correct smart memory instance

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v1/get_semantic_memory",
            body=maybe_transform(
                {
                    "object_id": object_id,
                    "smart_memory_location": smart_memory_location,
                },
                get_semantic_memory_create_params.GetSemanticMemoryCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=GetSemanticMemoryCreateResponse,
        )


class AsyncGetSemanticMemoryResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncGetSemanticMemoryResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncGetSemanticMemoryResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncGetSemanticMemoryResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#with_streaming_response
        """
        return AsyncGetSemanticMemoryResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        object_id: str,
        smart_memory_location: get_semantic_memory_create_params.SmartMemoryLocation,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> GetSemanticMemoryCreateResponse:
        """Retrieves a specific semantic memory document by its object ID.

        Returns the
        complete document with all its stored properties and metadata.

        Args:
          object_id: Unique object identifier of the document to retrieve

          smart_memory_location: Smart memory locator for targeting the correct smart memory instance

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v1/get_semantic_memory",
            body=await async_maybe_transform(
                {
                    "object_id": object_id,
                    "smart_memory_location": smart_memory_location,
                },
                get_semantic_memory_create_params.GetSemanticMemoryCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=GetSemanticMemoryCreateResponse,
        )


class GetSemanticMemoryResourceWithRawResponse:
    def __init__(self, get_semantic_memory: GetSemanticMemoryResource) -> None:
        self._get_semantic_memory = get_semantic_memory

        self.create = to_raw_response_wrapper(
            get_semantic_memory.create,
        )


class AsyncGetSemanticMemoryResourceWithRawResponse:
    def __init__(self, get_semantic_memory: AsyncGetSemanticMemoryResource) -> None:
        self._get_semantic_memory = get_semantic_memory

        self.create = async_to_raw_response_wrapper(
            get_semantic_memory.create,
        )


class GetSemanticMemoryResourceWithStreamingResponse:
    def __init__(self, get_semantic_memory: GetSemanticMemoryResource) -> None:
        self._get_semantic_memory = get_semantic_memory

        self.create = to_streamed_response_wrapper(
            get_semantic_memory.create,
        )


class AsyncGetSemanticMemoryResourceWithStreamingResponse:
    def __init__(self, get_semantic_memory: AsyncGetSemanticMemoryResource) -> None:
        self._get_semantic_memory = get_semantic_memory

        self.create = async_to_streamed_response_wrapper(
            get_semantic_memory.create,
        )

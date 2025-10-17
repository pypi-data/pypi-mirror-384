# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..types import delete_semantic_memory_delete_params
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
from ..types.delete_semantic_memory_delete_response import DeleteSemanticMemoryDeleteResponse

__all__ = ["DeleteSemanticMemoryResource", "AsyncDeleteSemanticMemoryResource"]


class DeleteSemanticMemoryResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> DeleteSemanticMemoryResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#accessing-raw-response-data-eg-headers
        """
        return DeleteSemanticMemoryResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> DeleteSemanticMemoryResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#with_streaming_response
        """
        return DeleteSemanticMemoryResourceWithStreamingResponse(self)

    def delete(
        self,
        *,
        object_id: str,
        smart_memory_location: delete_semantic_memory_delete_params.SmartMemoryLocation,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DeleteSemanticMemoryDeleteResponse:
        """Removes a specific semantic memory document by its object ID.

        This operation
        permanently deletes the document and is irreversible.

        Args:
          object_id: Unique object identifier of the document to delete

          smart_memory_location: Smart memory locator for targeting the correct smart memory instance

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v1/delete_semantic_memory",
            body=maybe_transform(
                {
                    "object_id": object_id,
                    "smart_memory_location": smart_memory_location,
                },
                delete_semantic_memory_delete_params.DeleteSemanticMemoryDeleteParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DeleteSemanticMemoryDeleteResponse,
        )


class AsyncDeleteSemanticMemoryResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncDeleteSemanticMemoryResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncDeleteSemanticMemoryResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncDeleteSemanticMemoryResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#with_streaming_response
        """
        return AsyncDeleteSemanticMemoryResourceWithStreamingResponse(self)

    async def delete(
        self,
        *,
        object_id: str,
        smart_memory_location: delete_semantic_memory_delete_params.SmartMemoryLocation,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DeleteSemanticMemoryDeleteResponse:
        """Removes a specific semantic memory document by its object ID.

        This operation
        permanently deletes the document and is irreversible.

        Args:
          object_id: Unique object identifier of the document to delete

          smart_memory_location: Smart memory locator for targeting the correct smart memory instance

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v1/delete_semantic_memory",
            body=await async_maybe_transform(
                {
                    "object_id": object_id,
                    "smart_memory_location": smart_memory_location,
                },
                delete_semantic_memory_delete_params.DeleteSemanticMemoryDeleteParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DeleteSemanticMemoryDeleteResponse,
        )


class DeleteSemanticMemoryResourceWithRawResponse:
    def __init__(self, delete_semantic_memory: DeleteSemanticMemoryResource) -> None:
        self._delete_semantic_memory = delete_semantic_memory

        self.delete = to_raw_response_wrapper(
            delete_semantic_memory.delete,
        )


class AsyncDeleteSemanticMemoryResourceWithRawResponse:
    def __init__(self, delete_semantic_memory: AsyncDeleteSemanticMemoryResource) -> None:
        self._delete_semantic_memory = delete_semantic_memory

        self.delete = async_to_raw_response_wrapper(
            delete_semantic_memory.delete,
        )


class DeleteSemanticMemoryResourceWithStreamingResponse:
    def __init__(self, delete_semantic_memory: DeleteSemanticMemoryResource) -> None:
        self._delete_semantic_memory = delete_semantic_memory

        self.delete = to_streamed_response_wrapper(
            delete_semantic_memory.delete,
        )


class AsyncDeleteSemanticMemoryResourceWithStreamingResponse:
    def __init__(self, delete_semantic_memory: AsyncDeleteSemanticMemoryResource) -> None:
        self._delete_semantic_memory = delete_semantic_memory

        self.delete = async_to_streamed_response_wrapper(
            delete_semantic_memory.delete,
        )

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional

import httpx

from ..types import delete_procedure_create_params
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
from ..types.delete_procedure_create_response import DeleteProcedureCreateResponse

__all__ = ["DeleteProcedureResource", "AsyncDeleteProcedureResource"]


class DeleteProcedureResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> DeleteProcedureResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#accessing-raw-response-data-eg-headers
        """
        return DeleteProcedureResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> DeleteProcedureResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#with_streaming_response
        """
        return DeleteProcedureResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        key: str,
        smart_memory_location: delete_procedure_create_params.SmartMemoryLocation,
        procedural_memory_id: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DeleteProcedureCreateResponse:
        """Removes a specific procedure from procedural memory.

        This operation is permanent
        and affects all future sessions.

        Args:
          key: Unique key of the procedure to delete

          smart_memory_location: Smart memory locator for targeting the correct smart memory instance

          procedural_memory_id: Optional procedural memory ID to use for actor isolation

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v1/delete_procedure",
            body=maybe_transform(
                {
                    "key": key,
                    "smart_memory_location": smart_memory_location,
                    "procedural_memory_id": procedural_memory_id,
                },
                delete_procedure_create_params.DeleteProcedureCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DeleteProcedureCreateResponse,
        )


class AsyncDeleteProcedureResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncDeleteProcedureResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncDeleteProcedureResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncDeleteProcedureResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#with_streaming_response
        """
        return AsyncDeleteProcedureResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        key: str,
        smart_memory_location: delete_procedure_create_params.SmartMemoryLocation,
        procedural_memory_id: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DeleteProcedureCreateResponse:
        """Removes a specific procedure from procedural memory.

        This operation is permanent
        and affects all future sessions.

        Args:
          key: Unique key of the procedure to delete

          smart_memory_location: Smart memory locator for targeting the correct smart memory instance

          procedural_memory_id: Optional procedural memory ID to use for actor isolation

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v1/delete_procedure",
            body=await async_maybe_transform(
                {
                    "key": key,
                    "smart_memory_location": smart_memory_location,
                    "procedural_memory_id": procedural_memory_id,
                },
                delete_procedure_create_params.DeleteProcedureCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DeleteProcedureCreateResponse,
        )


class DeleteProcedureResourceWithRawResponse:
    def __init__(self, delete_procedure: DeleteProcedureResource) -> None:
        self._delete_procedure = delete_procedure

        self.create = to_raw_response_wrapper(
            delete_procedure.create,
        )


class AsyncDeleteProcedureResourceWithRawResponse:
    def __init__(self, delete_procedure: AsyncDeleteProcedureResource) -> None:
        self._delete_procedure = delete_procedure

        self.create = async_to_raw_response_wrapper(
            delete_procedure.create,
        )


class DeleteProcedureResourceWithStreamingResponse:
    def __init__(self, delete_procedure: DeleteProcedureResource) -> None:
        self._delete_procedure = delete_procedure

        self.create = to_streamed_response_wrapper(
            delete_procedure.create,
        )


class AsyncDeleteProcedureResourceWithStreamingResponse:
    def __init__(self, delete_procedure: AsyncDeleteProcedureResource) -> None:
        self._delete_procedure = delete_procedure

        self.create = async_to_streamed_response_wrapper(
            delete_procedure.create,
        )

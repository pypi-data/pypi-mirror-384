# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional

import httpx

from ..types import get_procedure_create_params
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
from ..types.get_procedure_create_response import GetProcedureCreateResponse

__all__ = ["GetProcedureResource", "AsyncGetProcedureResource"]


class GetProcedureResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> GetProcedureResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#accessing-raw-response-data-eg-headers
        """
        return GetProcedureResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> GetProcedureResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#with_streaming_response
        """
        return GetProcedureResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        key: str,
        smart_memory_location: get_procedure_create_params.SmartMemoryLocation,
        procedural_memory_id: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> GetProcedureCreateResponse:
        """Retrieves a specific procedure by key from procedural memory.

        Procedures are
        persistent knowledge artifacts that remain available across all sessions and can
        be shared between different agent instances.

        Args:
          key: Unique key of the procedure to retrieve

          smart_memory_location: Smart memory locator for targeting the correct smart memory instance

          procedural_memory_id: Optional procedural memory ID to use for actor isolation

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v1/get_procedure",
            body=maybe_transform(
                {
                    "key": key,
                    "smart_memory_location": smart_memory_location,
                    "procedural_memory_id": procedural_memory_id,
                },
                get_procedure_create_params.GetProcedureCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=GetProcedureCreateResponse,
        )


class AsyncGetProcedureResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncGetProcedureResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncGetProcedureResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncGetProcedureResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#with_streaming_response
        """
        return AsyncGetProcedureResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        key: str,
        smart_memory_location: get_procedure_create_params.SmartMemoryLocation,
        procedural_memory_id: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> GetProcedureCreateResponse:
        """Retrieves a specific procedure by key from procedural memory.

        Procedures are
        persistent knowledge artifacts that remain available across all sessions and can
        be shared between different agent instances.

        Args:
          key: Unique key of the procedure to retrieve

          smart_memory_location: Smart memory locator for targeting the correct smart memory instance

          procedural_memory_id: Optional procedural memory ID to use for actor isolation

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v1/get_procedure",
            body=await async_maybe_transform(
                {
                    "key": key,
                    "smart_memory_location": smart_memory_location,
                    "procedural_memory_id": procedural_memory_id,
                },
                get_procedure_create_params.GetProcedureCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=GetProcedureCreateResponse,
        )


class GetProcedureResourceWithRawResponse:
    def __init__(self, get_procedure: GetProcedureResource) -> None:
        self._get_procedure = get_procedure

        self.create = to_raw_response_wrapper(
            get_procedure.create,
        )


class AsyncGetProcedureResourceWithRawResponse:
    def __init__(self, get_procedure: AsyncGetProcedureResource) -> None:
        self._get_procedure = get_procedure

        self.create = async_to_raw_response_wrapper(
            get_procedure.create,
        )


class GetProcedureResourceWithStreamingResponse:
    def __init__(self, get_procedure: GetProcedureResource) -> None:
        self._get_procedure = get_procedure

        self.create = to_streamed_response_wrapper(
            get_procedure.create,
        )


class AsyncGetProcedureResourceWithStreamingResponse:
    def __init__(self, get_procedure: AsyncGetProcedureResource) -> None:
        self._get_procedure = get_procedure

        self.create = async_to_streamed_response_wrapper(
            get_procedure.create,
        )

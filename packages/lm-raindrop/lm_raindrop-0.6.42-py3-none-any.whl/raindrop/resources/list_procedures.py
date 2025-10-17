# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional

import httpx

from ..types import list_procedure_create_params
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
from ..types.list_procedure_create_response import ListProcedureCreateResponse

__all__ = ["ListProceduresResource", "AsyncListProceduresResource"]


class ListProceduresResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ListProceduresResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#accessing-raw-response-data-eg-headers
        """
        return ListProceduresResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ListProceduresResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#with_streaming_response
        """
        return ListProceduresResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        smart_memory_location: list_procedure_create_params.SmartMemoryLocation,
        procedural_memory_id: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ListProcedureCreateResponse:
        """Lists all procedures stored in procedural memory.

        Returns metadata about each
        procedure including creation and modification times.

        Args:
          smart_memory_location: Smart memory locator for targeting the correct smart memory instance

          procedural_memory_id: Optional procedural memory ID to use for actor isolation

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v1/list_procedures",
            body=maybe_transform(
                {
                    "smart_memory_location": smart_memory_location,
                    "procedural_memory_id": procedural_memory_id,
                },
                list_procedure_create_params.ListProcedureCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ListProcedureCreateResponse,
        )


class AsyncListProceduresResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncListProceduresResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncListProceduresResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncListProceduresResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#with_streaming_response
        """
        return AsyncListProceduresResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        smart_memory_location: list_procedure_create_params.SmartMemoryLocation,
        procedural_memory_id: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ListProcedureCreateResponse:
        """Lists all procedures stored in procedural memory.

        Returns metadata about each
        procedure including creation and modification times.

        Args:
          smart_memory_location: Smart memory locator for targeting the correct smart memory instance

          procedural_memory_id: Optional procedural memory ID to use for actor isolation

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v1/list_procedures",
            body=await async_maybe_transform(
                {
                    "smart_memory_location": smart_memory_location,
                    "procedural_memory_id": procedural_memory_id,
                },
                list_procedure_create_params.ListProcedureCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ListProcedureCreateResponse,
        )


class ListProceduresResourceWithRawResponse:
    def __init__(self, list_procedures: ListProceduresResource) -> None:
        self._list_procedures = list_procedures

        self.create = to_raw_response_wrapper(
            list_procedures.create,
        )


class AsyncListProceduresResourceWithRawResponse:
    def __init__(self, list_procedures: AsyncListProceduresResource) -> None:
        self._list_procedures = list_procedures

        self.create = async_to_raw_response_wrapper(
            list_procedures.create,
        )


class ListProceduresResourceWithStreamingResponse:
    def __init__(self, list_procedures: ListProceduresResource) -> None:
        self._list_procedures = list_procedures

        self.create = to_streamed_response_wrapper(
            list_procedures.create,
        )


class AsyncListProceduresResourceWithStreamingResponse:
    def __init__(self, list_procedures: AsyncListProceduresResource) -> None:
        self._list_procedures = list_procedures

        self.create = async_to_streamed_response_wrapper(
            list_procedures.create,
        )

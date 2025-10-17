# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional

import httpx

from ..types import put_procedure_create_params
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
from ..types.put_procedure_create_response import PutProcedureCreateResponse

__all__ = ["PutProcedureResource", "AsyncPutProcedureResource"]


class PutProcedureResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> PutProcedureResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#accessing-raw-response-data-eg-headers
        """
        return PutProcedureResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> PutProcedureResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#with_streaming_response
        """
        return PutProcedureResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        key: str,
        smart_memory_location: put_procedure_create_params.SmartMemoryLocation,
        value: str,
        procedural_memory_id: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PutProcedureCreateResponse:
        """Stores a new procedure in the agent's procedural memory.

        Procedures are reusable
        knowledge artifacts like system prompts, templates, workflows, or instructions
        that can be retrieved and applied across different sessions and contexts.

        Args:
          key: Unique key to identify this procedure

          smart_memory_location: Smart memory locator for targeting the correct smart memory instance

          value: The procedure content (prompt, template, instructions, etc.)

          procedural_memory_id: Optional procedural memory ID to use for actor isolation

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v1/put_procedure",
            body=maybe_transform(
                {
                    "key": key,
                    "smart_memory_location": smart_memory_location,
                    "value": value,
                    "procedural_memory_id": procedural_memory_id,
                },
                put_procedure_create_params.PutProcedureCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PutProcedureCreateResponse,
        )


class AsyncPutProcedureResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncPutProcedureResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncPutProcedureResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncPutProcedureResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#with_streaming_response
        """
        return AsyncPutProcedureResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        key: str,
        smart_memory_location: put_procedure_create_params.SmartMemoryLocation,
        value: str,
        procedural_memory_id: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PutProcedureCreateResponse:
        """Stores a new procedure in the agent's procedural memory.

        Procedures are reusable
        knowledge artifacts like system prompts, templates, workflows, or instructions
        that can be retrieved and applied across different sessions and contexts.

        Args:
          key: Unique key to identify this procedure

          smart_memory_location: Smart memory locator for targeting the correct smart memory instance

          value: The procedure content (prompt, template, instructions, etc.)

          procedural_memory_id: Optional procedural memory ID to use for actor isolation

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v1/put_procedure",
            body=await async_maybe_transform(
                {
                    "key": key,
                    "smart_memory_location": smart_memory_location,
                    "value": value,
                    "procedural_memory_id": procedural_memory_id,
                },
                put_procedure_create_params.PutProcedureCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PutProcedureCreateResponse,
        )


class PutProcedureResourceWithRawResponse:
    def __init__(self, put_procedure: PutProcedureResource) -> None:
        self._put_procedure = put_procedure

        self.create = to_raw_response_wrapper(
            put_procedure.create,
        )


class AsyncPutProcedureResourceWithRawResponse:
    def __init__(self, put_procedure: AsyncPutProcedureResource) -> None:
        self._put_procedure = put_procedure

        self.create = async_to_raw_response_wrapper(
            put_procedure.create,
        )


class PutProcedureResourceWithStreamingResponse:
    def __init__(self, put_procedure: PutProcedureResource) -> None:
        self._put_procedure = put_procedure

        self.create = to_streamed_response_wrapper(
            put_procedure.create,
        )


class AsyncPutProcedureResourceWithStreamingResponse:
    def __init__(self, put_procedure: AsyncPutProcedureResource) -> None:
        self._put_procedure = put_procedure

        self.create = async_to_streamed_response_wrapper(
            put_procedure.create,
        )

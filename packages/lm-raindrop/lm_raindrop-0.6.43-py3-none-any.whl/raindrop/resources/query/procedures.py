# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional

import httpx

from ..._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...types.query import procedure_search_params
from ..._base_client import make_request_options
from ...types.query.procedure_search_response import ProcedureSearchResponse

__all__ = ["ProceduresResource", "AsyncProceduresResource"]


class ProceduresResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ProceduresResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#accessing-raw-response-data-eg-headers
        """
        return ProceduresResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ProceduresResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#with_streaming_response
        """
        return ProceduresResourceWithStreamingResponse(self)

    def search(
        self,
        *,
        smart_memory_location: procedure_search_params.SmartMemoryLocation,
        terms: str,
        n_most_recent: Optional[int] | Omit = omit,
        procedural_memory_id: Optional[str] | Omit = omit,
        search_keys: Optional[bool] | Omit = omit,
        search_values: Optional[bool] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ProcedureSearchResponse:
        """Searches procedures using text matching across keys and values.

        Supports
        filtering by procedure keys, values, or both with fuzzy matching and relevance
        scoring.

        TODO: Future enhancement will include vector search for semantic similarity.

        Args:
          smart_memory_location: Smart memory locator for targeting the correct smart memory instance

          terms: Search terms to match against procedure keys and values

          n_most_recent: Maximum number of results to return

          procedural_memory_id: Optional procedural memory ID to use for actor isolation

          search_keys: Whether to search in procedure keys

          search_values: Whether to search in procedure values

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v1/search_procedures",
            body=maybe_transform(
                {
                    "smart_memory_location": smart_memory_location,
                    "terms": terms,
                    "n_most_recent": n_most_recent,
                    "procedural_memory_id": procedural_memory_id,
                    "search_keys": search_keys,
                    "search_values": search_values,
                },
                procedure_search_params.ProcedureSearchParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ProcedureSearchResponse,
        )


class AsyncProceduresResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncProceduresResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncProceduresResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncProceduresResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#with_streaming_response
        """
        return AsyncProceduresResourceWithStreamingResponse(self)

    async def search(
        self,
        *,
        smart_memory_location: procedure_search_params.SmartMemoryLocation,
        terms: str,
        n_most_recent: Optional[int] | Omit = omit,
        procedural_memory_id: Optional[str] | Omit = omit,
        search_keys: Optional[bool] | Omit = omit,
        search_values: Optional[bool] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ProcedureSearchResponse:
        """Searches procedures using text matching across keys and values.

        Supports
        filtering by procedure keys, values, or both with fuzzy matching and relevance
        scoring.

        TODO: Future enhancement will include vector search for semantic similarity.

        Args:
          smart_memory_location: Smart memory locator for targeting the correct smart memory instance

          terms: Search terms to match against procedure keys and values

          n_most_recent: Maximum number of results to return

          procedural_memory_id: Optional procedural memory ID to use for actor isolation

          search_keys: Whether to search in procedure keys

          search_values: Whether to search in procedure values

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v1/search_procedures",
            body=await async_maybe_transform(
                {
                    "smart_memory_location": smart_memory_location,
                    "terms": terms,
                    "n_most_recent": n_most_recent,
                    "procedural_memory_id": procedural_memory_id,
                    "search_keys": search_keys,
                    "search_values": search_values,
                },
                procedure_search_params.ProcedureSearchParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ProcedureSearchResponse,
        )


class ProceduresResourceWithRawResponse:
    def __init__(self, procedures: ProceduresResource) -> None:
        self._procedures = procedures

        self.search = to_raw_response_wrapper(
            procedures.search,
        )


class AsyncProceduresResourceWithRawResponse:
    def __init__(self, procedures: AsyncProceduresResource) -> None:
        self._procedures = procedures

        self.search = async_to_raw_response_wrapper(
            procedures.search,
        )


class ProceduresResourceWithStreamingResponse:
    def __init__(self, procedures: ProceduresResource) -> None:
        self._procedures = procedures

        self.search = to_streamed_response_wrapper(
            procedures.search,
        )


class AsyncProceduresResourceWithStreamingResponse:
    def __init__(self, procedures: AsyncProceduresResource) -> None:
        self._procedures = procedures

        self.search = async_to_streamed_response_wrapper(
            procedures.search,
        )

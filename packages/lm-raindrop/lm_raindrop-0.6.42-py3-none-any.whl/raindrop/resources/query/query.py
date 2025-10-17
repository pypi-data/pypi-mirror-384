# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable, Optional

import httpx

from .memory import (
    MemoryResource,
    AsyncMemoryResource,
    MemoryResourceWithRawResponse,
    AsyncMemoryResourceWithRawResponse,
    MemoryResourceWithStreamingResponse,
    AsyncMemoryResourceWithStreamingResponse,
)
from ...types import (
    query_search_params,
    query_chunk_search_params,
    query_sumarize_page_params,
    query_document_query_params,
    query_get_paginated_search_params,
)
from ..._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from .procedures import (
    ProceduresResource,
    AsyncProceduresResource,
    ProceduresResourceWithRawResponse,
    AsyncProceduresResourceWithRawResponse,
    ProceduresResourceWithStreamingResponse,
    AsyncProceduresResourceWithStreamingResponse,
)
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...pagination import SyncPageNumber, AsyncPageNumber
from ..._base_client import AsyncPaginator, make_request_options
from .episodic_memory import (
    EpisodicMemoryResource,
    AsyncEpisodicMemoryResource,
    EpisodicMemoryResourceWithRawResponse,
    AsyncEpisodicMemoryResourceWithRawResponse,
    EpisodicMemoryResourceWithStreamingResponse,
    AsyncEpisodicMemoryResourceWithStreamingResponse,
)
from .semantic_memory import (
    SemanticMemoryResource,
    AsyncSemanticMemoryResource,
    SemanticMemoryResourceWithRawResponse,
    AsyncSemanticMemoryResourceWithRawResponse,
    SemanticMemoryResourceWithStreamingResponse,
    AsyncSemanticMemoryResourceWithStreamingResponse,
)
from ...types.bucket_locator_param import BucketLocatorParam
from ...types.query_search_response import QuerySearchResponse
from ...types.query_chunk_search_response import QueryChunkSearchResponse
from ...types.query_sumarize_page_response import QuerySumarizePageResponse
from ...types.query_document_query_response import QueryDocumentQueryResponse
from ...types.liquidmetal_v1alpha1_text_result import LiquidmetalV1alpha1TextResult

__all__ = ["QueryResource", "AsyncQueryResource"]


class QueryResource(SyncAPIResource):
    @cached_property
    def memory(self) -> MemoryResource:
        return MemoryResource(self._client)

    @cached_property
    def episodic_memory(self) -> EpisodicMemoryResource:
        return EpisodicMemoryResource(self._client)

    @cached_property
    def procedures(self) -> ProceduresResource:
        return ProceduresResource(self._client)

    @cached_property
    def semantic_memory(self) -> SemanticMemoryResource:
        return SemanticMemoryResource(self._client)

    @cached_property
    def with_raw_response(self) -> QueryResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#accessing-raw-response-data-eg-headers
        """
        return QueryResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> QueryResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#with_streaming_response
        """
        return QueryResourceWithStreamingResponse(self)

    def chunk_search(
        self,
        *,
        bucket_locations: Iterable[BucketLocatorParam],
        input: str,
        request_id: str,
        partition: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> QueryChunkSearchResponse:
        """
        Chunk Search provides search capabilities that serve as a complete drop-in
        replacement for traditional RAG pipelines. This system enables AI agents to
        leverage private data stored in SmartBuckets with zero additional configuration.

        Each input query is processed by our AI agent to determine the best way to
        search the data. The system will then return the most relevant results from the
        data ranked by relevance on the input query.

        Args:
          bucket_locations: The buckets to search. If provided, the search will only return results from
              these buckets

          input: Natural language query or question. Can include complex criteria and
              relationships. The system will optimize the search strategy based on this input

          request_id: Client-provided search session identifier. Required for pagination and result
              tracking. We recommend using a UUID or ULID for this value

          partition: Optional partition identifier for multi-tenant data isolation. Defaults to
              'default' if not specified

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v1/chunk_search",
            body=maybe_transform(
                {
                    "bucket_locations": bucket_locations,
                    "input": input,
                    "request_id": request_id,
                    "partition": partition,
                },
                query_chunk_search_params.QueryChunkSearchParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=QueryChunkSearchResponse,
        )

    def document_query(
        self,
        *,
        bucket_location: BucketLocatorParam,
        input: str,
        object_id: str,
        request_id: str,
        partition: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> QueryDocumentQueryResponse:
        """
        Enables natural conversational interactions with documents stored in
        SmartBuckets. This endpoint allows users to ask questions, request summaries,
        and explore document content through an intuitive conversational interface. The
        system understands context and can handle complex queries about document
        contents.

        The query system maintains conversation context throught the request_id,
        enabling follow-up questions and deep exploration of document content. It works
        across all supported file types and automatically handles multi-page documents,
        making complex file interaction as simple as having a conversation.

        The system will:

        - Maintain conversation history for context when using the same request_id
        - Process questions against file content
        - Generate contextual, relevant responses

        Document query is supported for all file types, including PDFs, images, and
        audio files.

        Args:
          bucket_location: The storage bucket containing the target document. Must be a valid, registered
              Smart Bucket. Used to identify which bucket to query against

          input: User's input or question about the document. Can be natural language questions,
              commands, or requests. The system will process this against the document content

          object_id: Document identifier within the bucket. Typically matches the storage path or
              key. Used to identify which document to chat with

          request_id: Client-provided conversation session identifier. Required for maintaining
              context in follow-up questions. We recommend using a UUID or ULID for this value

          partition: Optional partition identifier for multi-tenant data isolation. Defaults to
              'default' if not specified

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v1/document_query",
            body=maybe_transform(
                {
                    "bucket_location": bucket_location,
                    "input": input,
                    "object_id": object_id,
                    "request_id": request_id,
                    "partition": partition,
                },
                query_document_query_params.QueryDocumentQueryParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=QueryDocumentQueryResponse,
        )

    def get_paginated_search(
        self,
        *,
        page: Optional[int],
        page_size: Optional[int],
        request_id: str,
        partition: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncPageNumber[LiquidmetalV1alpha1TextResult]:
        """Retrieve additional pages from a previous search.

        This endpoint enables
        navigation through large result sets while maintaining search context and result
        relevance. Retrieving paginated results requires a valid request_id from a
        previously completed search.

        Args:
          page: Requested page number

          page_size: Results per page

          request_id: Original search session identifier from the initial search

          partition: Optional partition identifier for multi-tenant data isolation. Defaults to
              'default' if not specified

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/v1/search_get_page",
            page=SyncPageNumber[LiquidmetalV1alpha1TextResult],
            body=maybe_transform(
                {
                    "page": page,
                    "page_size": page_size,
                    "request_id": request_id,
                    "partition": partition,
                },
                query_get_paginated_search_params.QueryGetPaginatedSearchParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            model=LiquidmetalV1alpha1TextResult,
            method="post",
        )

    def search(
        self,
        *,
        bucket_locations: Iterable[BucketLocatorParam],
        input: str,
        request_id: str,
        partition: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> QuerySearchResponse:
        """
        Primary search endpoint that provides advanced search capabilities across all
        document types stored in SmartBuckets.

        Supports recursive object search within objects, enabling nested content search
        like embedded images, text content, and personally identifiable information
        (PII).

        The system supports complex queries like:

        - 'Show me documents containing credit card numbers or social security numbers'
        - 'Find images of landscapes taken during sunset'
        - 'Get documents mentioning revenue forecasts from Q4 2023'
        - 'Find me all PDF documents that contain pictures of a cat'
        - 'Find me all audio files that contain information about the weather in SF in
          2024'

        Key capabilities:

        - Natural language query understanding
        - Content-based search across text, images, and audio
        - Automatic PII detection
        - Multi-modal search (text, images, audio)

        Args:
          bucket_locations: The buckets to search. If provided, the search will only return results from
              these buckets

          input: Natural language search query that can include complex criteria. Supports
              queries like finding documents with specific content types, PII, or semantic
              meaning

          request_id: Client-provided search session identifier. Required for pagination and result
              tracking. We recommend using a UUID or ULID for this value

          partition: Optional partition identifier for multi-tenant data isolation. Defaults to
              'default' if not specified

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v1/search",
            body=maybe_transform(
                {
                    "bucket_locations": bucket_locations,
                    "input": input,
                    "request_id": request_id,
                    "partition": partition,
                },
                query_search_params.QuerySearchParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=QuerySearchResponse,
        )

    def sumarize_page(
        self,
        *,
        page: int,
        page_size: int,
        request_id: str,
        partition: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> QuerySumarizePageResponse:
        """
        Generates intelligent summaries of search result pages, helping users quickly
        understand large result sets without reading through every document. The system
        analyzes the content of all results on a given page and generates a detailed
        overview.

        The summary system:

        - Identifies key themes and topics
        - Extracts important findings
        - Highlights document relationships
        - Provides content type distribution
        - Summarizes metadata patterns

        This is particularly valuable when dealing with:

        - Large document collections
        - Mixed content types
        - Technical documentation
        - Research materials

        Args:
          page: Target page number (1-based)

          page_size: Results per page. Affects summary granularity

          request_id: Original search session identifier from the initial search

          partition: Optional partition identifier for multi-tenant data isolation. Defaults to
              'default' if not specified

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v1/summarize_page",
            body=maybe_transform(
                {
                    "page": page,
                    "page_size": page_size,
                    "request_id": request_id,
                    "partition": partition,
                },
                query_sumarize_page_params.QuerySumarizePageParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=QuerySumarizePageResponse,
        )


class AsyncQueryResource(AsyncAPIResource):
    @cached_property
    def memory(self) -> AsyncMemoryResource:
        return AsyncMemoryResource(self._client)

    @cached_property
    def episodic_memory(self) -> AsyncEpisodicMemoryResource:
        return AsyncEpisodicMemoryResource(self._client)

    @cached_property
    def procedures(self) -> AsyncProceduresResource:
        return AsyncProceduresResource(self._client)

    @cached_property
    def semantic_memory(self) -> AsyncSemanticMemoryResource:
        return AsyncSemanticMemoryResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncQueryResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncQueryResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncQueryResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LiquidMetal-AI/lm-raindrop-python-sdk#with_streaming_response
        """
        return AsyncQueryResourceWithStreamingResponse(self)

    async def chunk_search(
        self,
        *,
        bucket_locations: Iterable[BucketLocatorParam],
        input: str,
        request_id: str,
        partition: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> QueryChunkSearchResponse:
        """
        Chunk Search provides search capabilities that serve as a complete drop-in
        replacement for traditional RAG pipelines. This system enables AI agents to
        leverage private data stored in SmartBuckets with zero additional configuration.

        Each input query is processed by our AI agent to determine the best way to
        search the data. The system will then return the most relevant results from the
        data ranked by relevance on the input query.

        Args:
          bucket_locations: The buckets to search. If provided, the search will only return results from
              these buckets

          input: Natural language query or question. Can include complex criteria and
              relationships. The system will optimize the search strategy based on this input

          request_id: Client-provided search session identifier. Required for pagination and result
              tracking. We recommend using a UUID or ULID for this value

          partition: Optional partition identifier for multi-tenant data isolation. Defaults to
              'default' if not specified

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v1/chunk_search",
            body=await async_maybe_transform(
                {
                    "bucket_locations": bucket_locations,
                    "input": input,
                    "request_id": request_id,
                    "partition": partition,
                },
                query_chunk_search_params.QueryChunkSearchParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=QueryChunkSearchResponse,
        )

    async def document_query(
        self,
        *,
        bucket_location: BucketLocatorParam,
        input: str,
        object_id: str,
        request_id: str,
        partition: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> QueryDocumentQueryResponse:
        """
        Enables natural conversational interactions with documents stored in
        SmartBuckets. This endpoint allows users to ask questions, request summaries,
        and explore document content through an intuitive conversational interface. The
        system understands context and can handle complex queries about document
        contents.

        The query system maintains conversation context throught the request_id,
        enabling follow-up questions and deep exploration of document content. It works
        across all supported file types and automatically handles multi-page documents,
        making complex file interaction as simple as having a conversation.

        The system will:

        - Maintain conversation history for context when using the same request_id
        - Process questions against file content
        - Generate contextual, relevant responses

        Document query is supported for all file types, including PDFs, images, and
        audio files.

        Args:
          bucket_location: The storage bucket containing the target document. Must be a valid, registered
              Smart Bucket. Used to identify which bucket to query against

          input: User's input or question about the document. Can be natural language questions,
              commands, or requests. The system will process this against the document content

          object_id: Document identifier within the bucket. Typically matches the storage path or
              key. Used to identify which document to chat with

          request_id: Client-provided conversation session identifier. Required for maintaining
              context in follow-up questions. We recommend using a UUID or ULID for this value

          partition: Optional partition identifier for multi-tenant data isolation. Defaults to
              'default' if not specified

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v1/document_query",
            body=await async_maybe_transform(
                {
                    "bucket_location": bucket_location,
                    "input": input,
                    "object_id": object_id,
                    "request_id": request_id,
                    "partition": partition,
                },
                query_document_query_params.QueryDocumentQueryParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=QueryDocumentQueryResponse,
        )

    def get_paginated_search(
        self,
        *,
        page: Optional[int],
        page_size: Optional[int],
        request_id: str,
        partition: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[LiquidmetalV1alpha1TextResult, AsyncPageNumber[LiquidmetalV1alpha1TextResult]]:
        """Retrieve additional pages from a previous search.

        This endpoint enables
        navigation through large result sets while maintaining search context and result
        relevance. Retrieving paginated results requires a valid request_id from a
        previously completed search.

        Args:
          page: Requested page number

          page_size: Results per page

          request_id: Original search session identifier from the initial search

          partition: Optional partition identifier for multi-tenant data isolation. Defaults to
              'default' if not specified

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/v1/search_get_page",
            page=AsyncPageNumber[LiquidmetalV1alpha1TextResult],
            body=maybe_transform(
                {
                    "page": page,
                    "page_size": page_size,
                    "request_id": request_id,
                    "partition": partition,
                },
                query_get_paginated_search_params.QueryGetPaginatedSearchParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            model=LiquidmetalV1alpha1TextResult,
            method="post",
        )

    async def search(
        self,
        *,
        bucket_locations: Iterable[BucketLocatorParam],
        input: str,
        request_id: str,
        partition: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> QuerySearchResponse:
        """
        Primary search endpoint that provides advanced search capabilities across all
        document types stored in SmartBuckets.

        Supports recursive object search within objects, enabling nested content search
        like embedded images, text content, and personally identifiable information
        (PII).

        The system supports complex queries like:

        - 'Show me documents containing credit card numbers or social security numbers'
        - 'Find images of landscapes taken during sunset'
        - 'Get documents mentioning revenue forecasts from Q4 2023'
        - 'Find me all PDF documents that contain pictures of a cat'
        - 'Find me all audio files that contain information about the weather in SF in
          2024'

        Key capabilities:

        - Natural language query understanding
        - Content-based search across text, images, and audio
        - Automatic PII detection
        - Multi-modal search (text, images, audio)

        Args:
          bucket_locations: The buckets to search. If provided, the search will only return results from
              these buckets

          input: Natural language search query that can include complex criteria. Supports
              queries like finding documents with specific content types, PII, or semantic
              meaning

          request_id: Client-provided search session identifier. Required for pagination and result
              tracking. We recommend using a UUID or ULID for this value

          partition: Optional partition identifier for multi-tenant data isolation. Defaults to
              'default' if not specified

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v1/search",
            body=await async_maybe_transform(
                {
                    "bucket_locations": bucket_locations,
                    "input": input,
                    "request_id": request_id,
                    "partition": partition,
                },
                query_search_params.QuerySearchParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=QuerySearchResponse,
        )

    async def sumarize_page(
        self,
        *,
        page: int,
        page_size: int,
        request_id: str,
        partition: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> QuerySumarizePageResponse:
        """
        Generates intelligent summaries of search result pages, helping users quickly
        understand large result sets without reading through every document. The system
        analyzes the content of all results on a given page and generates a detailed
        overview.

        The summary system:

        - Identifies key themes and topics
        - Extracts important findings
        - Highlights document relationships
        - Provides content type distribution
        - Summarizes metadata patterns

        This is particularly valuable when dealing with:

        - Large document collections
        - Mixed content types
        - Technical documentation
        - Research materials

        Args:
          page: Target page number (1-based)

          page_size: Results per page. Affects summary granularity

          request_id: Original search session identifier from the initial search

          partition: Optional partition identifier for multi-tenant data isolation. Defaults to
              'default' if not specified

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v1/summarize_page",
            body=await async_maybe_transform(
                {
                    "page": page,
                    "page_size": page_size,
                    "request_id": request_id,
                    "partition": partition,
                },
                query_sumarize_page_params.QuerySumarizePageParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=QuerySumarizePageResponse,
        )


class QueryResourceWithRawResponse:
    def __init__(self, query: QueryResource) -> None:
        self._query = query

        self.chunk_search = to_raw_response_wrapper(
            query.chunk_search,
        )
        self.document_query = to_raw_response_wrapper(
            query.document_query,
        )
        self.get_paginated_search = to_raw_response_wrapper(
            query.get_paginated_search,
        )
        self.search = to_raw_response_wrapper(
            query.search,
        )
        self.sumarize_page = to_raw_response_wrapper(
            query.sumarize_page,
        )

    @cached_property
    def memory(self) -> MemoryResourceWithRawResponse:
        return MemoryResourceWithRawResponse(self._query.memory)

    @cached_property
    def episodic_memory(self) -> EpisodicMemoryResourceWithRawResponse:
        return EpisodicMemoryResourceWithRawResponse(self._query.episodic_memory)

    @cached_property
    def procedures(self) -> ProceduresResourceWithRawResponse:
        return ProceduresResourceWithRawResponse(self._query.procedures)

    @cached_property
    def semantic_memory(self) -> SemanticMemoryResourceWithRawResponse:
        return SemanticMemoryResourceWithRawResponse(self._query.semantic_memory)


class AsyncQueryResourceWithRawResponse:
    def __init__(self, query: AsyncQueryResource) -> None:
        self._query = query

        self.chunk_search = async_to_raw_response_wrapper(
            query.chunk_search,
        )
        self.document_query = async_to_raw_response_wrapper(
            query.document_query,
        )
        self.get_paginated_search = async_to_raw_response_wrapper(
            query.get_paginated_search,
        )
        self.search = async_to_raw_response_wrapper(
            query.search,
        )
        self.sumarize_page = async_to_raw_response_wrapper(
            query.sumarize_page,
        )

    @cached_property
    def memory(self) -> AsyncMemoryResourceWithRawResponse:
        return AsyncMemoryResourceWithRawResponse(self._query.memory)

    @cached_property
    def episodic_memory(self) -> AsyncEpisodicMemoryResourceWithRawResponse:
        return AsyncEpisodicMemoryResourceWithRawResponse(self._query.episodic_memory)

    @cached_property
    def procedures(self) -> AsyncProceduresResourceWithRawResponse:
        return AsyncProceduresResourceWithRawResponse(self._query.procedures)

    @cached_property
    def semantic_memory(self) -> AsyncSemanticMemoryResourceWithRawResponse:
        return AsyncSemanticMemoryResourceWithRawResponse(self._query.semantic_memory)


class QueryResourceWithStreamingResponse:
    def __init__(self, query: QueryResource) -> None:
        self._query = query

        self.chunk_search = to_streamed_response_wrapper(
            query.chunk_search,
        )
        self.document_query = to_streamed_response_wrapper(
            query.document_query,
        )
        self.get_paginated_search = to_streamed_response_wrapper(
            query.get_paginated_search,
        )
        self.search = to_streamed_response_wrapper(
            query.search,
        )
        self.sumarize_page = to_streamed_response_wrapper(
            query.sumarize_page,
        )

    @cached_property
    def memory(self) -> MemoryResourceWithStreamingResponse:
        return MemoryResourceWithStreamingResponse(self._query.memory)

    @cached_property
    def episodic_memory(self) -> EpisodicMemoryResourceWithStreamingResponse:
        return EpisodicMemoryResourceWithStreamingResponse(self._query.episodic_memory)

    @cached_property
    def procedures(self) -> ProceduresResourceWithStreamingResponse:
        return ProceduresResourceWithStreamingResponse(self._query.procedures)

    @cached_property
    def semantic_memory(self) -> SemanticMemoryResourceWithStreamingResponse:
        return SemanticMemoryResourceWithStreamingResponse(self._query.semantic_memory)


class AsyncQueryResourceWithStreamingResponse:
    def __init__(self, query: AsyncQueryResource) -> None:
        self._query = query

        self.chunk_search = async_to_streamed_response_wrapper(
            query.chunk_search,
        )
        self.document_query = async_to_streamed_response_wrapper(
            query.document_query,
        )
        self.get_paginated_search = async_to_streamed_response_wrapper(
            query.get_paginated_search,
        )
        self.search = async_to_streamed_response_wrapper(
            query.search,
        )
        self.sumarize_page = async_to_streamed_response_wrapper(
            query.sumarize_page,
        )

    @cached_property
    def memory(self) -> AsyncMemoryResourceWithStreamingResponse:
        return AsyncMemoryResourceWithStreamingResponse(self._query.memory)

    @cached_property
    def episodic_memory(self) -> AsyncEpisodicMemoryResourceWithStreamingResponse:
        return AsyncEpisodicMemoryResourceWithStreamingResponse(self._query.episodic_memory)

    @cached_property
    def procedures(self) -> AsyncProceduresResourceWithStreamingResponse:
        return AsyncProceduresResourceWithStreamingResponse(self._query.procedures)

    @cached_property
    def semantic_memory(self) -> AsyncSemanticMemoryResourceWithStreamingResponse:
        return AsyncSemanticMemoryResourceWithStreamingResponse(self._query.semantic_memory)

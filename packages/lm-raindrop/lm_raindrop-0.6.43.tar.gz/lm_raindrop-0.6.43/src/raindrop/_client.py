# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, Mapping
from typing_extensions import Self, override

import httpx

from . import _exceptions
from ._qs import Querystring
from ._types import (
    Omit,
    Timeout,
    NotGiven,
    Transport,
    ProxiesTypes,
    RequestOptions,
    not_given,
)
from ._utils import is_given, get_async_library
from ._version import __version__
from .resources import (
    bucket,
    get_memory,
    put_memory,
    end_session,
    delete_memory,
    get_procedure,
    put_procedure,
    start_session,
    list_procedures,
    delete_procedure,
    summarize_memory,
    rehydrate_session,
    get_semantic_memory,
    put_semantic_memory,
    delete_semantic_memory,
)
from ._streaming import Stream as Stream, AsyncStream as AsyncStream
from ._exceptions import RaindropError, APIStatusError
from ._base_client import (
    DEFAULT_MAX_RETRIES,
    SyncAPIClient,
    AsyncAPIClient,
)
from .resources.query import query

__all__ = [
    "Timeout",
    "Transport",
    "ProxiesTypes",
    "RequestOptions",
    "Raindrop",
    "AsyncRaindrop",
    "Client",
    "AsyncClient",
]


class Raindrop(SyncAPIClient):
    query: query.QueryResource
    bucket: bucket.BucketResource
    put_memory: put_memory.PutMemoryResource
    get_memory: get_memory.GetMemoryResource
    delete_memory: delete_memory.DeleteMemoryResource
    summarize_memory: summarize_memory.SummarizeMemoryResource
    start_session: start_session.StartSessionResource
    end_session: end_session.EndSessionResource
    rehydrate_session: rehydrate_session.RehydrateSessionResource
    put_procedure: put_procedure.PutProcedureResource
    get_procedure: get_procedure.GetProcedureResource
    delete_procedure: delete_procedure.DeleteProcedureResource
    list_procedures: list_procedures.ListProceduresResource
    put_semantic_memory: put_semantic_memory.PutSemanticMemoryResource
    get_semantic_memory: get_semantic_memory.GetSemanticMemoryResource
    delete_semantic_memory: delete_semantic_memory.DeleteSemanticMemoryResource
    with_raw_response: RaindropWithRawResponse
    with_streaming_response: RaindropWithStreamedResponse

    # client options
    api_key: str

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        # Configure a custom httpx client.
        # We provide a `DefaultHttpxClient` class that you can pass to retain the default values we use for `limits`, `timeout` & `follow_redirects`.
        # See the [httpx documentation](https://www.python-httpx.org/api/#client) for more details.
        http_client: httpx.Client | None = None,
        # Enable or disable schema validation for data returned by the API.
        # When enabled an error APIResponseValidationError is raised
        # if the API responds with invalid data for the expected schema.
        #
        # This parameter may be removed or changed in the future.
        # If you rely on this feature, please open a GitHub issue
        # outlining your use-case to help us decide if it should be
        # part of our public interface in the future.
        _strict_response_validation: bool = False,
    ) -> None:
        """Construct a new synchronous Raindrop client instance.

        This automatically infers the `api_key` argument from the `RAINDROP_API_KEY` environment variable if it is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("RAINDROP_API_KEY")
        if api_key is None:
            raise RaindropError(
                "The api_key client option must be set either by passing api_key to the client or by setting the RAINDROP_API_KEY environment variable"
            )
        self.api_key = api_key

        if base_url is None:
            base_url = os.environ.get("RAINDROP_BASE_URL")
        if base_url is None:
            base_url = f"https://api.raindrop.run"

        super().__init__(
            version=__version__,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
            http_client=http_client,
            custom_headers=default_headers,
            custom_query=default_query,
            _strict_response_validation=_strict_response_validation,
        )

        self.query = query.QueryResource(self)
        self.bucket = bucket.BucketResource(self)
        self.put_memory = put_memory.PutMemoryResource(self)
        self.get_memory = get_memory.GetMemoryResource(self)
        self.delete_memory = delete_memory.DeleteMemoryResource(self)
        self.summarize_memory = summarize_memory.SummarizeMemoryResource(self)
        self.start_session = start_session.StartSessionResource(self)
        self.end_session = end_session.EndSessionResource(self)
        self.rehydrate_session = rehydrate_session.RehydrateSessionResource(self)
        self.put_procedure = put_procedure.PutProcedureResource(self)
        self.get_procedure = get_procedure.GetProcedureResource(self)
        self.delete_procedure = delete_procedure.DeleteProcedureResource(self)
        self.list_procedures = list_procedures.ListProceduresResource(self)
        self.put_semantic_memory = put_semantic_memory.PutSemanticMemoryResource(self)
        self.get_semantic_memory = get_semantic_memory.GetSemanticMemoryResource(self)
        self.delete_semantic_memory = delete_semantic_memory.DeleteSemanticMemoryResource(self)
        self.with_raw_response = RaindropWithRawResponse(self)
        self.with_streaming_response = RaindropWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        api_key = self.api_key
        return {"Authorization": f"Bearer {api_key}"}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            "X-Stainless-Async": "false",
            **self._custom_headers,
        }

    def copy(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        http_client: httpx.Client | None = None,
        max_retries: int | NotGiven = not_given,
        default_headers: Mapping[str, str] | None = None,
        set_default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        set_default_query: Mapping[str, object] | None = None,
        _extra_kwargs: Mapping[str, Any] = {},
    ) -> Self:
        """
        Create a new client instance re-using the same options given to the current client with optional overriding.
        """
        if default_headers is not None and set_default_headers is not None:
            raise ValueError("The `default_headers` and `set_default_headers` arguments are mutually exclusive")

        if default_query is not None and set_default_query is not None:
            raise ValueError("The `default_query` and `set_default_query` arguments are mutually exclusive")

        headers = self._custom_headers
        if default_headers is not None:
            headers = {**headers, **default_headers}
        elif set_default_headers is not None:
            headers = set_default_headers

        params = self._custom_query
        if default_query is not None:
            params = {**params, **default_query}
        elif set_default_query is not None:
            params = set_default_query

        http_client = http_client or self._client
        return self.__class__(
            api_key=api_key or self.api_key,
            base_url=base_url or self.base_url,
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
            http_client=http_client,
            max_retries=max_retries if is_given(max_retries) else self.max_retries,
            default_headers=headers,
            default_query=params,
            **_extra_kwargs,
        )

    # Alias for `copy` for nicer inline usage, e.g.
    # client.with_options(timeout=10).foo.create(...)
    with_options = copy

    @override
    def _make_status_error(
        self,
        err_msg: str,
        *,
        body: object,
        response: httpx.Response,
    ) -> APIStatusError:
        if response.status_code == 400:
            return _exceptions.BadRequestError(err_msg, response=response, body=body)

        if response.status_code == 401:
            return _exceptions.AuthenticationError(err_msg, response=response, body=body)

        if response.status_code == 403:
            return _exceptions.PermissionDeniedError(err_msg, response=response, body=body)

        if response.status_code == 404:
            return _exceptions.NotFoundError(err_msg, response=response, body=body)

        if response.status_code == 409:
            return _exceptions.ConflictError(err_msg, response=response, body=body)

        if response.status_code == 422:
            return _exceptions.UnprocessableEntityError(err_msg, response=response, body=body)

        if response.status_code == 429:
            return _exceptions.RateLimitError(err_msg, response=response, body=body)

        if response.status_code >= 500:
            return _exceptions.InternalServerError(err_msg, response=response, body=body)
        return APIStatusError(err_msg, response=response, body=body)


class AsyncRaindrop(AsyncAPIClient):
    query: query.AsyncQueryResource
    bucket: bucket.AsyncBucketResource
    put_memory: put_memory.AsyncPutMemoryResource
    get_memory: get_memory.AsyncGetMemoryResource
    delete_memory: delete_memory.AsyncDeleteMemoryResource
    summarize_memory: summarize_memory.AsyncSummarizeMemoryResource
    start_session: start_session.AsyncStartSessionResource
    end_session: end_session.AsyncEndSessionResource
    rehydrate_session: rehydrate_session.AsyncRehydrateSessionResource
    put_procedure: put_procedure.AsyncPutProcedureResource
    get_procedure: get_procedure.AsyncGetProcedureResource
    delete_procedure: delete_procedure.AsyncDeleteProcedureResource
    list_procedures: list_procedures.AsyncListProceduresResource
    put_semantic_memory: put_semantic_memory.AsyncPutSemanticMemoryResource
    get_semantic_memory: get_semantic_memory.AsyncGetSemanticMemoryResource
    delete_semantic_memory: delete_semantic_memory.AsyncDeleteSemanticMemoryResource
    with_raw_response: AsyncRaindropWithRawResponse
    with_streaming_response: AsyncRaindropWithStreamedResponse

    # client options
    api_key: str

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        # Configure a custom httpx client.
        # We provide a `DefaultAsyncHttpxClient` class that you can pass to retain the default values we use for `limits`, `timeout` & `follow_redirects`.
        # See the [httpx documentation](https://www.python-httpx.org/api/#asyncclient) for more details.
        http_client: httpx.AsyncClient | None = None,
        # Enable or disable schema validation for data returned by the API.
        # When enabled an error APIResponseValidationError is raised
        # if the API responds with invalid data for the expected schema.
        #
        # This parameter may be removed or changed in the future.
        # If you rely on this feature, please open a GitHub issue
        # outlining your use-case to help us decide if it should be
        # part of our public interface in the future.
        _strict_response_validation: bool = False,
    ) -> None:
        """Construct a new async AsyncRaindrop client instance.

        This automatically infers the `api_key` argument from the `RAINDROP_API_KEY` environment variable if it is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("RAINDROP_API_KEY")
        if api_key is None:
            raise RaindropError(
                "The api_key client option must be set either by passing api_key to the client or by setting the RAINDROP_API_KEY environment variable"
            )
        self.api_key = api_key

        if base_url is None:
            base_url = os.environ.get("RAINDROP_BASE_URL")
        if base_url is None:
            base_url = f"https://api.raindrop.run"

        super().__init__(
            version=__version__,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
            http_client=http_client,
            custom_headers=default_headers,
            custom_query=default_query,
            _strict_response_validation=_strict_response_validation,
        )

        self.query = query.AsyncQueryResource(self)
        self.bucket = bucket.AsyncBucketResource(self)
        self.put_memory = put_memory.AsyncPutMemoryResource(self)
        self.get_memory = get_memory.AsyncGetMemoryResource(self)
        self.delete_memory = delete_memory.AsyncDeleteMemoryResource(self)
        self.summarize_memory = summarize_memory.AsyncSummarizeMemoryResource(self)
        self.start_session = start_session.AsyncStartSessionResource(self)
        self.end_session = end_session.AsyncEndSessionResource(self)
        self.rehydrate_session = rehydrate_session.AsyncRehydrateSessionResource(self)
        self.put_procedure = put_procedure.AsyncPutProcedureResource(self)
        self.get_procedure = get_procedure.AsyncGetProcedureResource(self)
        self.delete_procedure = delete_procedure.AsyncDeleteProcedureResource(self)
        self.list_procedures = list_procedures.AsyncListProceduresResource(self)
        self.put_semantic_memory = put_semantic_memory.AsyncPutSemanticMemoryResource(self)
        self.get_semantic_memory = get_semantic_memory.AsyncGetSemanticMemoryResource(self)
        self.delete_semantic_memory = delete_semantic_memory.AsyncDeleteSemanticMemoryResource(self)
        self.with_raw_response = AsyncRaindropWithRawResponse(self)
        self.with_streaming_response = AsyncRaindropWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        api_key = self.api_key
        return {"Authorization": f"Bearer {api_key}"}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            "X-Stainless-Async": f"async:{get_async_library()}",
            **self._custom_headers,
        }

    def copy(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        http_client: httpx.AsyncClient | None = None,
        max_retries: int | NotGiven = not_given,
        default_headers: Mapping[str, str] | None = None,
        set_default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        set_default_query: Mapping[str, object] | None = None,
        _extra_kwargs: Mapping[str, Any] = {},
    ) -> Self:
        """
        Create a new client instance re-using the same options given to the current client with optional overriding.
        """
        if default_headers is not None and set_default_headers is not None:
            raise ValueError("The `default_headers` and `set_default_headers` arguments are mutually exclusive")

        if default_query is not None and set_default_query is not None:
            raise ValueError("The `default_query` and `set_default_query` arguments are mutually exclusive")

        headers = self._custom_headers
        if default_headers is not None:
            headers = {**headers, **default_headers}
        elif set_default_headers is not None:
            headers = set_default_headers

        params = self._custom_query
        if default_query is not None:
            params = {**params, **default_query}
        elif set_default_query is not None:
            params = set_default_query

        http_client = http_client or self._client
        return self.__class__(
            api_key=api_key or self.api_key,
            base_url=base_url or self.base_url,
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
            http_client=http_client,
            max_retries=max_retries if is_given(max_retries) else self.max_retries,
            default_headers=headers,
            default_query=params,
            **_extra_kwargs,
        )

    # Alias for `copy` for nicer inline usage, e.g.
    # client.with_options(timeout=10).foo.create(...)
    with_options = copy

    @override
    def _make_status_error(
        self,
        err_msg: str,
        *,
        body: object,
        response: httpx.Response,
    ) -> APIStatusError:
        if response.status_code == 400:
            return _exceptions.BadRequestError(err_msg, response=response, body=body)

        if response.status_code == 401:
            return _exceptions.AuthenticationError(err_msg, response=response, body=body)

        if response.status_code == 403:
            return _exceptions.PermissionDeniedError(err_msg, response=response, body=body)

        if response.status_code == 404:
            return _exceptions.NotFoundError(err_msg, response=response, body=body)

        if response.status_code == 409:
            return _exceptions.ConflictError(err_msg, response=response, body=body)

        if response.status_code == 422:
            return _exceptions.UnprocessableEntityError(err_msg, response=response, body=body)

        if response.status_code == 429:
            return _exceptions.RateLimitError(err_msg, response=response, body=body)

        if response.status_code >= 500:
            return _exceptions.InternalServerError(err_msg, response=response, body=body)
        return APIStatusError(err_msg, response=response, body=body)


class RaindropWithRawResponse:
    def __init__(self, client: Raindrop) -> None:
        self.query = query.QueryResourceWithRawResponse(client.query)
        self.bucket = bucket.BucketResourceWithRawResponse(client.bucket)
        self.put_memory = put_memory.PutMemoryResourceWithRawResponse(client.put_memory)
        self.get_memory = get_memory.GetMemoryResourceWithRawResponse(client.get_memory)
        self.delete_memory = delete_memory.DeleteMemoryResourceWithRawResponse(client.delete_memory)
        self.summarize_memory = summarize_memory.SummarizeMemoryResourceWithRawResponse(client.summarize_memory)
        self.start_session = start_session.StartSessionResourceWithRawResponse(client.start_session)
        self.end_session = end_session.EndSessionResourceWithRawResponse(client.end_session)
        self.rehydrate_session = rehydrate_session.RehydrateSessionResourceWithRawResponse(client.rehydrate_session)
        self.put_procedure = put_procedure.PutProcedureResourceWithRawResponse(client.put_procedure)
        self.get_procedure = get_procedure.GetProcedureResourceWithRawResponse(client.get_procedure)
        self.delete_procedure = delete_procedure.DeleteProcedureResourceWithRawResponse(client.delete_procedure)
        self.list_procedures = list_procedures.ListProceduresResourceWithRawResponse(client.list_procedures)
        self.put_semantic_memory = put_semantic_memory.PutSemanticMemoryResourceWithRawResponse(
            client.put_semantic_memory
        )
        self.get_semantic_memory = get_semantic_memory.GetSemanticMemoryResourceWithRawResponse(
            client.get_semantic_memory
        )
        self.delete_semantic_memory = delete_semantic_memory.DeleteSemanticMemoryResourceWithRawResponse(
            client.delete_semantic_memory
        )


class AsyncRaindropWithRawResponse:
    def __init__(self, client: AsyncRaindrop) -> None:
        self.query = query.AsyncQueryResourceWithRawResponse(client.query)
        self.bucket = bucket.AsyncBucketResourceWithRawResponse(client.bucket)
        self.put_memory = put_memory.AsyncPutMemoryResourceWithRawResponse(client.put_memory)
        self.get_memory = get_memory.AsyncGetMemoryResourceWithRawResponse(client.get_memory)
        self.delete_memory = delete_memory.AsyncDeleteMemoryResourceWithRawResponse(client.delete_memory)
        self.summarize_memory = summarize_memory.AsyncSummarizeMemoryResourceWithRawResponse(client.summarize_memory)
        self.start_session = start_session.AsyncStartSessionResourceWithRawResponse(client.start_session)
        self.end_session = end_session.AsyncEndSessionResourceWithRawResponse(client.end_session)
        self.rehydrate_session = rehydrate_session.AsyncRehydrateSessionResourceWithRawResponse(
            client.rehydrate_session
        )
        self.put_procedure = put_procedure.AsyncPutProcedureResourceWithRawResponse(client.put_procedure)
        self.get_procedure = get_procedure.AsyncGetProcedureResourceWithRawResponse(client.get_procedure)
        self.delete_procedure = delete_procedure.AsyncDeleteProcedureResourceWithRawResponse(client.delete_procedure)
        self.list_procedures = list_procedures.AsyncListProceduresResourceWithRawResponse(client.list_procedures)
        self.put_semantic_memory = put_semantic_memory.AsyncPutSemanticMemoryResourceWithRawResponse(
            client.put_semantic_memory
        )
        self.get_semantic_memory = get_semantic_memory.AsyncGetSemanticMemoryResourceWithRawResponse(
            client.get_semantic_memory
        )
        self.delete_semantic_memory = delete_semantic_memory.AsyncDeleteSemanticMemoryResourceWithRawResponse(
            client.delete_semantic_memory
        )


class RaindropWithStreamedResponse:
    def __init__(self, client: Raindrop) -> None:
        self.query = query.QueryResourceWithStreamingResponse(client.query)
        self.bucket = bucket.BucketResourceWithStreamingResponse(client.bucket)
        self.put_memory = put_memory.PutMemoryResourceWithStreamingResponse(client.put_memory)
        self.get_memory = get_memory.GetMemoryResourceWithStreamingResponse(client.get_memory)
        self.delete_memory = delete_memory.DeleteMemoryResourceWithStreamingResponse(client.delete_memory)
        self.summarize_memory = summarize_memory.SummarizeMemoryResourceWithStreamingResponse(client.summarize_memory)
        self.start_session = start_session.StartSessionResourceWithStreamingResponse(client.start_session)
        self.end_session = end_session.EndSessionResourceWithStreamingResponse(client.end_session)
        self.rehydrate_session = rehydrate_session.RehydrateSessionResourceWithStreamingResponse(
            client.rehydrate_session
        )
        self.put_procedure = put_procedure.PutProcedureResourceWithStreamingResponse(client.put_procedure)
        self.get_procedure = get_procedure.GetProcedureResourceWithStreamingResponse(client.get_procedure)
        self.delete_procedure = delete_procedure.DeleteProcedureResourceWithStreamingResponse(client.delete_procedure)
        self.list_procedures = list_procedures.ListProceduresResourceWithStreamingResponse(client.list_procedures)
        self.put_semantic_memory = put_semantic_memory.PutSemanticMemoryResourceWithStreamingResponse(
            client.put_semantic_memory
        )
        self.get_semantic_memory = get_semantic_memory.GetSemanticMemoryResourceWithStreamingResponse(
            client.get_semantic_memory
        )
        self.delete_semantic_memory = delete_semantic_memory.DeleteSemanticMemoryResourceWithStreamingResponse(
            client.delete_semantic_memory
        )


class AsyncRaindropWithStreamedResponse:
    def __init__(self, client: AsyncRaindrop) -> None:
        self.query = query.AsyncQueryResourceWithStreamingResponse(client.query)
        self.bucket = bucket.AsyncBucketResourceWithStreamingResponse(client.bucket)
        self.put_memory = put_memory.AsyncPutMemoryResourceWithStreamingResponse(client.put_memory)
        self.get_memory = get_memory.AsyncGetMemoryResourceWithStreamingResponse(client.get_memory)
        self.delete_memory = delete_memory.AsyncDeleteMemoryResourceWithStreamingResponse(client.delete_memory)
        self.summarize_memory = summarize_memory.AsyncSummarizeMemoryResourceWithStreamingResponse(
            client.summarize_memory
        )
        self.start_session = start_session.AsyncStartSessionResourceWithStreamingResponse(client.start_session)
        self.end_session = end_session.AsyncEndSessionResourceWithStreamingResponse(client.end_session)
        self.rehydrate_session = rehydrate_session.AsyncRehydrateSessionResourceWithStreamingResponse(
            client.rehydrate_session
        )
        self.put_procedure = put_procedure.AsyncPutProcedureResourceWithStreamingResponse(client.put_procedure)
        self.get_procedure = get_procedure.AsyncGetProcedureResourceWithStreamingResponse(client.get_procedure)
        self.delete_procedure = delete_procedure.AsyncDeleteProcedureResourceWithStreamingResponse(
            client.delete_procedure
        )
        self.list_procedures = list_procedures.AsyncListProceduresResourceWithStreamingResponse(client.list_procedures)
        self.put_semantic_memory = put_semantic_memory.AsyncPutSemanticMemoryResourceWithStreamingResponse(
            client.put_semantic_memory
        )
        self.get_semantic_memory = get_semantic_memory.AsyncGetSemanticMemoryResourceWithStreamingResponse(
            client.get_semantic_memory
        )
        self.delete_semantic_memory = delete_semantic_memory.AsyncDeleteSemanticMemoryResourceWithStreamingResponse(
            client.delete_semantic_memory
        )


Client = Raindrop

AsyncClient = AsyncRaindrop

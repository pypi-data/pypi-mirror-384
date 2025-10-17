# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable, Optional
from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo
from .bucket_locator_param import BucketLocatorParam

__all__ = ["QueryChunkSearchParams"]


class QueryChunkSearchParams(TypedDict, total=False):
    bucket_locations: Required[Annotated[Iterable[BucketLocatorParam], PropertyInfo(alias="bucketLocations")]]
    """The buckets to search.

    If provided, the search will only return results from these buckets
    """

    input: Required[str]
    """Natural language query or question.

    Can include complex criteria and relationships. The system will optimize the
    search strategy based on this input
    """

    request_id: Required[Annotated[str, PropertyInfo(alias="requestId")]]
    """Client-provided search session identifier.

    Required for pagination and result tracking. We recommend using a UUID or ULID
    for this value
    """

    partition: Optional[str]
    """Optional partition identifier for multi-tenant data isolation.

    Defaults to 'default' if not specified
    """

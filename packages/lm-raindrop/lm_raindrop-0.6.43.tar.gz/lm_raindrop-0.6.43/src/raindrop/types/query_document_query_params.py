# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo
from .bucket_locator_param import BucketLocatorParam

__all__ = ["QueryDocumentQueryParams"]


class QueryDocumentQueryParams(TypedDict, total=False):
    bucket_location: Required[Annotated[BucketLocatorParam, PropertyInfo(alias="bucketLocation")]]
    """The storage bucket containing the target document.

    Must be a valid, registered Smart Bucket. Used to identify which bucket to query
    against
    """

    input: Required[str]
    """User's input or question about the document.

    Can be natural language questions, commands, or requests. The system will
    process this against the document content
    """

    object_id: Required[Annotated[str, PropertyInfo(alias="objectId")]]
    """Document identifier within the bucket.

    Typically matches the storage path or key. Used to identify which document to
    chat with
    """

    request_id: Required[Annotated[str, PropertyInfo(alias="requestId")]]
    """Client-provided conversation session identifier.

    Required for maintaining context in follow-up questions. We recommend using a
    UUID or ULID for this value
    """

    partition: Optional[str]
    """Optional partition identifier for multi-tenant data isolation.

    Defaults to 'default' if not specified
    """

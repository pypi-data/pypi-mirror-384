# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from typing_extensions import Required, Annotated, TypedDict

from .._types import Base64FileInput
from .._utils import PropertyInfo
from .bucket_locator_param import BucketLocatorParam

__all__ = ["BucketPutParams"]


class BucketPutParams(TypedDict, total=False):
    bucket_location: Required[Annotated[BucketLocatorParam, PropertyInfo(alias="bucketLocation")]]
    """The buckets to search.

    If provided, the search will only return results from these buckets
    """

    content: Required[Annotated[Union[str, Base64FileInput], PropertyInfo(format="base64")]]
    """Binary content of the object"""

    content_type: Required[Annotated[str, PropertyInfo(alias="contentType")]]
    """MIME type of the object"""

    key: Required[str]
    """Object key/path in the bucket"""

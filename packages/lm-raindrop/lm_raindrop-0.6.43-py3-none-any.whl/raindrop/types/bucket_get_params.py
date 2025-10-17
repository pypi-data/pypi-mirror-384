# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo
from .bucket_locator_param import BucketLocatorParam

__all__ = ["BucketGetParams"]


class BucketGetParams(TypedDict, total=False):
    bucket_location: Required[Annotated[BucketLocatorParam, PropertyInfo(alias="bucketLocation")]]
    """The buckets to search.

    If provided, the search will only return results from these buckets
    """

    key: Required[str]
    """Object key/path to download"""

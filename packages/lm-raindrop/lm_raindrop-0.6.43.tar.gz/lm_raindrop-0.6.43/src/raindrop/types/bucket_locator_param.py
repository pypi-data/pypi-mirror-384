# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from typing_extensions import Required, TypeAlias, TypedDict

from .liquidmetal_v1alpha1_bucket_name_param import LiquidmetalV1alpha1BucketNameParam

__all__ = ["BucketLocatorParam", "Bucket"]


class Bucket(TypedDict, total=False):
    bucket: Required[LiquidmetalV1alpha1BucketNameParam]
    """**EXAMPLE** { name: 'my-smartbucket' } **REQUIRED** FALSE"""


BucketLocatorParam: TypeAlias = Union[Bucket, object]

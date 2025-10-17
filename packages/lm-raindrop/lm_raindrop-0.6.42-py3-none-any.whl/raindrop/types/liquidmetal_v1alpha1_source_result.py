# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel
from .shared.liquidmetal_v1alpha1_bucket_response import LiquidmetalV1alpha1BucketResponse

__all__ = ["LiquidmetalV1alpha1SourceResult"]


class LiquidmetalV1alpha1SourceResult(BaseModel):
    bucket: Optional[LiquidmetalV1alpha1BucketResponse] = None
    """The bucket information containing this result"""

    object: Optional[str] = None
    """The object key within the bucket"""

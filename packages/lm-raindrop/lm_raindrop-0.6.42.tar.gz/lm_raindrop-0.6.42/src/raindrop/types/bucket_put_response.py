# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel
from .shared.liquidmetal_v1alpha1_bucket_response import LiquidmetalV1alpha1BucketResponse

__all__ = ["BucketPutResponse"]


class BucketPutResponse(BaseModel):
    bucket: Optional[LiquidmetalV1alpha1BucketResponse] = None
    """Information about the bucket where the object was uploaded"""

    key: Optional[str] = None
    """Key/path of the uploaded object"""

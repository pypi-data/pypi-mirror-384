# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["BucketGetResponse"]


class BucketGetResponse(BaseModel):
    content: Optional[str] = None
    """
    No specific comments in original for these fields directly, but they were part
    of the original GetObjectResponse.
    """

    content_type: Optional[str] = FieldInfo(alias="contentType", default=None)

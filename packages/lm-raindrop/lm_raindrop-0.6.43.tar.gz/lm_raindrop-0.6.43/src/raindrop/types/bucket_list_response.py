# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Union
from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["BucketListResponse", "Object"]


class Object(BaseModel):
    content_type: str = FieldInfo(alias="contentType")
    """MIME type of the object"""

    key: str
    """Object key/path in the bucket"""

    last_modified: datetime = FieldInfo(alias="lastModified")
    """Last modification timestamp"""

    size: Union[int, str]
    """Size of the object in bytes"""


class BucketListResponse(BaseModel):
    objects: List[Object]
    """List of objects in the bucket with their metadata."""

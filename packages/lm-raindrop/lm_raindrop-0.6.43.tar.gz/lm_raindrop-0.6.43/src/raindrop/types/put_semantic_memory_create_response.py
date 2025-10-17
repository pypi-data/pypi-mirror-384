# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["PutSemanticMemoryCreateResponse"]


class PutSemanticMemoryCreateResponse(BaseModel):
    error: Optional[str] = None
    """Error message if the operation failed"""

    object_id: Optional[str] = FieldInfo(alias="objectId", default=None)
    """Unique object identifier for the stored document"""

    success: Optional[bool] = None
    """Indicates whether the document was stored successfully"""

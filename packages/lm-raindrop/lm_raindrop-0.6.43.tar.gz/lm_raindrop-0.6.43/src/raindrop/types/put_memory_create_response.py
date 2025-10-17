# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["PutMemoryCreateResponse"]


class PutMemoryCreateResponse(BaseModel):
    memory_id: Optional[str] = FieldInfo(alias="memoryId", default=None)
    """Unique identifier for the stored memory entry"""

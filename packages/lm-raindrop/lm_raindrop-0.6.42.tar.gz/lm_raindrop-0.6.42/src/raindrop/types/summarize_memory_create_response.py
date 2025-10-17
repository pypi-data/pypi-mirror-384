# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["SummarizeMemoryCreateResponse"]


class SummarizeMemoryCreateResponse(BaseModel):
    summarized_memory_ids: Optional[List[str]] = FieldInfo(alias="summarizedMemoryIds", default=None)
    """List of memory IDs that were summarized"""

    summary: Optional[str] = None
    """AI-generated summary of the memories"""

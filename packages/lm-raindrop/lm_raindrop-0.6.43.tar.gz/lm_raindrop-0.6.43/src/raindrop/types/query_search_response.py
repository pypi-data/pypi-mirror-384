# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .liquidmetal_v1alpha1_text_result import LiquidmetalV1alpha1TextResult

__all__ = ["QuerySearchResponse", "Pagination"]


class Pagination(BaseModel):
    page: int
    """Current page number (1-based)"""

    page_size: int = FieldInfo(alias="pageSize")
    """Results per page. May be adjusted for performance"""

    has_more: Optional[bool] = FieldInfo(alias="hasMore", default=None)
    """Indicates more results available. Used for infinite scroll implementation"""

    total: Optional[int] = None
    """Total number of available results"""

    total_pages: Optional[int] = FieldInfo(alias="totalPages", default=None)
    """Total available pages. Calculated as ceil(total/pageSize)"""


class QuerySearchResponse(BaseModel):
    pagination: Optional[Pagination] = None
    """Pagination details for result navigation"""

    results: Optional[List[LiquidmetalV1alpha1TextResult]] = None
    """Matched results with metadata"""

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from .._models import BaseModel
from .liquidmetal_v1alpha1_text_result import LiquidmetalV1alpha1TextResult

__all__ = ["QueryChunkSearchResponse"]


class QueryChunkSearchResponse(BaseModel):
    results: Optional[List[LiquidmetalV1alpha1TextResult]] = None
    """Ordered list of relevant text segments.

    Each result includes full context and metadata
    """

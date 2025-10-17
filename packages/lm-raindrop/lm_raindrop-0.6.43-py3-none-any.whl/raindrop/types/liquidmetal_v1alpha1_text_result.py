# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .liquidmetal_v1alpha1_source_result import LiquidmetalV1alpha1SourceResult

__all__ = ["LiquidmetalV1alpha1TextResult"]


class LiquidmetalV1alpha1TextResult(BaseModel):
    chunk_signature: Optional[str] = FieldInfo(alias="chunkSignature", default=None)
    """Unique identifier for this text segment.

    Used for deduplication and result tracking
    """

    embed: Optional[str] = None
    """Vector representation for similarity matching.

    Used in semantic search operations
    """

    payload_signature: Optional[str] = FieldInfo(alias="payloadSignature", default=None)
    """Parent document identifier. Links related content chunks together"""

    score: Optional[float] = None
    """Relevance score (0.0 to 1.0). Higher scores indicate better matches"""

    source: Optional[LiquidmetalV1alpha1SourceResult] = None
    """Source document references. Contains bucket and object information"""

    text: Optional[str] = None
    """The actual content of the result. May be a document excerpt or full content"""

    type: Optional[str] = None
    """Content MIME type. Helps with proper result rendering"""

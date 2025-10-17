# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["SemanticMemorySearchResponse", "DocumentSearchResponse", "DocumentSearchResponseResult"]


class DocumentSearchResponseResult(BaseModel):
    chunk_signature: Optional[str] = FieldInfo(alias="chunkSignature", default=None)
    """Unique signature for this search result chunk"""

    embed: Optional[str] = None
    """Embedding vector information (if available)"""

    payload_signature: Optional[str] = FieldInfo(alias="payloadSignature", default=None)
    """Payload signature for the original document"""

    score: Optional[float] = None
    """Relevance score for this search result"""

    source: Optional[str] = None
    """Source reference for the matched content"""

    text: Optional[str] = None
    """Matched text content from the document"""

    type: Optional[str] = None
    """Type of the matched content"""


class DocumentSearchResponse(BaseModel):
    results: Optional[List[DocumentSearchResponseResult]] = None
    """List of matching documents ordered by relevance"""


class SemanticMemorySearchResponse(BaseModel):
    document_search_response: Optional[DocumentSearchResponse] = FieldInfo(alias="documentSearchResponse", default=None)
    """Search results with matching documents"""

    error: Optional[str] = None
    """Error message if the search failed"""

    success: Optional[bool] = None
    """Indicates whether the search was performed successfully"""

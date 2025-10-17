# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Union, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["EpisodicMemorySearchResponse", "Entry", "Pagination"]


class Entry(BaseModel):
    agent: Optional[str] = None
    """Agent that created this episodic memory"""

    created_at: Optional[datetime] = FieldInfo(alias="createdAt", default=None)
    """When this episodic memory was created"""

    duration: Union[int, str, None] = None
    """Duration of the session in milliseconds"""

    entry_count: Optional[int] = FieldInfo(alias="entryCount", default=None)
    """Number of individual memory entries in this session"""

    score: Optional[float] = None
    """Relevance score for this search result"""

    session_id: Optional[str] = FieldInfo(alias="sessionId", default=None)
    """Session identifier for this episodic memory"""

    summary: Optional[str] = None
    """AI-generated summary of the session"""

    timeline_count: Optional[int] = FieldInfo(alias="timelineCount", default=None)
    """Number of different timelines in this session"""


class Pagination(BaseModel):
    has_more: Optional[bool] = FieldInfo(alias="hasMore", default=None)
    """Whether there are more results available"""

    page: Optional[int] = None
    """Current page number"""

    page_size: Optional[int] = FieldInfo(alias="pageSize", default=None)
    """Number of results per page"""

    total: Optional[int] = None
    """Total number of results available"""

    total_pages: Optional[int] = FieldInfo(alias="totalPages", default=None)
    """Total number of pages available"""


class EpisodicMemorySearchResponse(BaseModel):
    entries: Optional[List[Entry]] = None
    """List of matching episodic memory entries ordered by relevance"""

    pagination: Optional[Pagination] = None
    """Pagination information for the search results"""

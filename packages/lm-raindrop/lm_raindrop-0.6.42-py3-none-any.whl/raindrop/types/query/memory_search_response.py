# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["MemorySearchResponse", "Memory"]


class Memory(BaseModel):
    id: Optional[str] = None
    """Unique identifier for this memory entry"""

    agent: Optional[str] = None
    """Optional agent identifier"""

    at: Optional[datetime] = None
    """When this memory was created"""

    by: Optional[str] = None
    """Agent that created this memory"""

    content: Optional[str] = None
    """The actual memory content"""

    due_to: Optional[str] = FieldInfo(alias="dueTo", default=None)
    """What triggered this memory creation"""

    key: Optional[str] = None
    """Optional key for direct retrieval"""

    session_id: Optional[str] = FieldInfo(alias="sessionId", default=None)
    """Session identifier where this memory was created"""

    timeline: Optional[str] = None
    """Timeline this memory belongs to"""


class MemorySearchResponse(BaseModel):
    memories: Optional[List[Memory]] = None
    """List of matching memory entries ordered by relevance"""

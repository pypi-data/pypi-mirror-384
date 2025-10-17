# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["StartSessionCreateResponse"]


class StartSessionCreateResponse(BaseModel):
    session_id: Optional[str] = FieldInfo(alias="sessionId", default=None)
    """Unique identifier for the new session"""

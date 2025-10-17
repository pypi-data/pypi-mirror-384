# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel

__all__ = ["QuerySumarizePageResponse"]


class QuerySumarizePageResponse(BaseModel):
    summary: Optional[str] = None
    """
    AI-generated summary including key themes and topics, content type distribution,
    important findings, and document relationships
    """

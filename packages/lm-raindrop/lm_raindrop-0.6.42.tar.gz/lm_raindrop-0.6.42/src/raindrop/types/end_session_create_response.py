# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel

__all__ = ["EndSessionCreateResponse"]


class EndSessionCreateResponse(BaseModel):
    success: Optional[bool] = None
    """Indicates whether the session was ended successfully"""

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["RehydrateSessionRehydrateResponse"]


class RehydrateSessionRehydrateResponse(BaseModel):
    operation: Optional[str] = None
    """
    Operation status: 'initiated' for async processing, 'failed' for immediate
    failure
    """

    status_key: Optional[str] = FieldInfo(alias="statusKey", default=None)
    """Storage key for checking async operation status (optional)"""

    success: Optional[bool] = None
    """Indicates whether the rehydration was successful"""

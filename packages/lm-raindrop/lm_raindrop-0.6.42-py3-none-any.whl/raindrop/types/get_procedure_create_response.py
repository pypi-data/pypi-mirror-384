# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel

__all__ = ["GetProcedureCreateResponse"]


class GetProcedureCreateResponse(BaseModel):
    found: Optional[bool] = None
    """Indicates whether the procedure was found"""

    value: Optional[str] = None
    """The procedure content, or empty if not found"""

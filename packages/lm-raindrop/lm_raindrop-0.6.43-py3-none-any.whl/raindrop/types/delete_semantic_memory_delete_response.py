# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel

__all__ = ["DeleteSemanticMemoryDeleteResponse"]


class DeleteSemanticMemoryDeleteResponse(BaseModel):
    error: Optional[str] = None
    """Error message if the operation failed"""

    success: Optional[bool] = None
    """Indicates whether the document was deleted successfully"""

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["ListProcedureCreateResponse", "Procedure"]


class Procedure(BaseModel):
    created_at: Optional[datetime] = FieldInfo(alias="createdAt", default=None)
    """When this procedure was first created"""

    key: Optional[str] = None
    """Unique key for this procedure"""

    updated_at: Optional[datetime] = FieldInfo(alias="updatedAt", default=None)
    """When this procedure was last updated"""

    value: Optional[str] = None
    """The procedure content"""


class ListProcedureCreateResponse(BaseModel):
    procedures: Optional[List[Procedure]] = None
    """List of all stored procedures"""

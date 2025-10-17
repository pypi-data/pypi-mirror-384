# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["LiquidmetalV1alpha1SmartMemoryName"]


class LiquidmetalV1alpha1SmartMemoryName(BaseModel):
    application_name: Optional[str] = FieldInfo(alias="applicationName", default=None)
    """Optional Application **EXAMPLE** "my-app" **REQUIRED** TRUE"""

    name: str
    """The name of the smart memory **EXAMPLE** "my-smartmemory" **REQUIRED** TRUE"""

    version: Optional[str] = None
    """
    Optional version of the smart memory **EXAMPLE** "01jtryx2f2f61ryk06vd8mr91p"
    **REQUIRED** TRUE
    """

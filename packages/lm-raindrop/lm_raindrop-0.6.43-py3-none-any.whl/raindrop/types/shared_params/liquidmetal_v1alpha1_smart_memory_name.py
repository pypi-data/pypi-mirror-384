# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["LiquidmetalV1alpha1SmartMemoryName"]


class LiquidmetalV1alpha1SmartMemoryName(TypedDict, total=False):
    application_name: Required[Annotated[Optional[str], PropertyInfo(alias="applicationName")]]
    """Optional Application **EXAMPLE** "my-app" **REQUIRED** TRUE"""

    name: Required[str]
    """The name of the smart memory **EXAMPLE** "my-smartmemory" **REQUIRED** TRUE"""

    version: Required[Optional[str]]
    """
    Optional version of the smart memory **EXAMPLE** "01jtryx2f2f61ryk06vd8mr91p"
    **REQUIRED** TRUE
    """

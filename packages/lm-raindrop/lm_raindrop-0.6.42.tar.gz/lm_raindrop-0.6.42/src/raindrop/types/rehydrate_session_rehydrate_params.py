# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Optional
from typing_extensions import Required, Annotated, TypeAlias, TypedDict

from .._utils import PropertyInfo
from .shared_params.liquidmetal_v1alpha1_smart_memory_name import LiquidmetalV1alpha1SmartMemoryName

__all__ = ["RehydrateSessionRehydrateParams", "SmartMemoryLocation", "SmartMemoryLocationSmartMemory"]


class RehydrateSessionRehydrateParams(TypedDict, total=False):
    session_id: Required[Annotated[str, PropertyInfo(alias="sessionId")]]
    """Session identifier to restore from episodic memory"""

    smart_memory_location: Required[Annotated[SmartMemoryLocation, PropertyInfo(alias="smartMemoryLocation")]]
    """Smart memory locator for targeting the correct smart memory instance"""

    summary_only: Annotated[Optional[bool], PropertyInfo(alias="summaryOnly")]
    """If true, only restore a summary. If false, restore all memories"""


class SmartMemoryLocationSmartMemory(TypedDict, total=False):
    smart_memory: Required[Annotated[LiquidmetalV1alpha1SmartMemoryName, PropertyInfo(alias="smartMemory")]]
    """
    **EXAMPLE** {"name":"memory-name","applicationName":"demo","version":"1234"}
    **REQUIRED** FALSE
    """


SmartMemoryLocation: TypeAlias = Union[SmartMemoryLocationSmartMemory, object]

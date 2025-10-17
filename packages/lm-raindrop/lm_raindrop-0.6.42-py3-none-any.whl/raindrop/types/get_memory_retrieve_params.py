# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Optional
from datetime import datetime
from typing_extensions import Required, Annotated, TypeAlias, TypedDict

from .._utils import PropertyInfo
from .shared_params.liquidmetal_v1alpha1_smart_memory_name import LiquidmetalV1alpha1SmartMemoryName

__all__ = ["GetMemoryRetrieveParams", "SmartMemoryLocation", "SmartMemoryLocationSmartMemory"]


class GetMemoryRetrieveParams(TypedDict, total=False):
    session_id: Required[Annotated[str, PropertyInfo(alias="sessionId")]]
    """Unique session identifier for the working memory instance"""

    smart_memory_location: Required[Annotated[SmartMemoryLocation, PropertyInfo(alias="smartMemoryLocation")]]
    """Smart memory locator for targeting the correct smart memory instance"""

    end_time: Annotated[Union[str, datetime, None], PropertyInfo(alias="endTime", format="iso8601")]
    """End time for temporal filtering"""

    key: Optional[str]
    """Specific key to retrieve"""

    n_most_recent: Annotated[Optional[int], PropertyInfo(alias="nMostRecent")]
    """Maximum number of most recent memories to return"""

    start_time: Annotated[Union[str, datetime, None], PropertyInfo(alias="startTime", format="iso8601")]
    """Start time for temporal filtering"""

    timeline: Optional[str]
    """Timeline to filter memories"""


class SmartMemoryLocationSmartMemory(TypedDict, total=False):
    smart_memory: Required[Annotated[LiquidmetalV1alpha1SmartMemoryName, PropertyInfo(alias="smartMemory")]]
    """
    **EXAMPLE** {"name":"memory-name","applicationName":"demo","version":"1234"}
    **REQUIRED** FALSE
    """


SmartMemoryLocation: TypeAlias = Union[SmartMemoryLocationSmartMemory, object]

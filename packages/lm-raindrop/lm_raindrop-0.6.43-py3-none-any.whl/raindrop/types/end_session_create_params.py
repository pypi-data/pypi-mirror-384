# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Optional
from typing_extensions import Required, Annotated, TypeAlias, TypedDict

from .._utils import PropertyInfo
from .shared_params.liquidmetal_v1alpha1_smart_memory_name import LiquidmetalV1alpha1SmartMemoryName

__all__ = ["EndSessionCreateParams", "SmartMemoryLocation", "SmartMemoryLocationSmartMemory"]


class EndSessionCreateParams(TypedDict, total=False):
    session_id: Required[Annotated[str, PropertyInfo(alias="sessionId")]]
    """Unique session identifier to end"""

    smart_memory_location: Required[Annotated[SmartMemoryLocation, PropertyInfo(alias="smartMemoryLocation")]]
    """Smart memory locator for targeting the correct smart memory instance"""

    flush: Optional[bool]
    """Whether to flush working memory to long-term storage"""

    system_prompt: Annotated[Optional[str], PropertyInfo(alias="systemPrompt")]
    """Optional custom system prompt for memory summarization during flush"""


class SmartMemoryLocationSmartMemory(TypedDict, total=False):
    smart_memory: Required[Annotated[LiquidmetalV1alpha1SmartMemoryName, PropertyInfo(alias="smartMemory")]]
    """
    **EXAMPLE** {"name":"memory-name","application_name":"demo","version":"1234"}
    **REQUIRED** FALSE
    """


SmartMemoryLocation: TypeAlias = Union[SmartMemoryLocationSmartMemory, object]

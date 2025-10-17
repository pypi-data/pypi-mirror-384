# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["QuerySumarizePageParams"]


class QuerySumarizePageParams(TypedDict, total=False):
    page: Required[int]
    """Target page number (1-based)"""

    page_size: Required[Annotated[int, PropertyInfo(alias="pageSize")]]
    """Results per page. Affects summary granularity"""

    request_id: Required[Annotated[str, PropertyInfo(alias="requestId")]]
    """Original search session identifier from the initial search"""

    partition: Optional[str]
    """Optional partition identifier for multi-tenant data isolation.

    Defaults to 'default' if not specified
    """

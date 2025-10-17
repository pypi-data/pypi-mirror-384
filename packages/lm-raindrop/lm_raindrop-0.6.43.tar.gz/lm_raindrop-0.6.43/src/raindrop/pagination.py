# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Generic, TypeVar, Optional, cast
from typing_extensions import override

from pydantic import Field as FieldInfo

from ._models import BaseModel
from ._base_client import BasePage, PageInfo, BaseSyncPage, BaseAsyncPage

__all__ = ["PageNumberPagination", "SyncPageNumber", "AsyncPageNumber"]

_T = TypeVar("_T")


class PageNumberPagination(BaseModel):
    page: Optional[int] = None

    page_size: Optional[int] = FieldInfo(alias="pageSize", default=None)

    total_pages: Optional[int] = FieldInfo(alias="totalPages", default=None)


class SyncPageNumber(BaseSyncPage[_T], BasePage[_T], Generic[_T]):
    results: List[_T]
    pagination: Optional[PageNumberPagination] = None

    @override
    def _get_page_items(self) -> List[_T]:
        results = self.results
        if not results:
            return []
        return results

    @override
    def next_page_info(self) -> Optional[PageInfo]:
        last_page = cast("int | None", self._options.params.get("page")) or 1

        return PageInfo(json={"page": last_page + 1})


class AsyncPageNumber(BaseAsyncPage[_T], BasePage[_T], Generic[_T]):
    results: List[_T]
    pagination: Optional[PageNumberPagination] = None

    @override
    def _get_page_items(self) -> List[_T]:
        results = self.results
        if not results:
            return []
        return results

    @override
    def next_page_info(self) -> Optional[PageInfo]:
        last_page = cast("int | None", self._options.params.get("page")) or 1

        return PageInfo(json={"page": last_page + 1})

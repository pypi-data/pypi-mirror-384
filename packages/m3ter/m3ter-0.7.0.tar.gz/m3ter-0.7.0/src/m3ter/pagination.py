# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Generic, TypeVar, Optional
from typing_extensions import override

from pydantic import Field as FieldInfo

from ._base_client import BasePage, PageInfo, BaseSyncPage, BaseAsyncPage

__all__ = ["SyncCursor", "AsyncCursor"]

_T = TypeVar("_T")


class SyncCursor(BaseSyncPage[_T], BasePage[_T], Generic[_T]):
    data: List[_T]
    next_token: Optional[str] = FieldInfo(alias="nextToken", default=None)

    @override
    def _get_page_items(self) -> List[_T]:
        data = self.data
        if not data:
            return []
        return data

    @override
    def next_page_info(self) -> Optional[PageInfo]:
        next_token = self.next_token
        if not next_token:
            return None

        return PageInfo(params={"nextToken": next_token})


class AsyncCursor(BaseAsyncPage[_T], BasePage[_T], Generic[_T]):
    data: List[_T]
    next_token: Optional[str] = FieldInfo(alias="nextToken", default=None)

    @override
    def _get_page_items(self) -> List[_T]:
        data = self.data
        if not data:
            return []
        return data

    @override
    def next_page_info(self) -> Optional[PageInfo]:
        next_token = self.next_token
        if not next_token:
            return None

        return PageInfo(params={"nextToken": next_token})

from langgraph.store.base import (
    BaseStore,
    SearchItem,
    _ensure_refresh,
)
from typing import Any, Optional, NamedTuple


class SearchOp(NamedTuple):
    """Operation to search for items within a specified namespace hierarchy, with sorting support."""

    namespace_prefix: tuple[str, ...]
    filter: Optional[dict[str, Any]] = None
    limit: int = 10
    offset: int = 0
    query: Optional[str] = None
    refresh_ttl: bool = True
    sort: Optional[dict[str, str]] = None  # Added sorting functionality


class EagleBaseStore(BaseStore):
    """Base store for Eagle-specific functionality, extending BaseStore."""

    def search(
        self,
        namespace_prefix: tuple[str, ...],
        /,
        *,
        query: Optional[str] = None,
        filter: Optional[dict[str, Any]] = None,
        limit: int = 10,
        offset: int = 0,
        sort: Optional[dict[str, str]] = None,
        refresh_ttl: Optional[bool] = None,
    ) -> list[SearchItem]:
        """Search for items within a namespace prefix, with optional sorting."""
        return self.batch(
            [
                SearchOp(
                    namespace_prefix,
                    filter,
                    limit,
                    offset,
                    query,
                    _ensure_refresh(self.ttl_config, refresh_ttl),
                    sort,
                )
            ]
        )[0]

    async def asearch(
        self,
        namespace_prefix: tuple[str, ...],
        /,
        *,
        query: Optional[str] = None,
        filter: Optional[dict[str, Any]] = None,
        limit: int = 10,
        offset: int = 0,
        sort: Optional[dict[str, str]] = None,
        refresh_ttl: Optional[bool] = None,
    ) -> list[SearchItem]:
        """Asynchronously search for items within a namespace prefix, with optional sorting."""
        return (
            await self.abatch(
                [
                    SearchOp(
                        namespace_prefix,
                        filter,
                        limit,
                        offset,
                        query,
                        _ensure_refresh(self.ttl_config, refresh_ttl),
                        sort,
                    )
                ]
            )
        )[0]

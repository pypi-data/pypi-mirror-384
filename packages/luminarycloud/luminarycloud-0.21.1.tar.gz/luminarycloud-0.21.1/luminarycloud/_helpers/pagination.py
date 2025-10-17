from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar

from .._client import get_default_client

T = TypeVar("T")


class PaginationIterator(ABC, Generic[T]):
    """Generic iterator class that provides length hint for paginated results."""

    @abstractmethod
    def _fetch_page(self, page_size: int, page_token: str) -> tuple[list[T], str, int]:
        """
        Fetch a page of results from the server.  Must return a tuple of the list of results, the
        next page token, and the total count of results.
        """
        pass

    def __init__(self, page_size: int):
        self._page_size: int = page_size
        self._page_token: str = ""
        self._total_count: Optional[int] = None
        self._current_page: Optional[list[T]] = None
        self._client = get_default_client()
        self._iterated_count: int = 0

    def __iter__(self) -> "PaginationIterator[T]":
        return self

    def __next__(self) -> T:
        if self._current_page is None:
            self._fetch_next_page()

        # _current_page really can't be None here, but this assertion is needed to appease mypy
        assert self._current_page is not None

        if len(self._current_page) == 0:
            if not self._page_token:
                raise StopIteration
            self._fetch_next_page()

        self._iterated_count += 1

        return self._current_page.pop(0)

    def _fetch_next_page(self) -> None:
        items, next_page_token, total_count = self._fetch_page(self._page_size, self._page_token)

        self._current_page = items
        self._page_token = next_page_token

        # Set length hint on first fetch if available
        if self._total_count is None:
            self._total_count = total_count

    def __length_hint__(self) -> int:
        if self._total_count is None:
            # Fetch first page to get total size if not already fetched
            if self._current_page is None:
                self._fetch_next_page()
        return max(0, (self._total_count or 0) - self._iterated_count)

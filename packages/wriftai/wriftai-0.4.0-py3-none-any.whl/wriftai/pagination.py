"""Pagination module."""

from dataclasses import dataclass
from typing import Generic, TypedDict, TypeVar

from wriftai.common_types import NotRequired

T = TypeVar("T")


class PaginationOptions(TypedDict):
    """Options for pagination.

    Attributes:
        cursor (NotRequired[str]): Cursor for pagination.
        page_size (NotRequired[int]): Number of items per page.
    """

    cursor: NotRequired[str]
    page_size: NotRequired[int]


@dataclass
class PaginatedResponse(Generic[T]):
    """Represents a paginated response.

    Attributes:
        items (list[T]): List of items returned in the current page.
        next_cursor (str | None): Cursor pointing to the next page.
        previous_cursor (str | None): Cursor pointing to the previous page.
        next_url (str | None): URL to fetch the next page.
        previous_url (str | None): URL to fetch the previous page.
    """

    items: list[T]
    next_cursor: str | None
    previous_cursor: str | None
    next_url: str | None
    previous_url: str | None

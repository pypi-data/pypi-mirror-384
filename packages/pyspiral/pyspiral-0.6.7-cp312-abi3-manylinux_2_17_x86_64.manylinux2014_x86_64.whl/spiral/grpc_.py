from collections.abc import AsyncIterator, Awaitable, Callable
from typing import TypeVar

R = TypeVar("R")
T = TypeVar("T")


async def paged(stub_fn: Callable[[R], Awaitable[T]], request: R, page_size: int = None) -> AsyncIterator[T]:
    """Page through a gRPC paged API.

    Assumes fields exist as per https://cloud.google.com/apis/design/design_patterns#list_pagination
    """
    next_page_token: str | None = None
    while True:
        request.page_size = page_size
        request.page_token = next_page_token
        res = await stub_fn(request)
        if not res.next_page_token:
            # No more items
            yield res
            break

        next_page_token = res.next_page_token
        yield res


async def paged_items(
    stub_fn: Callable[[R], Awaitable[T]], request: R, collection_name: str, page_size: int = None
) -> AsyncIterator:
    async for page in paged(stub_fn, request, page_size=page_size):
        for item in getattr(page, collection_name):
            yield item

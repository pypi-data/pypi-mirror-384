"""Pagination."""

import builtins
import itertools
from typing import Generic, TypeVar

T = TypeVar("T")


class Pager(Generic[T]):
    """Adapts OpenAPI pagination to the Python iterator protocol.

    TileDB API listings consists of a sequence of "pages", or batches,
    of lists of assets. A Pager instance represents one page of the
    listing. It also serves as an iterator over all items from that page
    to the last page, and it can be indexed to get all or a subset of
    items from that page to the last page.

    Attributes
    ----------
    func : callable
        A function that takes at least a page keyword argument and
        returns a page of results. The signature of func is
        (*args, page: int, **kwargs) -> list.
    args : tuple
        Positional arguments to be passed to func.
    kwargs : dict
        Keyword arguments to be passed to func.
    page : int
        The number of the current listing page.
    response : object
        The value of the current listing page.

    Notes
    -----
    Negative indexing is based on an initial snapshot of the total
    number of items in a result set. If items are added or removed
    during pagination, the indexing may no longer be correct.
    """

    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.page = None
        self.response = None

    def _generate(self):
        """Yield all items from current page to last page."""
        if not self.response:
            self.call_page(1)
        if self.response.data:
            yield from self.response.data
            page = self.page + 1
            while page <= self.response.pagination_metadata.total_pages:
                results_page = self.func(*self.args, page=page, **self.kwargs)
                if not results_page.data:
                    break
                yield from results_page.data
                page += 1

    def __getitem__(self, index):
        if not self.response:
            self.call_page(1)
        total_items = self.response.pagination_metadata.total_items
        if isinstance(index, int):
            if index < 0:
                index += total_items
            return builtins.list(itertools.islice(self, index, index + 1))[0]
        elif isinstance(index, slice):
            start = index.start
            if isinstance(start, int) and start < 0:
                start += total_items
            stop = index.stop
            if isinstance(stop, int) and stop < 0:
                stop += total_items
            return builtins.list(itertools.islice(self, start, stop, index.step))

    def __iter__(self):
        return self._generate()

    @property
    def data(self):
        """Data of current results page."""
        return self.response.data

    @property
    def pagination_metadata(self):
        """Description of pagination scheme."""
        return self.response.pagination_metadata

    def call_page(self, page):
        """Call for a page of results to store."""
        response = self.func(*self.args, page=page, **self.kwargs)
        self.response = response
        self.page = response.pagination_metadata.page

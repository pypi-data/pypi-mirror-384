from spiral.core.client import KeySpaceIndex as CoreKeySpaceIndex
from spiral.expressions import Expr
from spiral.types_ import Timestamp


class KeySpaceIndex:
    """
    KeysIndex represents an optionally materialized key space, defined by a projection and a filter over a table.
    It can be used to efficiently and precisely shard the table for parallel processing or distributed training.

    An index is defined by:
    - A granularity that defines the target size of key ranges in the index.
        IMPORTANT: Actual key ranges may be smaller, but will not exceed twice the granularity.
    - A projection expression that defines which columns are included in the resulting key space.
    - An optional filter expression that defines which rows are included in the index.
    """

    def __init__(self, core: CoreKeySpaceIndex, *, name: str | None = None):
        self.core = core
        self._name = name

    @property
    def index_id(self) -> str:
        return self.core.id

    @property
    def table_id(self) -> str:
        return self.core.table_id

    @property
    def name(self) -> str:
        return self._name or self.index_id

    @property
    def asof(self) -> Timestamp:
        return self.core.asof

    @property
    def projection(self) -> Expr:
        return Expr(self.core.projection)

    @property
    def filter(self) -> Expr | None:
        return Expr(self.core.filter) if self.core.filter is not None else None

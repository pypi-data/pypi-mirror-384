from typing import TYPE_CHECKING

from spiral.core.table import Snapshot as CoreSnapshot
from spiral.core.table.spec import Schema
from spiral.types_ import Timestamp

if TYPE_CHECKING:
    import duckdb
    import polars as pl
    import pyarrow.dataset as ds
    import torch.utils.data as torchdata  # noqa

    from spiral.table import Table


class Snapshot:
    """Spiral table snapshot.

    A snapshot represents a point-in-time view of a table.
    """

    def __init__(self, table: "Table", core: CoreSnapshot):
        self.core = core
        self._table = table

    @property
    def asof(self) -> Timestamp:
        """Returns the asof timestamp of the snapshot."""
        return self.core.asof

    def schema(self) -> Schema:
        """Returns the schema of the snapshot."""
        return self.core.table.get_schema(asof=self.asof)

    @property
    def table(self) -> "Table":
        """Returns the table associated with the snapshot."""
        return self._table

    def to_dataset(self) -> "ds.Dataset":
        """Returns a PyArrow Dataset representing the table."""
        from spiral.dataset import Dataset

        return Dataset(self)

    def to_polars(self) -> "pl.LazyFrame":
        """Returns a Polars LazyFrame for the Spiral table."""
        import polars as pl

        return pl.scan_pyarrow_dataset(self.to_dataset())

    def to_duckdb(self) -> "duckdb.DuckDBPyRelation":
        """Returns a DuckDB relation for the Spiral table."""
        import duckdb

        return duckdb.from_arrow(self.to_dataset())

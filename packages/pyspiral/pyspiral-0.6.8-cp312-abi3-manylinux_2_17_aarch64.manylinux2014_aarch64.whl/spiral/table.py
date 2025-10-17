from datetime import datetime
from typing import TYPE_CHECKING, Any

from spiral.core.table import Table as CoreTable
from spiral.core.table.spec import Schema
from spiral.expressions.base import Expr, ExprLike
from spiral.settings import settings
from spiral.snapshot import Snapshot
from spiral.transaction import Transaction

if TYPE_CHECKING:
    import duckdb
    import polars as pl
    import pyarrow.dataset as ds
    import streaming
    import torch.utils.data as torchdata  # noqa

    from spiral.client import Spiral
    from spiral.dataloader import SpiralDataLoader
    from spiral.key_space_index import KeySpaceIndex


class Table(Expr):
    """API for interacting with a SpiralDB's Table.

    Spiral Table is a powerful and flexible way for storing, analyzing,
    and querying massive and/or multimodal datasets. The data model will feel familiar
    to users of SQL- or DataFrame-style systems, yet is designed to be more flexible, more powerful,
    and more useful in the context of modern data processing.

    Tables are stored and queried directly from object storage.
    """

    def __init__(self, spiral: "Spiral", core: CoreTable, *, identifier: str | None = None):
        super().__init__(core.__expr__)

        self.spiral = spiral
        self.core = core

        self._key_schema = core.key_schema
        self._key_columns = set(self._key_schema.names)
        self._identifier = identifier

    @property
    def table_id(self) -> str:
        return self.core.id

    @property
    def identifier(self) -> str:
        """Returns the fully qualified identifier of the table."""
        return self._identifier or self.table_id

    @property
    def dataset(self) -> str | None:
        """Returns the dataset of the table."""
        if self._identifier is None:
            return None
        _, dataset, _ = self._identifier.split(".")
        return dataset

    @property
    def name(self) -> str | None:
        """Returns the name of the table."""
        if self._identifier is None:
            return None
        _, _, name = self._identifier.split(".")
        return name

    def last_modified_at(self) -> int:
        return self.core.get_wal(asof=None).last_modified_at

    def __str__(self):
        return self.identifier

    def __repr__(self):
        return f'Table("{self.identifier}")'

    def __getitem__(self, item: str) -> Expr:
        return super().__getitem__(item)

    def select(self, *paths: str, exclude: list[str] = None) -> "Expr":
        return super().select(*paths, exclude=exclude)

    @property
    def key_schema(self) -> Schema:
        """Returns the key schema of the table."""
        return self._key_schema

    def schema(self) -> Schema:
        """Returns the FULL schema of the table.

        NOTE: This can be expensive for large tables.
        """
        return self.core.get_schema(asof=None)

    def write(
        self,
        expr: ExprLike,
        *,
        partition_size_bytes: int | None = None,
    ) -> None:
        """Write an item to the table inside a single transaction.

        :param expr: The expression to write. Must evaluate to a struct array.
        :param partition_size_bytes: The maximum partition size in bytes.
        """
        with self.txn() as txn:
            txn.write(
                expr,
                partition_size_bytes=partition_size_bytes,
            )

    def drop_columns(self, column_paths: list[str]) -> None:
        """
        Drops the specified columns from the table.


        :param column_paths: Fully qualified column names. (e.g., "column_name" or "nested.field").
            All columns must exist, if a column doesn't exist the function will return an error.
        """
        with self.txn() as txn:
            txn.drop_columns(column_paths)

    def snapshot(self, asof: datetime | int | None = None) -> Snapshot:
        """Returns a snapshot of the table at the given timestamp."""
        if isinstance(asof, datetime):
            asof = int(asof.timestamp() * 1_000_000)
        return Snapshot(self, self.core.get_snapshot(asof=asof))

    def txn(self, retries: int | None = 3) -> Transaction:
        """Begins a new transaction. Transaction must be committed for writes to become visible.

        :param retries: Maximum number of retry attempts on conflict (default: 3). Set to None for a single attempt.

        IMPORTANT: While transaction can be used to atomically write data to the table,
             it is important that the primary key columns are unique within the transaction.
             The behavior is undefined if this is not the case.
        """
        return Transaction(self.spiral._core.transaction(self.core, settings().file_format, retries=retries))

    def to_dataset(self) -> "ds.Dataset":
        """Returns a PyArrow Dataset representing the table."""
        return self.snapshot().to_dataset()

    def to_polars(self) -> "pl.LazyFrame":
        """Returns a Polars LazyFrame for the Spiral table."""
        return self.snapshot().to_polars()

    def to_duckdb(self) -> "duckdb.DuckDBPyRelation":
        """Returns a DuckDB relation for the Spiral table."""
        return self.snapshot().to_duckdb()

    def to_data_loader(
        self,
        index: "KeySpaceIndex",
        *,
        projection: Expr | None = None,
        **kwargs,
    ) -> "SpiralDataLoader":
        """Read into a Torch-compatible DataLoader for single-node training.

        Args:
            index: Prebuilt KeysIndex to use when creating the stream.
                The index's `asof` will be used when scanning.
            projection: Optional projection to use when scanning the table if index's projection is not used.
                Projection must be compatible with the index's projection for correctness.
            **kwargs: Additional arguments passed to SpiralDataLoader constructor.
                See Scan#to_data_loader for supported arguments.

        Returns:
            SpiralDataLoader with shuffled shards.
        """
        if index.table_id != self.table_id:
            raise ValueError("Index must be built on the same table as the scan.")
        if index.asof == 0:
            raise ValueError("Index have to be synced before it can be used.")

        shards = self.spiral._core._ops().compute_shards(index=index.core)

        return self.spiral.scan(
            projection if projection is not None else index.projection,
            where=index.filter,
            asof=index.asof,
        ).to_data_loader(shards=shards, **kwargs)

    def to_distributed_data_loader(
        self,
        index: "KeySpaceIndex",
        *,
        projection: Expr | None = None,
        **kwargs,
    ) -> "SpiralDataLoader":
        """Read into a Torch-compatible DataLoader for distributed training.

        Args:
            index: Prebuilt KeysIndex to use when creating the stream.
                The index's `asof` will be used when scanning.
            projection: Optional projection to use when scanning the table if index's projection is not used.
                Projection must be compatible with the index's projection for correctness.
            **kwargs: Additional arguments passed to SpiralDataLoader constructor.
                See Scan#to_distributed_data_loader for supported arguments.

        Returns:
            SpiralDataLoader with shuffled shards.
        """
        if index.table_id != self.table_id:
            raise ValueError("Index must be built on the same table as the scan.")
        if index.asof == 0:
            raise ValueError("Index have to be synced before it can be used.")

        shards = self.spiral._core._ops().compute_shards(index=index.core)

        return self.spiral.scan(
            projection if projection is not None else index.projection,
            where=index.filter,
            asof=index.asof,
        ).to_distributed_data_loader(shards=shards, **kwargs)

    def resume_data_loader(
        self,
        index: "KeySpaceIndex",
        *,
        state: dict[str, Any],
        **kwargs,
    ) -> "SpiralDataLoader":
        """Resume a previously created DataLoader from a saved state.

        Args:
            index: Prebuilt KeysIndex to use when creating the stream.
                The index's `asof` will be used when scanning.
            state: State dictionary returned from a previous DataLoader's `state_dict()` method.
            **kwargs: Additional arguments passed to SpiralDataLoader constructor.
                See Scan#to_data_loader for supported arguments.

        Returns:
            SpiralDataLoader with shuffled shards.
        """
        if index.table_id != self.table_id:
            raise ValueError("Index must be built on the same table as the scan.")
        if index.asof == 0:
            raise ValueError("Index have to be synced before it can be used.")

        shards = self.spiral._core._ops().compute_shards(index=index.core)

        return self.spiral.scan(
            index.projection,
            where=index.filter,
            asof=index.asof,
        ).resume_data_loader(shards=shards, state=state, **kwargs)

    def to_streaming(
        self,
        index: "KeySpaceIndex",
        *,
        projection: Expr | None = None,
        cache_dir: str | None = None,
        shard_row_block_size: int | None = None,
    ) -> "streaming.Stream":
        """Returns a stream to be used with MosaicML's StreamingDataset.

        Requires `streaming` package to be installed.

        Args:
            index: Prebuilt KeysIndex to use when creating the stream.
                The index's `asof` will be used when scanning.
            projection: Optional projection to use when scanning the table if index's projection is not used.
                Projection must be compatible with the index's projection for correctness.
            cache_dir: Directory to use for caching data. If None, a temporary directory will be used.
            shard_row_block_size: Number of rows per segment of a shard file. Defaults to 8192.
                Value should be set to lower for larger rows.
        """
        from spiral.streaming_ import SpiralStream

        if index.table_id != self.table_id:
            raise ValueError("Index must be built on the same table as the scan.")
        if index.asof == 0:
            raise ValueError("Index have to be synced before it can be used.")

        # We know table from projection is in the session cause this method is on it.
        scan = self.spiral.scan(
            projection if projection is not None else index.projection,
            where=index.filter,
            asof=index.asof,
        )
        shards = self.spiral._core._ops().compute_shards(index=index.core)

        return SpiralStream(
            sp=self.spiral,
            scan=scan,
            shards=shards,
            cache_dir=cache_dir,
            shard_row_block_size=shard_row_block_size,
        )  # type: ignore[return-value]

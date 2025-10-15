from typing import Any, Literal

import pyarrow as pa
from spiral.api.types import DatasetName, IndexName, ProjectId, RootUri, TableName
from spiral.core.authn import Authn
from spiral.core.table import ColumnGroupState, KeyRange, KeySpaceState, Scan, Snapshot, Table, Transaction
from spiral.core.table.spec import ColumnGroup, Schema
from spiral.expressions import Expr

class Spiral:
    """A client for Spiral database"""
    def __init__(
        self,
        api_url: str | None = None,
        spfs_url: str | None = None,
        authn: Authn | None = None,
    ):
        """Initialize the Spiral client."""
        ...
    def authn(self) -> Authn:
        """Get the current authentication context."""
        ...

    def scan(
        self,
        projection: Expr,
        filter: Expr | None = None,
        asof: int | None = None,
        exclude_keys: bool | None = None,
    ) -> Scan:
        """Construct a table scan."""
        ...

    def transaction(self, table: Table, format: str | None = None, retries: int | None = 3) -> Transaction:
        """Being a table transaction."""
        ...

    def search(
        self,
        top_k: int,
        rank_by: Expr,
        *,
        filters: Expr | None = None,
        freshness_window_s: int | None = None,
    ) -> pa.RecordBatchReader:
        """Search an index.

        Searching an index returns a stream of record batches that match table's key schema + float score column.
        """
        ...

    def table(self, table_id: str) -> Table:
        """Get a table."""
        ...

    def create_table(
        self,
        project_id: ProjectId,
        dataset: DatasetName,
        table: TableName,
        key_schema: Schema,
        *,
        root_uri: RootUri | None = None,
        exist_ok: bool = False,
    ) -> Table:
        """Create a new table in the specified project."""
        ...

    def text_index(self, index_id: str) -> TextIndex:
        """Get a text index."""
        ...

    def create_text_index(
        self,
        project_id: ProjectId,
        name: IndexName,
        projection: Expr,
        filter: Expr | None = None,
        *,
        root_uri: RootUri | None = None,
        exist_ok: bool = False,
    ) -> TextIndex:
        """Create a new index in the specified project."""
        ...

    def key_space_index(self, index_id: str) -> KeySpaceIndex:
        """Get a key space index."""
        ...

    def create_key_space_index(
        self,
        project_id: ProjectId,
        name: IndexName,
        granularity: int,
        projection: Expr,
        filter: Expr | None = None,
        *,
        root_uri: RootUri | None = None,
        exist_ok: bool = False,
    ) -> KeySpaceIndex:
        """Create a new key space index in the specified project."""
        ...

    def _ops(self, *, format: str | None = None) -> Operations:
        """Access maintenance operations.

        IMPORTANT: This API is internal and is currently exposed for development & testing.
            Maintenance operations are run by SpiralDB.
        """
        ...

class TextIndex:
    id: str

class KeySpaceIndex:
    id: str
    table_id: str
    granularity: int
    projection: Expr
    filter: Expr
    asof: int

class Shard:
    key_range: KeyRange
    cardinality: int

    def __init__(self, key_range: KeyRange, cardinality: int): ...

class ShuffleStrategy:
    # Results are buffered in a pool of `shuffle_buffer_size` rows and shuffled again.
    shuffle_buffer_size: int

    # All randomness is derived from this seed. If None, a random seed is generated from the OS.
    seed: int | None

    # Externally provided shards to shuffle before reading rows.
    shards: list[Shard] | None

    # Maximum number of rows to return in a single batch.
    # If None, it is derived from the shuffle buffer size.
    # IMPORTANT: The returned batch may be smaller than this size.
    max_batch_size: int | None

    def __init__(
        self,
        shuffle_buffer_size: int,
        *,
        seed: int | None = None,
        shards: list[Shard] | None = None,
        max_batch_size: int | None = None,
    ): ...

class Operations:
    def flush_wal(self, table: Table) -> None:
        """
        Flush the write-ahead log of the table.
        """
        ...
    def compact_key_space(
        self,
        *,
        table: Table,
        mode: Literal["plan", "read", "write"] | None = None,
        partition_bytes_min: int | None = None,
    ):
        """
        Compact the key space of the table.
        """
        ...
    def compact_column_group(
        self,
        table: Table,
        column_group: ColumnGroup,
        *,
        mode: Literal["plan", "read", "write"] | None = None,
        partition_bytes_min: int | None = None,
    ):
        """
        Compact a column group in the table.
        """
        ...
    def update_text_index(self, index: TextIndex, snapshot: Snapshot) -> None:
        """
        Index table changes up to the given snapshot.
        """
        ...
    def update_key_space_index(self, index: KeySpaceIndex, snapshot: Snapshot) -> None:
        """
        Index table changes up to the given snapshot.
        """
        ...
    def key_space_state(self, snapshot: Snapshot) -> KeySpaceState:
        """
        The key space state for the table.
        """
        ...
    def column_group_state(
        self, snapshot: Snapshot, key_space_state: KeySpaceState, column_group: ColumnGroup
    ) -> ColumnGroupState:
        """
        The state the column group of the table.
        """
        ...
    def column_groups_states(self, snapshot: Snapshot, key_space_state: KeySpaceState) -> list[ColumnGroupState]:
        """
        The state of each column group of the table.
        """
        ...
    def compute_shards(self, index: KeySpaceIndex) -> list[Shard]:
        """
        Compute the scan shards from a key space index.
        """
        ...
    def metrics(self) -> dict[str, Any]: ...

def flush_telemetry() -> None:
    """Flush telemetry data to the configured exporter."""
    ...

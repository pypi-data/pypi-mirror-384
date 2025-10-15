from typing import TYPE_CHECKING, Any

import pyarrow as pa

from spiral.core.client import ShuffleStrategy
from spiral.core.table import KeyRange
from spiral.core.table import Scan as CoreScan
from spiral.core.table.spec import Schema
from spiral.settings import CI, DEV

if TYPE_CHECKING:
    import dask.dataframe as dd
    import datasets.iterable_dataset as hf  # noqa
    import pandas as pd
    import polars as pl
    import streaming  # noqa
    import torch.utils.data as torchdata  # noqa


class Scan:
    """Scan object."""

    def __init__(self, core: CoreScan):
        self.core = core

    @property
    def metrics(self) -> dict[str, Any]:
        """Returns metrics about the scan."""
        return self.core.metrics()

    @property
    def schema(self) -> Schema:
        """Returns the schema of the scan."""
        return self.core.schema()

    def is_empty(self) -> bool:
        """Check if the Spiral is empty for the given key range.

        **IMPORTANT**: False negatives are possible, but false positives are not,
            i.e. is_empty can return False and scan can return zero rows.
        """
        return self.core.is_empty()

    def to_record_batches(
        self,
        key_table: pa.Table | pa.RecordBatchReader | None = None,
        batch_size: int | None = None,
        batch_readahead: int | None = None,
    ) -> pa.RecordBatchReader:
        """Read as a stream of RecordBatches.

        Args:
            key_table: a table of keys to "take" (including aux columns for cell-push-down).
                If None, the scan will be executed without a key table.
            batch_size: the maximum number of rows per returned batch.
                IMPORTANT: This is currently only respected when the key_table is used. If key table is a
                    RecordBatchReader, the batch_size argument must be None, and the existing batching is respected.
            batch_readahead: the number of batches to prefetch in the background.
        """
        if isinstance(key_table, pa.RecordBatchReader):
            if batch_size is not None:
                raise ValueError(
                    "batch_size must be None when key_table is a RecordBatchReader, the existing batching is respected."
                )
        elif isinstance(key_table, pa.Table):
            key_table = key_table.to_reader(max_chunksize=batch_size)

        return self.core.to_record_batches(key_table=key_table, batch_readahead=batch_readahead)

    def to_table(
        self,
        key_table: pa.Table | pa.RecordBatchReader | None = None,
    ) -> pa.Table:
        """Read into a single PyArrow Table.

        Args:
            key_table: a table of keys to "take" (including aux columns for cell-push-down).
                If None, the scan will be executed without a key table.
        """
        # NOTE: Evaluates fully on Rust side which improved debuggability.
        if DEV and not CI and key_table is None:
            rb = self.core.to_record_batch()
            return pa.Table.from_batches([rb])

        return self.to_record_batches(key_table=key_table).read_all()

    def to_dask(self) -> "dd.DataFrame":
        """Read into a Dask DataFrame.

        Requires the `dask` package to be installed.
        """
        import dask.dataframe as dd
        import pandas as pd

        def _read_key_range(key_range: KeyRange) -> pd.DataFrame:
            # TODO(ngates): we need a way to preserve the existing asofs?
            raise NotImplementedError()

        # Fetch a set of partition ranges
        return dd.from_map(_read_key_range, self._splits())

    def to_pandas(self) -> "pd.DataFrame":
        """Read into a Pandas DataFrame.

        Requires the `pandas` package to be installed.
        """
        return self.to_table().to_pandas()

    def to_polars(self) -> "pl.DataFrame":
        """Read into a Polars DataFrame.

        Requires the `polars` package to be installed.
        """
        import polars as pl

        return pl.from_arrow(self.to_record_batches())

    def to_iterable_dataset(
        self,
        shuffle: ShuffleStrategy | None = None,
        batch_readahead: int | None = None,
        num_workers: int | None = None,
        worker_id: int | None = None,
        infinite: bool = False,
    ) -> "hf.IterableDataset":
        """Returns a Huggingface's IterableDataset.

        Requires `datasets` package to be installed.

        Args:
            shuffle: Controls sample shuffling. If None, no shuffling is performed.
            batch_readahead: Controls how many batches to read ahead concurrently.
                If pipeline includes work after reading (e.g. decoding, transforming, ...) this can be set higher.
                Otherwise, it should be kept low to reduce next batch latency. Defaults to 2.
            num_workers: If not None, shards the scan across multiple workers.
                Must be used together with worker_id.
            worker_id: If not None, the id of the current worker.
                Scan will only return a subset of the data corresponding to the worker_id.
            infinite: If True, the returned IterableDataset will loop infinitely over the data,
                re-shuffling ranges after exhausting all data.
        """

        stream = self.core.to_shuffled_record_batches(
            shuffle,
            batch_readahead,
            num_workers,
            worker_id,
            infinite,
        )

        from spiral.iterable_dataset import to_iterable_dataset

        return to_iterable_dataset(stream)

    def _splits(self) -> list[KeyRange]:
        # Splits the scan into a set of key ranges.
        return self.core.splits()

    def _debug(self):
        # Visualizes the scan, mainly for debugging purposes.
        from spiral.debug.scan import show_scan

        show_scan(self.core)

    def _dump_manifests(self):
        # Print manifests in a human-readable format.
        from spiral.debug.manifests import display_scan_manifests

        display_scan_manifests(self.core)

    def _dump_metrics(self):
        # Print metrics in a human-readable format.
        from spiral.debug.metrics import display_metrics

        display_metrics(self.metrics)

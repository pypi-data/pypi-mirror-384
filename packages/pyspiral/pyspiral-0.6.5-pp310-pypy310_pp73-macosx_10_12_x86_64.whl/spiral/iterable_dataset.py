from collections.abc import Callable, Iterator
from typing import TYPE_CHECKING

import pyarrow as pa

if TYPE_CHECKING:
    import datasets.iterable_dataset as hf  # noqa
    import streaming  # noqa
    import torch.utils.data as torchdata  # noqa


def _hf_compatible_schema(schema: pa.Schema) -> pa.Schema:
    """
    Replace string-view and binary-view columns in the schema with strings/binary.
    Recursively handles nested types (struct, list, etc).
    We use this converted schema as Features in the returned Dataset.
    Remove this method once we have https://github.com/huggingface/datasets/pull/7718
    """

    def _convert_type(dtype: pa.DataType) -> pa.DataType:
        if dtype == pa.string_view():
            return pa.string()
        elif dtype == pa.binary_view():
            return pa.binary()
        elif pa.types.is_struct(dtype):
            new_fields = [
                pa.field(field.name, _convert_type(field.type), nullable=field.nullable, metadata=field.metadata)
                for field in dtype
            ]
            return pa.struct(new_fields)
        elif pa.types.is_list(dtype):
            return pa.list_(_convert_type(dtype.value_type))
        elif pa.types.is_large_list(dtype):
            return pa.large_list(_convert_type(dtype.value_type))
        elif pa.types.is_fixed_size_list(dtype):
            return pa.list_(_convert_type(dtype.value_type), dtype.list_size)
        elif pa.types.is_map(dtype):
            return pa.map_(_convert_type(dtype.key_type), _convert_type(dtype.item_type))
        else:
            return dtype

    new_fields = []
    for field in schema:
        new_type = _convert_type(field.type)
        new_fields.append(pa.field(field.name, new_type, nullable=field.nullable, metadata=field.metadata))

    return pa.schema(new_fields)


def to_iterable_dataset(stream: pa.RecordBatchReader) -> "hf.IterableDataset":
    from datasets import DatasetInfo, Features
    from datasets.builder import ArrowExamplesIterable
    from datasets.iterable_dataset import IterableDataset

    def _generate_tables(**kwargs) -> Iterator[tuple[int, pa.Table]]:
        # This key is unused when training with IterableDataset.
        # Default implementation returns shard id, e.g. parquet row group id.
        for i, rb in enumerate(stream):
            yield i, pa.Table.from_batches([rb], stream.schema)

    # TODO(marko): This is temporary until we stop returning IterableDataset from this function.
    class _IterableDataset(IterableDataset):
        # Diff with datasets.iterable_dataset.IterableDataset:
        # - Removes torch handling which attempts to handle worker processes.
        # - Assumes arrow iterator.
        def __iter__(self):
            from datasets.formatting import get_formatter

            prepared_ex_iterable = self._prepare_ex_iterable_for_iteration()
            if self._formatting and (prepared_ex_iterable.iter_arrow or self._formatting.is_table):
                formatter = get_formatter(self._formatting.format_type, features=self.features)
                iterator = prepared_ex_iterable.iter_arrow()
                for key, pa_table in iterator:
                    yield formatter.format_row(pa_table)
                return

            for key, example in prepared_ex_iterable:
                # no need to format thanks to FormattedExamplesIterable
                yield example

        def map(self, *args, **kwargs):
            # Map constructs a new IterableDataset, so we need to "patch" it
            base = super().map(*args, **kwargs)
            if isinstance(base, IterableDataset):
                # Patch __iter__ to avoid torch handling
                base.__class__ = _IterableDataset  # type: ignore
            return base

    class _ArrowExamplesIterable(ArrowExamplesIterable):
        def __init__(self, generate_tables_fn: Callable[..., Iterator[tuple[int, pa.Table]]], features: Features):
            # NOTE: generate_tables_fn type annotations are wrong, return type must be an iterable of tuples.
            super().__init__(generate_tables_fn, kwargs={})  # type: ignore
            self._features = features

        @property
        def is_typed(self) -> bool:
            return True

        @property
        def features(self) -> Features:
            return self._features

    target_features = Features.from_arrow_schema(_hf_compatible_schema(stream.schema))
    ex_iterable = _ArrowExamplesIterable(_generate_tables, target_features)
    info = DatasetInfo(features=target_features)
    return _IterableDataset(ex_iterable=ex_iterable, info=info)

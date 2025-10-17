from collections import defaultdict
from collections.abc import Callable, Iterable
from functools import reduce

import numpy as np
import pyarrow as pa
from pyarrow import compute as pc


def arange(*args, **kwargs) -> pa.Array:
    return pa.array(np.arange(*args, **kwargs), type=pa.int32())


def zip_tables(tables: Iterable[pa.Table]) -> pa.Table:
    data = []
    names = []
    for table in tables:
        data.extend(table.columns)
        names.extend(table.column_names)
    return pa.Table.from_arrays(data, names=names)


def merge_arrays(*arrays: pa.StructArray) -> pa.StructArray:
    """Recursively merge arrays into nested struct arrays."""
    if len(arrays) == 1:
        return arrays[0]

    nstructs = sum(pa.types.is_struct(a.type) for a in arrays)
    if nstructs == 0:
        # Then we have conflicting arrays and we choose the last.
        return arrays[-1]

    if nstructs != len(arrays):
        raise ValueError("Cannot merge structs with non-structs.")

    data = defaultdict(list)
    for array in arrays:
        if isinstance(array, pa.ChunkedArray):
            array = array.combine_chunks()
        for field in array.type:
            data[field.name].append(array.field(field.name))

    return pa.StructArray.from_arrays([merge_arrays(*v) for v in data.values()], names=list(data.keys()))


def merge_scalars(*scalars: pa.StructScalar) -> pa.StructScalar:
    """Recursively merge scalars into nested struct scalars."""
    if len(scalars) == 1:
        return scalars[0]

    nstructs = sum(pa.types.is_struct(a.type) for a in scalars)
    if nstructs == 0:
        # Then we have conflicting scalars and we choose the last.
        return scalars[-1]

    if nstructs != len(scalars):
        raise ValueError("Cannot merge scalars with non-scalars.")

    data = defaultdict(list)
    for scalar in scalars:
        for field in scalar.type:
            data[field.name].append(scalar[field.name])

    return pa.scalar({k: merge_scalars(*v) for k, v in data.items()})


def null_table(schema: pa.Schema, length: int = 0) -> pa.Table:
    # We add an extra nulls column to ensure the length is correctly applied.
    return pa.table(
        [pa.nulls(length, type=field.type) for field in schema] + [pa.nulls(length)],
        schema=pa.schema(list(schema) + [pa.field("__", type=pa.null())]),
    ).drop(["__"])


def coalesce_all(table: pa.Table) -> pa.Table:
    """Coalesce all columns that share the same name."""
    columns: dict[str, list[pa.Array]] = defaultdict(list)
    for i, col in enumerate(table.column_names):
        columns[col].append(table[i])

    data = []
    names = []
    for col, arrays in columns.items():
        names.append(col)
        if len(arrays) == 1:
            data.append(arrays[0])
        else:
            data.append(pc.coalesce(*arrays))

    return pa.Table.from_arrays(data, names=names)


def join(left: pa.Table, right: pa.Table, keys: list[str], join_type: str) -> pa.Table:
    """Arrow's builtin join doesn't support struct columns. So we join ourselves and zip them in."""
    # TODO(ngates): if join_type == inner, we may have better luck performing two index_in operations since this
    #   also preserves sort order.
    lhs = left.select(keys).add_column(0, "__lhs", arange(len(left)))
    rhs = right.select(keys).add_column(0, "__rhs", arange(len(right)))
    joined = lhs.join(rhs, keys=keys, join_type=join_type).sort_by([(k, "ascending") for k in keys])
    return zip_tables(
        [joined.select(keys), left.take(joined["__lhs"]).drop(keys), right.take(joined["__rhs"]).drop(keys)]
    )


def nest_structs(array: pa.StructArray | pa.StructScalar | dict) -> dict:
    """Turn a struct-like value with dot-separated column names into a nested dictionary."""
    data = {}

    if isinstance(array, pa.StructArray | pa.StructScalar):
        array = {f.name: field(array, f.name) for f in array.type}

    for name in array.keys():
        if "." not in name:
            data[name] = array[name]
            continue

        parts = name.split(".")
        child_data = data
        for part in parts[:-1]:
            if part not in child_data:
                child_data[part] = {}
            child_data = child_data[part]
        child_data[parts[-1]] = array[name]

    return data


def flatten_struct_table(table: pa.Table, separator=".") -> pa.Table:
    """Turn a nested struct table into a flat table with dot-separated names."""
    data = []
    names = []

    def _unfold(array: pa.Array, prefix: str):
        if pa.types.is_struct(array.type):
            if isinstance(array, pa.ChunkedArray):
                array = array.combine_chunks()
            for f in array.type:
                _unfold(field(array, f.name), f"{prefix}{separator}{f.name}")
        else:
            data.append(array)
            names.append(prefix)

    for col in table.column_names:
        _unfold(table[col], col)

    return pa.Table.from_arrays(data, names=names)


def struct_array(fields: list[tuple[str, bool, pa.Array]], /, mask: list[bool] | None = None) -> pa.StructArray:
    return pa.StructArray.from_arrays(
        arrays=[x[2] for x in fields],
        fields=[pa.field(x[0], type=x[2].type, nullable=x[1]) for x in fields],
        mask=pa.array(mask) if mask else mask,
    )


def table(fields: list[tuple[str, bool, pa.Array]], /) -> pa.Table:
    return pa.Table.from_struct_array(struct_array(fields))


def dict_to_table(data) -> pa.Table:
    return pa.Table.from_struct_array(dict_to_struct_array(data))


def dict_to_struct_array(data: dict | pa.StructArray, propagate_nulls: bool = False) -> pa.StructArray:
    """Convert a nested dictionary of arrays to a table with nested structs."""
    if isinstance(data, pa.Array):
        return data
    arrays = [dict_to_struct_array(value) for value in data.values()]
    return pa.StructArray.from_arrays(
        arrays,
        names=list(data.keys()),
        mask=reduce(pc.and_, [pc.is_null(array) for array in arrays]) if propagate_nulls else None,
    )


def struct_array_to_dict[T](array: pa.StructArray, array_fn: Callable[[pa.Array], T] = lambda a: a) -> dict | T:
    """Convert a struct array to a nested dictionary."""
    if not pa.types.is_struct(array.type):
        return array_fn(array)
    if isinstance(array, pa.ChunkedArray):
        array = array.combine_chunks()
    return {field.name: struct_array_to_dict(array.field(i), array_fn=array_fn) for i, field in enumerate(array.type)}


def table_to_struct_array(table: pa.Table) -> pa.StructArray:
    if not table.num_rows:
        return pa.array([], type=pa.struct(table.schema))
    array = table.to_struct_array()
    if isinstance(array, pa.ChunkedArray):
        array = array.combine_chunks()
    return array


def table_from_struct_array(array: pa.StructArray | pa.ChunkedArray):
    if len(array) == 0:
        return null_table(pa.schema(array.type))
    return pa.Table.from_struct_array(array)


def field(value: pa.StructArray | pa.StructScalar, name: str) -> pa.Array | pa.Scalar:
    """Get a field from a struct-like value."""
    if isinstance(value, pa.StructScalar):
        return value[name]
    return value.field(name)


def concat_tables(tables: list[pa.Table]) -> pa.Table:
    """
    Concatenate pyarrow.Table objects, filling "missing" data with appropriate null arrays
    and casting arrays to the most common denominator type that fits all fields.
    """
    if len(tables) == 1:
        return tables[0]
    else:
        return pa.concat_tables(tables, promote_options="permissive")

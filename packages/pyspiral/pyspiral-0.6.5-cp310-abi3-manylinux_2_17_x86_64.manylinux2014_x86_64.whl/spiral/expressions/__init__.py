import builtins
import functools
import operator
import warnings
from typing import Any

import pyarrow as pa

from spiral import _lib, arrow_

from . import http as http
from . import io as io
from . import list_ as list
from . import mp4 as mp4
from . import png as png
from . import qoi as qoi
from . import refs as refs
from . import str_ as str
from . import struct as struct
from . import text as text
from . import tiff as tiff
from .base import Expr, ExprLike, NativeExpr

__all__ = [
    "Expr",
    "add",
    "and_",
    "deref",
    "divide",
    "eq",
    "getitem",
    "gt",
    "gte",
    "http",
    "io",
    "is_not_null",
    "is_null",
    "lift",
    "list",
    "lt",
    "lte",
    "merge",
    "modulo",
    "multiply",
    "negate",
    "neq",
    "not_",
    "or_",
    "pack",
    "aux",
    "ref",
    "refs",
    "scalar",
    "select",
    "str",
    "struct",
    "subtract",
    "tiff",
    "xor",
    "png",
    "qoi",
    "mp4",
    "text",
]

# Inline some of the struct expressions since they're so common
getitem = struct.getitem
merge = struct.merge
pack = struct.pack
select = struct.select
ref = refs.ref
deref = refs.deref


def lift(expr: ExprLike) -> Expr:
    # Convert an ExprLike into an Expr.
    if isinstance(expr, Expr):
        return expr
    if isinstance(expr, NativeExpr):
        return Expr(expr)

    if isinstance(expr, dict):
        # NOTE: we assume this is a struct expression. We could be smarter and be context aware to determine if
        # this is in fact a struct scalar, but the user can always create one of those manually.

        # First we un-nest any dot-separated field names
        expr: dict = arrow_.nest_structs(expr)

        return pack({k: lift(v) for k, v in expr.items()})

    if isinstance(expr, builtins.list):
        return lift(pa.array(expr))

    # Unpack tables and chunked arrays
    if isinstance(expr, pa.Table | pa.RecordBatch):
        expr = expr.to_struct_array()
    if isinstance(expr, pa.ChunkedArray):
        expr = expr.combine_chunks()

    # If the value is struct-like, we un-nest any dot-separated field names
    if isinstance(expr, pa.StructArray | pa.StructScalar):
        # TODO(marko): Figure out what to do with nullable struct arrays when unpacking them.
        #   We need to merge struct validity into the child validity?
        if isinstance(expr, pa.StructArray) and expr.null_count != 0:
            # raise ValueError("lift: cannot lift a struct array with nulls.")
            warnings.warn("found a struct array with nulls", stacklevel=2)
        if isinstance(expr, pa.StructScalar) and not expr.is_valid:
            # raise ValueError("lift: cannot lift a struct scalar with nulls.")
            warnings.warn("found a struct scalar with nulls", stacklevel=2)
        return lift(arrow_.nest_structs(expr))

    if isinstance(expr, pa.Array):
        return Expr(_lib.expr.array_lit(expr))

    # Otherwise, assume it's a scalar.
    return scalar(expr)


def aux(name: builtins.str, dtype: pa.DataType) -> Expr:
    """Create a variable expression referencing a column in the auxiliary table.

    Auxiliary table is optionally given to `Scan#to_record_batches` function when reading only specific keys
    or doing cell pushdown.

    Args:
        name: variable name
        dtype: must match dtype of the column in the auxiliary table.
    """
    return Expr(_lib.expr.aux(name, dtype))


def scalar(value: Any) -> Expr:
    """Create a scalar expression."""
    if not isinstance(value, pa.Scalar):
        value = pa.scalar(value)
    # TODO(marko): Use Vortex scalar instead of passing as array.
    return Expr(_lib.expr.scalar(pa.array([value.as_py()], type=value.type)))


def cast(expr: ExprLike, dtype: pa.DataType) -> Expr:
    """Cast an expression into another PyArrow DataType."""
    expr = lift(expr)
    return Expr(_lib.expr.cast(expr.__expr__, dtype))


def and_(expr: ExprLike, *exprs: ExprLike) -> Expr:
    """Create a conjunction of one or more expressions."""

    return functools.reduce(operator.and_, [lift(e) for e in exprs], lift(expr))


def or_(expr: ExprLike, *exprs: ExprLike) -> Expr:
    """Create a disjunction of one or more expressions."""
    return functools.reduce(operator.or_, [lift(e) for e in exprs], lift(expr))


def eq(lhs: ExprLike, rhs: ExprLike) -> Expr:
    """Create an equality comparison."""
    return operator.eq(lift(lhs), rhs)


def neq(lhs: ExprLike, rhs: ExprLike) -> Expr:
    """Create a not-equal comparison."""
    return operator.ne(lift(lhs), rhs)


def xor(lhs: ExprLike, rhs: ExprLike) -> Expr:
    """Create a XOR comparison."""
    return operator.xor(lift(lhs), rhs)


def lt(lhs: ExprLike, rhs: ExprLike) -> Expr:
    """Create a less-than comparison."""
    return operator.lt(lift(lhs), rhs)


def lte(lhs: ExprLike, rhs: ExprLike) -> Expr:
    """Create a less-than-or-equal comparison."""
    return operator.le(lift(lhs), rhs)


def gt(lhs: ExprLike, rhs: ExprLike) -> Expr:
    """Create a greater-than comparison."""
    return operator.gt(lift(lhs), rhs)


def gte(lhs: ExprLike, rhs: ExprLike) -> Expr:
    """Create a greater-than-or-equal comparison."""
    return operator.ge(lift(lhs), rhs)


def negate(expr: ExprLike) -> Expr:
    """Negate the given expression."""
    return operator.neg(lift(expr))


def not_(expr: ExprLike) -> Expr:
    """Negate the given expression."""
    expr = lift(expr)
    return Expr(_lib.expr.not_(expr.__expr__))


def is_null(expr: ExprLike) -> Expr:
    """Check if the given expression is null."""
    expr = lift(expr)
    return Expr(_lib.expr.is_null(expr.__expr__))


def is_not_null(expr: ExprLike) -> Expr:
    """Check if the given expression is not null."""
    return not_(is_null(expr))


def add(lhs: ExprLike, rhs: ExprLike) -> Expr:
    """Add two expressions."""
    return operator.add(lift(lhs), rhs)


def subtract(lhs: ExprLike, rhs: ExprLike) -> Expr:
    """Subtract two expressions."""
    return operator.sub(lift(lhs), rhs)


def multiply(lhs: ExprLike, rhs: ExprLike) -> Expr:
    """Multiply two expressions."""
    return operator.mul(lift(lhs), rhs)


def divide(lhs: ExprLike, rhs: ExprLike) -> Expr:
    """Divide two expressions."""
    return operator.truediv(lift(lhs), rhs)


def modulo(lhs: ExprLike, rhs: ExprLike) -> Expr:
    """Modulo two expressions."""
    return operator.mod(lift(lhs), rhs)

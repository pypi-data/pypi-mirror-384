import pyarrow as pa
import pyarrow.compute as pc
import re2 as re

from spiral import _lib
from spiral.expressions.base import Expr, ExprLike

# TODO(ngates): we can add a symmetric "ascii" expression namespace in the future if
#  the performance is required.


def substr(expr: ExprLike = None, *, begin: int = 0, end: int | None = None) -> Expr:
    """Slice a string.

    Args:
        expr: The string expression to slice.
        begin: The starting index of the slice.
        end: The ending index of the slice.
    """
    from spiral import expressions as se

    expr = se.lift(expr)
    return Expr(_lib.spql.str.substr(expr.__expr__, begin=begin, end=end))


def extract_regex(pattern: str, *, strings: ExprLike) -> Expr:
    # Extract the first occurrence of a regex pattern from a string.
    raise NotImplementedError


def _extract_regex(arg: pa.Array | pa.Scalar, pattern: str) -> pa.Array | pa.Scalar:
    # Compute the return type based on the regex groups
    m = re.compile(pattern)
    dtype = pa.struct([pa.field(k, type=pa.string()) for k in m.groupindex.keys()])

    if pa.types.is_string(arg.type):
        return pc.extract_regex(arg, pattern=pattern).cast(dtype)

    raise TypeError("Input argument does not have the expected type")

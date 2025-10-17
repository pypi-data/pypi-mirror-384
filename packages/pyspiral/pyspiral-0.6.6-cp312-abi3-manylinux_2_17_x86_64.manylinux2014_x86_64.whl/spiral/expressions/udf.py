import abc

import pyarrow as pa

from spiral import _lib
from spiral.expressions.base import Expr


class BaseUDF:
    def __init__(self, udf):
        self._udf = udf

    def __call__(self, *args) -> Expr:
        """Create an expression that calls this UDF with the given arguments."""
        from spiral import expressions as se

        args = [se.lift(arg).__expr__ for arg in args]
        return Expr(self._udf(args))

    @abc.abstractmethod
    def return_type(self, *input_types: pa.DataType) -> pa.DataType: ...


class UDF(BaseUDF):
    """A User-Defined Function (UDF)."""

    def __init__(self, name: str):
        super().__init__(_lib.expr.udf.create(name, return_type=self.return_type, invoke=self.invoke))

    @abc.abstractmethod
    def invoke(self, *input_args: pa.Array) -> pa.Array: ...


class RefUDF(BaseUDF):
    """A UDF over a single ref cell, and therefore can access the file object."""

    def __init__(self, name: str):
        super().__init__(_lib.expr.udf.create(name, return_type=self.return_type, invoke=self.invoke, scope="ref"))

    @abc.abstractmethod
    def invoke(self, fp, *input_args: pa.Array) -> pa.Array:
        """Invoke the UDF with the given arguments.

        NOTE: The first argument is always the ref cell. All array input args will be sliced to the appropriate row.
        """
        ...

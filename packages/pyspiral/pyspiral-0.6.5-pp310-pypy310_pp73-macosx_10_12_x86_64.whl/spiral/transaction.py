from spiral.core.table import Transaction as CoreTransaction
from spiral.expressions.base import ExprLike


class Transaction:
    """Spiral table transaction.

    IMPORTANT: While transaction can be used to atomically write data to the table,
            it is important that the primary key columns are unique within the transaction.
    """

    def __init__(self, core: CoreTransaction):
        self._core = core

    @property
    def status(self) -> str:
        """The status of the transaction."""
        return self._core.status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self._core.commit()
        else:
            self._core.abort()

    def write(self, expr: ExprLike, *, partition_size_bytes: int | None = None):
        """Write an item to the table inside a single transaction.

        :param expr: The expression to write. Must evaluate to a struct array.
        :param partition_size_bytes: The maximum partition size in bytes.
            If not provided, the default partition size is used.
        """
        from spiral import expressions as se

        expr = se.lift(expr)

        self._core.write(expr.__expr__, partition_size_bytes=partition_size_bytes)

    def drop_columns(self, column_paths: list[str]):
        """
        Drops the specified columns from the table.


        :param column_paths: Fully qualified column names. (e.g., "column_name" or "nested.field").
            All columns must exist, if a column doesn't exist the function will return an error.
        """
        self._core.drop_columns(column_paths)

    def commit(self):
        """Commit the transaction."""
        self._core.commit()

    def abort(self):
        """Abort the transaction."""
        self._core.abort()

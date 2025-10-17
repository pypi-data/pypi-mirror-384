from spiral.expressions.base import Expr, ExprLike


def in_(expr: ExprLike, values: ExprLike) -> Expr:
    """Check if a value is in a list.

    Args:
        expr: The value to check.
        values: The list array expression to check against.
    """
    # `se.list.in_(Array[2, 4], Array[[1, 2], [1, 2]]) -> Array[True, False]`
    from spiral.expressions import lift

    expr = lift(expr)
    return expr.in_(values)


def element_at(expr: ExprLike, index: ExprLike) -> Expr:
    """Get the element at the given index.

    Args:
        expr: The list array expression.
        index: The index to get.
    """
    # e.g. `se.list.element_at([1, 2, 3], 1) -> 2`
    ...
    from spiral import _lib
    from spiral.expressions import lift

    expr = lift(expr)
    index = lift(index)
    return Expr(_lib.expr.list.element_at(expr.__expr__, index.__expr__))


def of(*expr: ExprLike) -> Expr:
    # Creates an array or scalar list from a series of expressions, all values must be of the same type.
    # The expressions must all also have the same length (1 for scalars).
    #
    # e.g. `se.list.of(1+3, 2, 3) -> [4, 2, 3]`
    ...


def zip(*lists: ExprLike) -> Expr:
    # Merge the given lists, with duplicates.
    #
    # e.g. `se.list.merge([1, 2], [3, 4]) -> [(1, 2), (3, 4)]`
    ...


def concat(*lists: ExprLike) -> Expr:
    # Concatenate the given lists. The types of all the lists must be the same.
    #
    # e.g. `se.list.concat([1, 2], [3, 4]) -> [1, 2, 3, 4]`
    ...


def slice_(expr: ExprLike, start: int | None = None, stop: int | None = None) -> Expr:
    # Slice a list.
    #
    # e.g. `se.list.slice_([0, 1, 2], slice(0,2)) -> [0, 1]`
    ...


def length(expr: ExprLike) -> Expr:
    # Get the length of a list.
    #
    # e.g. `se.list.length([1, 2, 3]) -> 3`
    ...

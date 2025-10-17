from spiral.expressions.base import Expr, ExprLike


def field(expr: ExprLike, field_name: str | None = None, tokenizer: str | None = None) -> Expr:
    """Configure a column for text indexing.

    Args:
        expr: An input column. The expression must either evaluate to a UTF-8,
            or, if a `field_name` is provided, to a struct with a field of that name.
        field_name: If provided, the expression must evaluate to a struct with a field of that name.
            The given field will be indexed.
        tokenizer: If provided, the text will be tokenized using the given tokenizer.

    Returns:
        An expression that can be used to construct a text index.
    """
    from spiral import _lib
    from spiral.expressions import getitem, lift, merge, pack

    expr = lift(expr)
    if field_name is None:
        return Expr(_lib.expr.text.field(expr.__expr__, tokenizer))

    child = _lib.expr.text.field(getitem(expr, field_name).__expr__)
    return merge(
        expr,
        pack({field_name: child}),
    )


def find(expr: ExprLike, term: str) -> Expr:
    """Search for a term in the text.

    Args:
        expr: An index field.
        term: The term to search for.

    Returns:
        An expression that can be used in ranking for text search.
    """
    from spiral import _lib
    from spiral.expressions import lift

    expr = lift(expr)
    return Expr(_lib.expr.text.find(expr.__expr__, term))


def boost(expr: ExprLike, factor: float) -> Expr:
    """Boost the relevance of a ranking expression.

    Args:
        expr: Rank by expression.
        factor: The factor by which to boost the relevance.

    Returns:
        An expression that can be used in ranking for text search.
    """
    from spiral import _lib
    from spiral.expressions import lift

    expr = lift(expr)
    return Expr(_lib.expr.text.boost(expr.__expr__, factor))

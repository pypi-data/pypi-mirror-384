from spiral.expressions.base import Expr, ExprLike


def encode(expr: ExprLike) -> Expr:
    """Encode the given expression as a QOI image.

    Args:
        expr: The expression to encode.
            Expects a struct with `pixels`, `width`, `height`, `channels`, `channel_bit_depth` fields.

    Returns:
        The encoded QOI images.
    """
    from spiral import _lib
    from spiral.expressions import lift

    expr = lift(expr)
    return Expr(_lib.expr.img.encode(expr.__expr__, format="qoi"))

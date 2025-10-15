from spiral import _lib
from spiral.expressions.base import Expr, ExprLike


def getitem(expr: ExprLike, field: str) -> Expr:
    """Get field from a struct.

    Args:
        expr: The struct expression to get the field from.
        field: The field to get. Dot-separated string is supported to access nested fields.
    """
    from spiral import expressions as se

    expr = se.lift(expr)
    return Expr(_lib.expr.struct.getitem(expr.__expr__, field))


def pack(fields: dict[str, ExprLike], *, nullable: bool = False) -> Expr:
    """Assemble a new struct from the given named fields.

    Args:
        fields: A dictionary of field names to expressions. The field names will be used as the struct field names.
    """
    from spiral import expressions as se

    return Expr(
        _lib.expr.struct.pack(list(fields.keys()), [se.lift(expr).__expr__ for expr in fields.values()], nullable)
    )


def merge(*structs: "ExprLike") -> Expr:
    """Merge fields from the given structs into a single struct.

    Args:
        *structs: Each expression must evaluate to a struct.

    Returns:
        A single struct containing all the fields from the input structs.
        If a field is present in multiple structs, the value from the last struct is used.
    """
    from spiral import expressions as se

    if len(structs) == 1:
        return se.lift(structs[0])
    return Expr(_lib.expr.struct.merge([se.lift(struct).__expr__ for struct in structs]))


def select(expr: ExprLike, names: list[str] = None, exclude: list[str] = None) -> Expr:
    """Select fields from a struct.

    Args:
        expr: The struct-like expression to select fields from.
        names: Field names to select. If a path contains a dot, it is assumed to be a nested struct field.
        exclude: List of field names to exclude from result. Exactly one of `names` or `exclude` must be provided.
    """
    from spiral import expressions as se

    expr = se.lift(expr)
    return Expr(_lib.expr.struct.select(expr.__expr__, names, exclude))
